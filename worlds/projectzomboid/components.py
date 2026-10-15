from worlds.LauncherComponents import Component, components, Type, launch_subprocess
 
 
def launch_client(*args):
    """Start the Project Zomboid client"""
    from .client import launch
    launch_subprocess(launch, name="ProjectZomboidClient", args=args)
 
 
components.append(
    Component(
        "Project Zomboid Client",
        func=launch_client,
        component_type=Type.CLIENT,
        game_name="Project Zomboid",
        supports_uri=True,
    )
)