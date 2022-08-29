import os
import shutil
from LRFutils.color import Color

accept = ["y", "yes", "yeah", "oui", "", "allez pourquoi pas, soyons fou"]

#####################
# SQUASHING CONFIGS #
#####################

print("\n📦 Squashing configuration files...")

if not os.path.isfile("config.py"): shutil.copyfile("config-example.py", "config.py")

with open("config.py", "r") as f:
    before = []
    started = False
    for line in f:
        if not started: before.append(line)
        if line.startswith("# Plugin documentation"): started = True

with open("config.py","w+") as config:
    for line in before: config.write(line)
    config.write("\n")

    for plugin in os.listdir(f'plugins'):
        if os.path.isfile(f'plugins/' + plugin + "/config.py"):
            config.write(f"\n# {plugin}\n")
            for line in open(f'plugins/' + plugin + "/config.py", "r"):
                config.write(line)

########################
# INSTALL DEPENDENCIEs #
########################

choice = input(f"\n{Color.Blue}🏗️ Do you want to install dependencies? [Y/n]\n{Color.Yellow}⚠️ It will upgrade (or rarely downgrade) some python modules already installed on your machine.{Color.NC}\n")
if choice.lower() in accept:
    print("🏗️ Installing dependencies...")
    os.system("python3 -m pip install -r requirements.txt")
else:
    print("💀 Dependencies not installed.")

print(f"\n{Color.Green}✅ Installation complete!{Color.NC}")

#############
# START BOT #
#############

import config

if config.token == "<YOUR_DISCORD_TOKEN>":
    print(f"\n{Color.Yellow}🔥 You need to set your Discord bot token in config.py.\n{Color.NC}To do so, go on {Color.Blue}https://discord.com/developers/applications{Color.NC}, select your application, go in bot section and copy your token.\nTo create a bot application, please refere to this page: {Color.Blue}https://discord.com/developers/docs/intro{Color.NC}.\nAlso, be sure to anable all intents.\n")
    exit()

choixe = input(f"\n{Color.LightBlue}▶️ Do you want to start the bot? [Y/n]{Color.NC}\n")
if choixe.lower() in accept:
    print("▶️ Starting the bot...")
    os.system("python3 start.py")