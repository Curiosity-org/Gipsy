import asyncio
import os
import sys
import time
from platform import system as system_name  # Returns the system/OS name
from subprocess import call as system_call  # Execute a shell command

import discord
import psutil
from discord.ext import commands
from git import Repo
from utils import Gunibot, MyContext


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
            for root, dirs, files in os.walk("."):
                if "/lib/python" in root:
                    continue
                for file in files:
                    if file.endswith(".py"):
                        with open(os.path.join(root, file), "r", encoding="utf8") as f:
                            for line in f.read().split("\n"):
                                if len(line.strip()) > 2 and line[0] != "#":
                                    count += 1
        except Exception as e:
            await self.bot.get_cog("Errors").on_error(e, None)
        self.codelines = count

    @commands.command(name="hs")
    async def hs(self, ctx: MyContext, channel: discord.abc.GuildChannel = None):
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
        m = await ctx.send("Ping...")
        t = (m.created_at - ctx.message.created_at).total_seconds()
        try:
            p = round(self.bot.latency * 1000)
        except OverflowError:
            p = "∞"
        await m.edit(
            content=":ping_pong:  Pong !\nBot ping: {}ms\nDiscord ping: {}ms".format(
                round(t * 1000), p
            )
        )

    @commands.command(name="stats")
    @commands.cooldown(2, 60, commands.BucketType.guild)
    async def stats(self, ctx: MyContext):
        """Display some statistics about the bot"""
        v = sys.version_info
        version = str(v.major) + "." + str(v.minor) + "." + str(v.micro)
        pid = os.getpid()
        try:
            py = psutil.Process(pid)
            ram_usage = round(py.memory_info()[0] / 2.0**30, 3)  # , py.cpu_percent()]
        except OSError:
            ram_usage = latency = "?"
            py = None
        latency = round(self.bot.latency * 1000, 3)
        CPU_INTERVAL = 3.0
        try:
            async with ctx.channel.typing():
                branch = Repo(os.getcwd()).active_branch
                len_servers = len(ctx.bot.guilds)
                users = len(ctx.bot.users)
                bots = len([None for u in ctx.bot.users if u.bot])
                d = await self.bot._(ctx.channel, "general.stats.servs", c=len_servers)
                d += "\n" + await self.bot._(
                    ctx.channel, "general.stats.members", c=users, bots=bots
                )
                d += "\n" + await self.bot._(
                    ctx.channel, "general.stats.codelines", c=self.codelines
                )
                d += "\n" + await self.bot._(
                    ctx.channel, "general.stats.pyver", v=version
                )
                d += "\n" + await self.bot._(
                    ctx.channel, "general.stats.diver", v=discord.__version__
                )
                d += "\n" + await self.bot._(ctx.channel, "general.stats.git", b=branch)
                d += "\n" + await self.bot._(
                    ctx.channel, "general.stats.ram", c=ram_usage
                )
                cpu_txt = await self.bot._(ctx.channel, "general.stats.cpu-loading")
                d += "\n" + cpu_txt
                d += "\n" + await self.bot._(
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
                    description=d,
                )
                embed.set_thumbnail(url=self.bot.user.display_avatar)
                msg: discord.Message = await ctx.send(embed=embed)
                if py is None:  # PSUtil can't be used
                    cpu_usage = "?"
                else:
                    cpu_usage = py.cpu_percent(CPU_INTERVAL)
                cpu_ended = await self.bot._(
                    ctx.channel, "general.stats.cpu-ended", c=cpu_usage
                )
                embed.description = embed.description.replace(cpu_txt, cpu_ended)
                await msg.edit(embed=embed)
            else:
                msg = await ctx.send(d)
                if py is None:  # PSUtil can't be used
                    cpu_usage = "?"
                else:
                    cpu_usage = py.cpu_percent(CPU_INTERVAL)
                cpu_ended = await self.bot._(
                    ctx.channel, "general.stats.cpu-ended", c=cpu_usage
                )
                d = d.replace(cpu_txt, cpu_ended)
                await msg.edit(content=d)
        except Exception as e:
            await ctx.bot.get_cog("Errors").on_command_error(ctx, e)

    @commands.command(name="halp", enabled=False)
    async def halp(self, ctx):
        embed = discord.Embed(name="Help", colour=discord.Colour.green())
        embed.set_author(name=f"Gunibot commands")
        embed.add_field(name="admin", value="Affiche les commandes admin disponibles")
        embed.add_field(name="admin", value="Affiche les commandes admin disponibles")
        await ctx.send(embed=embed)

config = {}
async def setup(bot:Gunibot=None, plugin_config:dict=None):
    if bot is not None:
        await bot.add_cog(General(bot), icon="🌍")
    if plugin_config is not None:
        global config
        config.update(plugin_config)
