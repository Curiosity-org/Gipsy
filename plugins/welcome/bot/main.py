import discord
from discord.ext import commands
from utils import Gunibot, MyContext
from bot.utils.sconfig import Sconfig


class Welcome(commands.Cog):

    def __init__(self, bot: Gunibot):
        self.bot = bot
        self.config_options = ["welcome_roles"]

        bot.get_command("config").add_command(self.config_welcome_roles)
        bot.get_command("config").add_command(self.config_info_channel)
        bot.get_command("config").add_command(self.config_verification_role)
        bot.get_command("config").add_command(self.config_verification_add_role)
        bot.get_command("config").add_command(self.config_pass_message)
        bot.get_command("config").add_command(self.config_verification_channel_id)

    @commands.command(name="welcome_roles")
    async def config_welcome_roles(self, ctx: MyContext, roles: commands.Greedy[discord.Role]):
        if len(roles) == 0:
            roles = None
        else:
            roles = [role.id for role in roles]
        await ctx.send(await Sconfig.edit_config(ctx.guild.id, "welcome_roles", roles))

    @commands.command(name="info_channel")
    async def config_info_channel(self, ctx: MyContext, *, channel: discord.TextChannel):
        await ctx.send(await Sconfig.edit_config(ctx.guild.id, "info_channel", channel.id))

    @commands.command(name="verification_role")
    async def config_verification_role(self, ctx: MyContext, *, role: discord.Role):
        await ctx.send(await Sconfig.edit_config(ctx.guild.id, "verification_role", role.id))

    @commands.command(name="verification_add_role")
    async def config_verification_add_role(self, ctx: MyContext, value: bool):
        await ctx.send(await Sconfig.edit_config(ctx.guild.id, "verification_add_role", value))

    @commands.command(name="verification_info_message")
    async def config_verification_add_role(self, ctx: MyContext, *, value: str = None):
        """Informative message sent in the verification channel when someone joins your message
        Put nothing to reset it, or "None" for no message"""
        if value.lower() == "none":
            value = "None"  # no message
        await ctx.send(await Sconfig.edit_config(ctx.guild.id, "verification_info_message", value))

    @commands.command(name="pass_message")
    async def config_pass_message(self, ctx: MyContext, *, message):
        await ctx.send(await Sconfig.edit_config(ctx.guild.id, "pass_message", message))

    @commands.command(name="verification_channel")
    async def config_verification_channel_id(self, ctx: MyContext, *, channel: discord.TextChannel):
        await ctx.send(await Sconfig.edit_config(ctx.guild.id, "verification_channel", channel.id))
    
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
            self.bot.log.info(f"Module - Welcome: Missing \"manage_roles\" permission on guild \"{g.name}\"")
            return
        if "MEMBER_VERIFICATION_GATE_ENABLED" not in g.features:
            # we give new members roles if the verification gate is disabled
            await self.give_welcome_roles(member)
    
    @commands.Cog.listener()
    async def on_member_update(self, before:discord.Member, after:discord.Member):
        """Main function called when a member got verified in a community server"""
        if before.pending and not after.pending:
            if "MEMBER_VERIFICATION_GATE_ENABLED" in after.guild.features:
                await self.give_welcome_roles(after)

def setup(bot):
    bot.add_cog(Welcome(bot))
