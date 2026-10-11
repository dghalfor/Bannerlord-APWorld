import logging
from BaseClasses import MultiWorld, Item, Tutorial, Region, Location
from worlds.AutoWorld import World, CollectionState, WebWorld
from typing import Dict

from .Locations import get_location_names, get_location_table 
from .Items import create_item, create_itempool, item_table
from .Options import ProjectZomboidOptions
from .Regions import create_regions

class ProjectZomboidWeb(WebWorld):
    theme = "partyTime"
    tutorials = [Tutorial(
        "Project Zomboid Setup Guide",
        "A guide to setting up Project Zomboid for Archipelago.",
        "English",
        "setup_en.md",
        "setup/en",
        ["Player"]
    )]

class ProjectZomboidWorld(World):
    """
    Project Zomboid is a zombie survival game. Kill zombies to unlock items and progress
    through your Archipelago multiworld. Survive the apocalypse while helping others!
    """

    game = "Project Zomboid"
    item_name_to_id = {name: data.ap_code for name, data in item_table.items()}
    location_name_to_id = get_location_names()
    options_dataclass = ProjectZomboidOptions
    web = ProjectZomboidWeb()
    required_client_version = (0, 6, 5)

    def __init__(self, multiworld: "MultiWorld", player: int):
        super().__init__(multiworld, player)

    def create_items(self):
        self.multiworld.itempool += create_itempool(self)

    def create_item(self, name: str) -> Item:
        return create_item(self, name)
    
    def create_regions(self):
        create_regions(self)

    def fill_slot_data(self) -> Dict[str, object]:
        return {
            "kill_goal": self.options.KillsRequired.value,
            "milestone_interval": self.options.MilestoneInterval.value,
            "maxfoodrandom": self.options.MaxFoodRandom.value,
            "maxclothrandom": self.options.MaxClothRandom.value,
            "maxmedicrandom": self.options.MaxMedicRandom.value,
            "Seed": self.multiworld.seed_name,
            "Slot": self.multiworld.player_name[self.player]
        }
    
    def collect(self, state: "CollectionState", item: "Item") -> bool:
        return super().collect(state, item)
    
    def remove(self, state: "CollectionState", item: "Item") -> bool:
        return super().remove(state, item)