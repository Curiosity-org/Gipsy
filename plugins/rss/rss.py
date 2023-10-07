"""
Ce programme est régi par la licence CeCILL soumise au droit français et
respectant les principes de diffusion des logiciels libres. Vous pouvez
utiliser, modifier et/ou redistribuer ce programme sous les conditions
de la licence CeCILL diffusée sur le site "http://www.cecill.info".
"""

import asyncio
import datetime
import html
import re
import time
import typing
from marshal import dumps, loads
import async_timeout

from feedparser.util import FeedParserDict
import discord
from aiohttp.client import ClientSession
from aiohttp import client_exceptions
from discord.ext import commands, tasks
import twitter
import feedparser

from bot import checks, args
from utils import Gunibot, MyContext
import core
from core import setup_logger

from core import configuration

async def setup(bot:Gunibot):
    await bot.add_cog(Rss(bot), icon="📰")

class TwitterConfiguration(configuration.Configuration):
    namespace = "twitter"

    consumer_key = configuration.ConfigurationField(type=str)
    consumer_secret = configuration.ConfigurationField(type=str)
    access_token_key = configuration.ConfigurationField(type=str)
    access_token_secret = configuration.ConfigurationField(type=str)

class RssConfiguration(configuration.Configuration):
    namespace = "rss"

    twitter = TwitterConfiguration()

    rss_loop_enabled = configuration.ConfigurationField(type=bool, default=True)

