import discord
from discord.ext import commands
import io
import json
import asyncio
import checks
import args

roles_config = ('verification_role', 'welcome_roles', 'voice_roles',
                'contact_roles', 'thanks_allowed_roles')
channels_config = ('verification_channel', 'logs_channel',
                   'info_channel', 'contact_channel', 'voice_channel')
categories_config = ('contact_category', 'voices_category')
duration_config = ('thanks_duration')


class Sconfig(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.file = "sconfig"

    def edit_config(self, guildID, key, value):
        if value is None:
            del self.bot.server_configs[guildID][key]
            return f"L'option `{key}` a bien été remise à zéro !"
        try:
            self.bot.server_configs[guildID][key] = value
        except ValueError:
            return "Cette option de configuration n'existe pas :confused:"
        else:
            return f"L'option `{key}` a bien été modifiée !"

    async def format_config(self, guild: discord.Guild, key: str, value: str, mention: bool = True) -> str:
        if value is None:
            return None

        def getname(x): return (x.mention if mention else x.name)
        sep = ' ' if mention else ' | '
        if key in roles_config:
            value = [value] if isinstance(value, int) else value
            roles = [guild.get_role(x) for x in value]
            roles = [getname(x) for x in roles if x is not None]
            return sep.join(roles)
        if key in channels_config:
            value = [value] if isinstance(value, int) else value
            channels = [guild.get_channel(x) for x in value]
            channels = [getname(x) for x in channels if x is not None]
            return sep.join(channels)
        if key in categories_config:
            value = [value] if isinstance(value, int) else value
            categories = [guild.get_channel(x) for x in value]
            categories = [x.name for x in categories if x is not None]
            return " | ".join(categories)
        if key in duration_config:
            return await self.bot.get_cog("TimeCog").time_delta(value, lang='fr', year=True, precision=0)
        if key == 'modlogs_flags':
            flags = self.bot.get_cog("ConfigCog").LogsFlags().intToFlags(value)
            return " - ".join(flags) if len(flags) > 0 else None
        return value

    @commands.group(name="config")
    @commands.guild_only()
    @commands.check(checks.is_admin)
    async def main_config(self, ctx: commands.Context):
        """Edit your server configuration"""
        if ctx.subcommand_passed is None:
            res = ""
            config = ctx.bot.server_configs[ctx.guild.id]
            max_length = max([len(k)+2 for k in config.keys()])
            # Let's desactivate embeds with a small False
            if False and ctx.guild.me.guild_permissions.embed_links:
                emb = discord.Embed(
                    title="Server configuration", color=16098851)
                for k, v in sorted(config.items()):
                    v = await self.format_config(ctx.guild, k, v, True)
                    emb.add_field(name=k, value=v, inline=False)
                await ctx.send(embed=emb)
            else:
                for k, v in sorted(config.items()):
                    v = await self.format_config(ctx.guild, k, v, False)
                    res += (f"[{k}]").ljust(max_length+1) + f" {v}\n"
                res = "```ini\n"+res+"```"
                await ctx.send(res)
        elif ctx.invoked_subcommand is None:
            await ctx.send("Option inexistante")

    @main_config.command(name="prefix")
    async def config_prefix(self, ctx: commands.Context, new_prefix=None):
        if new_prefix is not None and len(new_prefix) > 5:
            await ctx.send("Le préfixe doit faire moins de 5 caractères !")
            return
        await ctx.send(self.edit_config(ctx.guild.id, "prefix", new_prefix))

    @main_config.command(name="verification_channel")
    async def config_verification_channel_id(self, ctx: commands.Context, *, channel: discord.TextChannel):
        await ctx.send(self.edit_config(ctx.guild.id, "verification_channel", channel.id))

    @main_config.command(name="logs_channel")
    async def config_logs_channel(self, ctx: commands.Context, *, channel: discord.TextChannel):
        await ctx.send(self.edit_config(ctx.guild.id, "logs_channel", channel.id))
        logs_cog = self.bot.get_cog("Logs")
        if logs_cog:
            emb = discord.Embed(title="Configuration activée",
                                description="Ce salon sera maintenant utilisé pour les logs du serveur", color=16098851)
            await logs_cog.send_embed(ctx.guild, emb)

    @main_config.command(name="info_channel")
    async def config_info_channel(self, ctx: commands.Context, *, channel: discord.TextChannel):
        await ctx.send(self.edit_config(ctx.guild.id, "info_channel", channel.id))

    @main_config.command(name="verification_role")
    async def config_verification_role(self, ctx: commands.Context, *, role: discord.Role):
        await ctx.send(self.edit_config(ctx.guild.id, "verification_role", role.id))

    @main_config.command(name="verification_add_role")
    async def config_verification_add_role(self, ctx: commands.Context, value: bool):
        await ctx.send(self.edit_config(ctx.guild.id, "verification_add_role", value))

    @main_config.command(name="pass_message")
    async def config_pass_message(self, ctx: commands.Context, *, message):
        await ctx.send(self.edit_config(ctx.guild.id, "pass_message", message))

    @main_config.command(name="contact_channel")
    async def config_contact_channel(self, ctx: commands.Context, *, channel: discord.TextChannel):
        await ctx.send(self.edit_config(ctx.guild.id, "contact_channel", channel.id))

    @main_config.command(name="contact_category")
    async def config_contact_category(self, ctx: commands.Context, *, category: discord.CategoryChannel):
        await ctx.send(self.edit_config(ctx.guild.id, "contact_category", category.id))

    @main_config.command(name="contact_roles")
    async def config_contact_roles(self, ctx: commands.Context, roles: commands.Greedy[discord.Role]):
        if len(roles) == 0:
            roles = None
        else:
            roles = [role.id for role in roles]
        await ctx.send(self.edit_config(ctx.guild.id, "contact_roles", roles))

    @main_config.command(name="welcome_roles")
    async def config_welcome_roles(self, ctx: commands.Context, roles: commands.Greedy[discord.Role]):
        if len(roles) == 0:
            roles = None
        else:
            roles = [role.id for role in roles]
        await ctx.send(self.edit_config(ctx.guild.id, "welcome_roles", roles))

    @main_config.command(name="voices_category")
    async def config_voices_category(self, ctx: commands.Context, *, category: discord.CategoryChannel):
        await ctx.send(self.edit_config(ctx.guild.id, "voices_category", category.id))

    @main_config.command(name="voice_channel")
    async def config_voice_channel(self, ctx: commands.Context, *, channel: discord.VoiceChannel):
        await ctx.send(self.edit_config(ctx.guild.id, "voice_channel", channel.id))

    @main_config.command(name="modlogs_flags")
    async def config_modlogs_flags(self, ctx: commands.Context):
        await ctx.send("Cette option n'est pas directement modifiable. Vous pouvez utiliser les commandes `{p}config modlogs enable/disable <option>` pour activer ou désactiver certains logs, et `{p}config modlogs list` pour avoir la liste des logs possibles.".format(p=ctx.prefix))

    @main_config.group(name="modlogs")
    async def config_modlogs(self, ctx: commands.Context):
        """Enable or disable logs categories in your logs channel
        You can set your channel with the 'logs_channel' config option"""
        if ctx.subcommand_passed is None:
            await ctx.send_help("config modlogs")

    @config_modlogs.command(name="enable")
    async def modlogs_enable(self, ctx: commands.Context, options: commands.Greedy[args.moderatorFlag]):
        """Enable one or multiple logs categories"""
        if not options:
            await ctx.send("Catégorie invalide")
            return
        LogsFlags = self.bot.get_cog('ConfigCog').LogsFlags()
        flags = self.bot.server_configs[ctx.guild.id]['modlogs_flags']
        flags = LogsFlags.intToFlags(flags) + options
        flags = list(set(flags)) # remove duplicates
        self.edit_config(ctx.guild.id, 'modlogs_flags',
                         LogsFlags.flagsToInt(flags))
        await ctx.send("Les logs de type {} ont bien été activés".format(', '.join(options)))

    @config_modlogs.command(name="disable")
    async def modlogs_disable(self, ctx: commands.Context, options: commands.Greedy[args.moderatorFlag]):
        """Disable one or multiple logs categories"""
        if not options:
            await ctx.send("Catégorie invalide")
            return
        LogsFlags = self.bot.get_cog('ConfigCog').LogsFlags()
        flags = self.bot.server_configs[ctx.guild.id]['modlogs_flags']
        flags = LogsFlags.intToFlags(flags)
        flags = [x for x in flags if x not in options]
        self.edit_config(ctx.guild.id, 'modlogs_flags', LogsFlags.flagsToInt(flags))
        await ctx.send("Les logs de type {} ont bien été désactivés".format(', '.join(options)))

    @config_modlogs.command(name="list")
    async def modlogs_list(self, ctx: commands.Context):
        """See available logs categories"""
        f = self.bot.get_cog('ConfigCog').LogsFlags.FLAGS.values()
        await ctx.send("Liste des logs disponibles : " + " - ".join(f))

    @main_config.command(name="voice_channel_format")
    async def config_voice_channel_format(self, ctx: commands.Context, *, text: str):
        """Format of voice channels names
        Use {random} for any random name, {asterix} for any asterix name"""
        await ctx.send(self.edit_config(ctx.guild.id, "voice_channel_format", text[:40]))

    @main_config.command(name="voice_roles")
    async def config_voice_roles(self, ctx: commands.Context, roles: commands.Greedy[discord.Role]):
        if len(roles) == 0:
            roles = None
        else:
            roles = [role.id for role in roles]
        await ctx.send(self.edit_config(ctx.guild.id, "voice_roles", roles))

    @main_config.command(name="thanks_allowed_roles")
    async def config_thanks_allowed_roles(self, ctx: commands.Context, roles: commands.Greedy[discord.Role]):
        if len(roles) == 0:
            roles = None
        else:
            roles = [role.id for role in roles]
        await ctx.send(self.edit_config(ctx.guild.id, "thanks_allowed_roles", roles))

    @main_config.command(name="thanks_duration")
    async def config_thanks_duration(self, ctx: commands.Context, duration: commands.Greedy[args.tempdelta]):
        duration = sum(duration)
        if duration == 0:
            if ctx.message.content.split(" ")[-1] != "thanks_duration":
                await ctx.send("Durée invalide")
                return
            duration = None
        x = self.edit_config(ctx.guild.id, "thanks_duration", duration)
        await ctx.send(x)

    @commands.group(name="config-backup", aliases=["config-bkp"])
    @commands.guild_only()
    @commands.check(checks.is_admin)
    async def config_backup(self, ctx: commands.Context):
        """Create or load your server configuration"""
        if ctx.subcommand_passed is None:
            await ctx.send_help('config-backup')

    @config_backup.command(name="get", aliases=["create"])
    async def backup_create(self, ctx: commands.Context):
        "Create a backup of your configuration"
        data = json.dumps(self.bot.server_configs[ctx.guild.id])
        data = io.BytesIO(data.encode("utf8"))
        await ctx.send("Here you go!", file=discord.File(data, filename="config-backup.json"))

    @config_backup.command(name="load")
    async def backup_load(self, ctx: commands.Context):
        "Load a backup of your configuration (in attached file) and apply it"
        if not (ctx.message.attachments and ctx.message.attachments[0].filename.endswith(".json")):
            await ctx.send("Aucun fichier compatible trouvé")
            return
        data = json.loads(await ctx.message.attachments[0].read())
        conf = self.bot.server_configs[ctx.guild.id]
        for k in data.keys():
            if not k in conf.keys():
                await ctx.send("Fichier incompatible")
                return
        merge = {k: v for k, v in data.items() if v != conf[k]}
        if len(merge) == 0:
            await ctx.send("Aucune modification appliquable")
            return
        msg = await ctx.send("Êtes-vous sûr de vouloir écraser votre configuration ? Cela écrasera {} options".format(len(merge)))
        await msg.add_reaction("✅")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) == "✅" and reaction.message.id == msg.id
        try:
            await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send('Trop long ! Abandon de la procédure')
        else:
            d = dict(self.bot.server_configs[ctx.guild.id])
            d.update(merge)
            self.bot.server_configs[ctx.guild.id] = d
            await ctx.send('👍')

    @main_config.group(name="thanks", aliases=['thx'], enabled=False)
    async def thanks_main(self, ctx: commands.Context):
        """Edit your thanks-levels settings"""
        if ctx.subcommand_passed is None:
            await ctx.send_help("config thanks")

    @thanks_main.command(name="list")
    async def thanks_list(self, ctx: commands.Context):
        """List your current thanks levels"""
        await self.bot.get_cog("Thanks").thankslevels_list(ctx)

    @thanks_main.command(name="add")
    async def thanks_add(self, ctx: commands.Context, amount: int, role: discord.Role):
        """Add a role to give when someone reaches a certain amount of thanks"""
        await self.bot.get_cog("Thanks").thankslevel_add(ctx, amount, role)
    
    @thanks_main.command(name="reset")
    async def thanks_reset(self, ctx: commands.Context, amount: int = None):
        """Remove every role given for a certain amount of thanks
        If no amount is specified, it will reset the whole configuration"""
        if amount is None:
            await self.bot.get_cog("Thanks").thankslevel_reset(ctx)
        else:
            await self.bot.get_cog("Thanks").thankslevel_remove(ctx, amount)




def setup(bot):
    bot.add_cog(Sconfig(bot))
    if bot.get_cog("Thanks"):
        bot.get_command("config thanks").enabled = True
