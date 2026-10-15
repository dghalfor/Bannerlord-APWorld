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

from ..Locations import ZONES, LOCATION_BASE, ZONE_KILL_OFFSET, ZONE_ID_STRIDE, KEY_TO_LOCATION_ID

ZOMBOID_LUA_PATH = os.path.join(os.path.expanduser("~"), "Zomboid", "Lua")

os.makedirs(ZOMBOID_LUA_PATH, exist_ok=True)

pz_msgs = os.path.join(ZOMBOID_LUA_PATH, "pztalk.txt")
ap_msgs = os.path.join(ZOMBOID_LUA_PATH, "aptalk.txt")


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
        self.max_food = 20
        self.max_cloth = 5
        self.max_medic = 5
        self.milestone_percent = 5
        self.checked_milestones = set()
        self.zone_kills = {}
        self.zone_baseline = {}  # zone key -> highest kill count already checked in it
        self.zone_thresholds = {}  # zone key -> {kills: location id}, from the locations in this slot
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
            self.zone_thresholds = self.find_zone_thresholds(
                set(args.get("missing_locations", [])) | set(args.get("checked_locations", [])))
            self.zone_baseline = {zone: max(t) for zone, t in self.find_zone_thresholds(
                set(args.get("checked_locations", []))).items()}
            self.max_food = slot_data.get("maxfoodrandom", 20)
            self.max_cloth = slot_data.get("maxclothrandom", 5)
            self.max_medic = slot_data.get("maxmedicrandom", 5)
            self.checked_milestones = set(args.get("checked_locations", []))
            server_seed = slot_data.get("Seed") or args.get("seed_name")
            if server_seed:
                self.seed_name = str(server_seed)
                self.auth_finished.set()
            logger.info(f"Connected to Project Zomboid world")
            logger.info(f"Goal: Kill {self.kill_goal} zombies")
            if not self.pz_connected:
                asyncio.create_task(init_communication_files_async(self))

        if cmd == "ReceivedItems":
            for i, item in enumerate(args['items']):
                idx = args.get("index", 0) + i  # the game skips indexes it already received
                item_name = self.item_names.lookup_in_slot(item.item)
                if item_name == "Random Food":
                    self.send_to_lua(f"ITEM:{idx}:AP_RAND_FOOD_{self.max_food}")
                elif item_name == "Random Cloth":
                    self.send_to_lua(f"ITEM:{idx}:AP_RAND_CLOTH_{self.max_cloth}")
                elif item_name == "Random Medic":
                    self.send_to_lua(f"ITEM:{idx}:AP_RAND_MEDIC_{self.max_medic}")
                elif item_name == "Victory":
                    self.send_to_lua(f"ITEM:{idx}:AP_WON_YIPPEEEEE")
                elif item_name and item_name.startswith("Map of "):
                    self.send_to_lua(f"ITEM:{idx}:{item_name}")

    def update_kills(self, total):
        """The game saves the kill total in the world; we only move forward."""
        if total > self.current_killcnt:
            self.current_killcnt = total
            logger.info(f"Kill progress: {self.current_killcnt}/{self.kill_goal} ({(self.current_killcnt/max(self.kill_goal, 1)*100):.1f}%)")

    @staticmethod
    def find_zone_thresholds(location_ids):
        """Works out each zone's kill-count locations from the location ids that exist in this slot."""
        thresholds = {}
        for loc_id in location_ids:
            zone_index, kills = divmod(loc_id - LOCATION_BASE - ZONE_KILL_OFFSET, ZONE_ID_STRIDE)
            if kills > 0 and 0 <= zone_index < len(ZONES):
                thresholds.setdefault(ZONES[zone_index][0], {})[kills] = loc_id
        return thresholds

    def update_zone_kills(self, zone, count):
        """Per-zone kill counts, saved in the world; we only move forward."""
        if count <= self.zone_kills.get(zone, 0):
            return
        self.zone_kills[zone] = count
        new_checks = []
        for needed, loc_id in self.zone_thresholds.get(zone, {}).items():
            if count >= needed and loc_id not in self.checked_milestones:
                new_checks.append(loc_id)
                self.checked_milestones.add(loc_id)
        if new_checks:
            logger.info(f"{zone}: {count} kills")
            asyncio.create_task(self.send_msgs([{"cmd": "LocationChecks", "locations": new_checks}]))

    def handle_item_check(self, key):
        """A check token was picked up in game: CHECK:<key> -> the matching location.

        The game re-sends every found check each time it connects, so anything already
        checked is skipped here.
        """
        loc_id = KEY_TO_LOCATION_ID.get(key)
        if loc_id is None:
            logger.warning(f"Unknown item check from the game: {key}")
            return
        if loc_id in self.checked_milestones or loc_id in self.checked_locations:
            return
        if loc_id not in self.server_locations:
            # e.g. the seed was generated before this check existed
            logger.warning(f"Item check '{key}' is not part of this multiworld; ignoring it.")
            return
        self.checked_milestones.add(loc_id)
        logger.info(f"Item check found: {key}")
        asyncio.create_task(self.send_msgs([{"cmd": "LocationChecks", "locations": [loc_id]}]))

    def send_to_lua(self, message: str):
        logger.info(f"[debug] to game: {message}")  # temporary
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
        f.write(f"AP_READY:{ctx.seed_name or ''}:{ctx.auth}\n")

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
                    # Archipelago is the source of truth: ask it to resend every item.
                    # The game skips the ones it already has.
                    await ctx.send_msgs([{"cmd": "Sync"}])
                    # Seed the game's per-zone counts from the checks already made, in case the
                    # world was started over. The game only uses it for zones it has no count for.
                    if ctx.zone_baseline:
                        ctx.send_to_lua("ZONEBASE:" + ",".join(f"{z}={n}" for z, n in ctx.zone_baseline.items()))
                    # Then ask the game for its saved kill total and per-zone counts.
                    ctx.send_to_lua("RESEND")
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
                    # KILLCNT:<total>[:<zone>=<count>,<zone>=<count>...]
                    parts = data.split(":")
                    if len(parts) in (2, 3):
                        ctx.update_kills(int(parts[1]))
                        if len(parts) == 3:
                            for entry in parts[2].split(","):
                                zone, _, count = entry.partition("=")
                                ctx.update_zone_kills(zone, int(count))
                elif data.startswith("CHECK:"):
                    ctx.handle_item_check(data[len("CHECK:"):].strip())
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

    if gui_enabled:
        ctx.run_gui()
    ctx.run_cli()

    await asyncio.gather(
        file_polling_loop(ctx),
        check_victory(ctx),
        ctx.exit_event.wait()
    )

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