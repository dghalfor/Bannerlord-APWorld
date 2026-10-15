from dataclasses import dataclass
from worlds.AutoWorld import PerGameCommonOptions
from Options import Range, OptionGroup, DefaultOnToggle, DeathLink

class KillsRequired(Range):
    """How many zombies you must kill to achieve victory."""
    display_name = "Kills Required"
    range_start = 1
    range_end = 10000
    default = 100

class KillChecksPerZone(Range):
    """
    The highest kill count in each zone that gives a location check.
    Checks are placed every Milestone Interval kills up to this number.
    With a Milestone Interval of 10 and 30 here, each zone has checks at 10, 20 and 30 kills.
    """
    display_name = "Kill Checks Per Zone"
    range_start = 1
    range_end = 500
    default = 30

class MilestoneInterval(Range):
    """
    How many kills in a zone between each location check in that zone.
    If set to 5, you get a check at 5, 10, 15... kills in each zone, up to Kill Checks Per Zone.
    """
    display_name = "Milestone Interval"
    range_start = 1
    range_end = 500
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
    KillChecksPerZone: KillChecksPerZone
    MilestoneInterval: MilestoneInterval
    MaxFoodRandom: MaxFoodRandom
    MaxClothRandom: MaxClothRandom
    MaxMedicRandom: MaxMedicRandom

def create_option_groups():
    return [OptionGroup(name="Goal Options", options=[KillsRequired, KillChecksPerZone, MilestoneInterval, MaxFoodRandom, MaxClothRandom, MaxMedicRandom])]