<div align=center>

# 👻 Gipsy

</div>

Gipsy is a multifunction bot managed by the [Gunivers](https://gunivers.net) community.

# 👋 Invite

This bot is public and open-source. It mean that anyone can host the bot and propose you an invite link. The following link is the official one, an instance of the bot hosted by Gunivers itself.

<div align=center>

👋 [Invite Gipsy](http://utip.io/s/1yhs7W)

</div>

You can also invite the bot in beta version to enjoy the latest features added. Be careful though: the bot in beta version may contain security breaches and many bugs. It may also stop working suddenly and for long periods. If you want to invite it though, [click here](https://discordapp.com/oauth2/authorize?client_id=813836349147840513&scope=bot&permissions=8)


# 🔌 Installation (self host)

First, install [git CLI](https://git-scm.com/book/en/v2/Getting-Started-The-Command-Line)

Please use at least **Python 3.9** to run this project.

Open a terminal and go in the folder you want to install the bot. Then, enter

```bash
git clone -recursive https://github.com/Gunivers/Gipsy
```

This command will install Gipsy and the official plugins. If you don't want these plugins, you can simply remove the `-recursive` from the command.

Then, install all the dependencies by running

```bash
pip install -r requirements.txt
```

or, if you are running Gipsy 2.x, simply run `python setup.py` and say yes when it ask if you want to install the dependencies.


> **Note**
> 
> If you updated Gipsy from 1.x to 2.x, you may noticed that plugin files disapeared from your installation. To fix that, empty the `plugins` folder (it may remain `__pycache__` data) and run the command `git submodule update`


> **Note**
>
> This branch is the rewrite of the beta version and require special steps to checkout for developers.
> To checkout this branch, commit and push your changes to the plugins repo, and then run the command `git submodule deinit plugins`. This will remove all the files from the `plugins/` folder.
> You can then checkout the branch safely.
> 
> To go back to the `beta` branch and get the submodule back, you need to follow these special steps :
> - checkout to the beta branch
> - run `rm -r plugins/*` to remove python cached files
> - run `git submodule init` to reinitialize the submodule
> - run `git submodule update` to get the submodule back


# 📚 About

Gipsy is a Discord bot whose first objective is to meet the expectations of the Gunivers community. However, if we want to create new features, we might as well let those who might be interested in them enjoy them !
You can invite the bot, learn what it can do and follow its evolution.

## ⚡ Features

> TODO

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
