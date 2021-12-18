import nextcord
from nextcord.ext import commands
import logging
import sqlite3
import json
import sys
from typing import Any, Callable, Coroutine, Dict, Union, List, TYPE_CHECKING
import os

if TYPE_CHECKING:
    from bot.utils.sconfig import Sconfig


class MyContext(commands.Context):
    """Replacement for the official commands.Context class
    It allows us to add more methods and properties in the whole bot code"""

    @property
    def bot_permissions(self) -> nextcord.Permissions:
        """Permissions of the bot in the current context"""
        if self.guild:
            # message in a guild
            return self.channel.permissions_for(self.guild.me)
        else:
            # message in DM
            return self.channel.permissions_for(self.bot)

    @property
    def user_permissions(self) -> nextcord.Permissions:
        """Permissions of the message author in the current context"""
        return self.channel.permissions_for(self.author)

    @property
    def can_send_embed(self) -> bool:
        """If the bot has the right permissions to send an embed in the current context"""
        return self.bot_permissions.embed_links


class Gunibot(commands.bot.AutoShardedBot):
    """Bot class, with everything needed to run it"""

    def __init__(self, case_insensitive=None, status=None, beta=False, config: dict = None):
        self.config = config
        # defining allowed default mentions
        ALLOWED = nextcord.AllowedMentions(everyone=False, roles=False)
        # defining intents usage
        intents = nextcord.Intents.default()
        intents.members = True
        # we now initialize the bot class
        super().__init__(command_prefix=self.get_prefix, case_insensitive=case_insensitive, status=status,
                         allowed_mentions=ALLOWED, intents=intents)
        self.log = logging.getLogger("runner") # logs module
        self.beta: bool = beta # if the bot is in beta mode
        self.database = sqlite3.connect('data/database.db') # database connection
        self.database.row_factory = sqlite3.Row
        self._update_database_structure()

    async def get_context(self, message: nextcord.Message, *, cls=MyContext):
        """Get a custom context class when creating one from a message"""
        # when you override this method, you pass your new Context
        # subclass to the super() method, which tells the bot to
        # use the new MyContext class
        return await super().get_context(message, cls=cls)

    @property
    def server_configs(self):
        """Guilds configuration manager"""
        return self.get_cog("ConfigCog").confManager
    
    @property
    def sconfig(self) -> 'Sconfig':
        """Return sconfig configuration manager"""
        return self.get_cog("Sconfig")

    def _update_database_structure(self):
        """Create tables and indexes from 'data/model.sql' file"""
        c = self.database.cursor()
        with open('data/model.sql', 'r', encoding='utf-8') as f:
            c.executescript(f.read())
        for plugin in os.listdir('./plugins/'):
            if plugin[0] != '_':
                if os.path.isfile('./plugins/' + plugin + '/data/model.sql'):
                    with open('./plugins/' + plugin + '/data/model.sql', 'r', encoding='utf-8') as f:
                        c.executescript(f.read())
        c.close()

    async def user_avatar_as(self, user, size=512):
        """Get the avatar of an user, format gif or png (as webp isn't supported by some browsers)"""
        if not hasattr(user, "avatar_url_as"):
            raise ValueError
        try:
            if user.is_avatar_animated():
                return user.display_avatar_as(format='gif', size=size)
            else:
                return user.display_avatar_as(format='png', size=size)
        except Exception as e:
            await self.cogs['Errors'].on_error(e, None)

    class SafeDict(dict):
        def __missing__(self, key):
            return '{' + key + '}'

    async def get_prefix(self, msg):
        """Get a prefix from a message... what did you expect?"""
        prefix = None
        if msg.guild is not None:
            prefix = self.server_configs[msg.guild.id]["prefix"]
        if prefix is None:
            prefix = "?"
        return commands.when_mentioned_or(prefix)(self, msg)

    async def update_config(self, key: str, value):
        """Change a value in the config file
        No undo can be done"""
        self.config[key] = value
        with open("config.json", 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4)
    
    def db_query(self, query: str, args: Union[tuple, dict], *, fetchone: bool=False, returnrowcount: bool=False, astuple: bool=False) -> Union[int, List[dict], dict]:
        """Do any query to the bot database
        If SELECT, it will return a list of results, or only the first result (if fetchone)
        For any other query, it will return the affected row ID if returnrowscount, or the amount of affected rows (if returnrowscount)"""
        cursor = self.database.cursor()
        try:
            cursor.execute(query, args)
            if query.startswith("SELECT"):
                _type = tuple if astuple else dict
                if fetchone:
                    v = cursor.fetchone()
                    result = _type() if v is None else _type(v)
                else:
                    result = list(map(_type, cursor.fetchall()))
            else:
                self.database.commit()
                if returnrowcount:
                    result = cursor.rowcount
                else:
                    result = cursor.lastrowid
        except Exception as e:
            cursor.close()
            raise e
        cursor.close()
        return result

    
    @property
    def _(self) -> Callable[[Any, str], Coroutine[Any, Any, str]]:
        """Translate something"""
        cog = self.get_cog('Languages')
        if cog is None:
            self.log.error("Unable to load Languages cog")
            return lambda *args, **kwargs: args[1]
        return cog.tr
    
    def add_cog(self, cog: commands.Cog):
        """Adds a "cog" to the bot.
        A cog is a class that has its own event listeners and commands.
        
        Parameters
        -----------
        cog: :class:`Cog`
            The cog to register to the bot.

        Raises
        -------
        TypeError
            The cog does not inherit from :class:`Cog`.

        CommandError
            An error happened during loading.
        """
        super().add_cog(cog)
        for module in self.cogs.values():
            if type(cog) != type(module):
                if hasattr(module, 'on_anycog_load'):
                    try:
                        module.on_anycog_load(cog)
                    except:
                        self.log.warning(f"[add_cog]", exc_info=True)
    
    def remove_cog(self, cog: str):
        """Removes a cog from the bot.

        All registered commands and event listeners that the
        cog has registered will be removed as well.

        If no cog is found then this method has no effect.

        Parameters
        -----------
        name: :class:`str`
            The name of the cog to remove.
        """
        super().remove_cog(cog)
        for module in self.cogs.values():
            if type(cog) != type(module):
                if hasattr(module, 'on_anycog_unload'):
                    try:
                        module.on_anycog_unload(cog)
                    except:
                        self.log.warning(f"[remove_cog]", exc_info=True)


