import discord
from discord.ext import tasks, commands
from utils import Gunibot, MyContext


class Gunivers(commands.Cog):

    def __init__(self, bot: Gunibot):
        self.bot = bot
        self.file = "gunivers"
        self.update_loop.start()

    def cog_unload(self):
        self.update_loop.cancel()

    @tasks.loop(minutes=60.0 * 24.0)
    async def update_loop(self):
        channel = self.bot.get_channel(757879277776535664) # Round Table
        if channel is not None:
            await channel.send("Bon, qu'est-ce qu'on peut poster aujourd'hui ?")

    #------------------#
    # Commande /rlban  #
    #------------------#

    @commands.command(name="rlban")
    @commands.guild_only()
    @commands.has_guild_permissions(ban_members=True)
    async def ban(self, ctx: MyContext, *, user: discord.User):
        if user == ctx.author:
            await ctx.send("Tu ne peux pas te bannir toi-même !")
            return
        if not ctx.guild.me.guild_permissions.ban_members:
            await ctx.send("Permission 'Bannir des membres' manquante :confused:")
            return
        member = ctx.guild.get_member(user.id)
        if member is not None and member.roles[-1].position >= ctx.guild.me.roles[-1].position:
            await ctx.send("Mon rôle n'est pas assez haut pour bannir cet individu :confused:")
            return
        try:
            await ctx.guild.ban(user, delete_message_days=0, reason=f"Banned by {ctx.author} ({ctx.author.id})")
        except discord.Forbidden:
            await ctx.send("Permissions manquantes :confused: (vérifiez la hiérarchie)")
        else:
            await ctx.send(f"{user} a bien été banni !")
        await ctx.send("https://thumbs.gfycat.com/AllFeminineCaribou-size_restricted.gif")


def setup(bot):
    bot.add_cog(Gunivers(bot))
