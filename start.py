#!/usr/bin/env python
# coding=utf-8

import discord
import time
import asyncio
import logging
import json
import sys
import os
import argparse
from shutil import copyfile

# check python version
py_version = sys.version_info
if py_version.major != 3 or py_version.minor < 9:
    print("Vous devez utiliser au moins Python 3.9 !", file=sys.stderr)
    sys.exit(1)

sys.path.append("./bot")
from utils import Gunibot, setup_logger


# Loaded plugins
initial_extensions = []
global_systems = []

docs = open("SUMMARY.md","w+")
docs.write("""# Summary

* [FAQ](docs/FAQ.md)
* [Contribute](docs/CONTRIBUTING.md)
* [License](LICENSE.md)

## Plugins
""")

# Loading global systems
for system in os.listdir('./bot/utils/'):
    if os.path.isfile('./bot/utils/' + system) and system[-3:] == '.py':
        global_systems.append("bot.utils." + system[0:-3])

# Loading plugins
for plugin in os.listdir('./plugins/'):
    if plugin[0] != '_':
        if os.path.isdir('./plugins/' + plugin):
            initial_extensions.append("plugins." + plugin + '.bot.main')
        if os.path.isfile('./plugins/' + plugin + "/docs/user_documentation.md"):
            docs.write("* [" + plugin + "](plugins/" + plugin + "/docs/user_documentation.md)\n")
        

docs.close()

def get_config(path, isBotConfig):
    if not os.path.isfile(path + ".json"):
        copyfile(path + '-example.json', path + '.json')
        if isBotConfig:
            print("TOKEN MISSING: Please, enter your bot token in the config/config.json and restart the bot.")
            return None
    with open(path + ".json") as f:
        conf = json.load(f)
    if isBotConfig:
        if conf["token"] == "Discord token for main bot":
            print("TOKEN MISSING: Please, enter your bot token in the config/config.json and restart the bot.")
            return None
    return conf
        

def main():
    
    conf = get_config('./config/config', isBotConfig = True)
    if conf == None:
        return 1

    for plugin in os.listdir('./plugins/'):
        if plugin[0] != '_':
            if os.path.isfile('./plugins/' + plugin + '/config/require-example.json'):
                conf.update(get_config('./plugins/' + plugin + '/config/require', isBotConfig = False))
    
    print(conf)

    
    client = Gunibot(case_insensitive=True, status=discord.Status(
        "online"), beta=False, config=conf)
    log = setup_logger()
    log.setLevel(logging.DEBUG)
    log.info("Lancement du bot")

    # Here we load our extensions(cogs) listed above in [initial_extensions]
    count = 0
    notloaded = ""
    for extension in global_systems + initial_extensions:
        try:
            client.load_extension(extension)
        except:
            log.exception(f'\nFailed to load extension {extension}')
            notloaded += "\n - " + extension
            count += 1
    if count > 0:
        raise Exception("\n{} modules not loaded".format(count) + notloaded)
    del count

    async def on_ready():
        """Called when the bot is connected to Discord API"""
        print('\nBot connecté')
        print("Nom : "+client.user.name)
        print("ID : "+str(client.user.id))
        if len(client.guilds) < 200:
            serveurs = [x.name for x in client.guilds]
            print(
                "Connecté sur ["+str(len(client.guilds))+"] "+", ".join(serveurs))
        else:
            print("Connecté sur "+str(len(client.guilds))+" serveurs")
        print(time.strftime("%d/%m  %H:%M:%S"))
        print('------')
        await asyncio.sleep(2)

    client.add_listener(on_ready)

    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--beta", help="Run with the beta bot token", action='store_true')
    args = parser.parse_args()

    if args.beta:
        client.beta = True
        client.run(conf["token_beta"])
    else:
        log.debug("Pas d'arguments trouvés!")
        instance_type = "y"
        if instance_type == "y":
            client.run(conf["token"])
        elif instance_type == 'n':
            client.beta = True
            client.run(conf["token_beta"])


if __name__ == "__main__":
    main()
