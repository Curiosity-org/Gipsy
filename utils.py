"""
Ce programme est régi par la licence CeCILL soumise au droit français et
respectant les principes de diffusion des logiciels libres. Vous pouvez
utiliser, modifier et/ou redistribuer ce programme sous les conditions
de la licence CeCILL diffusée sur le site "http://www.cecill.info".
"""

import json
import os
import sqlite3
import sys
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Dict, List, Optional, Union

import discord
from discord import app_commands
from discord.ext import commands

from core import config
from core import setup_logger

if TYPE_CHECKING:
    from bot.utils.sconfig import Sconfig


class MyContext(commands.Context):
    """Replacement for the official commands.Context class
    It allows us to add more methods and properties in the whole bot code"""

    @property
    def bot_permissions(self) -> discord.Permissions:
        """Permissions of the bot in the current context"""
        if self.guild:
            # message in a guild
            return self.channel.permissions_for(self.guild.me)
        # message in DM
        return self.channel.permissions_for(self.bot)

    @property
    def user_permissions(self) -> discord.Permissions:
        """Permissions of the message author in the current context"""
        return self.channel.permissions_for(self.author)

    @property
    def can_send_embed(self) -> bool:
        """If the bot has the right permissions to send an embed in the current context"""
        return self.bot_permissions.embed_links

# defining allowed default mentions
ALLOWED = discord.AllowedMentions(everyone=False, roles=False)

