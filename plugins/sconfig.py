import discord
from discord.ext import commands
import checks


class Sconfig(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.file = "sconfig"
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Called when a member joins a guild"""
        if not member.guild.me.guild_permissions.manage_roles: # si pas la perm de gérer les rôles
            return
        config = self.bot.server_configs[member.guild.id]
        if config["welcome_roles"] == None: # si rien n'a été configuré
            return
        roles = list()
        for roleID in config["welcome_roles"]:
            try:
                role = member.guild.get_role(roleID)
                if role.position < member.guild.me.roles[-1].position:
                    roles.append(role)
            except discord.errors.NotFound:
                pass
        await member.add_roles(*roles, reason="Welcome plugin")

    def edit_config(self, guildID, key, value):
        try:
            self.bot.server_configs[guildID][key] = value
        except ValueError:
            return "Cette option de configuration n'existe pas :confused:"
        else:
            return f"L'option `{key}` a bien été modifiée !"

    @commands.group(name="config")
    @commands.guild_only()
    async def main_config(self, ctx:commands.Context):
        """Edit your server configuration"""
        if ctx.subcommand_passed==None:
            res = ""
            config = ctx.bot.server_configs[ctx.guild.id]
            max_length = max([len(k)+2 for k in config.keys()])
            for k,v in config.items():
                res += (f"[{k}]").ljust(max_length+1) + f" {v}\n"
            res = "```ini\n"+res+"```"
            await ctx.send(res)

    @main_config.command(name="prefix")
    async def config_prefix(self, ctx:commands.Context, new_prefix=None):
        if new_prefix != None and len(new_prefix) > 5:
            await ctx.send("Le préfixe doit faire moins de 5 caractères !")
            return
        await ctx.send(self.edit_config(ctx.guild.id, "prefix", new_prefix))
    
    @main_config.command(name="verification_channel")
    async def config_verification_channel_id(self, ctx:commands.Context, *, channel:discord.TextChannel):
        await ctx.send(self.edit_config(ctx.guild.id, "verification_channel", channel.id))
    @main_config.command(name="logs_channel")
    async def config_logs_channel(self, ctx:commands.Context, *, channel:discord.TextChannel):
        await ctx.send(self.edit_config(ctx.guild.id, "logs_channel", channel.id))
    @main_config.command(name="info_channel")
    async def config_info_channel(self, ctx:commands.Context, *, channel:discord.TextChannel):
        await ctx.send(self.edit_config(ctx.guild.id, "info_channel", channel.id))
    
    @main_config.command(name="verification_role")
    async def config_verification_role(self, ctx:commands.Context, *, role:discord.Role):
        await ctx.send(self.edit_config(ctx.guild.id, "verification_role", role.id))

    @main_config.command(name="verification_add_role")
    async def config_verification_add_role(self, ctx:commands.Context, value:bool):
        await ctx.send(self.edit_config(ctx.guild.id, "verification_add_role", value))
    
    @main_config.command(name="pass_message")
    async def config_pass_message(self, ctx:commands.Context, *, message):
        await ctx.send(self.edit_config(ctx.guild.id, "pass_message", message))

    @main_config.command(name="contact_channel")
    async def config_contact_channel(self, ctx:commands.Context, *, channel:discord.TextChannel):
        await ctx.send(self.edit_config(ctx.guild.id, "contact_channel", channel.id))
    
    @main_config.command(name="contact_category")
    async def config_contact_category(self, ctx:commands.Context, *, category:discord.CategoryChannel):
        await ctx.send(self.edit_config(ctx.guild.id, "contact_category", category.id))
    
    @main_config.command(name="welcome_roles")
    async def config_welcome_roles(self, ctx:commands.Context, roles:commands.Greedy[discord.Role]):
        if len(roles)==0:
            return
        await ctx.send(self.edit_config(ctx.guild.id, "welcome_roles", [role.id for role in roles]))
    
    

def setup(bot):
    bot.add_cog(Sconfig(bot))
