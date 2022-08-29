import os
import shutil
from LRFutils.color import Color
from LRFutils import log

accept = ["y", "yes", "yeah", "ye"]
refuse = ["n", "no", "nope", "nah"]

def token_set(force_set = False):
    import config

    if config.core.token == "<YOUR_DISCORD_TOKEN>" or force_set:
        print(f"\n🔑 You need to set your Discord bot token in config.py.\n   To do so, go on {Color.Blue}https://discord.com/developers/applications{Color.NC}, select your application, go in bot section and copy your token.\n   To create a bot application, please refere to this page: {Color.Blue}https://discord.com/developers/docs/intro{Color.NC}.\n   Also, be sure to anable all intents.\n")
        
        with open("config.py", "r") as conf_file:
            lines = conf_file.readlines()
        if "token" not in lines[2] : 
            log.warn("🤕 The config.py file as been manually modified. To avoid overwriting something, this script will not edit the file. Please edit the file manually or delete it and run again this script.")
            return False
        else:
            token = input(f"{Color.Blue}🔑 Paste your token here (let empty and press 'enter' to ignore):{Color.NC} ")
            if token == "":
                print(f"\n{Color.Red}❌ Setup uncomplete 🙁{Color.NC}")
                return False

            lines[2] = f"    token = '{token}'\n"
            with open("config.py", "w") as conf_file:
                conf_file.writelines(lines)
            print("   Token successfully edited!")
        config.token = token
        print(f"\n{Color.Green}✅ Setup complete!{Color.NC}")
                
    
    return True

if __name__ != "__main__":
    if not os.path.isfile("config.py"):
        log.warn("⛔ The bot is not correctly setup. Running setup script...")
        os.system("python3 setup.py")
        exit()

if __name__ == "__main__":

    #####################
    # SQUASHING CONFIGS #
    #####################

    if os.path.isfile("config.py"):
        print("\n📃 Config.py already exist. If you want to update it, please delect it and restart the setup tool.")
    else: 
        print("\n📦 Squashing configuration files...")

        shutil.copyfile("config-example.py", "config.py")

        with open("config.py", "r") as f:
            before = []
            started = False
            for line in f:
                if not started: before.append(line)
                if line.startswith("# Plugin config"): started = True

        with open("config.py","w+") as config:
            for line in before: config.write(line)
            config.write("\n")

            for plugin in os.listdir(f'plugins'):
                if os.path.isfile(f'plugins/' + plugin + "/config.py"):
                    config.write(f"\nclass {plugin}():\n")
                    for line in open(f'plugins/' + plugin + "/config.py", "r"):
                        config.write("    " + line)

    ########################
    # INSTALL DEPENDENCIEs #
    ########################

    choice = input(f"\n🏗️ You need to install the bot dependencies. The automatic script will probably upgrade (or rarely downgrade) some python modules already installed on your machine.\n{Color.Blue}\n🏗️ Do you want to install dependencies? [y/N]{Color.NC}")
    if choice.lower() in accept:
        print("🏗️ Installing dependencies...")
        os.system("python3 -m pip install -r requirements.txt")
    else:
        print("   Dependencies not installed.")

    #############
    # START BOT #
    #############

    if not token_set(): exit()

    choixe = input(f"\n▶️ Your config.py file is probably incomplete, which can break some features.\n\n{Color.Blue}▶️ Do you want to start the bot anyway? [Y/n]{Color.NC} ")
    if choixe.lower() not in refuse:
        print("   Starting the bot...\n--------------------------------------------------------------------------------")
        os.system("python3 start.py")