class CheckException(commands.CommandError):
    """Exception raised when a custom check failed, to send errors when needed"""
    def __init__(self, id, *args):
        super().__init__(message=f"Custom check '{id}' failed", *args)
        self.id = id

def setup_logger():
    """Create the logger module, used for logs"""
    # on chope le premier logger
    log = logging.getLogger("runner")
    # on défini un formatteur
    format = logging.Formatter(
        "%(asctime)s %(levelname)s: %(message)s", datefmt="[%d/%m/%Y %H:%M]")
    # ex du format : [08/11/2018 14:46] WARNING RSSCog fetch_rss_flux l.288 : Cannot get the RSS flux because of the following error: (suivi du traceback)

    # log vers un fichier
    file_handler = logging.FileHandler("logs/debug.log")
    # tous les logs de niveau DEBUG et supérieur sont evoyés dans le fichier
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(format)

    # log vers la console
    stream_handler = logging.StreamHandler(sys.stdout)
    # tous les logs de niveau INFO et supérieur sont evoyés dans le fichier
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(format)

    # supposons que tu veuille collecter les erreurs sur ton site d'analyse d'erreurs comme sentry
    #sentry_handler = x
    # sentry_handler.setLevel(logging.ERROR)  # on veut voir que les erreurs et au delà, pas en dessous
    # sentry_handler.setFormatter(format)

    # log.debug("message de debug osef")
    # log.info("message moins osef")
    # log.warn("y'a un problème")
    # log.error("y'a un gros problème")
    # log.critical("y'a un énorme problème")

    log.addHandler(file_handler)
    log.addHandler(stream_handler)
    # log.addHandler(sentry_handler)

    return log

CONFIG_OPTIONS: Dict[str, Dict[str, Any]] = {}

if os.path.isfile('./config/global_options.json'):
    with open('./config/global_options.json') as config:
        CONFIG_OPTIONS.update(json.load(config))

for plugin in os.listdir('./plugins/'):
    if plugin[0] != '_':
        if os.path.isfile('./plugins/' + plugin + '/config/options.json'):
            with open('./plugins/' + plugin + '/config/options.json') as config:
                CONFIG_OPTIONS.update(json.load(config))