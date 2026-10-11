import random
from BaseClasses import Item, ItemClassification
from .Types import ItemData, ProjectZomboidItem
from .Locations import get_total_locations
from typing import List, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from . import ProjectZomboidWorld

def create_itempool(world: "ProjectZomboidWorld") -> List[Item]:
    itempool: List[Item] = []
    victory = create_item(world, "Victory")
    world.multiworld.get_location("Kill Goal Reached", world.player).place_locked_item(victory)
    total_locations = get_total_locations(world)
    fillers = ["Random Food", "Random Cloth", "Random Medic"]
    for _ in range(total_locations - 1):
        itempool.append(create_item(world, random.choice(fillers)))
    return itempool

def create_item(world: "ProjectZomboidWorld", name: str) -> Item:
    data = item_table[name]
    return ProjectZomboidItem(name, data.classification, data.ap_code, world.player)

item_table = {
    "Victory": ItemData(20050007, ItemClassification.progression),
    "Random Food": ItemData(20050001, ItemClassification.filler),
    "Random Cloth": ItemData(20050002, ItemClassification.filler),
    "Random Medic": ItemData(20050003, ItemClassification.filler),
    "500 cigarettes": ItemData(20050005, ItemClassification.filler),
}