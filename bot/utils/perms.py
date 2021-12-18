import typing

import nextcord
from nextcord.ext import commands
from utils import Gunibot, MyContext


class Perms(commands.Cog):
    """Cog with a single command, allowing you to see the permissions of a member or a role in a channel."""

    def __init__(self, bot: Gunibot):
        self.bot = bot
        self.file = "perms"
        chan_perms = [key for key, value in nextcord.Permissions().all_channel() if value]
        self.perms_name = {'general': [key for key, value in nextcord.Permissions().general() if value],
                           'text': [key for key, value in nextcord.Permissions().text() if value],
                           'voice': [key for key, value in nextcord.Permissions().voice() if value]}
        self.perms_name['common_channel'] = [
            x for x in chan_perms if x in self.perms_name['general']]

    @commands.command(name='perms', aliases=['permissions'])
    @commands.guild_only()
    async def check_permissions(self, ctx: MyContext, channel: typing.Optional[typing.Union[nextcord.TextChannel, nextcord.VoiceChannel, nextcord.CategoryChannel]] = None, *, target: typing.Union[nextcord.Member, nextcord.Role] = None):
        """Permissions assigned to a member/role (the user by default)
        The channel used to view permissions is the channel in which the command is entered."""
        if target == None:
            target = ctx.author
        perms = None
        if isinstance(target, nextcord.Member):
            if channel == None:
                perms = target.guild_permissions
            else:
                perms = channel.permissions_for(target)
            col = target.color
            avatar = await self.bot.user_avatar_as(target, size=256)
            name = str(target)
        elif isinstance(target, nextcord.Role):
            perms = target.permissions
            if channel != None:
                perms.update(
                    **{x[0]: x[1] for x in channel.overwrites_for(ctx.guild.default_role) if x[1] != None})
                perms.update(**{x[0]: x[1] for x in channel.overwrites_for(target) if x[1] != None})
            col = target.color
            avatar = ctx.guild.icon_url_as(format='png', size=256)
            name = str(target)
        permsl = list()
        
        if perms is None:
            return

        async def perms_tr(x) -> str:
            """Get the translation of a permission"""
            return await self.bot._(ctx.guild.id, "perms.list."+x)

        # Get the perms translations
        if perms.administrator:
            # If the user is admin, we just say it
            permsl.append(":white_check_mark: " + await perms_tr('administrator'))
        else:
            # Here we check if the value of each permission is True.
            for perm, value in perms:
                if (perm not in self.perms_name['text']+self.perms_name['common_channel'] and isinstance(channel, nextcord.TextChannel)) or (perm not in self.perms_name['voice']+self.perms_name['common_channel'] and isinstance(channel, nextcord.VoiceChannel)):
                    continue
                perm = await perms_tr(perm)
                if 'perms.list.' in perm:
                    # missing translation
                    perm = perm.replace('_', ' ').title()
                    self.bot.log.warn(f"[perms] missing permission translation: {perm}")
                if value:
                    permsl.append(":white_check_mark: " + perm)
                else:
                    permsl.append(":x: " + perm)
        if ctx.can_send_embed:
            # \uFEFF is a Zero-Width Space, which basically allows us to have an empty field name.
            # And to make it look nice, we wrap it in an Embed.
            desc = "Permissions générales" if channel is None else channel.mention
            embed = nextcord.Embed(color=col, description=desc)
            embed.set_author(name=name, icon_url=avatar)
            if len(permsl) > 10:
                sep = int(len(permsl)/2)
                if len(permsl) % 2 == 1:
                    sep += 1
                embed.add_field(name='\uFEFF', value="\n".join(permsl[:sep]))
                embed.add_field(name='\uFEFF', value="\n".join(permsl[sep:]))
            else:
                embed.add_field(name='\uFEFF', value="\n".join(permsl))
            await ctx.send(embed=embed)
            # Thanks to Gio for the Command.
        else:
            try:
                await ctx.send("**Permission de '{}' :**\n\n".format(name.replace('@', '')) + "\n".join(permsl))
            except:
                pass


def setup(bot):
    bot.add_cog(Perms(bot))
