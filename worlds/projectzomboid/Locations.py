from typing import Dict, TYPE_CHECKING
from .Types import LocData

if TYPE_CHECKING:
    from . import ProjectZomboidWorld

def get_location_table(world: "ProjectZomboidWorld") -> Dict[str, LocData]:
    table = {"Kill Goal Reached": LocData(20050110, "Menu")}
    interval = world.options.MilestoneInterval.value
    count = 100 // interval
    
    for i in range(1, count + 1):
        percentage = i * interval
        if percentage > 100:
            break
        name = f"Zombie Milestone {percentage}%"
        table[name] = LocData(20050000 + i, "Project Zomboid")
        
    return table

def get_location_names(world: "ProjectZomboidWorld" = None) -> Dict[str, int]:
    temp_table = {"Kill Goal Reached": LocData(20050110, "Menu")}
    for i in range(1, 101):
        temp_table[f"Zombie Milestone {i}%"] = LocData(20050000 + i, "Project Zomboid")
    return {name: data.ap_code for name, data in temp_table.items()}

def get_total_locations(world: "ProjectZomboidWorld") -> int:
    return len(get_location_table(world))