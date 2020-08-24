from discord.ext import commands
from json import load, dump
import os

CONFIG_FOLDER = "configs"

CONFIG_TEMPLATE = {
    "prefix": "/",
    "verification_channel": None,
    "logs_channel": None,
    "info_channel": None,
    "pass_message": None,
    "verification_role": None,
    "verification_add_role": True,
    "contact_channel": None,
    "contact_category": None,
    "welcome_roles": None,
    "voices_category": None,
    "voice_channel": None
}

class serverConfig(dict):
    def __init__(self, manager, serverID, value):
        super().__init__(value)
        self.manager = manager
        self.serverID = serverID

    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError as e:
            if key in CONFIG_TEMPLATE.keys():
                return CONFIG_TEMPLATE[key]
            raise e

    def __setitem__(self, key, item):
        if key in CONFIG_TEMPLATE.keys():
            super().__setitem__(key, item)
            self.manager[self.serverID] = self
        else:
            raise ValueError("Invalid config key")

class ConfigCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.file = "configManager"
        self.confManager = self.configManager()

    class configManager(dict):

        def __setitem__(self, key, item):
            if not (isinstance(key, int) or key.isnumeric()):
                raise ValueError("Key need to be a valid guild ID")
            with open(f"{CONFIG_FOLDER}/{key}.json", "w", encoding="utf8") as f:
                dump(item, f)

        def __getitem__(self, key):
            if not (isinstance(key, int) or key.isnumeric()):
                raise ValueError("Key need to be a valid guild ID")
            result = CONFIG_TEMPLATE
            try:
                with open(f"{CONFIG_FOLDER}/{key}.json", "r", encoding="utf8") as f:
                    result.update(load(f))
            except FileNotFoundError:
                pass
            return serverConfig(self, key, result)

        def __repr__(self):
            return "<configManager>"

        def __len__(self):
            return len([name for name in os.listdir(CONFIG_FOLDER) if os.path.isfile(name)])

        def __delitem__(self, key):
            pass

        def has_key(self, k):
            return os.path.isfile(f"{CONFIG_FOLDER}/{k}.json")

        def update(self, *args, **kwargs):
            for arg in args:
                if isinstance(arg, dict):
                    for k, v in arg.items():
                        self.__setitem__(k, v)
            for kwarg in kwargs:
                for k, v in kwarg.items():
                    self.__setitem__(k, v)

        def keys(self):
            return [name for name in os.listdir(CONFIG_FOLDER) if os.path.isfile(name)]

        # def values(self):
        #     return self.__dict__.values()

        # def items(self):
        #     return self.__dict__.items()

        # def pop(self, *args):
        #     return self.__dict__.pop(*args)

        def __contains__(self, item):
            return self.has_key(item)

def setup(bot):
    bot.add_cog(ConfigCog(bot))