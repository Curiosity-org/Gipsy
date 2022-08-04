#!/usr/bin/env python
# coding=utf-8

import discord, time, asyncio, logging, json, sys, os, argparse
from   shutil import copyfile
import core.log as log
from LRFutils.color import Color
import yaml

################################################################################
# Checking files
################################################################################

log.info(f'🔎 Checking files...')
if not os.path.isfile("config.py"):
    log.error(f"🤕 Oops, I don't find the 'config.py' file.")
    if os.path.isfile("config_example.py"):
        copyfile("config_example.py", "config.py")
        log.info(f"✅ I created the 'config.py' file for you, don't forget to fill the information in it 😘")
    else: log.warn(f"🤔 Hmmm, I don't even find the 'config_example.py' file. You should re-install me 😅")
    exit()

import config
from core.i18n import I18N
from core.bot import client, Sconfig

################################################################################
# Loading plugins
################################################################################

log.info(f'🔄️ Loading plugins...')
plugins = []
discord_plugins = []

# Checkin files in plugins folder
for plugin in os.listdir('./plugins/'):
    if not plugin.startswith('_'):
        if os.path.isdir('./plugins/' + plugin):
            
            # Adding plugin to the lists
            plugins.append("plugins." + plugin)
            discord_plugins.append("plugins." + plugin + '.discord')

# Loading translations
I18N.load()

modules = map(__import__, plugins)
for ext in discord_plugins: client.load_extension(ext)

################################################################################
# Loading config
################################################################################

log.info(f'📃 Reading config...')
if config.bot_token == '<YOUR_TOKEN>':
    log.error(f"🤕 Oops, you need to fill the 'token' variable in the 'config.py' file.")
    exit()

################################################################################
# Starting bot
################################################################################

log.info("✅ Everything seems ok, I'm ready!")
print(f"""{Color.Blue}
  ___  __  ____  ____  _  _    ____     __  
 / __)(  )(  _ \/ ___)( \/ )  (___ \   /  \ 
( (_ \ )(  ) __/\___ \ )  /    / __/ _(  0 )
 \___/(__)(__)  (____/(__/    (____)(_)\__/ 
{Color.NC}\n""")

try: client.run(config.bot_token)
except discord.errors.LoginFailure as e:
    log.error("🤕 Arg, discord refuse the token you gave me.")

