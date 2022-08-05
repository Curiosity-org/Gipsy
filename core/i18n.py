import os, yaml, discord
from core.bot          import client
from core.serverConfig import ServerConfig

class I18N():
    """
    A class that store and deliver all translations
    """

    translations = {} # global translation storage

    def get(guild, key, **kwargs):
        """Translate a string using the bot's i18n dictionary"""

        # Getting guild id
        if type(guild) is discord.Guild: guild = guild.id
        if type(guild) is not str: guild = str(guild)

        # Getting translation
        try:
            trad = I18N.translations[ServerConfig.get(guild, "language")]
            for i in key.split("."):
                trad = trad[i]
            return trad.format(**kwargs)
        except KeyError:
            return key

    def load():
        """Load translations from plugin's translation files"""

        for plugin in os.listdir('./plugins/'):
            if not plugin.startswith('_'):
                if os.path.isdir('./plugins/' + plugin + '/langs'):
                    for lang in os.listdir('./plugins/' + plugin + '/langs'):
                        if lang.endswith('.yml') or lang.endswith('.yaml'):
                            trad = yaml.safe_load(open('./plugins/' + plugin + '/langs/' + lang))
                            I18N.translations.update({lang[:2]:
                                {plugin:trad}
                            })