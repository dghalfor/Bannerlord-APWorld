from typing import NamedTuple, Optional
from BaseClasses import Location, Item, ItemClassification

class ProjectZomboidLocation(Location):
    game = "Project Zomboid"

class ProjectZomboidItem(Item):
    game = "Project Zomboid"

class ItemData(NamedTuple):
    ap_code: Optional[int]
    classification: ItemClassification

class LocData(NamedTuple):
    ap_code: Optional[int]
    region: str