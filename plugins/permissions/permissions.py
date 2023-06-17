"""
Ce programme est régi par la licence CeCILL soumise au droit français et
respectant les principes de diffusion des logiciels libres. Vous pouvez
utiliser, modifier et/ou redistribuer ce programme sous les conditions
de la licence CeCILL diffusée sur le site "http://www.cecill.info".
"""

import typing

import discord
from discord.ext import commands

from utils import Gunibot, MyContext
from core import setup_logger


class Perms(commands.Cog):
    """Cog with a command allowing you to see the permissions of a member or a role in a channel."""

    def __init__(self, bot: Gunibot):
        self.bot = bot
        self.file = "perms"
        chan_perms = [
            key for key, value in discord.Permissions().all_channel() if value
        ]
        self.perms_name = {
            "general": [key for key, value in discord.Permissions().general() if value],
            "text": [key for key, value in discord.Permissions().text() if value],
            "voice": [key for key, value in discord.Permissions().voice() if value],
        }
        self.perms_name["common_channel"] = [
            x for x in chan_perms if x in self.perms_name["general"]
        ]
        self.logger = setup_logger('perms')

    @commands.command(name="perms", aliases=["permissions"])
    @commands.guild_only()
    async def check_permissions(
        self,
        ctx: MyContext,
        channel: typing.Optional[
            typing.Union[
                discord.TextChannel, discord.VoiceChannel, discord.CategoryChannel
            ]
        ] = None,
        *,
        target: typing.Union[discord.Member, discord.Role] = None,
    ):
        """Permissions assigned to a member/role (the user by default)
        The channel used to view permissions is the channel in which the command is entered."""
        if target is None:
            target = ctx.author
        perms = None
        if isinstance(target, discord.Member):
            if channel is None:
                perms = target.guild_permissions
            else:
                perms = channel.permissions_for(target)
            col = target.color
            avatar = await self.bot.user_avatar_as(target, size=256)
            name = str(target)
        elif isinstance(target, discord.Role):
            perms = target.permissions
            if channel is not None:
                perms.update(
                    **{
                        x[0]: x[1]
                        for x in channel.overwrites_for(ctx.guild.default_role)
                        if x[1] is not None
                    }
                )
                perms.update(
                    **{
                        x[0]: x[1]
                        for x in channel.overwrites_for(target)
                        if x[1] is not None
                    }
                )
            col = target.color
            if target.guild.icon is not None: # the guild could have no icon
                avatar = ctx.guild.icon.with_size(256).with_format('png')
            else:
                avatar = None
            name = str(target)
        permsl = list()

        if perms is None:
            return

        async def perms_tr(perm) -> str:
            """Get the translation of a permission"""
            return await self.bot._(ctx.guild.id, "perms.list." + perm)

        # Get the perms translations
        if perms.administrator:
            # If the user is admin, we just say it
            permsl.append(":white_check_mark: " + await perms_tr("administrator"))
        else:
            # Here we check if the value of each permission is True.
            for perm, value in perms:
                if (
                    perm
                    not in self.perms_name["text"] + self.perms_name["common_channel"]
                    and isinstance(channel, discord.TextChannel)
                ) or (
                    perm
                    not in self.perms_name["voice"] + self.perms_name["common_channel"]
                    and isinstance(channel, discord.VoiceChannel)
                ):
                    continue
                perm = await perms_tr(perm)
                if "perms.list." in perm:
                    # missing translation
                    perm = perm.replace("_", " ").title()
                    self.logger.warning("[perms] missing permission translation: %s", perm)
                if value:
                    permsl.append(":white_check_mark: " + perm)
                else:
                    permsl.append(":x: " + perm)
        if ctx.can_send_embed:
            # \uFEFF is a Zero-Width Space, which basically allows us to have an empty field name.
            # And to make it look nice, we wrap it in an Embed.
            desc = "Permissions générales" if channel is None else channel.mention
            embed = discord.Embed(color=col, description=desc)
            embed.set_author(name=name, icon_url=avatar)
            if len(permsl) > 10:
                sep = int(len(permsl) / 2)
                if len(permsl) % 2 == 1:
                    sep += 1
                embed.add_field(name="\uFEFF", value="\n".join(permsl[:sep]))
                embed.add_field(name="\uFEFF", value="\n".join(permsl[sep:]))
            else:
                embed.add_field(name="\uFEFF", value="\n".join(permsl))
            await ctx.send(embed=embed)
            # Thanks to Gio for the Command.
        else:
            await ctx.send(
                f"**Permission de '{name.replace('@', '')}' :**\n\n" + "\n".join(permsl),
            )


async def setup(bot: Gunibot = None):
    await bot.add_cog(Perms(bot))
