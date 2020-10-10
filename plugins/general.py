import discord
from discord.ext import commands
import checks
import asyncio
import time
import sys
import psutil
import os
from platform import system as system_name  # Returns the system/OS name
from subprocess import call as system_call  # Execute a shell command


class General(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.file = "general"
        self.codelines = 0

    @commands.Cog.listener()
    async def on_ready(self):
        await self.count_lines_code()

    async def count_lines_code(self):
        """Count the number of lines for the whole project"""
        count = 0
        try:
            with open('start.py', 'r') as file:
                for line in file.read().split("\n"):
                    if len(line.strip()) > 2 and line[0] != '#':
                        count += 1
            for filename in [f"plugins/{x.file}.py" for x in self.bot.cogs.values()]+['checks.py']:
                with open(filename, 'r') as file:
                    for line in file.read().split("\n"):
                        if len(line.strip()) > 2 and line[0] != '#':
                            count += 1
        except Exception as e:
            await self.bot.get_cog('Errors').on_error(e, None)
        self.codelines = count

    @commands.command(name="ping")
    async def rep(self, ctx, ip=None):
        """Get bot latency
        You can also use this command to ping any other server"""
        if ip is None:
            m = await ctx.send("Ping...")
            t = (m.created_at - ctx.message.created_at).total_seconds()
            await m.edit(content=":ping_pong:  Pong !\nBot ping: {}ms\nDiscord ping: {}ms".format(round(t*1000), round(self.bot.latency*1000)))
        else:
            asyncio.run_coroutine_threadsafe(
                self.ping_adress(ctx, ip), asyncio.get_event_loop())

    async def ping_adress(self, ctx, ip):
        packages = 30
        wait = 0.3
        try:
            try:
                m = await ctx.send(f"Pinging {ip}...")
            except:
                m = None
            t1 = time.time()
            param = '-n' if system_name().lower() == 'windows' else '-c'
            command = ['ping', param, str(packages), '-i', str(wait), ip]
            result = system_call(command) == 0
        except Exception as e:
            await ctx.send("`Error:` {}".format(e))
            return
        if result:
            t = (time.time() - t1 - wait*(packages-1))/(packages)*1000
            await ctx.send("Pong ! (average of {}ms per 64 byte, sent at {})".format(round(t, 2), ip))
        else:
            await ctx.send("Unable to ping this adress")
        if m is not None:
            await m.delete()

    @commands.command(name="stats", enabled=True)
    @commands.cooldown(2, 60, commands.BucketType.guild)
    async def stats(self, ctx):
        """Display some statistics about the bot"""
        v = sys.version_info
        version = str(v.major)+"."+str(v.minor)+"."+str(v.micro)
        pid = os.getpid()
        py = psutil.Process(pid)
        ram_usage = round(py.memory_info()[0]/2.**30, 3) #, py.cpu_percent()]
        latency = round(self.bot.latency*1000, 3)
        CPU_INTERVAL = 3.0
        try:
            async with ctx.channel.typing():
                len_servers = len(ctx.bot.guilds)
                users = len(ctx.bot.users)
                bots = len([None for u in ctx.bot.users if u.bot])
                d = """**Nombre de serveurs :** {s_count}
**Nombre de membres visibles :** {m_count} (dont {b_count} **bots**)
**Nombre de lignes de code :** {l_count}
**Version de Python :** {p_v}
**Version de la bibliothèque `discord.py` :** {d_v}
**Charge sur la mémoire vive :** {ram} GB
**Charge sur le CPU :** *calcul en cours*
**Temps de latence de l'api :** {api} ms""".format(s_count=len_servers, m_count=users, b_count=bots, l_count=self.codelines, p_v=version, d_v=discord.__version__, ram=ram_usage, api=latency,)
            if isinstance(ctx.channel, discord.DMChannel) or ctx.channel.permissions_for(ctx.guild.me).embed_links:
                embed = discord.Embed(title="**Statistiques du bot**", color=8311585, timestamp=ctx.message.created_at, description=d, thumbnail=self.bot.user.avatar_url_as(format="png"))
                msg = await ctx.send(embed=embed)
                cpu_usage = py.cpu_percent(CPU_INTERVAL)
                embed.description = embed.description.replace("*calcul en cours*", f"{cpu_usage} %")
                await msg.edit(embed=embed)
            else:
                msg = await ctx.send(d)
                cpu_usage = py.cpu_percent(CPU_INTERVAL)
                d = d.replace("*calcul en cours*", f"{cpu_usage} %")
                await msg.edit(content=d)
        except Exception as e:
            await ctx.bot.get_cog("Errors").on_cmd_error(ctx, e)

    @commands.command(name="halp", enabled=True)
    async def halp(self, ctx):
        embed = discord.Embed(
            name="Help",
            colour=discord.Colour.green()
        )
        embed.set_author(name=f'Gunibot commands')
        embed.add_field(name="admin", value="Affiche les commandes admin disponibles")
        embed.add_field(name="admin", value="Affiche les commandes admin disponibles")
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(General(bot))
