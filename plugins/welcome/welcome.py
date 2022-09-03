import discord
from discord.ext import commands
from utils import Gunibot, MyContext


class Welcome(commands.Cog):
    def __init__(self, bot: Gunibot):
        self.bot = bot
        self.config_options = ["welcome_roles"]

        bot.get_command("config").add_command(self.config_welcome_roles)

    @commands.command(name="welcome_roles")
    async def config_welcome_roles(
        self, ctx: MyContext, roles: commands.Greedy[discord.Role]
    ):
        if len(roles) == 0:
            roles = None
        else:
            roles = [role.id for role in roles]
        await ctx.send(
            await self.bot.sconfig.edit_config(ctx.guild.id, "welcome_roles", roles)
        )

    async def give_welcome_roles(self, member: discord.Member):
        g = member.guild
        config = self.bot.server_configs[g.id]
        rolesID = config["welcome_roles"]
        if not rolesID:  # if nothing has been setup
            return
        roles = [g.get_role(x) for x in rolesID]
        pos = g.me.top_role.position
        roles = filter(lambda x: (x is not None) and (x.position < pos), roles)
        await member.add_roles(*roles, reason="New members roles")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Called when a member joins a guild"""
        g = member.guild
        if not g.me.guild_permissions.manage_roles:  # if not allowed to manage roles
            self.bot.log.info(
                f'Module - Welcome: Missing "manage_roles" permission on guild "{g.name}"'
            )
            return
        if "MEMBER_VERIFICATION_GATE_ENABLED" not in g.features:
            # we give new members roles if the verification gate is disabled
            await self.give_welcome_roles(member)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """Main function called when a member got verified in a community server"""
        if before.pending and not after.pending:
            if "MEMBER_VERIFICATION_GATE_ENABLED" in after.guild.features:
                await self.give_welcome_roles(after)


config = {}
async def setup(bot:Gunibot=None, plugin_config:dict=None):
    if bot is not None:
        await bot.add_cog(Welcome(bot))
    if plugin_config is not None:
        global config
        config.update(plugin_config)

