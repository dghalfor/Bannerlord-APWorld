from worlds.LauncherComponents import Component, components, Type, launch_subprocess

def launch_client():
    """Launch the Project Zomboid client"""
    from .client import launch
    launch()


components.append(
    Component(
        "Project Zomboid Client",
        func=launch_client,
        component_type=Type.CLIENT,
    )
)