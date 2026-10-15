from typing import Dict, List, NamedTuple, TYPE_CHECKING
from .Types import LocData

if TYPE_CHECKING:
    from . import ProjectZomboidWorld

LOCATION_BASE = 20050000
ZONE_KILL_OFFSET = 1000
MAX_KILLS = 500  # highest kill count a check can be placed at; KillChecksPerZone must not exceed it
ZONE_ID_STRIDE = 1000


def zone_kill_tiers(interval: int, kill_checks_per_zone: int) -> list:
    interval = max(1, interval)
    tiers = list(range(interval, kill_checks_per_zone + 1, interval))
    if kill_checks_per_zone > 0 and (not tiers or tiers[-1] != kill_checks_per_zone):
        tiers.append(kill_checks_per_zone)
    return tiers


ZONES = [
    ("KY79South", "KY-79 South"),
    ("IrvingtonSouth", "Irvington South"),
    ("IrvingtonNorth", "Irvington North"),
    ("IrvingtonSpeedway", "Irvington Speedway"),
    ("WadsworthLake", "Wadsworth Lake"),
    ("EchoCreek", "Echo Creek"),
    ("GunsUnlimited", "Guns Unlimited"),
    ("Ekron", "Ekron"),
    ("KY60", "KY-60"),
    ("BrandenburgSouth", "Brandenburg South"),
    ("BrandenburgNorth", "Brandenburg North"),
    ("Sanatorium", "Sanatorium"),
    ("WestMapleCountryClub", "West Maple Country Club"),
    ("RiversideWest", "Riverside West"),
    ("RiversideEast", "Riverside East"),
    ("KY163", "KY-163"),
    ("DeerheadLake", "Deerhead Lake"),
    ("FallasLake", "Fallas Lake"),
    ("KY60East", "KY-60 East"),
    ("RosewoodPrison", "Rosewood Prison"),
    ("Rosewood", "Rosewood"),
    ("MarchRidge", "March Ridge"),
    ("MuldraughSouth", "Muldraugh South"),
    ("MuldraughNorth", "Muldraugh North"),
    ("WestPointoutskirts", "West Point outskirts"),
    ("WestPoint", "West Point"),
    ("DixieHighway", "Dixie Highway"),
    ("CrossroadsMall", "Crossroads Mall"),
    ("LouisvilleOutskirts", "Louisville Outskirts"),
    ("LouivilleChapelmountDowns", "Louiville - Chapelmount Downs"),
    ("LouivilleStateUniversity", "Louiville State University"),
    ("LouisvilleEvergreenHill", "Louisville - Evergreen Hill"),
    ("IroquoisPark", "Iroquois Park"),
    ("LouisvilleFairgrounds", "Louisville - Fairgrounds"),
    ("LouisvilleGrandOhioMall", "Louisville - Grand Ohio Mall"),
    ("LouisvilleGeneralHospital", "Louisville General Hospital"),
    ("LouisvilleOilRefineries", "Louisville - Oil Refineries"),
    ("LouisvilleRiverRoad", "Louisville - River Road"),
    ("LouisvilleKentuckyStatePrison", "Louisville - Kentucky State Prison"),
    ("LouisvilleDowntown", "Louisville - Downtown"),
]


def zone_location_name(title: str, kills: int) -> str:
    return f"{title} - {kills} Kills"


def zone_location_id(zone_index: int, kills: int) -> int:
    return LOCATION_BASE + ZONE_KILL_OFFSET + zone_index * ZONE_ID_STRIDE + kills

ITEM_CHECK_BASE = 20200000

class ItemCheck(NamedTuple):
    key: str
    label: str
    region: str
    offset: int

ITEM_CHECKS: List[ItemCheck] = [
    ItemCheck("muldraugh_north_1", "Muldraugh North Cache", "Muldraugh North", 1),
    ItemCheck("muldraugh_south_1", "Muldraugh South - Stale Pizza", "Muldraugh South", 2),
]


def item_check_location_name(check: ItemCheck) -> str:
    return f"Found: {check.label}"


def item_check_location_id(check: ItemCheck) -> int:
    return ITEM_CHECK_BASE + check.offset


# For the client: the "CHECK:<key>" message payload -> location ID.
KEY_TO_LOCATION_ID: Dict[str, int] = {c.key: item_check_location_id(c) for c in ITEM_CHECKS}


def get_location_table(world: "ProjectZomboidWorld") -> Dict[str, LocData]:
    table = {"Kill Goal Reached": LocData(20050110, "Menu")}
    tiers = zone_kill_tiers(world.options.MilestoneInterval.value, world.options.KillChecksPerZone.value)
    for zi, (key, title) in enumerate(ZONES):
        for kills in tiers:
            table[zone_location_name(title, kills)] = LocData(zone_location_id(zi, kills), title)
    for check in ITEM_CHECKS:
        table[item_check_location_name(check)] = LocData(item_check_location_id(check), check.region)
    return table


def get_location_names(world: "ProjectZomboidWorld" = None) -> Dict[str, int]:
    names = {"Kill Goal Reached": 20050110}
    for zi, (key, title) in enumerate(ZONES):
        for kills in range(1, MAX_KILLS + 1):
            names[zone_location_name(title, kills)] = zone_location_id(zi, kills)
    for check in ITEM_CHECKS:
        names[item_check_location_name(check)] = item_check_location_id(check)
    return names


def get_total_locations(world: "ProjectZomboidWorld") -> int:
    return len(get_location_table(world))