"""
Ce programme est régi par la licence CeCILL soumise au droit français et
respectant les principes de diffusion des logiciels libres. Vous pouvez
utiliser, modifier et/ou redistribuer ce programme sous les conditions
de la licence CeCILL diffusée sur le site "http://www.cecill.info".
"""

import logging
import sqlite3
import json
import sys
from typing import Any, Callable, Coroutine, Dict, Union, List, TYPE_CHECKING
import os

import discord
from discord.ext import commands

from core import config

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


class Gunibot(commands.bot.AutoShardedBot):
    """
    Classe principale du bot
    """

    def __init__(self, case_insensitive=None, status=None, beta=False):
        # defining allowed default mentions
        ALLOWED = discord.AllowedMentions(everyone=False, roles=False)
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
        self.log = logging.getLogger("runner")  # logs module
        self.beta: bool = beta  # if the bot is in beta mode
        self.database = sqlite3.connect("data/database.db")  # database connection
        self.database.row_factory = sqlite3.Row
        self.cog_icons = {}  # icons for cogs
        self._update_database_structure()

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
        return self.get_cog("ConfigCog").confManager

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
        avatar = user.display_avatar.with_size(size) # the avatar always exist, returns the URL to the default one
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
        Pour toute autre requête, retourne l'ID de la ligne affectée si returnrowscount,
        ou le nombre de lignes affectées (si returnrowscount)

        :param query: La requête à faire
        :param args: Les arguments de la requête
        :param fetchone: Si la requête est un SELECT, retourne seulement le premier résultat
        :param returnrowcount: Si la requête est un INSERT, UPDATE ou DELETE, retourne le nombre de lignes affectées
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
    def _(self) -> Callable[[Any, str], Coroutine[Any, Any, str]]:
        """
        Traduire un texte

        :return: La fonction de traduction
        """
        cog = self.get_cog("Languages")
        if cog is None:
            self.log.error("Unable to load Languages cog")
            return lambda *args, **kwargs: args[1]
        return cog.tr

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
        self.id = check_id


def setup_logger():
    """
    Initialiser le logger

    :return: None
    """
    # on chope le premier logger
    log = logging.getLogger("runner")
    # on définit un formatteur
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s: %(message)s", datefmt="[%d/%m/%Y %H:%M]"
    )
    # ex du format : [08/11/2018 14:46] WARNING RSSCog fetch_rss_flux l.288 :
    # Cannot get the RSS flux because of the following error: (suivi du
    # traceback)

    # log vers un fichier
    file_handler = logging.FileHandler("logs/debug.log")
    # tous les logs de niveau DEBUG et supérieur sont evoyés dans le fichier
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # log vers la console
    stream_handler = logging.StreamHandler(sys.stdout)
    # tous les logs de niveau INFO et supérieur sont evoyés dans le fichier
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)

    # supposons que nous voulions collecter les erreurs sur ton site d'analyse d'erreurs comme sentry
    # sentry_handler = x
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
            with open("./plugins/" + plugin + "/config/options.json", "r", encoding="utf8") as config:
                CONFIG_OPTIONS.update(json.load(config))
