import os
from core.bot import client, Sconfig
import yaml
import discord

class I18N():
    translations = {}

    def get(guild, key, **kwargs):
        """Translate a string using the bot's i18n dictionary"""
        if type(guild) is discord.Guild: guild = guild.id
        if type(guild) is not str: guild = str(guild)

        try:
            trad = I18N.translations[Sconfig.get(guild, "language")]
            for i in key.split("."):
                trad = trad[i]
            return trad.format(**kwargs)
        except KeyError:
            print(guild)
            print(type(guild))
            print(Sconfig.get(guild, "language"))
            print(key)
            print(I18N.translations["en"]["misc"]["cookie"]["self"])
            return key

    def load():
        for plugin in os.listdir('./plugins/'):
            if not plugin.startswith('_'):
                if os.path.isdir('./plugins/' + plugin + '/langs'):
                    for lang in os.listdir('./plugins/' + plugin + '/langs'):
                        if lang.endswith('.yml') or lang.endswith('.yaml'):
                            trad = yaml.safe_load(open('./plugins/' + plugin + '/langs/' + lang))
                            I18N.translations.update(trad)