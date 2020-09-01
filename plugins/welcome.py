import discord
from discord.ext import commands
import checks


class Welcome(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.file = "welcome"

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Called when a member joins a guild"""
        g = member.guild
        config = self.bot.server_configs[g.id]
        rolesID = config["welcome_roles"]
        if not rolesID:  # si rien n'a été configuré
            return
        roles = [g.get_role(x) for x in rolesID]
        pos = g.me.top_role.position
        roles = filter(lambda x: (x is not None) and (x.position < pos), roles)
        await member.add_roles(*roles, reason="New members roles")


def setup(bot):
    bot.add_cog(Welcome(bot))
