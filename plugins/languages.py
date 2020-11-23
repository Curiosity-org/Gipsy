import i18n
import discord
from discord.ext import commands
from utils import Gunibot, MyContext

i18n.translations.container.clear()  # invalidate old cache
i18n.set('filename_format', '{locale}.{format}')
i18n.set('fallback', 'fr')
i18n.load_path.append('./langs')


class Languages(commands.Cog):

    def __init__(self, bot: Gunibot):
        self.bot = bot
        self.file = "languages"
        self.languages = ['fr', 'en']

    async def tr(self, ctx, key: str, **kwargs):
        """Translate something
        Ctx can be either a Context, a guild, a guild id, a channel or a lang directly"""
        lang = self.languages[0]
        if isinstance(ctx, commands.Context):
            if ctx.guild:
                lang = self.languages[await self.get_lang(ctx.guild.id)]
        elif isinstance(ctx, discord.Guild):
            lang = self.languages[await self.get_lang(ctx.id)]
        elif isinstance(ctx, discord.abc.GuildChannel):
            lang = self.languages[await self.get_lang(ctx.guild.id)]
        elif isinstance(ctx, str) and ctx in self.languages:
            lang = ctx
        elif isinstance(ctx, int):  # guild ID
            if self.bot.get_guild(ctx):  # if valid guild
                lang = self.languages[await self.get_lang(ctx)]
            else:
                lang = self.languages[0]
        return i18n.t(key, locale=lang, **kwargs)

    async def get_lang(self, guildID: int) -> int:
        return self.bot.server_configs[guildID]['language']


def setup(bot):
    bot.add_cog(Languages(bot))
