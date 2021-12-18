import sys
sys.path.append("./bot")
import checks
import nextcord
from nextcord.channel import TextChannel
from nextcord.ext import commands
from utils import Gunibot, MyContext

WELCOME_MESSAGE = """(FR) Bienvenue sur {server} {user} !
Vous n'avez accès qu'au salon Lobby pour le moment. Pour débloquer l'accès au reste du Discord, lisez les instructions présentes dans le salon {channel} :wink:

(EN) Welcome to {server} {user} !
You only have access to the Lobby channel. To unlock the acess to the rest of our Discord, please follow the instructions in the {channel} channel :wink:"""

CONFIRM_MESSAGE = """{user} a lu {channel}

{user} read {channel}"""


class Antikikoo(commands.Cog):
    """Prevents kikoos from entering the server"""

    def __init__(self, bot: Gunibot):
        self.bot = bot
        self.config_options = ["verification_channel", "info_channel", "pass_message", "verification_add_role", "verification_info_message", "verification_role"]

    @commands.Cog.listener()
    async def on_member_join(self, member: nextcord.Member):
        """Called when a member joins a guild
        Sends a message in the verification channel to inform new users"""
        self.bot.log.info(f"{member} ({member.id}) joined the server")
        config = self.bot.server_configs[member.guild.id]
        if config["verification_channel"] is None or config["verification_info_message"] == "None":  # if nothing has been configured
            return
        verif_channel: TextChannel = self.bot.get_channel(config["verification_channel"])
        info_channel = "<#{}>".format(config["info_channel"])
        welcome_msg: str = config["verification_info_message"] or WELCOME_MESSAGE # if config is None, we use the default one
        await verif_channel.send(welcome_msg.format(user=member.mention, channel=info_channel, server=member.guild.name))

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        """Called for every new message
        We use it to check when someone send the verification message"""
        if message.guild is None:  # if the message is not in a server
            return
        config = self.bot.server_configs[message.guild.id]
        if message.channel.id != config["verification_channel"]:
            return
        info_channel = "<#{}>".format(config["info_channel"])
        if message.content.lower() == config["pass_message"].lower():
            emb = nextcord.Embed(description=CONFIRM_MESSAGE.format(
                user=message.author.mention, channel=info_channel))
            await message.channel.send(embed=emb)
            try:
                await message.delete()
            except:
                self.bot.log.exception("Cannot delete the verification message")
            verif_role = message.guild.get_role(config["verification_role"])
            if verif_role == None:
                return
            try:
                if config["verification_add_role"]:
                    await message.author.add_roles(verif_role)
                else:
                    await message.author.remove_roles(verif_role)
            except:
                self.bot.log.exception(
                    f"Cannot give or take away verification role from member {message.author}")

    @commands.group(name="antikikoo", aliases=["ak", "antitroll"])
    @commands.guild_only()
    async def ak_main(self, ctx: MyContext):
        """Kikoo filter configuration"""
        if ctx.subcommand_passed is None:
            await ctx.send_help('antikikoo')

    @ak_main.command(name="channel")
    @commands.check(checks.is_admin)
    async def ak_channel(self, ctx: MyContext, channel: nextcord.TextChannel):
        """Modifies the channel where members will have to check themselves"""
        self.bot.server_configs[ctx.guild.id]["verification_channel"] = channel.id
        await ctx.send(await self.bot._(ctx.guild.id, "antikikoo.channel-edited", channel=channel.mention))
    
    @ak_main.command(name="info_message")
    @commands.check(checks.is_admin)
    async def ak_msg(self, ctx: MyContext, *, message: str = None):
        """Modifies the informative message sent in the verification channel
        Put nothing to reset it, or "None" for no message"""
        if message.lower() == "none":
            value = "None" # no message
        self.bot.server_configs[ctx.guild.id]["verification_info_message"] = message
        await ctx.send(await self.bot._(ctx.guild.id, "antikikoo.msg-edited"))


def setup(bot):
    bot.add_cog(Antikikoo(bot))
