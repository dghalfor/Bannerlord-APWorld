#!/usr/bin/env python3
"""
Archipelago Project Zomboid Client
Cross-platform client for Project Zomboid integration with Archipelago
"""

import sys
import os
import platform

if __name__ == "__main__":
    import ModuleUpdate
    ModuleUpdate.update()

import asyncio
import json
import Utils
import time
import logging

from CommonClient import CommonContext, server_loop, gui_enabled, logger, CommandProcessor, get_base_parser
from NetUtils import ClientStatus

ZOMBOID_LUA_PATH = os.path.join(os.path.expanduser("~"), "Zomboid", "Lua")

os.makedirs(ZOMBOID_LUA_PATH, exist_ok=True)

pz_msgs = os.path.join(ZOMBOID_LUA_PATH, "pztalk.sock")
ap_msgs = os.path.join(ZOMBOID_LUA_PATH, "aptalk.sock")
sv_file = os.path.join(ZOMBOID_LUA_PATH, "apsave.json")


class ProjectZomboidCommandProcessor(CommandProcessor):
    def __init__(self, ctx):
        self.ctx = ctx
    
    def output(self, text: str):
        """Helper function to abstract logging to the CommonClient UI"""
        logger.info(text)
    
    def _cmd_pzconnect(self):
        """Force a reconnection handshake with Project Zomboid."""
        if self.ctx.pz_connected:
            self.output("Project Zomboid is already connected.")
        else:
            self.output("Attempting to reconnect to Project Zomboid...")
            asyncio.create_task(init_communication_files_async(self.ctx))
        return True
    
    def _cmd_pzstatus(self):
        """Show current Project Zomboid connection status and progress."""
        if not self.ctx.pz_connected:
            self.output("Project Zomboid: Not Connected")
        else:
            self.output(f"Project Zomboid: Connected")
            self.output(f"Kill Progress: {self.ctx.current_killcnt} out of {self.ctx.kill_goal} ({(self.ctx.current_killcnt/max(self.ctx.kill_goal, 1)*100):.1f}%)")
            self.output(f"Seed: {self.ctx.seed_name}")
        return True


