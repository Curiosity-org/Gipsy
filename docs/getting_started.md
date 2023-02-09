# 👋 Getting Started

## 📥 Get it on your Discord server

::::{tab-set}
:::{tab-item} 💌 Invite Gunivers' instance

<div align=center>

You can simply invite the bot instance hosted by the Gunivers community itself by clicking on the button below!

```{button-link} http://utip.io/s/1yhs7W
:color: primary
:align: center
:shadow:

Invite the bot on your server
```

Alternatively, you can invite the beta version by [clicking here](https://discordapp.com/oauth2/authorize?client_id=813836349147840513&scope=bot)

</div>

```{admonition} If you use the beta version
:class: important

If you invite the beta version, you will be able to test the latest features added to the bot. However, the bot in beta version may contain security holes and many bugs. It may also stop working suddenly and for long periods.
```

:::
:::{tab-item} ⚙️ Self-host the bot

1. Create a Discord application and add a bot to it by following [this tutorial](https://discord.com/developers/docs/getting-started).

2. Install [Python 3.9](https://www.python.org/downloads/release/python-390/) or higher.

3. Install [Git CLI](https://git-scm.com/book/en/v2/Getting-Started-The-Command-Line)

4. Open a terminal and go where you want to install it

      ```bash
      cd /path/to/installation
      ```

5. Clone the repository

      ```bash
      git clone https://github.com/Gunivers/Gipsy
      ```

6. (Optional) Create a virtual environment with 

      ```
      python3.9 -m venv venv
      ```
      and activate it with
      ```
      source venv/bin/activate # Linux.
      venv\Scripts\activate # Windows
      ```

7. Install dependencies
8. 
      ```
      pip install -r requirements.txt
      ```

9.  Run the setup script and answer the questions.

      ```bash
      python setup.py
      ```

10. Start the bot
      ```bash
      python start.py
      ```

11. In the logs, find a line like this:

      ```
      09/02/2023 at 19:59:32 | [INFO] ID : 786546781919641600
      ```

12. Copy the ID an place it in the following URL (replace the underscores with the ID):

      ```
      https://discord.com/oauth2/authorize?scope=bot&client_id=__________________
      ```
   
13. Open the URL in your browser and invite the bot to your server.

:::
::::
## 👶 First steps

In a channel where the bot can read and write messages, follow the instructions below.

1. Define your language with the command `@gipsy config language <en|fr>`
2. Define the prefix with the command `@gipsy config prefix <prefix>`. 
   Exemple: type `@gipsy config prefix !` and then `!ping`

```{note}
In this documentation, we will use `@gipsy` as the prefix because it always work, even if another prefix is set.
```
3. Type `@gipsy config` to see the rest of the option you can configure. To edit a config option, enter `@gipsy config <option> <value>`
4. Type `@gipsy help` to see the list of commands.
5. Enjoy!