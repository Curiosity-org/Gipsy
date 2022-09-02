import yaml
import os

#################
# GLOBAL CONFIG #
#################

global_config = {}

def reload_config():
    """This function read the core/default_config.yaml file and store it in a dictionnary.
    Then, it update the dict' using all the plugins/<plguin>/config.yaml files.
    Finally, it update the dict' using the config.yaml file wich is defined by the user.
    Each step overwrite the previus one."""

    global global_config

    with open("core/default_config.yaml", "r") as f:
        global_config.update(yaml.safe_load(f))

    if os.path.isfile("config.yaml"):
        with open("config.yaml") as f:
            global_config.update(yaml.safe_load(f))

    for plugin in os.listdir(f'plugins'):

        if os.path.isfile(f'plugins/' + plugin + "/config.yaml"):
            with open(f'plugins/' + plugin + "/config.yaml") as f:
                global_config.update(yaml.safe_load(f))

if global_config == {}:
    reload_config()