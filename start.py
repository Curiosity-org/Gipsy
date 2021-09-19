#!/usr/bin/env python
# coding=utf-8

import discord
import time
import asyncio
import logging
import json
import sys
import os

# check python version
py_version = sys.version_info
if py_version.major != 3 or py_version.minor < 9:
    print("Vous devez utiliser au moins Python 3.9 !", file=sys.stderr)
    sys.exit(1)

from utils import Gunibot, setup_logger


# Loaded plugins
initial_extensions = []
docs = open("SUMMARY.md","w+")
docs.write("""# Summary

* [FAQ](FAQ.md)
* [Contribute](CONTRIBUTING.md)
* [License](LICENSE.md)

## Plugins
""")

for plugin in os.listdir('./plugins/'):
    if plugin[0] != '_':
        if os.path.isdir('./plugins/' + plugin):
            initial_extensions.append(plugin + '.main')
        if os.path.isfile('./plugins/' + plugin) and plugin[-3:] == '.py':
            initial_extensions.append(plugin[0:-3])
        if os.path.isfile('./plugins/' + plugin + "/documentation.md"):
            docs.write("* [" + plugin + "](plugins/" + plugin + "/documentation.md)\n")
        

def main():
    with open('config.json') as f:
        conf = json.load(f)
    client = Gunibot(case_insensitive=True, status=discord.Status(
        "online"), beta=False, config=conf)
    log = setup_logger()
    log.setLevel(logging.DEBUG)
    log.info("Lancement du bot")

    # Here we load our extensions(cogs) listed above in [initial_extensions]
    count = 0
    for extension in initial_extensions:
        try:
            client.load_extension("plugins."+extension)
        except:
            log.exception(f'\nFailed to load extension {extension}')
            count += 1
        if count > 0:
            raise Exception("\n{} modules not loaded".format(count))
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

    if (not len(sys.argv) < 2):
        if (sys.argv[1].lower() == "stable"):
            client.run(conf["token"])
        elif (sys.argv[1].lower() == "beta"):
            client.beta = True
            client.run(conf["token_beta"])
    else:
        log.debug("Pas d'arguments trouvés!")
        instance_type = input("Lancer la version stable ? (y/n) ").lower()
        if instance_type == "y":
            client.run(conf["token"])
        elif instance_type == 'n':
            client.beta = True
            client.run(conf["token_beta"])


if __name__ == "__main__":
    main()
