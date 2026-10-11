#!/usr/bin/env python3
if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    import ModuleUpdate
    ModuleUpdate.update()
    from worlds.projectzomboid.client import launch
    launch()