class ProjectZomboidContext(CommonContext):
    game = "Project Zomboid"
    items_handling = 0b011 
    location_base = 20050000
    command_processor = ProjectZomboidCommandProcessor

    def __init__(self, server_address, password):
        super().__init__(server_address, password)
        self.kill_goal = 0
        self.current_killcnt = 0 
        self.seed_name = None
        self.victory_sent = False
        self.auth_finished = asyncio.Event()
        self.full_save_data = {}
        self.last_save_time = 0
        self.max_food = 20
        self.max_cloth = 5
        self.max_medic = 5
        self.milestone_percent = 5 
        self.checked_milestones = set()
        self.pz_connected = False

    async def server_auth(self, password_requested: bool = False):
        """Standard AP Auth flow: asks for password if the server requires it."""
        if password_requested and not self.password:
            await super().server_auth(password_requested)
        await self.get_username()
        await self.send_connect()

    def on_package(self, cmd: str, args: dict):
        super().on_package(cmd, args)
        if cmd == "Connected":
            slot_data = args.get("slot_data", {})
            self.kill_goal = slot_data.get("kill_goal", 100)
            self.milestone_percent = slot_data.get("milestone_interval", 5)
            self.max_food = slot_data.get("maxfoodrandom", 20)
            self.max_cloth = slot_data.get("maxclothrandom", 5)
            self.max_medic = slot_data.get("maxmedicrandom", 5)
            self.checked_milestones = set(args.get("checked_locations", []))
            server_seed = slot_data.get("Seed") or args.get("seed_name")
            if server_seed:
                self.seed_name = str(server_seed)
                self.load_seed_data()
                self.auth_finished.set()
            logger.info(f"Connected to Project Zomboid world")
            logger.info(f"Goal: Kill {self.kill_goal} zombies")

        if cmd == "ReceivedItems":
            for item in args['items']:
                item_name = self.item_names.lookup_in_slot(item.item)
                if item_name == "Random Food":
                    self.send_to_lua(f"AP_RAND_FOOD_{self.max_food}")
                elif item_name == "Random Cloth":
                    self.send_to_lua(f"AP_RAND_CLOTH_{self.max_cloth}")
                elif item_name == "Random Medic":
                    self.send_to_lua(f"AP_RAND_MEDIC_{self.max_medic}")
                elif item_name == "Victory":
                    self.send_to_lua("AP_WON_YIPPEEEEE")

    def load_seed_data(self):
        if os.path.exists(sv_file):
            try:
                with open(sv_file, "r") as f:
                    self.full_save_data = json.load(f)
                seed_dict = self.full_save_data.get(self.seed_name, {})
                self.current_killcnt = sum(data.get("killcnt", 0) for data in seed_dict.values())
                logger.info(f"Loaded save data from seed {self.seed_name}")
                logger.info(f"Current progress: {self.current_killcnt} out of {self.kill_goal} kills")
            except Exception as e:
                logger.error(f"Error loading save data: {e}")
                self.full_save_data = {}

    def update_uid_kills(self, uid, count):
        if self.seed_name not in self.full_save_data:
            self.full_save_data[self.seed_name] = {}
        
        new_val = int(count)
        current_uid_data = self.full_save_data[self.seed_name].get(uid, {})
        old_val = current_uid_data.get("killcnt", 0)

        if new_val > old_val:
            self.full_save_data[self.seed_name][uid] = {"killcnt": new_val}
            self.current_killcnt = sum(d.get("killcnt", 0) for d in self.full_save_data[self.seed_name].values())
            logger.info(f"Kill progress: {self.current_killcnt}/{self.kill_goal} ({(self.current_killcnt/max(self.kill_goal, 1)*100):.1f}%)")
            
            self.check_milestones()

            if time.time() - self.last_save_time > 2:
                self.save_seed_data()
                self.last_save_time = time.time()

    def check_milestones(self):
        if self.kill_goal <= 0: 
            return
        progress_pct = (self.current_killcnt / self.kill_goal) * 100
        milestones_count = int(progress_pct // self.milestone_percent)

        new_checks = []
        for i in range(1, milestones_count + 1):
            loc_id = self.location_base + i
            if loc_id not in self.checked_milestones:
                new_checks.append(loc_id)
                self.checked_milestones.add(loc_id)

        if new_checks:
            asyncio.create_task(self.send_msgs([{"cmd": "LocationChecks", "locations": new_checks}]))

    def save_seed_data(self):
        if not self.seed_name:
            return
        try:
            with open(sv_file, "w") as f:
                json.dump(self.full_save_data, f, indent=4)
        except Exception as e:
            logger.error(f"Save Error: {e}")
    
    def send_to_lua(self, message: str):
        try:
            with open(ap_msgs, 'a') as f:
                f.write(message + "\n")
        except Exception as e:
            logger.error(f"Error writing to Lua: {e}")
    
    def make_gui(self):
        from kvui import GameManager
        
        class ProjectZomboidManager(GameManager):
            base_title = "Archipelago Project Zomboid Client"
        
        return ProjectZomboidManager


# --- Logic Loops ---

async def init_communication_files_async(ctx):
    """Initialize communication files and wait for Project Zomboid to connect"""
    if not os.path.exists(pz_msgs):
        with open(pz_msgs, 'w') as f: 
            f.write("")
    with open(ap_msgs, 'w') as f: 
        f.write("AP_READY\n")
    
    logger.info(f"Awaiting connection from Project Zomboid...")
    last_mtime = 0
    timeout = 0
    
    while not ctx.exit_event.is_set():
        if os.path.exists(pz_msgs):
            mtime = os.path.getmtime(pz_msgs)
            if mtime > last_mtime:
                with open(pz_msgs, 'r+') as f:
                    data = f.read().strip()
                    f.seek(0)
                    f.truncate(0)
                if data == "PZ_READY": 
                    logger.info("Project Zomboid connected")
                    ctx.pz_connected = True
                    return
                last_mtime = mtime
        
        timeout += 0.5
        if timeout >= 30:
            logger.info("Still waiting for Project Zomboid... Make sure the mod is installed and the game is running.")
            timeout = 0
            
        await asyncio.sleep(0.5)


async def file_polling_loop(ctx):
    last_mtime = 0
    while not ctx.exit_event.is_set():
        if ctx.pz_connected and os.path.exists(pz_msgs):
            mtime = os.path.getmtime(pz_msgs)
            if mtime > last_mtime:
                with open(pz_msgs, 'r+') as f:
                    data = f.read().strip()
                    f.seek(0)
                    f.truncate(0)
                
                if data == "PZ_QUIT":
                    logger.warning("Project Zomboid disconnected")
                    ctx.pz_connected = False
                    await ctx.send_msgs([{"cmd": "StatusUpdate", "status": ClientStatus.CLIENT_CONNECTED}])
                    logger.info("Use /pzconnect to try reconnecting.")
                elif data.startswith("KILLCNT:"):
                    parts = data.split(":")
                    if len(parts) == 3:
                        ctx.update_uid_kills(parts[2], parts[1])
                last_mtime = mtime
        await asyncio.sleep(0.5)


async def check_victory(ctx):
    """Monitor for victory condition and send goal status when reached"""
    while not ctx.victory_sent and not ctx.exit_event.is_set():
        if ctx.kill_goal > 0 and ctx.current_killcnt >= ctx.kill_goal:
            await ctx.send_msgs([{"cmd": "StatusUpdate", "status": ClientStatus.CLIENT_GOAL}])
            ctx.victory_sent = True
        await asyncio.sleep(1)


async def main(args):
    """Main entry point for the client"""
    ctx = ProjectZomboidContext(args.connect, args.password)
    ctx.auth = args.name
    
    ctx.server_task = asyncio.create_task(server_loop(ctx), name="server loop")

    asyncio.create_task(init_communication_files_async(ctx))
    
    if gui_enabled:
        ctx.run_gui()
    ctx.run_cli()

    await asyncio.gather(
        file_polling_loop(ctx),
        check_victory(ctx),
        ctx.exit_event.wait()
    )

    logger.info("Saving current data to save file...")
    ctx.save_seed_data()
    logger.info("Closing client...")
    
    try:
        with open(ap_msgs, 'w') as f: 
            f.write("AP_QUIT\n")
    except: 
        pass
    
    await ctx.shutdown()


def launch():
    """Launch function for the Archipelago Launcher to call"""
    import colorama
    
    Utils.init_logging("ProjectZomboidClient", exception_logger="Client")
    
    parser = get_base_parser(description="Archipelago Project Zomboid Client")
    parser.add_argument('--name', default=None, help="Slot Name to connect as.")
    parser.add_argument("url", nargs="?", help="Archipelago connection url")
    args = parser.parse_args()

    if args.url:
        from CommonClient import handle_url_arg
        args = handle_url_arg(args, parser)

    colorama.just_fix_windows_console()
    
    asyncio.run(main(args))
    colorama.deinit()


if __name__ == "__main__":
    launch()