class Rss(commands.Cog):
    """
    Cog which deals with everything related to rss flows. Whether it is to add automatic tracking
    to a stream, or just to see the latest video released by Discord, it is this cog that will be
    used.
    """

    def __init__(self, bot: Gunibot):
        self.bot = bot
        self.logger = setup_logger('rss')
        
        self.config = RssConfiguration()
        self.bot.config.add_configuration_child(self.config)

        self.time_loop = 15  # min minutes between two rss loops
        # seconds between two rss checks within a loop
        self.time_between_flows_check = 0.15
        self.max_feeds_per_guild = 100

        self.embed_color = discord.Color(6017876)
        self.loop_processing = False

        self.twitterAPI = twitter.Api(
            consumer_key=self.config.twitter.consumer_key,
            consumer_secret=self.config.twitter.consumer_secret,
            access_token_key=self.config.twitter.access_token_key,
            access_token_secret=self.config.twitter.access_token_secret,
            tweet_mode="extended",
        )
        self.twitter_over_capacity = False
        self.min_time_between_posts = {"web": 120, "tw": 15, "yt": 120}
        self.cache = {}
        self.table = "rss_flows"

        try:
            self.date = bot.get_cog("TimeCog").date
        except BaseException:
            pass
            
        # launch rss loop
        self.loop_child.change_interval(minutes=self.time_loop) # pylint: disable=no-member
        self.loop_child.start() # pylint: disable=no-member

    async def cog_unload(self):
        self.loop_child.cancel() # pylint: disable=no-member

    class RSSMessage:
        def __init__(
            self,
            bot: Gunibot,
            message_type,
            url,
            title,
            date=datetime.datetime.now(),
            author=None,
            message_format=None,
            channel=None,
            image=None,
        ):
            self.bot = bot
            self.message_type = message_type
            self.url = url
            self.title = title
            self.embed = False  # WARNING COOKIES WARNINNG
            self.image = image
            if isinstance(date, datetime.datetime):
                self.date = date
            elif isinstance(date, time.struct_time):
                self.date = datetime.datetime(*date[:6])
            elif isinstance(date, str):
                self.date = date
            else:
                date = None
            self.author = author
            self.message_format = message_format
            self.logo = ":newspaper:"
            self.channel = channel
            self.mentions = []
            if self.author is None:
                self.author = channel

        def fill_embed_data(self, flow: dict):
            if not flow["use_embed"]:
                return
            self.embed_data = { # pylint: disable=attribute-defined-outside-init
                "color": discord.Colour(0).default(),
                "footer": "",
                "title": None,
            }
            if not flow["embed_structure"]:
                return
            structure: dict = flow["embed_structure"]
            if title := structure.get("title", None):
                self.embed_data["title"] = title[:256]
            if footer := structure.get("footer", None):
                self.embed_data["footer"] = footer[:2048]
            if color := structure.get("color", None):
                self.embed_data["color"] = color
            return

        async def fill_mention(
            self, guild: discord.Guild, roles: typing.List[str], translate
        ):
            if roles == []:
                roles = await translate(guild.id, "keywords.none")
            else:
                roles = list()
                for item in roles:
                    if item == "":
                        continue
                    role = discord.utils.get(guild.roles, id=int(item))
                    if role is not None:
                        roles.append(role.mention)
                    else:
                        roles.append(item)
                self.mentions = roles
            return self

        async def create_msg(self, language, msg_format=None):
            if msg_format is None:
                msg_format = self.message_format
            if not isinstance(self.date, str):
                date = await self.bot.get_cog("TimeCog").date(
                    self.date, lang=language, year=False, hour=True, digital=True
                )
            else:
                date = self.date
            msg_format = msg_format.replace("\\n", "\n")
            _channel = discord.utils.escape_markdown(self.channel)
            _author = discord.utils.escape_markdown(self.author)
            text = msg_format.format_map(
                self.bot.SafeDict(
                    channel=_channel,
                    title=self.title,
                    date=date,
                    url=self.url,
                    link=self.url,
                    mentions=", ".join(self.mentions),
                    logo=self.logo,
                    author=_author,
                )
            )
            if not self.embed:
                return text

            embed = discord.Embed(
                description=text,
                timestamp=self.date,
                color=self.embed_data.get("color", 0),
            )
            if footer := self.embed_data.get("footer", None):
                embed.set_footer(text=footer)
            if self.embed_data.get("title", None) is None:
                if self.message_type != "tw":
                    embed.title = self.title
                else:
                    embed.title = self.author
            else:
                embed.title = self.embed_data["title"]
            embed.add_field(name="URL", value=self.url, inline=False)
            if self.image is not None:
                embed.set_thumbnail(url=self.image)
            return embed

    async def get_lang(self, guild: typing.Optional[discord.Guild]) -> str:
        guild_id = guild.id if guild else None
        return await self.bot.get_cog("Languages").get_lang(guild_id, True)

    @commands.group(name="rss")
    @commands.cooldown(2, 15, commands.BucketType.channel)
    async def rss_main(self, ctx: MyContext):
        """See the last post of a rss feed"""
        if ctx.subcommand_passed is None:
            await ctx.send_help('rss')

    @rss_main.command(name="youtube", aliases=["yt"])
    async def request_yt(self, ctx: MyContext, video_id):
        """The last video of a YouTube channel

        ..Examples:
            - rss youtube UCZ5XnGb-3t7jCkXdawN2tkA
            - rss youtube https://www.youtube.com/channel/UCZ5XnGb-3t7jCkXdawN2tkA"""
        if "youtube.com" in video_id or "youtu.be" in video_id:
            video_id = await self.parse_yt_url(video_id)
        if video_id is None:
            return await ctx.send(await self.bot._(ctx.channel, "rss.web-invalid"))
        text = await self.rss_yt(ctx.channel, video_id)
        if isinstance(text, str):
            await ctx.send(text)
        else:
            form = await self.bot._(ctx.channel, "rss.yt-form-last")
            obj = await text[0].create_msg(await self.get_lang(ctx.guild), form)
            if isinstance(obj, discord.Embed):
                await ctx.send(embed=obj)
            else:
                await ctx.send(obj)

    @rss_main.command(name="twitch", aliases=["tv"])
    async def request_twitch(self, ctx: MyContext, channel):
        """The last video of a Twitch channel

        ..Examples:
            - rss twitch aureliensama
            - rss tv https://www.twitch.tv/aureliensama"""
        if "twitch.tv" in channel:
            channel = await self.parse_twitch_url(channel)
        text = await self.rss_twitch(ctx.channel, channel)
        if isinstance(text, str):
            await ctx.send(text)
        else:
            form = await self.bot._(ctx.channel, "rss.twitch-form-last")
            obj = await text[0].create_msg(await self.get_lang(ctx.guild), form)
            if isinstance(obj, discord.Embed):
                await ctx.send(embed=obj)
            else:
                await ctx.send(obj)

    @rss_main.command(name="twitter", aliases=["tw"])
    async def request_tw(self, ctx: MyContext, name):
        """The last tweet of a Twitter account

        ..Examples:
            - rss twitter https://twitter.com/z_runnerr
            - rss tw z_runnerr
        """
        if "twitter.com" in name:
            name = await self.parse_tw_url(name)
        try:
            text = await self.rss_tw(ctx.channel, name)
        except Exception as exc: # pylint: disable=broad-exception-caught
            return await self.bot.get_cog("Errors").on_error(exc, ctx)
        if isinstance(text, str):
            await ctx.send(text)
        else:
            form = await self.bot._(ctx.channel, "rss.tw-form-last")
            for single in text[:5]:
                obj = await single.create_msg(await self.get_lang(ctx.guild), form)
                if isinstance(obj, discord.Embed):
                    await ctx.send(embed=obj)
                else:
                    await ctx.send(obj)

    @rss_main.command(name="web")
    async def request_web(self, ctx: MyContext, link):
        """The last post on any other rss feed

        Example: rss web https://fr-minecraft.net/rss.php"""
        text = await self.rss_web(ctx.channel, link)
        if isinstance(text, str):
            await ctx.send(text)
        else:
            form = await self.bot._(ctx.channel, "rss.web-form-last")
            obj = await text[0].create_msg(await self.get_lang(ctx.guild), form)
            if isinstance(obj, discord.Embed):
                await ctx.send(embed=obj)
            else:
                await ctx.send(obj)

    @rss_main.command(name="deviantart", aliases=["deviant"])
    async def request_deviant(self, ctx: MyContext, user):
        """The last pictures of a DeviantArt user

        Example: rss deviant https://www.deviantart.com/adri526"""
        if "deviantart.com" in user:
            user = await self.parse_deviant_url(user)
        text = await self.rss_deviant(ctx.guild, user)
        if isinstance(text, str):
            await ctx.send(text)
        else:
            form = await self.bot._(ctx.channel, "rss.deviant-form-last")
            obj = await text[0].create_msg(await self.get_lang(ctx.guild), form)
            if isinstance(obj, discord.Embed):
                await ctx.send(embed=obj)
            else:
                await ctx.send(obj)

    async def is_overflow(self, guild: discord.Guild) -> bool:
        """Check if a guild still has at least a slot
        True if max number reached, followed by the flow limit"""
        return len(await self.db_get_guild_flows(guild.id)) >= self.max_feeds_per_guild

    @rss_main.command(name="add")
    @commands.guild_only()
    @commands.check(commands.has_guild_permissions(manage_webhooks=True))
    async def system_add(self, ctx: MyContext, link):
        """Subscribe to a rss feed, displayed on this channel regularly

        ..Examples:
            - rss add https://www.deviantart.com/adri526
            - rss add https://www.youtube.com/channel/UCZ5XnGb-3t7jCkXdawN2tkA"""
        is_over = await self.is_overflow(ctx.guild)
        if is_over:
            await ctx.send(
                str(await self.bot._(ctx.guild.id, "rss.flow-limit")).format(
                    self.max_feeds_per_guild
                )
            )
            return
        identifiant = await self.parse_yt_url(link)
        rss_type = None
        if identifiant is not None:
            rss_type = "yt"
            display_type = "youtube"
        if identifiant is None:
            identifiant = await self.parse_tw_url(link)
            if identifiant is not None:
                rss_type = "tw"
                display_type = "twitter"
        if identifiant is None:
            identifiant = await self.parse_twitch_url(link)
            if identifiant is not None:
                rss_type = "twitch"
                display_type = "twitch"
        if identifiant is None:
            identifiant = await self.parse_deviant_url(link)
            if identifiant is not None:
                rss_type = "deviant"
                display_type = "deviantart"
        if identifiant is not None and not link.startswith("https://"):
            link = "https://" + link
        if identifiant is None and link.startswith("http"):
            identifiant = link
            rss_type = "web"
            display_type = "website"
        elif not link.startswith("http"):
            await ctx.send(await self.bot._(ctx.guild, "rss.invalid-link"))
            return
        if rss_type is None or not await self.check_rss_url(link):
            return await ctx.send(await self.bot._(ctx.guild.id, "rss.invalid-flow"))
        try:
            feed_id = await self.db_add_flow(ctx.guild.id, ctx.channel.id, rss_type, identifiant)
            await ctx.send(
                str(await self.bot._(ctx.guild, "rss.success-add")).format(
                    display_type, link, ctx.channel.mention
                )
            )
            self.logger.info(
                "RSS feed added into server %i (%s - %i)",
                ctx.guild.ig,
                link,
                feed_id,
            )
            await self.send_log(
                f"Feed added into server {ctx.guild.id} ({feed_id})", ctx.guild,
            )
        except Exception as exception: # pylint: disable=broad-exception-caught
            await ctx.send(await self.bot._(ctx.guild, "rss.fail-add"))
            await self.bot.get_cog("Errors").on_error(exception, ctx)

    @rss_main.command(name="remove", aliases=["delete"])
    @commands.guild_only()
    @commands.check(commands.has_guild_permissions(manage_webhooks=True))
    async def systeme_rm(self, ctx: MyContext, rss_id: int = None):
        """Delete an rss feed from the list

        Example: rss remove"""
        flow = await self.ask_id(
            rss_id,
            ctx,
            await self.bot._(ctx.guild.id, "rss.choose-delete"),
            allow_mc=True,
            display_mentions=False,
        )
        if flow is None:
            return
        try:
            await self.db_remove_flow(flow[0]["ID"])
        except Exception as exc: # pylint: disable=broad-exception-caught
            await ctx.send(await self.bot._(ctx.guild, "rss.fail-add"))
            await self.bot.get_cog("Errors").on_error(exc, ctx)
            return
        await ctx.send(await self.bot._(ctx.guild, "rss.delete-success"))
        self.logger.info(
            "RSS feed deleted into server %i (%i)",
            ctx.guild.id,
            flow[0]['ID'],
        )
        await self.send_log(
            f"Feed deleted into server {ctx.guild.id} ({flow[0]['ID']})",
            ctx.guild,
        )

    @rss_main.command(name="list")
    @commands.guild_only()
    @commands.check(commands.has_permissions(manage_webhooks=True))
    async def list_flows(self, ctx: MyContext):
        """Get a list of every rss/Minecraft feed"""
        liste = await self.db_get_guild_flows(ctx.guild.id)
        if len(liste) == 0:
            # no rss feed
            await ctx.send(await self.bot._(ctx.guild.id, "rss.no-feed2"))
            return
        title = await self.bot._(ctx.guild.id, "rss.list-title", server=ctx.guild.name)
        translation = await self.bot._(ctx.guild.id, "rss.list-result")
        rss_feeds = []
        for feed in liste:
            channel = self.bot.get_channel(feed["channel"])
            if channel is not None:
                channel = channel.mention
            else:
                channel = feed["channel"]
            if len(feed["roles"]) == 0:
                roles = await self.bot._(ctx.guild.id, "keywords.none")
            else:
                roles = []
                for item in feed["roles"]:
                    role = discord.utils.get(ctx.guild.roles, id=int(item))
                    if role is not None:
                        roles.append(role.mention)
                    else:
                        roles.append(item)
                roles = ", ".join(roles)
            rss_type = await self.bot._(ctx.guild.id, "rss." + feed["type"])
            if len(rss_feeds) > 20:
                embed = discord.Embed(
                    title=title,
                    color=self.embed_color,
                    timestamp=ctx.message.created_at,
                )
                embed.set_footer(
                    text=str(ctx.author), icon_url=ctx.author.display_avatar
                )
                for text in rss_feeds:
                    embed.add_field(name="\uFEFF", value=text, inline=False)
                await ctx.send(embed=embed)
                rss_feeds.clear()
            rss_feeds.append(translation.format(
                rss_type,
                channel,
                feed["link"],
                roles,
                feed["ID"],
                feed["date"]
            ))
        if len(rss_feeds) > 0:
            embed = discord.Embed(
                title=title, color=self.embed_color, timestamp=ctx.message.created_at
            )
            embed.set_footer(text=str(ctx.author), icon_url=ctx.author.display_avatar)
            for feed in rss_feeds:
                embed.add_field(name="\uFEFF", value=feed, inline=False)
            await ctx.send(embed=embed)

    async def ask_id(
        self,
        feed_id,
        ctx: MyContext,
        title: str,
        allow_mc: bool = False,
        display_mentions: bool = True,
    ):
        """Request the ID of an rss stream"""
        flow = list()
        if feed_id is not None:
            flow = await self.db_get_flow(feed_id)
            if flow == []:
                feed_id = None
            elif str(flow[0]["guild"]) != str(ctx.guild.id):
                feed_id = None
            elif (not allow_mc) and flow[0]["type"] == "mc":
                feed_id = None
        user_id = ctx.author.id
        if feed_id is None:
            guild_feeds = await self.db_get_guild_flows(ctx.guild.id)
            if len(guild_feeds) == 0:
                await ctx.send(await self.bot._(ctx.guild.id, "rss.no-feed"))
                return
            if display_mentions:
                text = [await self.bot._(ctx.guild.id, "rss.list")]
            else:
                text = [await self.bot._(ctx.guild.id, "rss.list2")]
            feed_ids = []
            iterator = 1
            translations = {}
            for feed in guild_feeds:
                if (not allow_mc) and feed["type"] == "mc":
                    continue
                if feed["type"] == "tw" and feed["link"].isnumeric():
                    try:
                        feed["link"] = self.twitter_api.GetUser(
                            user_id=int(feed["link"])
                        ).screen_name
                    except twitter.TwitterError:
                        pass
                feed_ids.append(feed["ID"])
                channel = self.bot.get_channel(feed["channel"])
                if channel is not None:
                    channel = channel.mention
                else:
                    channel = feed["channel"]
                feed_type = translations.get(
                    feed["type"], await self.bot._(ctx.guild.id, "rss." + feed["type"])
                )
                if display_mentions:
                    if len(feed["roles"]) == 0:
                        roles = await self.bot._(ctx.guild.id, "keywords.none")
                    else:
                        roles = list()
                        for item in feed["roles"]:
                            role = discord.utils.get(ctx.guild.roles, id=int(item))
                            if role is not None:
                                roles.append(role.mention)
                            else:
                                roles.append(item)
                        roles = ", ".join(roles)
                    text.append(
                        f"{iterator}) {feed_type} - {feed['link']} - {channel} - {roles}",
                    )
                else:
                    text.append(f"{iterator}) {feed_type} - {feed['link']} - {channel}")
                iterator += 1
            if len("\n".join(text)) < 2048:
                desc = "\n".join(text)
                fields = None
            else:
                desc = text[0].split("\n")[0]
                fields = []
                field = {"name": text[0].split("\n")[-2], "value": ""}
                for line in text[1:]:
                    if len(field["value"] + line) > 1020:
                        fields.append(field)
                        field = {"name": text[0].split("\n")[-2], "value": ""}
                    field["value"] += line + "\n"
                fields.append(field)
            embed = discord.Embed(
                title=title,
                color=self.embed_color,
                description=desc,
                timestamp=ctx.message.created_at,
            )
            embed.set_footer(text=str(ctx.author), icon_url=ctx.author.display_avatar)
            if fields is not None:
                for field in fields:
                    embed.add_field(**field)
            emb_msg: discord.Message = await ctx.send(embed=embed)

            def check(msg):
                if not msg.content.isnumeric():
                    return False
                return msg.author.id == user_id and int(msg.content) in range(
                    1, iterator
                )

            try:
                msg = await self.bot.wait_for(
                    "message", check=check, timeout=max(20, 1.5 * len(text))
                )
            except asyncio.TimeoutError:
                await ctx.send(await self.bot._(ctx.guild.id, "rss.too-long"))
                await emb_msg.delete()
                return
            flow = await self.db_get_flow(feed_ids[int(msg.content) - 1])
        if len(flow) == 0:
            await ctx.send(await self.bot._(ctx.guild, "rss.fail-add"))
            return
        return flow

    def parse_output(self, arg):
        pattern = re.findall(r"((?<![\\])[\"])((?:.(?!(?<![\\])\1))*.?)\1", arg)
        if len(pattern) > 0:

            def flatten(liste):
                return [item for sublist in liste for item in sublist]

            params = [[x for x in group if x != '"'] for group in pattern]
            return flatten(params)
        else:
            return arg.split(" ")

    @rss_main.command(name="roles", aliases=["mentions", "mention"])
    @commands.guild_only()
    @commands.check(commands.has_permissions(manage_webhooks=True))
    async def roles_flows(
        self,
        ctx: MyContext,
        flow_id: int = None,
        mentions: commands.Greedy[discord.Role] = None,
    ):
        """Configures a role to be notified when a news is posted
        If you want to use the @everyone role, please put the server ID instead of the role name.

        Examples:
            - rss mentions
            - rss mentions 6678466620137
            - rss mentions 6678466620137 "Announcements" "Twitch subs"
        """
        try:
            # ask for flow ID
            flow = await self.ask_id(
                flow_id, ctx, await self.bot._(ctx.guild.id, "rss.choose-mentions-1")
            )
        except Exception as exc: # pylint: disable=broad-exception-caught
            flow = []
            await self.bot.get_cog("Errors").on_error(exc, ctx)
        if flow is None:
            return
        if len(flow) == 0:
            await ctx.send(await self.bot._(ctx.guild, "rss.fail-add"))
            return
        flow = flow[0]
        no_role = ["aucun", "none", "_", "del"]
        if mentions is None:  # if no roles was specified: we ask for them
            if flow["roles"] == "":
                text = await self.bot._(ctx.guild.id, "rss.no-roles")
            else:
                roles = []
                for item in flow["roles"]:
                    role = discord.utils.get(ctx.guild.roles, id=int(item))
                    if role is not None:
                        roles.append(role.mention)
                    else:
                        roles.append(item)
                roles = ", ".join(roles)
                text = str(await self.bot._(ctx.guild.id, "rss.roles-list")).format(roles)
            # ask for roles
            embed = discord.Embed(
                title=await self.bot._(ctx.guild.id, "rss.choose-roles"),
                color=discord.Colour(0x77EA5C),
                description=text,
                timestamp=ctx.message.created_at,
            )
            emb_msg = await ctx.send(embed=embed)
            err = await self.bot._(ctx.guild.id, "find.role-0")
            user_id = ctx.author.id

            def check2(msg):
                return msg.author.id == user_id

            cond = False
            while cond is False:
                try:
                    msg = await self.bot.wait_for("message", check=check2, timeout=30.0)
                    if (
                        msg.content.lower() in no_role
                    ):  # if no role should be mentionned
                        id_list = [None]
                    else:
                        roles = self.parse_output(msg.content)
                        id_list = list()
                        name_list = list()
                        for role in roles:
                            role = role.strip()
                            try:
                                roles = await commands.RoleConverter().convert(ctx, role)
                                id_list.append(str(roles.id))
                                name_list.append(roles.name)
                            except BaseException: # pylint: disable=broad-exception-caught
                                await ctx.send(err)
                                id_list = []
                                break
                    if len(id_list) > 0:
                        cond = True
                except asyncio.TimeoutError:
                    await ctx.send(await self.bot._(ctx.guild.id, "rss.too-long"))
                    await emb_msg.delete()
                    return
        else:  # if roles were specified
            if mentions in no_role:  # if no role should be mentionned
                id_list = None
            else:
                id_list = list()
                name_list = list()
                for roles in mentions:
                    id_list.append(roles.id)
                    name_list.append(roles.name)
                if len(id_list) == 0:
                    await ctx.send(await self.bot._(ctx.guild.id, "find.role-0"))
                    return
        try:
            if id_list is None:
                await self.db_update_flow(flow["ID"], values=[("roles", None)])
                await ctx.send(await self.bot._(ctx.guild.id, "rss.roles-1"))
            else:
                await self.db_update_flow(flow["ID"], values=[("roles", dumps(id_list))])
                txt = ", ".join(name_list)
                await ctx.send(
                    str(await self.bot._(ctx.guild.id, "rss.roles-0")).format(txt)
                )
        except Exception as exc: # pylint: disable=broad-exception-caught
            await ctx.send(await self.bot._(ctx.guild, "rss.fail-add"))
            await self.bot.get_cog("Errors").on_error(exc, ctx)

    @rss_main.command(name="reload")
    @commands.guild_only()
    @commands.check(commands.has_permissions(manage_webhooks=True))
    @commands.cooldown(1, 600, commands.BucketType.guild)
    async def reload_guild_flows(self, ctx: MyContext):
        """Reload every rss feeds from your server"""
        try:
            start = time.time()
            msg: discord.Message = await ctx.send(
                str(await self.bot._(ctx.guild.id, "rss.guild-loading")).format("...")
            )
            liste = await self.db_get_guild_flows(ctx.guild.id)
            await self.main_loop(ctx.guild.id)
            await ctx.send(
                str(await self.bot._(ctx.guild.id, "rss.guild-complete")).format(
                    len(liste), round(time.time() - start, 1)
                )
            )
            await msg.delete()
        except Exception as exc: # pylint: disable=broad-exception-caught
            await ctx.send(
                str(await self.bot._(ctx.guild.id, "rss.guild-error")).format(exc)
            )

    @rss_main.command(name="move")
    @commands.guild_only()
    @commands.check(commands.has_permissions(manage_webhooks=True))
    async def move_guild_flow(
        self,
        ctx: MyContext,
        flow_id: typing.Optional[int] = None,
        channel: discord.TextChannel = None,
    ):
        """Move a rss feed in another channel

        Example:
            - rss move
            - rss move 3078731683662
            - rss move #cool-channels
            - rss move 3078731683662 #cool-channels
        """
        try:
            if channel is None:
                channel = ctx.channel
            try:
                flow = await self.ask_id(
                    flow_id, ctx, await self.bot._(ctx.guild.id, "rss.choose-mentions-1")
                )
                error = None
            except Exception: # pylint: disable=broad-exception-caught
                flow = []
            if flow is None:
                return
            if len(flow) == 0:
                await ctx.send(await self.bot._(ctx.guild, "rss.fail-add"))
                if error is not None:
                    await self.bot.get_cog("Errors").on_error(error, ctx)
                return
            flow = flow[0]
            await self.db_update_flow(flow["ID"], [("channel", channel.id)])
            await ctx.send(
                str(await self.bot._(ctx.guild.id, "rss.move-success")).format(
                    flow["ID"], channel.mention
                )
            )
        except Exception as exc: # pylint: disable=broad-exception-caught
            await ctx.send(
                str(await self.bot._(ctx.guild.id, "rss.guild-error")).format(exc)
            )

    @rss_main.command(name="text")
    @commands.guild_only()
    @commands.check(commands.has_permissions(manage_webhooks=True))
    async def change_text_flow(
        self, ctx: MyContext, flow_id: typing.Optional[int] = None, *, text=None
    ):
        """Change the text of an rss feed

        Available variables:
        - `{author}`: the author of the post
        - `{channel}`: the channel name (usually the same as author)
        - `{date}`: the post date (UTC)
        - `{link}` or `{url}`: a link to the post
        - `{logo}`: an emoji representing the type of post (web, Twitter, YouTube...)
        - `{mentions}`: the list of mentioned roles
        - `{title}`: the title of the post

        Examples:
            - rss text 3078731683662
            - rss text 3078731683662 {logo} | New post of {author} right here: {url}! [{date}]
            - rss text
        """
        try:
            try:
                flow = await self.ask_id(
                    flow_id, ctx, await self.bot._(ctx.guild.id, "rss.choose-mentions-1")
                )
            except Exception as exc: # pylint: disable=broad-exception-caught, unused-variable
                flow = []
            if flow is None:
                return
            if len(flow) == 0:
                await ctx.send(await self.bot._(ctx.guild, "rss.fail-add"))
                await self.bot.get_cog("Errors").on_error(exc, ctx) # pylint: disable=used-before-assignment
                return
            flow = flow[0]
            if text is None:
                await ctx.send(
                    str(await self.bot._(ctx.guild.id, "rss.change-txt")).format_map(
                        self.bot.SafeDict(text=flow["structure"])
                    )
                )

                def check(msg):
                    return msg.author == ctx.author and msg.channel == ctx.channel

                try:
                    msg = await self.bot.wait_for("message", check=check, timeout=90)
                except asyncio.TimeoutError:
                    return await ctx.send(
                        await self.bot._(ctx.guild.id, "rss.too-long")
                    )
                text = msg.content
            await self.db_update_flow(flow["ID"], [("structure", text)])
            await ctx.send(
                str(await self.bot._(ctx.guild.id, "rss.text-success")).format(
                    flow["ID"], text
                )
            )
        except Exception as exc: # pylint: disable=broad-exception-caught
            await ctx.send(
                str(await self.bot._(ctx.guild.id, "rss.guild-error")).format(exc)
            )
            await ctx.bot.get_cog("Errors").on_error(exc, ctx)

    @rss_main.command(name="use_embed", aliases=["embed"])
    @commands.guild_only()
    @commands.check(commands.has_permissions(manage_webhooks=True))
    async def change_use_embed(
        self,
        ctx: MyContext,
        flow_id: typing.Optional[int] = None,
        value: bool = None,
        *,
        arguments: args.arguments = None,
    ):
        """Use an embed (or not) for a flow
        You can also provide arguments to change the color/text of the embed. Followed arguments
        are usable:
        - color: color of the embed (hex or decimal value)
        - title: title override, which will disable the default one (max 256 characters)
        - footer: small text displayed at the bottom of the embed

        Examples:
            - rss embed 6678466620137 true title="hey u" footer = "Hi \\n i'm a footer"
            - rss embed 6678466620137 false
            - rss embed 6678466620137 1
        """
        try:
            error = None
            try:
                flow = await self.ask_id(
                    flow_id, ctx, await self.bot._(ctx.guild.id, "rss.choose-mentions-1")
                )
            except Exception as error: # pylint: disable=broad-exception-caught
                flow = []
                await self.bot.get_cog("Errors").on_error(error, ctx)
            if flow is None:
                return
            if len(flow) == 0:
                await ctx.send(await self.bot._(ctx.guild, "rss.fail-add"))
                if error is not None:
                    await self.bot.get_cog("Errors").on_error(error, ctx)
                return
            if arguments is None or len(arguments.keys()) == 0:
                arguments = None
            flow = flow[0]
            embed_data = flow["embed_structure"] or dict()
            txt = list()
            if value is None and arguments is None:
                await ctx.send(
                    await self.bot._(
                        ctx.guild.id,
                        "rss.use_embed_true"
                        if flow["use_embed"]
                        else "use_embed_false",
                    )
                )

                def check(msg):
                    try:
                        _ = commands.core._convert_to_bool(msg.content) # pylint: disable=protected-access, no-member
                    except BaseException: # pylint: disable=broad-exception-caught
                        return False
                    return msg.author == ctx.author and msg.channel == ctx.channel

                try:
                    msg = await self.bot.wait_for("message", check=check, timeout=20)
                except asyncio.TimeoutError:
                    return await ctx.send(
                        await self.bot._(ctx.guild.id, "rss.too-long")
                    )
                value = commands.core._convert_to_bool(msg.content) # pylint: disable=protected-access, no-member
            if value is not None and value != flow["use_embed"]:
                embed_data["use_embed"] = value
                txt.append(
                    await self.bot._(
                        ctx.guild.id, "rss.use_embed-success", v=value, f=flow["ID"]
                    )
                )
            elif value == flow["use_embed"] and arguments is None:
                await ctx.send(await self.bot._(ctx.guild.id, "rss.use_embed-same"))
                return
            if arguments is not None:
                if "color" in arguments.keys():
                    color = await commands.ColourConverter().convert(
                        ctx, arguments["color"]
                    )
                    if color is not None:
                        embed_data["color"] = color.value
                if "title" in arguments.keys():
                    embed_data["title"] = arguments["title"]
                if "footer" in arguments.keys():
                    embed_data["footer"] = arguments["footer"]
                txt.append(await self.bot._(ctx.guild.id, "rss.embed-json-changed"))
            if len(embed_data) > 0:
                await self.db_update_flow(
                    flow["ID"], [("embed_structure", dumps(embed_data))]
                )
            await ctx.send("\n".join(txt))
        except Exception as error: # pylint: disable=broad-exception-caught
            await ctx.send(
                str(await self.bot._(ctx.guild.id, "rss.guild-error")).format(error)
            )
            await ctx.bot.get_cog("Errors").on_error(error, ctx)

    @rss_main.command(name="test")
    @commands.check(checks.is_bot_admin)
    async def test_rss(self, ctx: MyContext, url, *, arguments=None):
        """Test if an rss feed is usable"""
        url = url.replace("<", "").replace(">", "")
        try:
            feeds = await self.feed_parse(url, 8)
            txt = f"feeds.keys()\n```py\n{feeds.keys()}\n```"
            if "bozo_exception" in feeds.keys():
                txt += f"\nException ({feeds['bozo']}): {str(feeds['bozo_exception'])}"
                return await ctx.send(txt)
            if len(str(feeds.feed)) < 1400 - len(txt):
                txt += f"feeds.feed\n```py\n{feeds.feed}\n```"
            else:
                txt += f"feeds.feed.keys()\n```py\n{feeds.feed.keys()}\n```"
            if len(feeds.entries) > 0:
                if len(str(feeds.entries[0])) < 1950 - len(txt):
                    txt += f"feeds.entries[0]\n```py\n{feeds.entries[0]}\n```"
                else:
                    txt += f"feeds.entries[0].keys()\n```py\n{feeds.entries[0].keys()}\n```"
            if arguments is not None and "feeds" in arguments and "ctx" not in arguments:
                txt += f"\n{arguments}\n```py\n{eval(arguments)}\n```" # we checked that the user is a bot admin pylint: disable=eval-used
            try:
                await ctx.send(txt)
            except Exception as exc: # pylint: disable=broad-exception-caught
                print("[rss_test] Error:", exc)
                await ctx.send("`Error`: " + str(exc))
                print(txt)
            if arguments is None:
                good = "✅"
                notgood = "❌"
                nothing = "\t"
                txt = ["**__Analyse :__**", ""]
                youtube = await self.parse_yt_url(feeds.feed["link"])
                if youtube is None:
                    tw_url = await self.parse_tw_url(feeds.feed["link"])
                    if tw_url is not None:
                        txt.append("<:twitter:437220693726330881>  " + tw_url)
                    elif "link" in feeds.feed.keys():
                        txt.append(":newspaper:  <" + feeds.feed["link"] + ">")
                    else:
                        txt.append(":newspaper:  No 'link' var")
                else:
                    txt.append("<:youtube:447459436982960143>  " + youtube)
                txt.append(f"Entrées : {len(feeds.entries)}")
                if len(feeds.entries) > 0:
                    entry = feeds.entries[0]
                    if "title" in entry.keys():
                        txt.append(nothing + good + " title: ")
                        if len(entry["title"].split("\n")) > 1:
                            txt[-1] += entry["title"].split("\n")[0] + "..."
                        else:
                            txt[-1] += entry["title"]
                    else:
                        txt.append(nothing + notgood + " title")
                    if "published_parsed" in entry.keys():
                        txt.append(nothing + good + " published_parsed")
                    elif "published" in entry.keys():
                        txt.append(nothing + good + " published")
                    elif "updated_parsed" in entry.keys():
                        txt.append(nothing + good + " updated_parsed")
                    else:
                        txt.append(nothing + notgood + " date")
                    if "author" in entry.keys():
                        txt.append(nothing + good + " author: " + entry["author"])
                    else:
                        txt.append(nothing + notgood + " author")
                await ctx.send("\n".join(txt))
        except Exception as exc: # pylint: disable=broad-exception-caught
            await ctx.bot.get_cog("Errors").on_command_error(ctx, exc)

    async def check_rss_url(self, url):
        result = await self.parse_yt_url(url)
        if result is not None:
            return True
        result = await self.parse_tw_url(url)
        if result is not None:
            return True
        result = await self.parse_twitch_url(url)
        if result is not None:
            return True
        result = await self.parse_deviant_url(url)
        if result is not None:
            return True
        try:
            feed = await self.feed_parse(url, 8)
            _ = feed.entries[0]
            return True
        except BaseException: # pylint: disable=broad-exception-caught
            return False

    async def parse_yt_url(self, url):
        pattern = r"(?:http.*://)?(?:www.)?(?:youtube.com|youtu.be)"\
            r"(?:(?:/channel/|/user/)(.+)|/[\w-]+$)"
        match = re.search(pattern, url)
        if match is None:
            return None
        else:
            return match.group(1)

    async def parse_tw_url(self, url):
        pattern = r"(?:http.*://)?(?:www.)?(?:twitter.com/)([^?\s]+)"
        match = re.search(pattern, url)
        if match is None:
            return None
        else:
            name = match.group(1)
            try:
                user = self.twitter_api.GetUser(screen_name=name)
            except twitter.TwitterError:
                return None
            return user.id

    async def parse_twitch_url(self, url):
        pattern = r"(?:http.*://)?(?:www.)?(?:twitch.tv/)([^?\s]+)"
        match = re.search(pattern, url)
        if match is None:
            return None
        else:
            return match.group(1)

    async def parse_deviant_url(self, url):
        pattern = r"(?:http.*://)?(?:www.)?(?:deviantart.com/)([^?\s]+)"
        match = re.search(pattern, url)
        if match is None:
            return None
        else:
            return match.group(1)

    async def feed_parse(
        self, url: str, timeout: int, session: ClientSession = None
    ) -> feedparser.FeedParserDict:
        """Asynchronous parsing using cool methods"""
        # if session is provided, we have to not close it
        _session = session or ClientSession()
        try:
            async with async_timeout.timeout(timeout) as clientconnection:
                async with _session.get(url) as response:
                    response_html = await response.text()
                    headers = response.raw_headers
        except (
            client_exceptions.ClientConnectorCertificateError,
            UnicodeDecodeError,
            client_exceptions.TooManyRedirects,
            client_exceptions.ClientConnectorError,
            client_exceptions.ClientPayloadError,
        ):
            if session is None:
                await _session.close()
            return FeedParserDict(entries=[])
        except asyncio.exceptions.TimeoutError:
            if session is None:
                await _session.close()
            return None
        if session is None:
            await _session.close()
        if clientconnection.expired:
            # request was cancelled by timeout
            self.bot.info("[RSS] feed_parse got a timeout")
            return None
        headers = {k.decode("utf-8").lower(): v.decode("utf-8") for k, v in headers}
        return feedparser.parse(response_html, response_headers=headers)

    async def rss_yt(
        self,
        channel: discord.TextChannel,
        identifiant: str,
        date=None,
        session: ClientSession = None,
    ):
        if identifiant == "help":
            return await self.bot._(channel, "rss.yt-help")
        url = "https://www.youtube.com/feeds/videos.xml?channel_id=" + identifiant
        feeds = await self.feed_parse(url, 7, session)
        if feeds is None:
            return await self.bot._(channel, "rss.research-timeout")
        if not feeds.entries:
            url = "https://www.youtube.com/feeds/videos.xml?user=" + identifiant
            feeds = await self.feed_parse(url, 7, session)
            if feeds is None:
                return await self.bot._(channel, "rss.nothing")
            if not feeds.entries:
                return await self.bot._(channel, "rss.nothing")
        if not date:
            feed = feeds.entries[0]
            img_url = None
            if "media_thumbnail" in feed.keys() and len(feed["media_thumbnail"]) > 0:
                img_url = feed["media_thumbnail"][0]["url"]
            obj = self.RSSMessage(
                bot=self.bot,
                message_type="yt",
                url=feed["link"],
                title=feed["title"],
                date=feed["published_parsed"],
                author=feed["author"],
                channel=feed["author"],
                image=img_url,
            )
            return [obj]
        else:
            liste = list()
            for feed in feeds.entries:
                if len(liste) > 10:
                    break
                if (
                    "published_parsed" not in feed
                    or (
                        datetime.datetime(*feed["published_parsed"][:6]) - date
                    ).total_seconds()
                    <= self.min_time_between_posts["yt"]
                ):
                    break
                img_url = None
                if (
                    "media_thumbnail" in feed.keys()
                    and len(feed["media_thumbnail"]) > 0
                ):
                    img_url = feed["media_thumbnail"][0]["url"]
                obj = self.RSSMessage(
                    bot=self.bot,
                    message_type="yt",
                    url=feed["link"],
                    title=feed["title"],
                    date=feed["published_parsed"],
                    author=feed["author"],
                    channel=feed["author"],
                    image=img_url,
                )
                liste.append(obj)
            liste.reverse()
            return liste

    async def rss_tw(
        self, channel: discord.TextChannel, name: str, date: datetime.datetime = None
    ):
        if name == "help":
            return await self.bot._(channel, "rss.tw-help")
        try:
            if name.isnumeric():
                posts = self.twitter_api.GetUserTimeline(
                    user_id=int(name), exclude_replies=True
                )
                username = self.twitter_api.GetUser(user_id=int(name)).screen_name
            else:
                posts = self.twitter_api.GetUserTimeline(
                    screen_name=name, exclude_replies=True
                )
                username = name
        except twitter.error.TwitterError as exc:
            if exc.message == "Not authorized.":
                return await self.bot._(channel, "rss.nothing")
            if "Unknown error" in exc.message:
                return await self.bot._(channel, "rss.nothing")
            if "The twitter.Api instance must be authenticated." in exc.message:
                return await self.bot._(channel, "rss.wrong-token")
            if exc.message[0]["code"] == 34:
                return await self.bot._(channel, "rss.nothing")
            raise exc
        if not date:
            if len(posts) == 0:
                return []
            lastpost = posts[0]
            text = html.unescape(getattr(lastpost, "full_text", lastpost.text))
            url = f"https://twitter.com/{username.lower()}/status/{lastpost.id}"
            img = None
            if lastpost.media:  # if exists and is not empty
                img = lastpost.media[0].media_url_https
            obj = self.RSSMessage(
                bot=self.bot,
                message_type="tw",
                url=url,
                title=text,
                date=datetime.datetime.fromtimestamp(lastpost.created_at_in_seconds),
                author=lastpost.user.screen_name,
                channel=lastpost.user.name,
                image=img,
            )
            return [obj]
        else:
            liste = list()
            for post in posts:
                if len(liste) > 10:
                    break
                if (
                    datetime.datetime.fromtimestamp(post.created_at_in_seconds) - date
                ).total_seconds() < self.min_time_between_posts["tw"]:
                    break
                text = html.unescape(getattr(post, "full_text", post.text))
                if result := re.search(r"https://t.co/([^\s]+)", text):
                    text = text.replace(result.group(0), "")
                url = f"https://twitter.com/{name.lower()}/status/{post.id}"
                img = None
                if post.media:  # if exists and is not empty
                    img = post.media[0].media_url_https
                obj = self.RSSMessage(
                    bot=self.bot,
                    message_type="tw",
                    url=url,
                    title=text,
                    date=datetime.datetime.fromtimestamp(post.created_at_in_seconds),
                    author=post.user.screen_name,
                    channel=post.user.name,
                    image=img,
                )
                liste.append(obj)
            liste.reverse()
            return liste

    async def rss_twitch(
        self,
        channel: discord.TextChannel,
        nom: str,
        date: datetime.datetime = None,
        session: ClientSession = None,
    ):
        url = "https://twitchrss.appspot.com/vod/" + nom
        feeds = await self.feed_parse(url, 5, session)
        if feeds is None:
            return await self.bot._(channel, "rss.research-timeout")
        if feeds.entries == []:
            return await self.bot._(channel, "rss.nothing")
        if not date:
            feed = feeds.entries[0]
            img_src = re.search(r'<img src="([^"]+)" />', feed["summary"])
            img_url = None
            if img_src is not None:
                img_url = img_src.group(1)
            obj = self.RSSMessage(
                bot=self.bot,
                message_type="twitch",
                url=feed["link"],
                title=feed["title"],
                date=feed["published_parsed"],
                author=feeds.feed["title"].replace("'s Twitch video RSS", ""),
                image=img_url,
                channel=nom,
            )
            return [obj]
        else:
            liste = list()
            for feed in feeds.entries:
                if len(liste) > 10:
                    break
                if datetime.datetime(*feed["published_parsed"][:6]) <= date:
                    break
                img_src = re.search(r'<img src="([^"]+)" />', feed["summary"])
                img_url = None
                if img_src is not None:
                    img_url = img_src.group(1)
                obj = self.RSSMessage(
                    bot=self.bot,
                    message_type="twitch",
                    url=feed["link"],
                    title=feed["title"],
                    date=feed["published_parsed"],
                    author=feeds.feed["title"].replace("'s Twitch video RSS", ""),
                    image=img_url,
                    channel=nom,
                )
                liste.append(obj)
            liste.reverse()
            return liste

    async def rss_web(
        self,
        channel: discord.TextChannel,
        url: str,
        date: datetime.datetime = None,
        session: ClientSession = None,
    ):
        if url == "help":
            return await self.bot._(channel, "rss.web-help")
        feeds = await self.feed_parse(url, 9, session)
        if feeds is None:
            return await self.bot._(channel, "rss.research-timeout")
        if "bozo_exception" in feeds.keys() or len(feeds.entries) == 0:
            return await self.bot._(channel, "rss.web-invalid")
        published = None
        for i in ["published_parsed", "published", "updated_parsed"]:
            if i in feeds.entries[0].keys() and feeds.entries[0][i] is not None:
                published = i
                break
        if published is not None and len(feeds.entries) > 1:
            while (
                (len(feeds.entries) > 1)
                and (feeds.entries[1][published] is not None)
                and (feeds.entries[0][published] < feeds.entries[1][published])
            ):
                del feeds.entries[0]
        if not date or published not in ["published_parsed", "updated_parsed"]:
            feed = feeds.entries[0]
            if published is None:
                datz = "Unknown"
            else:
                datz = feed[published]
            if "link" in feed.keys():
                link = feed["link"]
            elif "link" in feeds.keys():
                link = feeds["link"]
            else:
                link = url
            if "author" in feed.keys():
                author = feed["author"]
            elif "author" in feeds.keys():
                author = feeds["author"]
            elif "title" in feeds["feed"].keys():
                author = feeds["feed"]["title"]
            else:
                author = "?"
            if "title" in feed.keys():
                title = feed["title"]
            elif "title" in feeds.keys():
                title = feeds["title"]
            else:
                title = "?"
            img = None
            img_src = re.search(
                r"(http(s?):)([/|.|\w|\s|-])*\.(?:jpe?g|gif|png|webp)", str(feed)
            )
            if img_src is not None:
                img = img_src.group(0)
            obj = self.RSSMessage(
                bot=self.bot,
                message_type="web",
                url=link,
                title=title,
                date=datz,
                author=author,
                channel=feeds.feed["title"] if "title" in feeds.feed.keys() else "?",
                image=img,
            )
            return [obj]
        else:
            liste = list()
            for feed in feeds.entries:
                if len(liste) > 10:
                    break
                datz = feed[published]
                if (
                    feed[published] is None
                    or (
                        datetime.datetime(*feed[published][:6]) - date
                    ).total_seconds()
                    < self.min_time_between_posts["web"]
                ):
                    break
                if "link" in feed.keys():
                    link = feed["link"]
                elif "link" in feeds.keys():
                    link = feeds["link"]
                else:
                    link = url
                if "author" in feed.keys():
                    author = feed["author"]
                elif "author" in feeds.keys():
                    author = feeds["author"]
                elif "title" in feeds["feed"].keys():
                    author = feeds["feed"]["title"]
                else:
                    author = "?"
                if "title" in feed.keys():
                    title = feed["title"]
                elif "title" in feeds.keys():
                    title = feeds["title"]
                else:
                    title = "?"
                img = None
                img_src = re.search(
                    r"(http(s?):)([/|.|\w|\s|-])*\.(?:jpe?g|gif|png|webp)",
                    str(feed),
                )
                if img_src is not None:
                    img = img_src.group(0)
                obj = self.RSSMessage(
                    bot=self.bot,
                    message_type="web",
                    url=link,
                    title=title,
                    date=datz,
                    author=author,
                    channel=feeds.feed["title"]
                    if "title" in feeds.feed.keys()
                    else "?",
                    image=img,
                )
                liste.append(obj)
            liste.reverse()
            return liste

    async def rss_deviant(
        self,
        guild: discord.Guild,
        nom: str,
        date: datetime.datetime = None,
        session: ClientSession = None,
    ):
        url = "https://backend.deviantart.com/rss.xml?q=gallery%3A" + nom
        feeds = await self.feed_parse(url, 5, session)
        if feeds is None:
            return await self.bot._(guild, "rss.research-timeout")
        if feeds.entries == []:
            return await self.bot._(guild, "rss.nothing")
        if not date:
            feed = feeds.entries[0]
            img_url = feed["media_content"][0]["url"]
            title = re.search(
                r"DeviantArt: ([^ ]+)'s gallery", feeds.feed["title"]
            ).group(1)
            obj = self.RSSMessage(
                bot=self.bot,
                message_type="deviant",
                url=feed["link"],
                title=feed["title"],
                date=feed["published_parsed"],
                author=title,
                image=img_url,
            )
            return [obj]
        else:
            liste = list()
            for feed in feeds.entries:
                if datetime.datetime(*feed["published_parsed"][:6]) <= date:
                    break
                img_url = feed["media_content"][0]["url"]
                title = re.search(
                    r"DeviantArt: ([^ ]+)'s gallery", feeds.feed["title"]
                ).group(1)
                obj = self.RSSMessage(
                    bot=self.bot,
                    message_type="deviant",
                    url=feed["link"],
                    title=feed["title"],
                    date=feed["published_parsed"],
                    author=title,
                    image=img_url,
                )
                liste.append(obj)
            liste.reverse()
            return liste

    async def transform_feed(self, data: dict) -> dict:
        """Transform a feed from the database to be useful for the code
        ie blobs get their correct objects, dates become datetime objects"""
        if data["roles"]:
            try:
                data["roles"] = loads(data["roles"])
            except TypeError:
                data["roles"] = None
        else:
            data["roles"] = list()
        if data["embed_structure"]:
            try:
                data["embed_structure"] = loads(data["embed_structure"])
            except TypeError:
                data["embed_structure"] = None
        else:
            data["embed_structure"] = None
        if data["date"]:
            data["date"] = datetime.datetime.strptime(data["date"], "%Y-%m-%d %H:%M:%S")
        data["added_at"] = datetime.datetime.strptime(
            data["added_at"], "%Y-%m-%d %H:%M:%S"
        )
        return data

    async def db_get_flow(self, flow_id: int):
        query = f"SELECT rowid as ID, * FROM {self.table} WHERE `rowid`=?"
        liste = self.bot.db_query(query, (flow_id,))
        for index, value in enumerate(liste):
            liste[index] = await self.transform_feed(value)
        return liste

    async def db_get_guild_flows(self, guild_id: int):
        """Get every flow of a guild"""
        query = f"SELECT rowid as ID, * FROM {self.table} WHERE `guild`=?"
        liste = self.bot.db_query(query, (guild_id,))
        for index, value in enumerate(liste):
            liste[index] = await self.transform_feed(value)
        return liste

    async def db_add_flow(self, guild_id: int, channel_id: int, _type: str, link: str):
        """Add a flow in the database"""
        if _type == "mc":
            form = ""
        else:
            form = await self.bot._(guild_id, "rss." + _type + "-default-flow")
        query = f"INSERT INTO `{self.table}` (`guild`,`channel`,`type`,`link`,`structure`)"\
            "VALUES (:g, :c, :t, :l, :f)"
        flow_id = self.bot.db_query(
            query, {"g": guild_id, "c": channel_id, "t": _type, "l": link, "f": form}
        )
        return flow_id

    async def db_remove_flow(self, flow_id: int):
        """Remove a flow from the database"""
        if not isinstance(flow_id, int):
            raise ValueError
        query = f"DELETE FROM {self.table} WHERE rowid=?"
        self.bot.db_query(query, (flow_id,))
        return True

    async def db_get_all_flows(self):
        """Get every flow of the database"""
        query = "SELECT rowid as ID, * FROM `{}` WHERE `guild` in ({})".format( # pylint: disable=consider-using-f-string
            self.table, ",".join([f"'{x.id}'" for x in self.bot.guilds])
        )
        liste = self.bot.db_query(query, ())
        for index, value in enumerate(liste):
            liste[index] = await self.transform_feed(value)
        return liste

    async def db_get_count(self, get_disabled: bool = False):
        """Get the number of rss feeds"""
        query = f"SELECT COUNT(*) FROM `{self.table}`"
        if not get_disabled:
            query += (
                " WHERE `guild` in ("
                + ",".join([f"'{x.id}'" for x in self.bot.guilds])
                + ")"
            )
        result = self.bot.db_query(query, (), fetchone=True)
        return result[0]

    async def db_update_flow(self, flow_id: int, values=[(None, None)]): # pylint: disable=dangerous-default-value
        """Update a flow in the database"""
        temp = ", ".join([f"{v[0]}=?" for v in values])
        values = [v[1] for v in values]
        query = f"UPDATE `{self.table}` SET {temp} WHERE rowid={flow_id}"
        self.bot.db_query(query, values)

    async def send_rss_msg(
        self, obj, channel: discord.TextChannel, roles: typing.List[str], send_stats
    ):
        if channel is not None:
            content = await obj.create_msg(await self.get_lang(channel.guild))
            mentions = list()
            for item in roles:
                if item == "":
                    continue
                role = discord.utils.get(channel.guild.roles, id=int(item))
                if role is not None:
                    mentions.append(role)
            try:
                if isinstance(content, discord.Embed):
                    await channel.send(
                        " ".join(obj.mentions),
                        embed=content,
                        allowed_mentions=discord.AllowedMentions(
                            everyone=False, roles=True
                        ),
                    )
                else:
                    await channel.send(
                        content,
                        allowed_mentions=discord.AllowedMentions(
                            everyone=False, roles=True
                        ),
                    )
                if send_stats:
                    if statscog := self.bot.get_cog("BotStats"):
                        statscog.rss_stats["messages"] += 1
            except Exception as exc: # pylint: disable=broad-exception-caught
                self.logger.info(
                    "[send_rss_msg] Cannot send message on channel %i: %s",
                    channel.id,
                    repr(exc),
                )

    async def check_flow(
        self, flow: dict, session: ClientSession = None, send_stats: bool = False
    ):
        try:
            guild = self.bot.get_guild(flow["guild"])
            if flow["link"] in self.cache:
                objs = self.cache[flow["link"]]
            else:
                funct = getattr(self, f"rss_{flow['type']}")
                if flow["type"] == "tw":
                    objs = await funct(guild, flow["link"], flow["date"])
                else:
                    objs = await funct(
                        guild, flow["link"], flow["date"], session=session
                    )
                if isinstance(objs, twitter.error.TwitterError):
                    self.twitter_over_capacity = True
                    return False
                flow["link"] = objs
            if isinstance(objs, twitter.TwitterError):
                await self.bot.get_user(279568324260528128).send(
                    f"[send_rss_msg] twitter error dans `await check_flow(): {objs}`"
                )
                raise objs
            if isinstance(objs, (str, type(None), int)) or len(objs) == 0:
                return True
            elif isinstance(objs, list):
                for obj in objs:
                    guild = self.bot.get_guild(flow["guild"])
                    if guild is None:
                        self.logger.info(
                            "[send_rss_msg] Can not send message on server %i (unknown)",
                            flow['guild'],
                        )
                        return False
                    chan = guild.get_channel(flow["channel"])
                    if guild is None:
                        self.logger.info(
                            "[send_rss_msg] Can not send message on channel %i (unknown)",
                            flow['channel']
                        )
                        return False
                    obj.format = flow["structure"]
                    obj.embed = bool(flow["use_embed"])
                    if obj.embed:
                        obj.fill_embed_data(flow)
                    await obj.fill_mention(guild, flow["roles"], self.bot._)
                    await self.send_rss_msg(obj, chan, flow["roles"], send_stats)
                await self.db_update_flow(
                    flow["ID"],
                    [("date", obj.date)], # pylint: disable=undefined-loop-variable
                )
                return True
            else:
                return True
        except Exception as exc: # pylint: disable=broad-exception-caught
            await self.bot.get_cog("Errors").senf_err_msg(
                f"Erreur rss sur le flux {flow['link']} (type {flow['type']} -"\
                    f"salon {flow['channel']})"
            )
            await self.bot.get_cog("Errors").on_error(exc, None)
            return False

    async def main_loop(self, guild_id: int = None):
        if not self.config.rss_loop_enabled:
            return
        start = time.time()
        if self.loop_processing:
            return
        if guild_id is None:
            self.logger.info("Check RSS lancé")
            self.loop_processing = True
            liste = await self.db_get_all_flows()
        else:
            self.logger.info("Check RSS lancé pour le serveur %i", guild_id)
            liste = await self.db_get_guild_flows(guild_id)
        check = 0
        errors = []
        if guild_id is None:
            if statscog := self.bot.get_cog("BotStats"):
                statscog.rss_stats["messages"] = 0
        session = ClientSession()
        for flow in liste:
            try:
                if flow["type"] == "tw" and self.twitter_over_capacity:
                    continue
                if flow["type"] == "mc":
                    if minecraft_cog := self.bot.get_cog("Minecraft"):
                        await minecraft_cog.check_flow(flow, send_stats=guild_id is None)
                    check += 1
                else:
                    if await self.check_flow(
                        flow, session, send_stats=(guild_id is None)
                    ):
                        check += 1
                    else:
                        errors.append(flow["ID"])
            except Exception as exc: # pylint: disable=broad-exception-caught
                await self.bot.get_cog("Errors").on_error(exc, None)
            await asyncio.sleep(self.time_between_flows_check)
        await session.close()
        if minecraft_cog := self.bot.get_cog("Minecraft"):
            minecraft_cog.flows = dict()
        done = [
            f"**RSS loop done** in {round(time.time() - start, 3)}s ({check}/{len(liste)} flows)"
        ]
        if guild_id is None:
            if statscog := self.bot.get_cog("BotStats"):
                statscog.rss_stats["checked"] = check
                statscog.rss_stats["errors"] = len(errors)
        if len(errors) > 0:
            done.append(
                "{} errors: {}".format(len(errors), " ".join([str(x) for x in errors])) # pylint: disable=consider-using-f-string
            )
        emb = discord.Embed(
            description="\n".join(done),
            color=1655066,
            timestamp=datetime.datetime.utcnow(),
        )
        emb.set_author(name=str(self.bot.user), icon_url=self.bot.user.display_avatar)
        # await self.bot.get_cog("Embeds").send([emb],url="loop")
        self.logger.debug(done[0])
        if len(errors) > 0:
            self.logger.warning("[Rss loop] %s", done[1])
        if guild_id is None:
            self.loop_processing = False
        self.twitter_over_capacity = False
        self.cache = dict()

    @tasks.loop(minutes=20)
    async def loop_child(self):
        self.logger.info(" Boucle rss commencée !")
        start = time.time()
        await self.bot.get_cog("Rss").main_loop()
        self.logger.info(
            " Boucle rss terminée en %f s!",
            round(time.time() - start, 2),
        )

    @loop_child.before_loop
    async def before_loop(self):
        """Wait until the bot is ready"""
        await self.bot.wait_until_ready()

    @commands.command(name="rss_loop", hidden=True)
    @commands.check(checks.is_bot_admin)
    async def rss_loop_admin(self, ctx: MyContext, new_state: str = "start"):
        """Manage the rss loop
        new_state can be start, stop or once"""
        if new_state == "start":
            try:
                await self.loop_child.start() # pylint: disable=no-member
            except RuntimeError:
                await ctx.send("La boucle est déjà en cours !")
            else:
                await ctx.send("Boucle rss relancée !")
        elif new_state == "stop":
            await self.loop_child.cancel() # pylint: disable=no-member
            self.logger.info(" Boucle rss arrêtée de force par un admin")
            await ctx.send("Boucle rss arrêtée de force !")
        elif new_state == "once":
            if self.loop_processing:
                await ctx.send("Une boucle rss est déjà en cours !")
            else:
                await ctx.send("Et hop ! Une itération de la boucle en cours !")
                self.logger.info(" Boucle rss forcée")
                await self.main_loop()
        else:
            await ctx.send(
                "Option `new_start` invalide - choisissez start, stop ou once"
            )

    async def send_log(self, text: str, guild: discord.Guild): # pylint: disable=unused-argument
        """Send a log to the logging channel"""
        return
