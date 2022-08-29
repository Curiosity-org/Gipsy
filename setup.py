import os
import shutil
from LRFutils.color import Color
from LRFutils import log

def token_set(force_set = False):
    import config

    if config.token == "<YOUR_DISCORD_TOKEN>" or force_set:
        print(f"\n{Color.Yellow}🔥 You need to set your Discord bot token in config.py.\n{Color.NC}To do so, go on {Color.Blue}https://discord.com/developers/applications{Color.NC}, select your application, go in bot section and copy your token.\nTo create a bot application, please refere to this page: {Color.Blue}https://discord.com/developers/docs/intro{Color.NC}.\nAlso, be sure to anable all intents.\n")
        token = input(f"{Color.Blue}Paste your token here (let empty and press 'enter' to ignore):{Color.NC} ")
        
        if token == "":
            print(f"\n{Color.Red}❌ Setup uncomplete 🙁{Color.NC}")
            return False
        else:
            with open("config.py", "r") as config:
                lines = config.readlines()
            lines[0] = f"token = '{token}'\n"
            with open("config.py", "w") as config:
                config.writelines(lines)
                config.token = token
            print(f"\n{Color.Green}✅ Setup complete!{Color.NC}")
                
    
    return True

if __name__ != "__main__":
    if not os.path.isfile("config.py"):
        log.warn("⛔ The bot is not correctly setup. Running setup script...")
        os.system("python3 setup.py")
        exit()

if __name__ == "__main__":


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

    choice = input(f"\n{Color.Yellow}⚠️ You need to install the bot dependencies. The automatic script will probably upgrade (or rarely downgrade) some python modules already installed on your machine.\n{Color.Blue}🏗️ Do you want to install dependencies? [Y/n]{Color.NC}")
    if choice.lower() in accept:
        print("🏗️ Installing dependencies...")
        os.system("python3 -m pip install -r requirements.txt")
    else:
        print("💀 Dependencies not installed.")

    #############
    # START BOT #
    #############

    if not token_set(): exit()


    choixe = input(f"\n{Color.LightBlue}\n▶️ Do you want to start the bot? [Y/n]{Color.NC} ")
    if choixe.lower() in accept:
        print("▶️ Starting the bot...")
        os.system("python3 start.py")