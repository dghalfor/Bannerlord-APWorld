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
    world.multiworld.get_location("Louisville - River Road - 3 Kills", world.player).place_locked_item(victory)
    total_locations = get_total_locations(world)
    for name in zone_item_names:
        itempool.append(create_item(world, name))

    filler_count = total_locations - len(itempool) - 1
    fillers = ["Random Food", "Random Cloth", "Random Medic"]
    for _ in range(filler_count):
        itempool.append(create_item(world, random.choice(fillers)))
    return itempool

def create_item(world: "ProjectZomboidWorld", name: str) -> Item:
    data = item_table[name]
    return ProjectZomboidItem(name, data.classification, data.ap_code, world.player)

item_table = {
    "Victory": ItemData(20050007, ItemClassification.progression),

    #filler
    "Random Food": ItemData(20050001, ItemClassification.filler),
    "Random Cloth": ItemData(20050002, ItemClassification.filler),
    "Random Medic": ItemData(20050003, ItemClassification.filler),
    "500 cigarettes": ItemData(20050005, ItemClassification.filler),

    #zones
    "Map of KY79South": ItemData(20050100, ItemClassification.progression),
    "Map of IrvingtonSouth": ItemData(20050101, ItemClassification.progression),
    "Map of IrvingtonNorth": ItemData(20050102, ItemClassification.progression),
    "Map of IrvingtonSpeedway": ItemData(20050103, ItemClassification.progression),
    "Map of WadsworthLake": ItemData(20050104, ItemClassification.progression),
    "Map of EchoCreek": ItemData(20050105, ItemClassification.progression),
    "Map of GunsUnlimited": ItemData(20050106, ItemClassification.progression),
    "Map of Ekron": ItemData(20050107, ItemClassification.progression),
    "Map of KY60": ItemData(20050108, ItemClassification.progression),
    "Map of BrandenburgSouth": ItemData(20050109, ItemClassification.progression),
    "Map of BrandenburgNorth": ItemData(20050110, ItemClassification.progression),
    "Map of Sanatorium": ItemData(20050111, ItemClassification.progression),
    "Map of WestMapleCountryClub": ItemData(20050112, ItemClassification.progression),
    "Map of RiversideWest": ItemData(20050113, ItemClassification.progression),
    "Map of RiversideEast": ItemData(20050114, ItemClassification.progression),
    "Map of KY163": ItemData(20050115, ItemClassification.progression),
    "Map of DeerheadLake": ItemData(20050116, ItemClassification.progression),
    "Map of FallasLake": ItemData(20050117, ItemClassification.progression),
    "Map of KY60East": ItemData(20050118, ItemClassification.progression),
    "Map of RosewoodPrison": ItemData(20050119, ItemClassification.progression),
    "Map of Rosewood": ItemData(20050120, ItemClassification.progression),
    "Map of MarchRidge": ItemData(20050121, ItemClassification.progression),
    "Map of MuldraughSouth": ItemData(20050122, ItemClassification.progression),
    "Map of MuldraughNorth": ItemData(20050123, ItemClassification.progression),
    "Map of WestPointoutskirts": ItemData(20050124, ItemClassification.progression),
    "Map of WestPoint": ItemData(20050125, ItemClassification.progression),
    "Map of DixieHighway": ItemData(20050126, ItemClassification.progression),
    "Map of CrossroadsMall": ItemData(20050127, ItemClassification.progression),
    "Map of LouisvilleOutskirts": ItemData(20050128, ItemClassification.progression),
    "Map of LouivilleChapelmountDowns": ItemData(20050129, ItemClassification.progression),
    "Map of LouivilleStateUniversity": ItemData(20050130, ItemClassification.progression),
    "Map of LouisvilleEvergreenHill": ItemData(20050131, ItemClassification.progression),
    "Map of IroquoisPark": ItemData(20050132, ItemClassification.progression),
    "Map of LouisvilleFairgrounds": ItemData(20050133, ItemClassification.progression),
    "Map of LouisvilleGrandOhioMall": ItemData(20050134, ItemClassification.progression),
    "Map of LouisvilleGeneralHospital": ItemData(20050135, ItemClassification.progression),
    "Map of LouisvilleOilRefineries": ItemData(20050136, ItemClassification.progression),
    "Map of LouisvilleRiverRoad": ItemData(20050137, ItemClassification.progression),
    "Map of LouisvilleKentuckyStatePrison": ItemData(20050138, ItemClassification.progression),
    "Map of LouisvilleDowntown": ItemData(20050139, ItemClassification.progression),
    
}
zone_item_names: List[str] = [name for name in item_table if name.startswith("Map of ")]