import yaml
import os

#################
# GLOBAL CONFIG #
#################

global_config = {}

def reload_config():
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