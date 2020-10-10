import discord
import typing
from discord.ext import commands

perms_translations = {
    "add_reactions": "Ajouter des réactions",
    "administrator": "Administrateur",
    "attach_files": "Joindre des fichiers",
    "ban_members": "Bannir des membres",
    "change_nickname": "Changer de pseudo",
    "connect": "Se connecter",
    "create_instant_invite": "Créer une invitation",
    "deafen_members": "Mettre en sourdine des membres",
    "embed_links": "Intégrer des liens",
    "external_emojis": "Utiliser des émojis externes",
    "kick_members": "Expulser des membres",
    "manage_channels": "Gérer les salons",
    "manage_emojis": "Gérer les émojis",
    "manage_guild": "Gérer le serveur",
    "manage_messages": "Gérer les messages",
    "manage_nicknames": "Gérer les pseudos",
    "manage_roles": "Gérer les rôles",
    "manage_webhooks": "Gérer les webhooks",
    "mention_everyone": "Mentionner tout le monde",
    "move_members": "Déplacer des membres",
    "mute_members": "Couper le micro de membres",
    "priority_speaker": "Voix prioritaire",
    "read_message_history": "Voir les anciens messages",
    "read_messages": "Lire les messages",
    "send_messages": "Envoyer des messages",
    "send_tts_messages": "Envoyer des messages TTS",
    "speak": "Parler",
    "stream": "Passer en direct",
    "use_voice_activation": "Utiliser la Détection de la voix",
    "view_audit_log": "Voir les logs du serveur",
    "view_guild_insights": "Voir les analyses de serveur"
}


class Perms(commands.Cog):
    """Cog with a single command, allowing you to see the permissions of a member or a role in a channel."""

    def __init__(self, bot):
        self.bot = bot
        self.file = "perms"
        chan_perms = [key for key, value in discord.Permissions().all_channel() if value]
        self.perms_name = {'general': [key for key, value in discord.Permissions().general() if value],
                           'text': [key for key, value in discord.Permissions().text() if value],
                           'voice': [key for key, value in discord.Permissions().voice() if value]}
        self.perms_name['common_channel'] = [
            x for x in chan_perms if x in self.perms_name['general']]

    @commands.command(name='perms', aliases=['permissions'])
    @commands.guild_only()
    async def check_permissions(self, ctx, channel: typing.Optional[typing.Union[discord.TextChannel, discord.VoiceChannel]] = None, *, target: typing.Union[discord.Member, discord.Role] = None):
        """Permissions assigned to a member/role (the user by default)
        The channel used to view permissions is the channel in which the command is entered."""
        if target == None:
            target = ctx.author
        if isinstance(target, discord.Member):
            if channel == None:
                perms = target.guild_permissions
            else:
                perms = channel.permissions_for(target)
            col = target.color
            avatar = await self.bot.user_avatar_as(target, size=256)
            name = str(target)
        elif isinstance(target, discord.Role):
            perms = target.permissions
            if channel != None:
                perms.update(
                    **{x[0]: x[1] for x in channel.overwrites_for(ctx.guild.default_role) if x[1] != None})
                perms.update(**{x[0]: x[1] for x in channel.overwrites_for(target) if x[1] != None})
            col = target.color
            avatar = ctx.guild.icon_url_as(format='png', size=256)
            name = str(target)
        permsl = list()
        # Get the perms translations

        # if perms[""]
        if perms.administrator:
            # If the user is admin, we just say it
            if "administrator" in perms_translations.keys():
                perm = perms_translations["administrator"]
            else:
                perm = "Administrator"
            permsl.append(":white_check_mark:" + perm)
        else:
            # Here we check if the value of each permission is True.
            for perm, value in perms:
                if (perm not in self.perms_name['text']+self.perms_name['common_channel'] and isinstance(channel, discord.TextChannel)) or (perm not in self.perms_name['voice']+self.perms_name['common_channel'] and isinstance(channel, discord.VoiceChannel)):
                    continue
                #perm = perm.replace('_',' ').title()
                if perm in perms_translations.keys():
                    perm = perms_translations[perm]
                else:
                    perm = perm.replace('_', ' ').title()
                if value:
                    permsl.append(":white_check_mark:" + perm)
                else:
                    permsl.append(":x:" + perm)
        if ctx.channel.permissions_for(ctx.guild.me).embed_links:
            # \uFEFF is a Zero-Width Space, which basically allows us to have an empty field name.
            # And to make it look nice, we wrap it in an Embed.
            desc = "Permissions générales" if channel is None else channel.mention
            embed = discord.Embed(color=col, description=desc)
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
