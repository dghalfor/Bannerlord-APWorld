from typing import TYPE_CHECKING

from BaseClasses import Location, Region

from .Locations import ZONES, get_location_table

if TYPE_CHECKING:
    from . import ProjectZomboidWorld

# Zones the player can always enter (no map item needed). Must match M.START in apzones.lua.
START_ZONES = ("MuldraughNorth", "MuldraughSouth")

ZONE_LINKS = [
    ("BrandenburgNorth", "BrandenburgSouth"),
    ("BrandenburgNorth", "Sanatorium"),
    ("BrandenburgSouth", "KY60"),
    ("BrandenburgSouth", "Sanatorium"),
    ("CrossroadsMall", "DixieHighway"),
    ("CrossroadsMall", "LouisvilleOutskirts"),
    ("DeerheadLake", "FallasLake"),
    ("DeerheadLake", "KY163"),
    ("DeerheadLake", "KY60"),
    ("DeerheadLake", "KY60East"),
    ("DeerheadLake", "Sanatorium"),
    ("DeerheadLake", "WestMapleCountryClub"),
    ("DixieHighway", "LouisvilleOutskirts"),
    ("DixieHighway", "WestPoint"),
    ("EchoCreek", "GunsUnlimited"),
    ("EchoCreek", "KY60"),
    ("EchoCreek", "KY60East"),
    ("EchoCreek", "WadsworthLake"),
    ("Ekron", "GunsUnlimited"),
    ("Ekron", "IrvingtonSpeedway"),
    ("Ekron", "KY60"),
    ("FallasLake", "KY163"),
    ("FallasLake", "KY60East"),
    ("FallasLake", "MuldraughNorth"),
    ("FallasLake", "WestPointoutskirts"),
    ("GunsUnlimited", "IrvingtonSpeedway"),
    ("GunsUnlimited", "KY60"),
    ("GunsUnlimited", "WadsworthLake"),
    ("IroquoisPark", "LouisvilleEvergreenHill"),
    ("IroquoisPark", "LouisvilleFairgrounds"),
    ("IroquoisPark", "LouisvilleGeneralHospital"),
    ("IroquoisPark", "LouisvilleOutskirts"),
    ("IroquoisPark", "LouivilleChapelmountDowns"),
    ("IroquoisPark", "LouivilleStateUniversity"),
    ("IrvingtonNorth", "IrvingtonSouth"),
    ("IrvingtonNorth", "IrvingtonSpeedway"),
    ("IrvingtonNorth", "KY79South"),
    ("IrvingtonNorth", "WadsworthLake"),
    ("IrvingtonSouth", "KY79South"),
    ("IrvingtonSpeedway", "WadsworthLake"),
    ("KY163", "RiversideEast"),
    ("KY163", "WestMapleCountryClub"),
    ("KY163", "WestPointoutskirts"),
    ("KY60", "KY60East"),
    ("KY60", "Sanatorium"),
    ("KY60East", "KY79South"),
    ("KY60East", "MarchRidge"),
    ("KY60East", "MuldraughNorth"),
    ("KY60East", "MuldraughSouth"),
    ("KY60East", "Rosewood"),
    ("KY60East", "RosewoodPrison"),
    ("KY60East", "WadsworthLake"),
    ("KY79South", "MarchRidge"),
    ("KY79South", "Rosewood"),
    ("KY79South", "WadsworthLake"),
    ("LouisvilleDowntown", "LouisvilleGeneralHospital"),
    ("LouisvilleDowntown", "LouisvilleGrandOhioMall"),
    ("LouisvilleDowntown", "LouisvilleKentuckyStatePrison"),
    ("LouisvilleDowntown", "LouisvilleRiverRoad"),
    ("LouisvilleEvergreenHill", "LouisvilleFairgrounds"),
    ("LouisvilleEvergreenHill", "LouisvilleOutskirts"),
    ("LouisvilleFairgrounds", "LouisvilleGeneralHospital"),
    ("LouisvilleFairgrounds", "LouisvilleGrandOhioMall"),
    ("LouisvilleFairgrounds", "LouisvilleOutskirts"),
    ("LouisvilleGeneralHospital", "LouisvilleGrandOhioMall"),
    ("LouisvilleGeneralHospital", "LouisvilleKentuckyStatePrison"),
    ("LouisvilleGeneralHospital", "LouivilleStateUniversity"),
    ("LouisvilleGrandOhioMall", "LouisvilleRiverRoad"),
    ("LouisvilleKentuckyStatePrison", "LouisvilleOilRefineries"),
    ("LouisvilleKentuckyStatePrison", "LouisvilleRiverRoad"),
    ("LouisvilleKentuckyStatePrison", "LouivilleStateUniversity"),
    ("LouisvilleOilRefineries", "LouisvilleRiverRoad"),
    ("LouisvilleOilRefineries", "LouivilleStateUniversity"),
    ("LouisvilleOutskirts", "LouivilleChapelmountDowns"),
    ("LouivilleChapelmountDowns", "LouivilleStateUniversity"),
    ("MarchRidge", "MuldraughNorth"),
    ("MarchRidge", "MuldraughSouth"),
    ("MarchRidge", "Rosewood"),
    ("MuldraughNorth", "MuldraughSouth"),
    ("MuldraughNorth", "WestPoint"),
    ("MuldraughNorth", "WestPointoutskirts"),
    ("RiversideEast", "RiversideWest"),
    ("RiversideEast", "WestMapleCountryClub"),
    ("RiversideWest", "Sanatorium"),
    ("RiversideWest", "WestMapleCountryClub"),
    ("Rosewood", "RosewoodPrison"),
    ("Sanatorium", "WestMapleCountryClub"),
    ("WestPoint", "WestPointoutskirts"),
]

ZONE_TITLES = {key: title for key, title in ZONES}


def map_item_name(zone_key: str) -> str:
    return f"Map of {zone_key}"


def create_zone_regions(world: "ProjectZomboidWorld", menu: Region) -> None:

    player = world.player
    multiworld = world.multiworld
    table = get_location_table(world)

    regions = {}
    for key, title in ZONES:
        region = Region(title, player, multiworld)
        for name, data in table.items():
            if data.region == title:
                region.locations.append(Location(player, name, data.ap_code, region))
        regions[key] = region
        multiworld.regions.append(region)

    for key in START_ZONES:
        menu.connect(regions[key], f"Menu -> {ZONE_TITLES[key]}")

    for a, b in ZONE_LINKS:
        for source, target in ((a, b), (b, a)):
            item = map_item_name(target)
            regions[source].connect(
                regions[target],
                f"{ZONE_TITLES[source]} -> {ZONE_TITLES[target]}",
                lambda state, item=item: state.has(item, player),
            )


def create_regions(world: "ProjectZomboidWorld") -> None:
    player = world.player
    multiworld = world.multiworld

    menu = Region("Menu", player, multiworld)
    for name, data in get_location_table(world).items():
        if data.region == "Menu":
            menu.locations.append(Location(player, name, data.ap_code, menu))
    multiworld.regions.append(menu)

    create_zone_regions(world, menu)

    multiworld.completion_condition[player] = lambda state: state.has("Victory", player)