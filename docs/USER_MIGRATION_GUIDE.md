# User migration guide

## Migrating 1.3 -> 1.4

Save the following files:
- `data/database.db`
- `configs/*`
- `config/config.json`

Then, replace all the files with the new ones.

Now, place your previous `data/database.db` and  `configs/*` at their respective place and open the `config/config.json` file in a text editor.

In a terminal, go in the bot directory and run `python3 setup.py`. The script will ask you the informations previously contained in the `config/config.json` file. Once the script is done, you can start the bot with `python3 start.py`.