class Gunibot(commands.bot.AutoShardedBot):
    """
    Classe principale du bot
    """

    def __init__(self, case_insensitive=None, status=None, beta=False):
        # defining intents usage
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        # we now initialize the bot class
        super().__init__(
            command_prefix=self.get_prefix,
            case_insensitive=case_insensitive,
            status=status,
            allowed_mentions=ALLOWED,
            intents=intents,
        )
        self.log = setup_logger('core')  # logs module
        self.beta: bool = beta  # if the bot is in beta mode
        self.database = sqlite3.connect("data/database.db")  # database connection
        self.database.row_factory = sqlite3.Row
        self.cog_icons = {}  # icons for cogs
        self._update_database_structure()
        # app commands
        self.app_commands_list: Optional[list[discord.app_commands.AppCommand]] = None

    # pylint: disable=arguments-differ
    async def get_context(self, message: discord.Message, *, cls=MyContext):
        """
        Récupérer le contexte d'une commande

        :param message: Le message
        :param cls: La classe du contexte
        :return: Le contexte
        """
        # when you override this method, you pass your new Context
        # subclass to the super() method, which tells the bot to
        # use the new MyContext class
        return await super().get_context(message, cls=cls)

    @property
    def server_configs(self):
        """
        Récupérer la configuration du serveur

        :return: La configuration du serveur
        """
        return self.get_cog("ConfigCog").conf_manager

    @property
    def sconfig(self) -> "Sconfig":
        """
        Récupérer le gestionnaire de configuration du serveur

        :return: Le gestionnaire de configuration du serveur
        """
        return self.get_cog("Sconfig")

    def _update_database_structure(self):
        """
        Mettre à jour la structure de la base de données

        :return: None
        """
        cursor = self.database.cursor()
        with open("data/model.sql", "r", encoding="utf-8") as file:
            cursor.executescript(file.read())

        # pylint: disable=redefined-outer-name
        for plugin in os.listdir("./plugins/"):
            if plugin[0] != "_":
                if os.path.isfile("./plugins/" + plugin + "/data/model.sql"):
                    with open(
                        "./plugins/" + plugin + "/data/model.sql", "r", encoding="utf-8"
                    ) as file:
                        cursor.executescript(file.read())
        cursor.close()

    async def user_avatar_as(
        self,
        user: Union[discord.User, discord.Member],
        size=512,
    ):
        """
        Récupérer l'avatar d'un utilisateur au format PNG ou GIF

        :param user: L'utilisateur
        :param size: La taille de l'avatar
        :return: L'avatar
        """
        # the avatar always exist, returns the URL to the default one
        avatar = user.display_avatar.with_size(size)
        if avatar.is_animated():
            return avatar.with_format("gif")
        else:
            return avatar.with_format("png")

    class SafeDict(dict):
        """
        ???
        """
        def __missing__(self, key):
            return "{" + key + "}"

    # pylint: disable=arguments-differ
    async def get_prefix(self, msg):
        """
        Récupérer le préfixe du bot pour un message donné

        :param msg: Le message
        :return: Le préfixe
        """
        prefix = None
        if msg.guild is not None:
            prefix = self.server_configs[msg.guild.id]["prefix"]
        if prefix is None:
            prefix = "?"
        return commands.when_mentioned_or(prefix)(self, msg)

    def db_query(
        self,
        query: str,
        args: Union[tuple, dict],
        *,
        fetchone: bool = False,
        returnrowcount: bool = False,
        astuple: bool = False,
    ) -> Union[int, List[dict], dict]:
        """
        Faire une requête à la base de données du bot

        Si SELECT, retourne une liste de résultats, ou seulement le premier résultat (si fetchone)
        Pour toute autre requête, retourne l'ID de la ligne affectée, ou le nombre de lignes
        affectées (si returnrowscount)

        :param query: La requête à faire
        :param args: Les arguments de la requête
        :param fetchone: Si la requête est un SELECT, retourne seulement le premier résultat
        :param returnrowcount: Si la requête est un INSERT, UPDATE ou DELETE, retourne le nombre
            de lignes affectées
        :param astuple: Si la requête est un SELECT, retourne les résultats sous forme de tuple
        :return: Le résultat de la requête
        """

        cursor = self.database.cursor()
        try:
            cursor.execute(query, args)
            if query.startswith("SELECT"):
                _type = tuple if astuple else dict
                if fetchone:
                    row = cursor.fetchone()
                    result = _type() if row is None else _type(row)
                else:
                    result = list(map(_type, cursor.fetchall()))
            else:
                self.database.commit()
                if returnrowcount:
                    result = cursor.rowcount
                else:
                    result = cursor.lastrowid
        except Exception as exception:
            cursor.close()
            raise exception
        cursor.close()
        return result

    @property
    def _(self) -> Callable[..., Awaitable[str]]:
        """Translate something
        
        :param context: The guild, channel or user for which to translate
        :param key: The key to translate
        :param kwargs: The arguments to pass to the translation

        :return: The translated string
        """
        cog = self.get_cog('Languages')
        if cog is None:
            self.log.error("Unable to load Languages cog")
            return lambda *args, **kwargs: args[1]
        return cog.tr

    async def fetch_app_commands(self):
        "Populate the app_commands_list attribute from the Discord API"
        self.app_commands_list = await self.tree.fetch_commands(guild=None)

    async def fetch_app_command_by_name(self, name: str) -> Optional[app_commands.AppCommand]:
        "Get a specific app command from the Discord API"
        if self.app_commands_list is None:
            await self.fetch_app_commands()
        for command in self.app_commands_list:
            if command.name == name:
                return command
        return None

    async def get_command_mention(self, command_name: str):
        """
        Get how a command should be mentionned (either app-command mention or raw name)
        """
        if command := await self.fetch_app_command_by_name(command_name.split(' ')[0]):
            return f"</{command_name}:{command.id}>"
        if command := self.get_command(command_name):
            return f"`{command.qualified_name}`"
        self.log.error("Trying to mention invalid command: %s", command_name)
        return f"`{command_name}`"

    # pylint: disable=arguments-differ
    async def add_cog(self, cog: commands.Cog, icon=None):
        """
        Ajouter un cog au bot

        :param cog: Le cog à ajouter
        :param icon: L'icône du cog

        :return: None

        :raises TypeError: Le cog n'hérite pas de commands.Cog
        :raises CommandError: Une erreur est survenue lors du chargement
        """
        self.cog_icons.update({cog.qualified_name.lower(): icon})

        await super().add_cog(cog)
        for module in self.cogs.values():
            if not isinstance(cog, type(module)):
                if hasattr(module, "on_anycog_load"):
                    try:
                        module.on_anycog_load(cog)
                    # pylint: disable=broad-exception-caught
                    except BaseException:
                        self.log.warning("[add_cog]", exc_info=True)

    def get_cog_icon(self, cog_name):
        """
        Récupérer l'icône d'un cog

        :param cog_name: Le nom du cog
        :return: L'icône du cog
        """
        return self.cog_icons.get(cog_name.lower())

    async def remove_cog(self, cog: str):
        """
        Supprimer un cog du bot

        Toutes les commandes et listeners enregistrés par le cog seront supprimés

        :param cog: Le cog à supprimer
        :return: None
        """
        await super().remove_cog(cog)
        for module in self.cogs.values():
            if not isinstance(cog, type(module)):
                if hasattr(module, "on_anycog_unload"):
                    try:
                        module.on_anycog_unload(cog)
                    # pylint: disable=broad-exception-caught
                    except BaseException:
                        self.log.warning("[remove_cog]", exc_info=True)


class CheckException(commands.CommandError):
    """
    Exception personnalisée pour les checks
    """
    def __init__(self, check_id, *args):
        super().__init__(message=f"Custom check '{check_id}' failed", *args)
        self.id = check_id # pylint: disable=invalid-name

CONFIG_OPTIONS: Dict[str, Dict[str, Any]] = {}

CONFIG_OPTIONS.update(
    {
        "prefix": {
            "default": config.get("bot.default_prefix"),
            "type": "text",
            "command": 'prefix',
        },
        "language": {
            "default": config.get("bot.default_language"),
            "type": "text",
            "command": 'language',
        },
        "admins": {
            "default": config.get("bot.admins"),
            "type": "categories",
            "command": None,
        },
    }
)

for plugin in os.listdir("./plugins/"):
    if plugin[0] != "_":
        if os.path.isfile("./plugins/" + plugin + "/config/options.json"):
            with open(
                "./plugins/" + plugin + "/config/options.json",
                "r",
                encoding="utf8"
            ) as config:
                CONFIG_OPTIONS.update(json.load(config))
