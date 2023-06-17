"""
Ce programme est régi par la licence CeCILL soumise au droit français et
respectant les principes de diffusion des logiciels libres. Vous pouvez
utiliser, modifier et/ou redistribuer ce programme sous les conditions
de la licence CeCILL diffusée sur le site "http://www.cecill.info".
"""

import sys

import discord
from discord.ext import commands
from discord.channel import TextChannel

from utils import Gunibot, MyContext
from core import setup_logger

# pylint: disable=line-too-long
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
        self.config_options = [
            "verification_channel",
            "info_channel",
            "pass_message",
            "verification_add_role",
            "verification_info_message",
            "verification_role",
        ]
        self.logger = setup_logger("antikikoo")

        bot.get_command("config").add_command(self.ak_channel)
        bot.get_command("config").add_command(self.ak_msg)
        bot.get_command("config").add_command(self.pass_message)
        bot.get_command("config").add_command(self.info_channel)
        bot.get_command("config").add_command(self.verification_role)
        bot.get_command("config").add_command(self.verification_add_role)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Called when a member joins a guild
        Sends a message in the verification channel to inform new users"""
        self.logger.info(f"{member} ({member.id}) joined the server")
        config = self.bot.server_configs[member.guild.id]
        # if nothing has been configured
        if (
            config["verification_channel"] is None
            or config["verification_info_message"] == "None"
        ):
            return
        verif_channel: TextChannel = self.bot.get_channel(
            config["verification_channel"]
        )
        info_channel = f"<#{config['info_channel']}>"
        # if config is None, we use the default one
        welcome_msg: str = config["verification_info_message"] or WELCOME_MESSAGE
        await verif_channel.send(
            welcome_msg.format(
                user=member.mention, channel=info_channel, server=member.guild.name
            )
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Called for every new message
        We use it to check when someone send the verification message"""
        if message.guild is None:  # if the message is not in a server
            return
        config = self.bot.server_configs[message.guild.id]
        if message.channel.id != config["verification_channel"]:
            return

        if config["pass_message"] is None: # not set
            return

        info_channel = f"<#{config['info_channel']}>"
        if message.content.lower() == config["pass_message"].lower():
            emb = discord.Embed(
                description=CONFIRM_MESSAGE.format(
                    user=message.author.mention, channel=info_channel
                )
            )
            await message.channel.send(embed=emb)
            try:
                await message.delete()
            except BaseException:
                self.logger.exception("Cannot delete the verification message")
            verif_role = message.guild.get_role(config["verification_role"])
            if verif_role is None:
                return
            try:
                if config["verification_add_role"]:
                    await message.author.add_roles(verif_role)
                else:
                    await message.author.remove_roles(verif_role)
            except BaseException:
                self.logger.exception(
                    f"Cannot give or take away verification role from member {message.author}"
                )

    @commands.group(name="antikikoo", aliases=["ak", "antitroll"])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def ak_main(self, ctx: MyContext):
        """Kikoo filter configuration"""
        if ctx.subcommand_passed is None:
            await ctx.send_help("antikikoo")

    @ak_main.command(name="verification_channel")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def ak_channel(self, ctx: MyContext, channel: discord.TextChannel):
        """Modifies the channel where members will have to check themselves"""
        self.bot.server_configs[ctx.guild.id]["verification_channel"] = channel.id
        await ctx.send(
            await self.bot._(
                ctx.guild.id, "antikikoo.channel-edited", channel=channel.mention
            )
        )

    @ak_main.command(name="verification_info_message")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def ak_msg(self, ctx: MyContext, *, message: str = None):
        """Modifies the informative message sent in the verification channel
        Put nothing to reset it, or "None" for no message"""
        self.bot.server_configs[ctx.guild.id]["verification_info_message"] = message
        await ctx.send(await self.bot._(ctx.guild.id, "antikikoo.msg-edited"))

    @commands.command(name='pass_message')
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def pass_message(
        self,
        context: MyContext,
        message: str,
    ):
        """Set the pass message required to enter the server."""
        # because of the check above, we don't need to check again
        config = self.bot.server_configs[context.guild.id]
        config['pass_message'] = message
        await context.send(
            await self.bot._(
                context.guild.id, "antikikoo.pass-edited",
            )
        )

    @commands.command(name='info_channel')
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def info_channel(
        self,
        context: MyContext,
        channel: discord.TextChannel,
    ):
        """Change the channel where users can read more informations about the rules."""
        # because of the check above, we don't need to check again
        config = self.bot.server_configs[context.guild.id]
        config['info_channel'] = channel.id
        await context.send(
            await self.bot._(
                context.guild.id,
                "antikikoo.info-channel-edited",
                channel=channel.mention,
            )
        )

    @commands.command(name='verification_role')
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def verification_role(
        self,
        context: MyContext,
        role: discord.Role,
    ):
        """Set the role given by the bot when the user gets verified.
        Use the command "config verification_add_role" to toggle on or off.
        """
        config = self.bot.server_configs[context.guild.id]
        config['verification_role'] = role.id
        await context.send(
            await self.bot._(
                context.guild.id,
                "antikikoo.role-edited",
                role=role.mention,
            ),
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @commands.command(name='verification_add_role')
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def verification_add_role(
        self,
        context: MyContext,
        enabled: bool = True,
    ):
        """Enable or disable the give role feature of the verification system.
        """
        config = self.bot.server_configs[context.guild.id]
        config['verification_add_role'] = enabled
        role = context.guild.get_role(config['verification_role'])
        await context.send(
            await self.bot._(
                context.guild.id,
                "antikikoo.add-role-enabled" if enabled else "antikikoo.add-role-disabled",
                role=role.mention,
            ),
            allowed_mentions=discord.AllowedMentions.none(),
        )


async def setup(bot:Gunibot=None):
    if bot is not None:
        await bot.add_cog(Antikikoo(bot), icon="⛔")
