<div align=center>

# 👻 Gipsy

[![GitHub commit activity](https://img.shields.io/github/commit-activity/m/Gunivers/Gipsy?color=orange&label=average%20contributions&style=for-the-badge)](#) [![GitHub closed pull requests](https://img.shields.io/github/issues-pr-closed/Gunivers/Gipsy?color=orange&style=for-the-badge)](#) [![GitHub Repo stars](https://img.shields.io/github/stars/Gunivers/Gipsy?color=orange&style=for-the-badge)](#) [![GitHub Sponsors](https://img.shields.io/github/sponsors/Gunivers?color=orange&style=for-the-badge)](#)

[![Discord](https://img.shields.io/discord/125723125685026816?color=blue&label=Discord&style=for-the-badge&logo=Discord)](https://discord.gg/E8qq6tN)

</div>

Gipsy is a multifunction bot managed by the [Gunivers](https://gunivers.net) community.

# 👋 Invite

This bot is public and open-source. It mean that anyone can host the bot and propose you an invite link. The following link is the official one, an instance of the bot hosted by Gunivers itself.

<div align=center>

[![](https://img.shields.io/badge/Invite-Gipsy-blue?style=for-the-badge&logo=Discord)](http://utip.io/s/1yhs7W)

</div>

You can also invite the bot in beta version to enjoy the latest features added. Be careful though: the bot in beta version may contain security breaches and many bugs. It may also stop working suddenly and for long periods. If you want to invite it though, [click here](https://discordapp.com/oauth2/authorize?client_id=813836349147840513&scope=bot&permissions=8)


# 🔌 Installation (self host)

You need to install by yourself:

- [git CLI](https://git-scm.com/book/en/v2/Getting-Started-The-Command-Line)
- [Python 3.10](https://www.python.org/downloads/release/python-3100/)
- [`pipenv` package](https://pypi.org/project/pipenv/).

Open a terminal and go in the folder you want to install the bot. Then, enter

```bash
git clone https://github.com/Gunivers/Gipsy
```

Then go in the Gipsy directory
```bash
cd Gipsy
```

(optional) By default, you will be on the beta version which is the most recent one, but it might can contain bugs. If you want to switch on the stable version, run
```bash
git checkout master
```

Then start the python environment:
```bash
pipenv shell
```

Install the dependencies
```bash
pipenv install
```

And finally, run the setup script and follow the instructions:
```bash
python3 setup.py
```
The script will ask you if you want to run the bot at the end.

The next times, to run the bot, you will only have to run
```bash
python3 start.py
```

Also, if you want to install new plugins, you can find the official plugin list [here](https://github.com/Gunivers/Gipsy-plugins)

> **Note**
> 
> If you updated Gipsy from 1.x to 2.x, you may noticed that plugin files disapeared from your installation. To fix that, empty the `plugins` folder (it may remain `__pycache__` data) and run the command `git submodule update`

# 📚 About

Gipsy is a Discord bot whose first objective is to meet the expectations of the Gunivers community. However, if we want to create new features, we might as well let those who might be interested in them enjoy them !
You can invite the bot, learn what it can do and follow its evolution.

## ⚡ Features

This bot is modular, it means that features are provided by plugins. By default, it have 3 plugins:
- Misc: containding some simple out of context commands
- Wormhole: which allow to connect 2 text channels
- RSS: which allow to follow the news from your favorite website, twitter account or youtube channel

There is also several other plugins available here:

<div align=center>

🔌[Official plugins repo](https://github.com/Gunivers/Gipsy-plugins)

</div>

> **Note**
> 
> You are a plugin developer? You can create a Pull Request on the plugins repository to make your plugin officially supported by Gipsy

# ➕ Additional info

## 🔄️ Add a Gunibot service on linux

You can create a service for your gunibot instance, which will allow you to start and stop the bot using commands like `systemctl start gunibot`, or `service gunibot stop`. The bot will also reboot automatically after a crash.

For this method, you need to have screen installed, which allows you to create detached shell:

`sudo apt install screen` (debian)

First, create a file in /etc/systemd/system, where `gunibot` is the name of your service:

/etc/systemd/system/gunibot.service
```ini
[Unit]
Description=Gunibot
After=network.target

[Service]
WorkingDirectory=[/path/to/your/gunibot/folder]

User=[the user which owns the gunibot folder]
Group=[the user group which owns the gunibot folder]

Restart=always

ExecStart=/usr/bin/screen -dmS gunibot python3.9 start.py --beta

ExecStop=/usr/bin/screen -p 0 -S gunibot -X eval 'stuff "^C"'

[Install]
WantedBy=multi-user.target
```

Make sure to replace `WorkingDirectory`, `User` and `Group` with the correct value. You can also set the description as you want.

In the `ExecStart` command, we create a detached screen with -dmS parameters:

`-dmS name     Start as daemon: Screen session in detached mode.` (from screen help)

In the `ExecStop` command, we write the input "^C" in the screen session, to stop the bot.

You can replace gunibot in the `ExecStart` and `ExecStop` command with any value, this is going to be the name of the screen.

To access the bot command line, you can simply use `screen -r gunibot` where gunibot is the name of the screen.

You can use these commands to start and stop the bot :

* start the bot: `sudo systemctl start gunibot` or `sudo service gunibot start` where gunibot is the name of the .service file
* stop the bot: `sudo systemctl stop gunibot` or `sudo service gunibot stop`
* reload the bot: `sudo systemctl restart gunibot` or `sudo service gunibot restart`
