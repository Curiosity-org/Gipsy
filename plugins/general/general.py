"""
Ce programme est régi par la licence CeCILL soumise au droit français et
respectant les principes de diffusion des logiciels libres. Vous pouvez
utiliser, modifier et/ou redistribuer ce programme sous les conditions
de la licence CeCILL diffusée sur le site "http://www.cecill.info".
"""

from typing import Union
import os
import sys

import discord
import psutil
from discord.ext import commands
from git import Repo, InvalidGitRepositoryError

from utils import Gunibot, MyContext

ChannelTypes = Union[
    discord.Thread,
    discord.abc.GuildChannel,
]
CPU_INTERVAL = 3.0
CHANNEL_TYPES = Union[
    discord.Thread,
    discord.abc.GuildChannel,
]

class General(commands.Cog):
    def __init__(self, bot: Gunibot):
        self.bot = bot
        self.codelines = 0

    @commands.Cog.listener()
    async def on_ready(self):
        await self.count_lines_code()

    async def count_lines_code(self):
        """Count the number of lines for the whole project"""
        count = 0
        try:
            for root, dirs, files in os.walk("."): # pylint: disable=unused-variable
                if "/lib/python" in root:
                    continue
                for file in files:
                    if file.endswith(".py"):
                        with open(os.path.join(root, file), "r", encoding="utf8") as file:
                            for line in file.read().split("\n"):
                                if len(line.strip()) > 2 and line[0] != "#":
                                    count += 1
        except Exception as exception: # pylint: disable=broad-exception-caught
            await self.bot.get_cog("Errors").on_error(exception, None)
        self.codelines = count

    @commands.command(name="hs")
    async def hs(self, ctx: MyContext, channel: CHANNEL_TYPES = None): # pylint: disable=invalid-name
        if channel:
            msg = await self.bot._(
                ctx.channel,
                "general.hs-1",
                current=ctx.channel.mention,
                dest=channel.mention,
            )
        else:
            msg = await self.bot._(
                ctx.channel, "general.hs-2", current=ctx.channel.mention
            )
        if ctx.can_send_embed:
            emb = discord.Embed(description=msg, color=discord.Color.red())
            await ctx.send(embed=emb)
        else:
            await ctx.send(msg)

    @commands.command(name="ping")
    async def rep(self, ctx: MyContext):
        """Get bot latency"""
        msg = await ctx.send("Ping...")
        time = (msg.created_at - ctx.message.created_at).total_seconds()
        try:
            ping = round(self.bot.latency * 1000)
        except OverflowError:
            ping = "∞"
        await msg.edit(
            content=f":ping_pong:  Pong !\nBot ping: {round(time * 1000)}ms\nDiscord ping: {ping}ms"
        )

    @commands.command(name="stats")
    @commands.cooldown(2, 60, commands.BucketType.guild)
    async def stats(self, ctx: MyContext):
        """Display some statistics about the bot"""
        v_info = sys.version_info
        version = str(v_info.major) + "." + str(v_info.minor) + "." + str(v_info.micro)
        pid = os.getpid()
        try:
            process = psutil.Process(pid)
            ram_usage = round(process.memory_info()[0] / 2.0**30, 3)  # , py.cpu_percent()]
        except OSError:
            ram_usage = latency = "?"
            process = None

        latency = round(self.bot.latency * 1000, 3)

        try:
            async with ctx.channel.typing():
                len_servers = len(ctx.bot.guilds)
                users = len(ctx.bot.users)
                bots = len([None for u in ctx.bot.users if u.bot])
                stats = await self.bot._(ctx.channel, "general.stats.servs", c=len_servers)
                stats += "\n" + await self.bot._(
                    ctx.channel, "general.stats.members", c=users, bots=bots
                )
                stats += "\n" + await self.bot._(
                    ctx.channel, "general.stats.codelines", c=self.codelines
                )
                stats += "\n" + await self.bot._(
                    ctx.channel, "general.stats.pyver", v=version
                )
                stats += "\n" + await self.bot._(
                    ctx.channel, "general.stats.diver", v=discord.__version__
                )
                try:
                    branch = Repo(os.getcwd()).active_branch
                    stats += "\n" + await self.bot._(ctx.channel, "general.stats.git", b=branch)
                except InvalidGitRepositoryError:
                    pass
                stats += "\n" + await self.bot._(
                    ctx.channel, "general.stats.ram", c=ram_usage
                )
                cpu_txt = await self.bot._(ctx.channel, "general.stats.cpu-loading")
                stats += "\n" + cpu_txt
                stats += "\n" + await self.bot._(
                    ctx.channel, "general.stats.ping", c=latency
                )
            if ctx.can_send_embed:
                title = (
                    "**" + await self.bot._(ctx.channel, "general.stats.title") + "**"
                )
                embed = discord.Embed(
                    title=title,
                    color=8311585,
                    timestamp=ctx.message.created_at,
                    description=stats,
                )
                embed.set_thumbnail(url=self.bot.user.display_avatar)
                msg: discord.Message = await ctx.send(embed=embed)
                if process is None:  # PSUtil can't be used
                    cpu_usage = "?"
                else:
                    cpu_usage = process.cpu_percent(CPU_INTERVAL)
                cpu_ended = await self.bot._(
                    ctx.channel, "general.stats.cpu-ended", c=cpu_usage
                )
                embed.description = embed.description.replace(cpu_txt, cpu_ended)
                await msg.edit(embed=embed)
            else:
                msg = await ctx.send(stats)
                if process is None:  # PSUtil can't be used
                    cpu_usage = "?"
                else:
                    cpu_usage = process.cpu_percent(CPU_INTERVAL)
                cpu_ended = await self.bot._(
                    ctx.channel, "general.stats.cpu-ended", c=cpu_usage
                )
                stats = stats.replace(cpu_txt, cpu_ended)
                await msg.edit(content=stats)
        except Exception as exception: # pylint: disable=broad-exception-caught
            await ctx.bot.get_cog("Errors").on_command_error(ctx, exception)

    @commands.command(name="halp", enabled=False)
    async def halp(self, ctx):
        embed = discord.Embed(title="Help", colour=discord.Colour.green())
        embed.set_author(name="Gunibot commands")
        embed.add_field(name="admin", value="Affiche les commandes admin disponibles")
        embed.add_field(name="admin", value="Affiche les commandes admin disponibles")
        await ctx.send(embed=embed)

async def setup(bot:Gunibot=None):
    if bot is not None:
        await bot.add_cog(General(bot), icon="🌍")
