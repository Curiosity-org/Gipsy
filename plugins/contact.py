import discord
import aiohttp
import typing
from discord.ext import commands
from discord.utils import snowflake_time
from datetime import datetime, timedelta
import checks


class Contact(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.file = "contact"

    async def urlToByte(self, url: str) -> typing.Optional[bytes]:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(url) as response:
                if response.status >= 200 and response.status < 300:
                    res = await response.read()
                else:
                    res = None
        return res

    def db_get_channels(self, guildID: int):
        c = self.bot.database.cursor()
        c.execute('SELECT * FROM contact_channels WHERE guild=?', (guildID,))
        res = list(c)
        c.close()
        return res

    def db_add_channel(self, channel: discord.TextChannel):
        c = self.bot.database.cursor()
        c.execute(f"INSERT INTO contact_channels (guild,channel, author) VALUES (?, ?, ?)",
                  (channel.guild.id, channel.id, int(channel.topic)))
        self.bot.database.commit()
        c.close()

    def db_delete_channel(self, guildID: int, channelID: int):
        c = self.bot.database.cursor()
        c.execute(f"DELETE FROM contact_channels WHERE guild=? AND channel=?",
                  (guildID, channelID))
        self.bot.database.commit()
        c.close()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Called for every new message
        We use it to check when someone send a message in the contact channel"""
        if message.guild is None:  # si le message n'est pas dans un serveur
            return
        if message.author.bot:  # si le message a été envoyé par un bot
            return
        config = self.bot.server_configs[message.guild.id]
        if message.channel.id != config["contact_channel"]:
            return
        category: discord.CategoryChannel = self.bot.get_channel(config["contact_category"])
        channel: discord.TextChannel = discord.utils.get(
            category.text_channels, topic=str(message.author.id))
        if channel is None:
            try:
                perms = dict()
                if config["contact_roles"]:
                    over = discord.PermissionOverwrite(**dict(discord.Permissions.all()))
                    perms = {message.guild.get_role(x): over for x in config["contact_roles"]}
                    if message.guild.default_role not in perms.keys():
                        perms[message.guild.default_role] = discord.PermissionOverwrite(
                            read_messages=False)
                    perms.pop(None, None)
                perms[message.author] = discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True,
                                                                    embed_links=True, attach_files=True, read_message_history=True, use_external_emojis=True, add_reactions=True)
                channel = await category.create_text_channel(str(message.author), topic=str(message.author.id), overwrites=perms)
                self.db_add_channel(channel)
            except discord.errors.Forbidden as e:
                await self.bot.get_cog("Errors").on_error(e, await self.bot.get_context(message))
                return
        else:
            if channel.name != str(message.author):
                await channel.edit(name=str(message.author))
        try:
            webhook = await channel.create_webhook(name=message.author.name)
            await webhook.send(message.content, avatar_url=message.author.avatar_url)
        except discord.Forbidden:
            await channel.send(message.content)
        try:
            await message.delete()
        except discord.errors.Forbidden:
            pass

    @commands.command(name="contact-clear", aliases=["ct-clear"])
    @commands.check(checks.is_admin)
    @commands.guild_only()
    async def ct_clear(self, ctx: commands.Context, days: int = 15):
        """Nettoie tous les salons inutilisés depuix X jours"""
        if days < 1:
            await ctx.send("Vous ne pouvez pas choisir une durée de moins d'un jour")
            return
        categ_id = self.bot.server_configs[ctx.guild.id]["contact_category"]
        if categ_id is None:
            await ctx.send("Aucune catégorie de contact n'a été créée !")
            return
        categ = ctx.guild.get_channel(categ_id)
        if categ is None:
            await ctx.send("Impossible de trouver la catégorie de contact ! Vérifiez votre configuration")
            return
        i = 0  # compteur de suppressions
        errors = list()  # liste des éventuelles erreurs
        max_date = datetime.now()-timedelta(days=days)
        channels = self.db_get_channels(ctx.guild.id)
        for data in channels:
            chan = ctx.guild.get_channel(data[1])
            if chan is None:
                self.db_delete_channel(ctx.guild.id, data[1])
            else:
                # si la date du dernier message est trop ancienne
                if snowflake_time(chan.last_message_id) < max_date:
                    try:
                        await chan.delete(reason="Channel too old")
                        i += 1
                    except discord.DiscordException as e:
                        errors.append(str(e))
                    else:
                        self.db_delete_channel(ctx.guild.id, data[1])
        answer = "" if i == 0 else f"{i} salons ont été supprimés !"
        if len(errors) > 0:
            answer += "\n{} salons n'ont pu être supprimés :\n • {}".format(
                len(errors), "\n • ".join(errors))
        if len(answer) == 0:  # si aucun salon n'a eu besoin d'être supprimé
            answer = "Aucun salon n'est assez vieux !"
        await ctx.send(answer)


def setup(bot):
    bot.add_cog(Contact(bot))
