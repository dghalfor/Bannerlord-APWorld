from BaseClasses import Region, Location
from .Locations import get_location_table
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import ProjectZomboidWorld

def create_regions(world: "ProjectZomboidWorld"):
    menu = Region("Menu", world.player, world.multiworld)
    project_zomboid = Region("Project Zomboid", world.player, world.multiworld)
    loc_table = get_location_table(world)
    
    for name, data in loc_table.items():
        new_loc = Location(world.player, name, data.ap_code, project_zomboid)
        project_zomboid.locations.append(new_loc)
            
    world.multiworld.regions.append(menu)
    world.multiworld.regions.append(project_zomboid)
    menu.connect(project_zomboid)