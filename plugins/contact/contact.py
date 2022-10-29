import sqlite3
from utils import Gunibot, MyContext
from discord.utils import snowflake_time
from discord.ext import commands
import discord
from bot import checks
import typing
from datetime import datetime, timedelta

import aiohttp
import sys

# sys.path.append("./bot")


class Contact(commands.Cog):
    def __init__(self, bot: Gunibot):
        self.bot = bot
        self.file = "contact"
        self.config_options = [
            "contact_channel",
            "contact_category",
            "contact_roles",
            "contact_title",
        ]

        bot.get_command("config").add_command(self.config_contact_channel)
        bot.get_command("config").add_command(self.config_contact_category)
        bot.get_command("config").add_command(self.config_contact_roles)
        bot.get_command("config").add_command(self.config_contact_title)

    @commands.command(name="contact_channel")
    async def config_contact_channel(
        self, ctx: MyContext, *, channel: discord.TextChannel
    ):
        await ctx.send(
            await self.bot.sconfig.edit_config(
                self, ctx.guild.id, "contact_channel", channel.id
            )
        )

    @commands.command(name="contact_category")
    async def config_contact_category(
        self, ctx: MyContext, *, category: discord.CategoryChannel
    ):
        await ctx.send(
            await self.bot.sconfig.edit_config(
                self, ctx.guild.id, "contact_category", category.id
            )
        )

    @commands.command(name="contact_roles")
    async def config_contact_roles(
        self, ctx: MyContext, roles: commands.Greedy[discord.Role]
    ):
        if len(roles) == 0:
            roles = None
        else:
            roles = [role.id for role in roles]
        await ctx.send(
            await self.bot.sconfig.edit_config(
                self, ctx.guild.id, "contact_roles", roles
            )
        )

    @commands.command(name="contact_title")
    async def config_contact_title(self, ctx: MyContext, *, title):
        if title == "author" or title == "object":
            await ctx.send(
                await self.bot.sconfig.edit_config(
                    self, ctx.guild.id, "contact_title", title
                )
            )
        else:
            await ctx.send(
                await self.bot._(self, ctx.guild.id, "contact.invalid-title")
            )

    async def urlToByte(self, url: str) -> typing.Optional[bytes]:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10)
        ) as session:
            async with session.get(url) as response:
                if response.status >= 200 and response.status < 300:
                    res = await response.read()
                else:
                    res = None
        return res

    def db_get_channels(self, guildID: int):
        query = "SELECT * FROM contact_channels WHERE guild=?"
        res = self.bot.db_query(query, (guildID,))
        return res

    def db_add_channel(self, channel: discord.TextChannel, authorID):
        try:
            query = (
                "INSERT INTO contact_channels (guild,channel, author) VALUES (?, ?, ?)"
            )
            self.bot.db_query(query, (channel.guild.id, channel.id, authorID))
        except sqlite3.OperationalError as e:
            print(e)

    def db_delete_channel(self, guildID: int, channelID: int):
        query = "DELETE FROM contact_channels WHERE guild=? AND channel=?"
        self.bot.db_query(query, (guildID, channelID))

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
        category: discord.CategoryChannel = self.bot.get_channel(
            config["contact_category"]
        )
        if category is None:
            return
        try:
            perms = dict()
            if config["contact_roles"]:
                over = discord.PermissionOverwrite(**dict(discord.Permissions.all()))
                perms = {
                    message.guild.get_role(x): over for x in config["contact_roles"]
                }
                if message.guild.default_role not in perms.keys():
                    perms[message.guild.default_role] = discord.PermissionOverwrite(
                        read_messages=False
                    )
                perms.pop(None, None)
            perms[message.author] = discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True,
                manage_messages=True,
                embed_links=True,
                attach_files=True,
                read_message_history=True,
                use_external_emojis=True,
                add_reactions=True,
            )
            if config["contact_title"] == "author":
                channel = await category.create_text_channel(
                    str(message.author),
                    topic=message.content + " | " + str(message.author.id),
                    overwrites=perms,
                )
            else:
                channel = await category.create_text_channel(
                    message.content[:100],
                    topic=str(message.author) + " - " + str(message.author.id),
                    overwrites=perms,
                )
            self.db_add_channel(channel, message.author.id)

        except discord.errors.Forbidden as e:
            await self.bot.get_cog("Errors").on_error(
                e, await self.bot.get_context(message)
            )
            return
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
            await ctx.send(await self.bot._(ctx.guild.id, "contact.duration-short"))
            return
        categ_id = self.bot.server_configs[ctx.guild.id]["contact_category"]
        if categ_id is None:
            await ctx.send(await self.bot._(ctx.guild.id, "contact.no-category"))
            return
        categ = ctx.guild.get_channel(categ_id)
        if categ is None:
            await ctx.send(await self.bot._(ctx.guild.id, "contact.category-notfound"))
            return
        i = 0  # compteur de suppressions
        errors = list()  # liste des éventuelles erreurs
        max_date = datetime.now() - timedelta(days=days)
        channels = self.db_get_channels(ctx.guild.id)
        for data in channels:
            chan = ctx.guild.get_channel(data["channel"])
            if chan is None:
                self.db_delete_channel(ctx.guild.id, data["channel"])
            else:
                # si la date du dernier message est trop ancienne
                if snowflake_time(chan.last_message_id) < max_date:
                    try:
                        await chan.delete(reason="Channel too old")
                        i += 1
                    except discord.DiscordException as e:
                        errors.append(str(e))
                    else:
                        self.db_delete_channel(ctx.guild.id, data["channel"])
        answer = await self.bot._(ctx.guild.id, "contact.deleted", count=i)
        if len(errors) > 0:
            answer += "\n" + await self.bot._(
                ctx.guild.id, "contact.not-deleted", count=len(errors)
            )
            answer += "\n • {}" + "\n • ".join(errors)
        await ctx.send(answer)


config = {}
async def setup(bot:Gunibot=None, plugin_config:dict=None):
    if bot is not None:
        await bot.add_cog(Contact(bot), icon="💬")
    if plugin_config is not None:
        global config
        config.update(plugin_config)
