import discord
from discord.ext import commands
import os
import sys
import checks


class Admin(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.file = "admin"

    @commands.group(name='admin', hidden=True)
    @commands.check(checks.is_bot_admin)
    async def main_msg(self, ctx):
        """Commandes réservées aux administrateurs de ZBot"""
        if ctx.subcommand_passed == None:
            text = "Liste des commandes disponibles :"
            for cmd in sorted(self.main_msg.commands, key=lambda x: x.name):
                text += "\n- {} *({})*".format(cmd.name,
                                               '...' if cmd.help == None else cmd.help.split('\n')[0])
                if type(cmd) == commands.core.Group:
                    for cmds in cmd.commands:
                        text += "\n        - {} *({})*".format(
                            cmds.name, cmds.help.split('\n')[0])
            await ctx.send(text)

    @main_msg.command(name='shutdown')
    @commands.check(checks.is_bot_admin)
    async def shutdown(self, ctx):
        """Eteint le bot"""
        m = await ctx.send("Nettoyage de l'espace de travail...")
        await self.cleanup_workspace()
        await m.edit(content="Bot en voie d'extinction")
        await self.bot.change_presence(status=discord.Status('offline'))
        self.bot.log.info("Fermeture du bot")
        await self.bot.logout()
        await self.bot.close()

    async def cleanup_workspace(self):
        for folderName, _, filenames in os.walk('.'):
            for filename in filenames:
                if filename.endswith('.pyc'):
                    os.unlink(folderName+'/'+filename)
            if folderName.endswith('__pycache__'):
                os.rmdir(folderName)

    @main_msg.command(name='reboot')
    async def restart_bot(self, ctx):
        """Relance le bot"""
        await ctx.send(content="Redémarrage en cours...")
        await self.cleanup_workspace()
        self.bot.log.info("Redémarrage du bot")
        os.execl(sys.executable, sys.executable, *sys.argv)

    @main_msg.command(name='reload')
    async def reload_cog(self, ctx, *, cog: str):
        """Recharge un module"""
        cogs = cog.split(" ")
        errors_cog = self.bot.get_cog("Errors")
        if len(cogs) == 1 and cogs[0] == 'all':
            cogs = sorted([x.file for x in self.bot.cogs.values()])
        reloaded_cogs = list()
        for cog in cogs:
            try:
                self.bot.reload_extension(cog)
            except ModuleNotFoundError:
                await ctx.send("Cog {} can't be found".format(cog))
            except commands.errors.ExtensionNotLoaded:
                await ctx.send("Cog {} was never loaded".format(cog))
            except Exception as e:
                await errors_cog.on_error(e, ctx)
                await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')
            else:
                self.bot.log.info("Module {} rechargé".format(cog))
                reloaded_cogs.append(cog)
        if len(reloaded_cogs) > 0:
            await ctx.bot.get_cog("General").count_lines_code()
            await ctx.send("These cogs has successfully reloaded: {}".format(", ".join(reloaded_cogs)))

    @main_msg.command(name="add_cog", hidden=True)
    async def add_cog(self, ctx, name):
        """Ajouter un cog au bot"""
        try:
            self.bot.load_extension(name)
            await ctx.send("Module '{}' ajouté !".format(name))
            self.bot.log.info("Module {} ajouté".format(name))
        except Exception as e:
            await ctx.send(str(e))

    @main_msg.command(name="del_cog", aliases=['remove_cog'], hidden=True)
    async def rm_cog(self, ctx, name):
        """Enlever un cog au bot"""
        try:
            self.bot.unload_extension(+name)
            await ctx.send("Module '{}' désactivé !".format(name))
            self.bot.log.info("Module {} ajouté".format(name))
        except Exception as e:
            await ctx.send(str(e))
    
    @main_msg.command(name="cogs",hidden=True)
    async def cogs_list(self,ctx):
        """Voir la liste de tout les cogs"""
        text = str()
        for k,v in self.bot.cogs.items():
            text +="- {} ({}) \n".format(v.file,k)
        await ctx.send(text)

    @main_msg.command(name="activity")
    async def change_activity(self, ctx, Type: str, * act: str):
        """Change l'activité du bot (play, watch, listen, stream)"""
        act = " ".join(act)
        if Type in ['game', 'play', 'playing']:
            await self.bot.change_presence(activity=discord.Game(name=act))
        elif Type in ['watch', 'see', 'watching']:
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=act))
        elif Type in ['listen', 'listening']:
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=act))
        elif Type in ['stream']:
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.streaming, name=act))
        else:
            await ctx.send("Sélectionnez *play*, *watch*, *listen* ou *stream* suivi du nom")
        await ctx.message.delete()


def setup(bot):
    bot.add_cog(Admin(bot))
