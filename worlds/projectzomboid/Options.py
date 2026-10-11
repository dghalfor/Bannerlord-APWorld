from dataclasses import dataclass
from worlds.AutoWorld import PerGameCommonOptions
from Options import Range, OptionGroup, DefaultOnToggle, DeathLink

class KillsRequired(Range):
    """How many zombies you must kill to achieve victory."""
    display_name = "Kills Required"
    range_start = 1
    range_end = 10000
    default = 100

class MilestoneInterval(Range):
    """
    How often (in % of the goal) you receive a new location check.
    If set to 1, you get a check every 1%. 
    If set to 5, you get a check every 5%.
    """
    display_name = "Milestone Interval"
    range_start = 1
    range_end = 100
    default = 5

class MaxFoodRandom(Range):
    """Maximum amount of food items given when receiving 'Random Food' Check."""
    display_name = "Maximum Obtainable Food"
    range_start = 1
    range_end = 75
    default = 5

class MaxClothRandom(Range):
    """Maximum amount of Clothing items given when receiving 'Random Cloth' Check."""
    display_name = "Maximum Obtainable Clothing"
    range_start = 1
    range_end = 10
    default = 5

class MaxMedicRandom(Range):
    """Maximum amount of Medical items given when receiving 'Random Medic' Check."""
    display_name = "Maximum Obtainable Medical"
    range_start = 1
    range_end = 10
    default = 5

@dataclass
class ProjectZomboidOptions(PerGameCommonOptions):
    KillsRequired: KillsRequired
    MilestoneInterval: MilestoneInterval
    MaxFoodRandom: MaxFoodRandom
    MaxClothRandom: MaxClothRandom
    MaxMedicRandom: MaxMedicRandom

def create_option_groups():
    return [OptionGroup(name="Goal Options", options=[KillsRequired, MilestoneInterval, MaxFoodRandom, MaxClothRandom, MaxMedicRandom])]