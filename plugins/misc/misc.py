import random
from datetime import datetime

import discord
from discord.ext import commands
from utils import Gunibot, MyContext

from typing import Union


class Misc(commands.Cog):

    CONTAINS_TIMESTAMP = Union[
        int,
        discord.User,
        discord.TextChannel,
        discord.VoiceChannel,
        discord.StageChannel,
        discord.GroupChannel,
        discord.Message,
        discord.Emoji,
        discord.Guild,
    ]

    def __init__(self, bot: Gunibot):
        self.bot = bot
        self.file = "misc"

    # ------------------#
    # Commande /cookie #
    # ------------------#

    @commands.command(name="cookie")
    @commands.guild_only()
    async def cookie(self, ctx: MyContext, *, user: discord.User = None):
        """The most useful command: give a cookie to yourself or someone else."""
        if user:
            message = await self.bot._(
                ctx.guild.id,
                "misc.cookie.give",
                to=user.mention,
                giver=ctx.author.mention,
            )
        else:
            message = await self.bot._(
                ctx.guild.id, "misc.cookie.self", to=ctx.author.mention
            )

        # Créer un webhook qui prend l'apparence d'un Villageois
        webhook: discord.Webhook = await ctx.channel.create_webhook(
            name=f"Villager #{random.randint(1, 9)}"
        )
        await webhook.send(
            content=message,
            avatar_url="https://d31sxl6qgne2yj.cloudfront.net/wordpress/wp-content/uploads/20190121140737/Minecraft-Villager-Head.jpg",
        )
        await webhook.delete()
        try:
            await ctx.message.delete()
        except discord.errors.NotFound:
            pass

    # ------------------#
    # Commande /hoster #
    # ------------------#

    @commands.command(name="hoster")
    @commands.guild_only()
    async def hoster(self, ctx: MyContext):
        """Give all informations about the hoster"""
        embed = discord.Embed(colour=discord.Colour.blue())
        embed.add_field(
            name="mTx Serv", value=await self.bot._(ctx.guild.id, "misc.hoster.info")
        )
        embed.set_thumbnail(
            url="http://gunivers.net/wp-content/uploads/2021/07/Logo-mTxServ.png"
        )

        # Créer un webhook qui prend l'apparence d'Inovaperf
        webhook: discord.Webhook = await ctx.channel.create_webhook(name="mTx Serv")
        await webhook.send(
            embed=embed,
            avatar_url="http://gunivers.net/wp-content/uploads/2021/07/Logo-mTxServ.png",
        )
        await webhook.delete()
        await ctx.message.delete()

    # ---------------------#
    # Commande /flipacoin #
    # ---------------------#

    @commands.command(name="flipacoin", aliases=["fc"])
    async def flip(self, ctx: MyContext):
        """Flip a coin."""
        a = random.randint(-100, 100)
        if a > 0:
            await ctx.send(await self.bot._(ctx.guild.id, "misc.flipacoin.tails"))
        elif a < 0:
            await ctx.send(await self.bot._(ctx.guild.id, "misc.flipacoin.heads"))
        else:
            await ctx.send(await self.bot._(ctx.guild.id, "misc.flipacoin.side"))

    # ------------------#
    # Commande /dataja #
    # ------------------#

    @commands.command(name="dataja")
    async def dataja(self, ctx: MyContext):
        """Don't ask to ask, just ask."""
        await ctx.send(await self.bot._(ctx.guild.id, "misc.dataja"))

    # ------------------#
    # Commande /kill #
    # ------------------#

    @commands.command(name="kill")
    async def kill(self, ctx: MyContext, *, target: str = None):
        """Wanna kill someone?"""
        if target is None:  # victim is user
            victime = ctx.author.display_name
            ex = ctx.author.display_name.replace(" ", "\\_")
        else:  # victim is target
            victime = target
            ex = target.replace(" ", "\\_")
        author = ctx.author.mention
        tries = 0
        # now let's find a random answer
        msg = "misc.kills"
        while msg.startswith("misc.kills") or (
            "{0}" in msg and target is None and tries < 50
        ):
            choice = random.randint(0, 23)
            msg = await self.bot._(ctx.channel, f"misc.kills.{choice}")
            tries += 1
        # and send it
        await ctx.send(
            msg.format(author, victime, ex),
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @commands.group(name="timestamp")
    async def timestamp(self, ctx: MyContext):
        """This command helps you to use the discord timestamp feature.
        Use the timestamp command to see more !
        """
        if not ctx.subcommand_passed:
            await ctx.author.send(await self.bot._(ctx, "misc.timestamp.help"))

    @timestamp.command(name="get")
    async def get(self, ctx: MyContext, snowflake: CONTAINS_TIMESTAMP = None):
        """If you want to know how old is a thing

        Supported args :
        • Discord ID
        • User mention
        • Channel mention
        • Message link
        • Custom emoji
        """
        if isinstance(snowflake, int):
            source = f"`{snowflake}`"
        elif isinstance(snowflake, (discord.User, discord.abc.GuildChannel)):
            source = snowflake.mention
            snowflake = snowflake.id
        elif isinstance(snowflake, discord.Message):
            source = snowflake.jump_url
            snowflake = snowflake.id
        elif isinstance(snowflake, discord.Emoji):
            source = snowflake
            snowflake = snowflake.id
        elif isinstance(snowflake, discord.Guild):
            source = snowflake.name
            snowflake = snowflake.id
        elif snowflake is None:  # we get the user id
            source = ctx.author.mention
            snowflake = ctx.author.id
        else:
            await ctx.send(
                await self.bot._(
                    ctx.guild.id, "misc.timestamp.not-found", source=snowflake
                )
            )
            return
        timestamp = ((snowflake >> 22) + 1420070400000) // 1000
        await ctx.send(
            await self.bot._(
                ctx.guild.id,
                "misc.timestamp.read-result",
                source=source,
                timestamp=timestamp,
            ),
            allowed_mentions=discord.AllowedMentions(
                everyone=False, users=False, roles=False
            ),
        )

    @timestamp.command(name="create")
    async def create(
        self,
        ctx: MyContext,
        year: int,
        month: int = 1,
        day: int = 1,
        hour: int = 0,
        minute: int = 0,
        second: int = 0,
    ):
        """Show the timestamp for the specified date"""
        date = datetime(year, month, day, hour, minute, second)
        timestamp = int(date.timestamp())
        await ctx.send(
            await self.bot._(ctx, "misc.timestamp.create-result", timestamp=timestamp)
        )


# The end.
config = {}
async def setup(bot:Gunibot=None, plugin_config:dict=None):
    if bot is not None:
        await bot.add_cog(Misc(bot))
    if plugin_config is not None:
        global config
        config.update(plugin_config)

