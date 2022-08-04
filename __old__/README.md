# Gipsy

Gipsy is a multifunction bot managed by the [Gunivers](https://gunivers.net) community.

Please use at least **Python 3.9** to run this project.

Use `pip install -r requirements.txt` in the directory to install dependencies.

## **Description**

Gipsy is a Discord bot whose first objective is to meet the expectations of the Gunivers community. However, if we want to create new features, we might as well let those who might be interested in them enjoy them !
You can invite the bot, learn what it can do and follow its evolution.

## **Invite**

You can invite the bot by [![link](uploads/32dc3a164398f67799a6cfe7206c12ca/link.png) clicking here.](http://utip.io/s/1yhs7W)

You can also invite the bot in beta version to enjoy the latest features added. Be careful though: the bot in beta version may contain security holes and many bugs. It may also stop working suddenly and for long periods. If you want to invite it though, [click here](https://discordapp.com/oauth2/authorize?client_id=813836349147840513&scope=bot&permissions=8)

## **Features**


## **Add a Gunibot service on linux**

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
