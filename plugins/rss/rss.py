from utils import Gunibot, MyContext
from feedparser.util import FeedParserDict
from discord.ext import commands, tasks
from aiohttp.client import ClientSession
from aiohttp import client_exceptions
import twitter
import feedparser
import discord
from bot import checks
import async_timeout
import args
import asyncio
import datetime
import html
import re
import time
import typing
from marshal import dumps, loads
import core

async def setup(bot:Gunibot): await bot.add_cog(Rss(bot), icon="📰")

class Rss(commands.Cog):
    """Cog which deals with everything related to rss flows. Whether it is to add automatic tracking to a stream, or just to see the latest video released by Discord, it is this cog that will be used."""

    def __init__(self, bot: Gunibot):
        self.config = core.config.get("rss")
        self.bot = bot
        self.time_loop = 15  # min minutes between two rss loops
        # seconds between two rss checks within a loop
        self.time_between_flows_check = 0.15
        self.max_feeds_per_guild = 100

        self.embed_color = discord.Color(6017876)
        self.loop_processing = False
        self.twitterAPI = twitter.Api(**self.config["twitter"], tweet_mode="extended")
        self.twitter_over_capacity = False
        self.min_time_between_posts = {"web": 120, "tw": 15, "yt": 120}
        self.cache = dict()
        self.table = "rss_flows"
        try:
            self.date = bot.get_cog("TimeCog").date
        except BaseException:
            pass
        # launch rss loop
        self.loop_child.change_interval(minutes=self.time_loop)
        self.loop_child.start()

    @commands.Cog.listener()
    async def on_ready(self):
        self.date = self.bot.get_cog("TimeCog").date

    def cog_unload(self):
        self.loop_child.cancel()

    class rssMessage:
        def __init__(
            self,
            bot: Gunibot,
            Type,
            url,
            title,
            date=datetime.datetime.now(),
            author=None,
            Format=None,
            channel=None,
            image=None,
        ):
            self.bot = bot
            self.Type = Type
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
            self.format = Format
            self.logo = ":newspaper:"
            self.channel = channel
            self.mentions = []
            if self.author is None:
                self.author = channel

        def fill_embed_data(self, flow: dict):
            if not flow["use_embed"]:
                return
            self.embed_data = {
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
                r = await translate(guild.id, "keywords.none")
            else:
                r = list()
                for item in roles:
                    if item == "":
                        continue
                    role = discord.utils.get(guild.roles, id=int(item))
                    if role is not None:
                        r.append(role.mention)
                    else:
                        r.append(item)
                self.mentions = r
            return self

        async def create_msg(self, language, Format=None):
            if Format is None:
                Format = self.format
            if not isinstance(self.date, str):
                d = await self.bot.get_cog("TimeCog").date(
                    self.date, lang=language, year=False, hour=True, digital=True
                )
            else:
                d = self.date
            Format = Format.replace("\\n", "\n")
            _channel = discord.utils.escape_markdown(self.channel)
            _author = discord.utils.escape_markdown(self.author)
            text = Format.format_map(
                self.bot.SafeDict(
                    channel=_channel,
                    title=self.title,
                    date=d,
                    url=self.url,
                    link=self.url,
                    mentions=", ".join(self.mentions),
                    logo=self.logo,
                    author=_author,
                )
            )
            if not self.embed:
                return text
            else:
                emb = discord.Embed(
                    description=text,
                    timestamp=self.date,
                    color=self.embed_data.get("color", 0),
                )
                if footer := self.embed_data.get("footer", None):
                    emb.set_footer(text=footer)
                if self.embed_data.get("title", None) is None:
                    if self.Type != "tw":
                        emb.title = self.title
                    else:
                        emb.title = self.author
                else:
                    emb.title = self.embed_data["title"]
                emb.add_field(name="URL", value=self.url, inline=False)
                if self.image is not None:
                    emb.set_thumbnail(url=self.image)
                return emb

    async def get_lang(self, guild: typing.Optional[discord.Guild]) -> str:
        guildID = guild.id if guild else None
        return await self.bot.get_cog("Languages").get_lang(guildID, True)

    @commands.group(name="rss")
    @commands.cooldown(2, 15, commands.BucketType.channel)
    async def rss_main(self, ctx: MyContext):
        """See the last post of a rss feed"""
        if ctx.subcommand_passed is None:
            await self.bot.get_cog("Help").help_command(ctx, ["rss"])

    @rss_main.command(name="youtube", aliases=["yt"])
    async def request_yt(self, ctx: MyContext, ID):
        """The last video of a YouTube channel

        ..Examples:
            - rss youtube UCZ5XnGb-3t7jCkXdawN2tkA
            - rss youtube https://www.youtube.com/channel/UCZ5XnGb-3t7jCkXdawN2tkA"""
        if "youtube.com" in ID or "youtu.be" in ID:
            ID = await self.parse_yt_url(ID)
        if ID is None:
            return await ctx.send(await self.bot._(ctx.channel, "rss.web-invalid"))
        text = await self.rss_yt(ctx.channel, ID)
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
        except Exception as e:
            return await self.bot.get_cog("Errors").on_error(e, ctx)
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
        Type = None
        if identifiant is not None:
            Type = "yt"
            display_type = "youtube"
        if identifiant is None:
            identifiant = await self.parse_tw_url(link)
            if identifiant is not None:
                Type = "tw"
                display_type = "twitter"
        if identifiant is None:
            identifiant = await self.parse_twitch_url(link)
            if identifiant is not None:
                Type = "twitch"
                display_type = "twitch"
        if identifiant is None:
            identifiant = await self.parse_deviant_url(link)
            if identifiant is not None:
                Type = "deviant"
                display_type = "deviantart"
        if identifiant is not None and not link.startswith("https://"):
            link = "https://" + link
        if identifiant is None and link.startswith("http"):
            identifiant = link
            Type = "web"
            display_type = "website"
        elif not link.startswith("http"):
            await ctx.send(await self.bot._(ctx.guild, "rss.invalid-link"))
            return
        if Type is None or not await self.check_rss_url(link):
            return await ctx.send(await self.bot._(ctx.guild.id, "rss.invalid-flow"))
        try:
            ID = await self.db_add_flow(ctx.guild.id, ctx.channel.id, Type, identifiant)
            await ctx.send(
                str(await self.bot._(ctx.guild, "rss.success-add")).format(
                    display_type, link, ctx.channel.mention
                )
            )
            self.bot.log.info(
                "RSS feed added into server {} ({} - {})".format(ctx.guild.id, link, ID)
            )
            await self.send_log(
                "Feed added into server {} ({})".format(ctx.guild.id, ID), ctx.guild
            )
        except Exception as e:
            await ctx.send(await self.bot._(ctx.guild, "rss.fail-add"))
            await self.bot.get_cog("Errors").on_error(e, ctx)

    @rss_main.command(name="remove", aliases=["delete"])
    @commands.guild_only()
    @commands.check(commands.has_guild_permissions(manage_webhooks=True))
    async def systeme_rm(self, ctx: MyContext, ID: int = None):
        """Delete an rss feed from the list

        Example: rss remove"""
        flow = await self.askID(
            ID,
            ctx,
            await self.bot._(ctx.guild.id, "rss.choose-delete"),
            allow_mc=True,
            display_mentions=False,
        )
        if flow is None:
            return
        try:
            await self.db_remove_flow(flow[0]["ID"])
        except Exception as e:
            await ctx.send(await self.bot._(ctx.guild, "rss.fail-add"))
            await self.bot.get_cog("Errors").on_error(e, ctx)
            return
        await ctx.send(await self.bot._(ctx.guild, "rss.delete-success"))
        self.bot.log.info(
            "RSS feed deleted into server {} ({})".format(ctx.guild.id, flow[0]["ID"])
        )
        await self.send_log(
            "Feed deleted into server {} ({})".format(ctx.guild.id, flow[0]["ID"]),
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
        l = list()
        for x in liste:
            c = self.bot.get_channel(x["channel"])
            if c is not None:
                c = c.mention
            else:
                c = x["channel"]
            if len(x["roles"]) == 0:
                r = await self.bot._(ctx.guild.id, "keywords.none")
            else:
                r = list()
                for item in x["roles"]:
                    role = discord.utils.get(ctx.guild.roles, id=int(item))
                    if role is not None:
                        r.append(role.mention)
                    else:
                        r.append(item)
                r = ", ".join(r)
            Type = await self.bot._(ctx.guild.id, "rss." + x["type"])
            if len(l) > 20:
                embed = discord.Embed(
                    title=title,
                    color=self.embed_color,
                    timestamp=ctx.message.created_at,
                )
                embed.set_footer(
                    text=str(ctx.author), icon_url=ctx.author.display_avatar
                )
                for text in l:
                    embed.add_field(name="\uFEFF", value=text, inline=False)
                await ctx.send(embed=embed)
                l.clear()
            l.append(translation.format(Type, c, x["link"], r, x["ID"], x["date"]))
        if len(l) > 0:
            embed = discord.Embed(
                title=title, color=self.embed_color, timestamp=ctx.message.created_at
            )
            embed.set_footer(text=str(ctx.author), icon_url=ctx.author.display_avatar)
            for x in l:
                embed.add_field(name="\uFEFF", value=x, inline=False)
            await ctx.send(embed=embed)

    async def askID(
        self,
        ID,
        ctx: MyContext,
        title: str,
        allow_mc: bool = False,
        display_mentions: bool = True,
    ):
        """Request the ID of an rss stream"""
        flow = list()
        if ID is not None:
            flow = await self.db_get_flow(ID)
            if flow == []:
                ID = None
            elif str(flow[0]["guild"]) != str(ctx.guild.id):
                ID = None
            elif (not allow_mc) and flow[0]["type"] == "mc":
                ID = None
        userID = ctx.author.id
        if ID is None:
            gl = await self.db_get_guild_flows(ctx.guild.id)
            if len(gl) == 0:
                await ctx.send(await self.bot._(ctx.guild.id, "rss.no-feed"))
                return
            if display_mentions:
                text = [await self.bot._(ctx.guild.id, "rss.list")]
            else:
                text = [await self.bot._(ctx.guild.id, "rss.list2")]
            list_of_IDs = list()
            iterator = 1
            translations = dict()
            for x in gl:
                if (not allow_mc) and x["type"] == "mc":
                    continue
                if x["type"] == "tw" and x["link"].isnumeric():
                    try:
                        x["link"] = self.twitterAPI.GetUser(
                            user_id=int(x["link"])
                        ).screen_name
                    except twitter.TwitterError as e:
                        pass
                list_of_IDs.append(x["ID"])
                c = self.bot.get_channel(x["channel"])
                if c is not None:
                    c = c.mention
                else:
                    c = x["channel"]
                Type = translations.get(
                    x["type"], await self.bot._(ctx.guild.id, "rss." + x["type"])
                )
                if display_mentions:
                    if len(x["roles"]) == 0:
                        r = await self.bot._(ctx.guild.id, "keywords.none")
                    else:
                        r = list()
                        for item in x["roles"]:
                            role = discord.utils.get(ctx.guild.roles, id=int(item))
                            if role is not None:
                                r.append(role.mention)
                            else:
                                r.append(item)
                        r = ", ".join(r)
                    text.append(
                        "{}) {} - {} - {} - {}".format(iterator, Type, x["link"], c, r)
                    )
                else:
                    text.append("{}) {} - {} - {}".format(iterator, Type, x["link"], c))
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
                for f in fields:
                    embed.add_field(**f)
            emb_msg: discord.Message = await ctx.send(embed=embed)

            def check(msg):
                if not msg.content.isnumeric():
                    return False
                return msg.author.id == userID and int(msg.content) in range(
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
            flow = await self.db_get_flow(list_of_IDs[int(msg.content) - 1])
        if len(flow) == 0:
            await ctx.send(await self.bot._(ctx.guild, "rss.fail-add"))
            return
        return flow

    def parse_output(self, arg):
        r = re.findall(r"((?<![\\])[\"])((?:.(?!(?<![\\])\1))*.?)\1", arg)
        if len(r) > 0:

            def flatten(l):
                return [item for sublist in l for item in sublist]

            params = [[x for x in group if x != '"'] for group in r]
            return flatten(params)
        else:
            return arg.split(" ")

    @rss_main.command(name="roles", aliases=["mentions", "mention"])
    @commands.guild_only()
    @commands.check(commands.has_permissions(manage_webhooks=True))
    async def roles_flows(
        self,
        ctx: MyContext,
        ID: int = None,
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
            flow = await self.askID(
                ID, ctx, await self.bot._(ctx.guild.id, "rss.choose-mentions-1")
            )
        except Exception as e:
            flow = []
            await self.bot.get_cog("Errors").on_error(e, ctx)
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
                r = list()
                for item in flow["roles"]:
                    role = discord.utils.get(ctx.guild.roles, id=int(item))
                    if role is not None:
                        r.append(role.mention)
                    else:
                        r.append(item)
                r = ", ".join(r)
                text = str(await self.bot._(ctx.guild.id, "rss.roles-list")).format(r)
            # ask for roles
            embed = discord.Embed(
                title=await self.bot._(ctx.guild.id, "rss.choose-roles"),
                color=discord.Colour(0x77EA5C),
                description=text,
                timestamp=ctx.message.created_at,
            )
            emb_msg = await ctx.send(embed=embed)
            err = await self.bot._(ctx.guild.id, "find.role-0")
            userID = ctx.author.id

            def check2(msg):
                return msg.author.id == userID

            cond = False
            while cond == False:
                try:
                    msg = await self.bot.wait_for("message", check=check2, timeout=30.0)
                    if (
                        msg.content.lower() in no_role
                    ):  # if no role should be mentionned
                        IDs = [None]
                    else:
                        l = self.parse_output(msg.content)
                        IDs = list()
                        Names = list()
                        for x in l:
                            x = x.strip()
                            try:
                                r = await commands.RoleConverter().convert(ctx, x)
                                IDs.append(str(r.id))
                                Names.append(r.name)
                            except BaseException:
                                await ctx.send(err)
                                IDs = []
                                break
                    if len(IDs) > 0:
                        cond = True
                except asyncio.TimeoutError:
                    await ctx.send(await self.bot._(ctx.guild.id, "rss.too-long"))
                    await emb_msg.delete()
                    return
        else:  # if roles were specified
            if mentions in no_role:  # if no role should be mentionned
                IDs = None
            else:
                IDs = list()
                Names = list()
                for r in mentions:
                    IDs.append(r.id)
                    Names.append(r.name)
                if len(IDs) == 0:
                    await ctx.send(await self.bot._(ctx.guild.id, "find.role-0"))
                    return
        try:
            if IDs is None:
                await self.db_update_flow(flow["ID"], values=[("roles", None)])
                await ctx.send(await self.bot._(ctx.guild.id, "rss.roles-1"))
            else:
                await self.db_update_flow(flow["ID"], values=[("roles", dumps(IDs))])
                txt = ", ".join(Names)
                await ctx.send(
                    str(await self.bot._(ctx.guild.id, "rss.roles-0")).format(txt)
                )
        except Exception as e:
            await ctx.send(await self.bot._(ctx.guild, "rss.fail-add"))
            await self.bot.get_cog("Errors").on_error(e, ctx)
            return

    @rss_main.command(name="reload")
    @commands.guild_only()
    @commands.check(commands.has_permissions(manage_webhooks=True))
    @commands.cooldown(1, 600, commands.BucketType.guild)
    async def reload_guild_flows(self, ctx: MyContext):
        """Reload every rss feeds from your server"""
        try:
            t = time.time()
            msg: discord.Message = await ctx.send(
                str(await self.bot._(ctx.guild.id, "rss.guild-loading")).format("...")
            )
            liste = await self.db_get_guild_flows(ctx.guild.id)
            await self.main_loop(ctx.guild.id)
            await ctx.send(
                str(await self.bot._(ctx.guild.id, "rss.guild-complete")).format(
                    len(liste), round(time.time() - t, 1)
                )
            )
            await msg.delete()
        except Exception as e:
            await ctx.send(
                str(await self.bot._(ctx.guild.id, "rss.guild-error")).format(e)
            )

    @rss_main.command(name="move")
    @commands.guild_only()
    @commands.check(commands.has_permissions(manage_webhooks=True))
    async def move_guild_flow(
        self,
        ctx: MyContext,
        ID: typing.Optional[int] = None,
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
                flow = await self.askID(
                    ID, ctx, await self.bot._(ctx.guild.id, "rss.choose-mentions-1")
                )
                e = None
            except Exception as e:
                flow = []
            if flow is None:
                return
            if len(flow) == 0:
                await ctx.send(await self.bot._(ctx.guild, "rss.fail-add"))
                if e is not None:
                    await self.bot.get_cog("Errors").on_error(e, ctx)
                return
            flow = flow[0]
            await self.db_update_flow(flow["ID"], [("channel", channel.id)])
            await ctx.send(
                str(await self.bot._(ctx.guild.id, "rss.move-success")).format(
                    flow["ID"], channel.mention
                )
            )
        except Exception as e:
            await ctx.send(
                str(await self.bot._(ctx.guild.id, "rss.guild-error")).format(e)
            )

    @rss_main.command(name="text")
    @commands.guild_only()
    @commands.check(commands.has_permissions(manage_webhooks=True))
    async def change_text_flow(
        self, ctx: MyContext, ID: typing.Optional[int] = None, *, text=None
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
                flow = await self.askID(
                    ID, ctx, await self.bot._(ctx.guild.id, "rss.choose-mentions-1")
                )
            except Exception as e:
                flow = []
            if flow is None:
                return
            if len(flow) == 0:
                await ctx.send(await self.bot._(ctx.guild, "rss.fail-add"))
                await self.bot.get_cog("Errors").on_error(e, ctx)
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
        except Exception as e:
            await ctx.send(
                str(await self.bot._(ctx.guild.id, "rss.guild-error")).format(e)
            )
            await ctx.bot.get_cog("Errors").on_error(e, ctx)

    @rss_main.command(name="use_embed", aliases=["embed"])
    @commands.guild_only()
    @commands.check(commands.has_permissions(manage_webhooks=True))
    async def change_use_embed(
        self,
        ctx: MyContext,
        ID: typing.Optional[int] = None,
        value: bool = None,
        *,
        arguments: args.arguments = None,
    ):
        """Use an embed (or not) for a flow
        You can also provide arguments to change the color/text of the embed. Followed arguments are usable:
        - color: color of the embed (hex or decimal value)
        - title: title override, which will disable the default one (max 256 characters)
        - footer: small text displayed at the bottom of the embed

        Examples:
            - rss embed 6678466620137 true title="hey u" footer = "Hi \\n i'm a footer"
            - rss embed 6678466620137 false
            - rss embed 6678466620137 1
        """
        try:
            e = None
            try:
                flow = await self.askID(
                    ID, ctx, await self.bot._(ctx.guild.id, "rss.choose-mentions-1")
                )
            except Exception as e:
                flow = []
                await self.bot.get_cog("Errors").on_error(e, ctx)
            if flow is None:
                return
            if len(flow) == 0:
                await ctx.send(await self.bot._(ctx.guild, "rss.fail-add"))
                if e is not None:
                    await self.bot.get_cog("Errors").on_error(e, ctx)
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
                        _ = commands.core._convert_to_bool(msg.content)
                    except BaseException:
                        return False
                    return msg.author == ctx.author and msg.channel == ctx.channel

                try:
                    msg = await self.bot.wait_for("message", check=check, timeout=20)
                except asyncio.TimeoutError:
                    return await ctx.send(
                        await self.bot._(ctx.guild.id, "rss.too-long")
                    )
                value = commands.core._convert_to_bool(msg.content)
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
                    c = await commands.ColourConverter().convert(
                        ctx, arguments["color"]
                    )
                    if c is not None:
                        embed_data["color"] = c.value
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
        except Exception as e:
            await ctx.send(
                str(await self.bot._(ctx.guild.id, "rss.guild-error")).format(e)
            )
            await ctx.bot.get_cog("Errors").on_error(e, ctx)

    @rss_main.command(name="test")
    @commands.check(checks.is_bot_admin)
    async def test_rss(self, ctx: MyContext, url, *, args=None):
        """Test if an rss feed is usable"""
        url = url.replace("<", "").replace(">", "")
        try:
            feeds = await self.feed_parse(url, 8)
            txt = "feeds.keys()\n```py\n{}\n```".format(feeds.keys())
            if "bozo_exception" in feeds.keys():
                txt += "\nException ({}): {}".format(
                    feeds["bozo"], str(feeds["bozo_exception"])
                )
                return await ctx.send(txt)
            if len(str(feeds.feed)) < 1400 - len(txt):
                txt += "feeds.feed\n```py\n{}\n```".format(feeds.feed)
            else:
                txt += "feeds.feed.keys()\n```py\n{}\n```".format(feeds.feed.keys())
            if len(feeds.entries) > 0:
                if len(str(feeds.entries[0])) < 1950 - len(txt):
                    txt += "feeds.entries[0]\n```py\n{}\n```".format(feeds.entries[0])
                else:
                    txt += "feeds.entries[0].keys()\n```py\n{}\n```".format(
                        feeds.entries[0].keys()
                    )
            if args is not None and "feeds" in args and "ctx" not in args:
                txt += "\n{}\n```py\n{}\n```".format(args, eval(args))
            try:
                await ctx.send(txt)
            except Exception as e:
                print("[rss_test] Error:", e)
                await ctx.send("`Error`: " + str(e))
                print(txt)
            if args is None:
                ok = "✅"
                notok = "❌"
                nothing = "\t"
                txt = ["**__Analyse :__**", ""]
                yt = await self.parse_yt_url(feeds.feed["link"])
                if yt is None:
                    tw = await self.parse_tw_url(feeds.feed["link"])
                    if tw is not None:
                        txt.append("<:twitter:437220693726330881>  " + tw)
                    elif "link" in feeds.feed.keys():
                        txt.append(":newspaper:  <" + feeds.feed["link"] + ">")
                    else:
                        txt.append(":newspaper:  No 'link' var")
                else:
                    txt.append("<:youtube:447459436982960143>  " + yt)
                txt.append("Entrées : {}".format(len(feeds.entries)))
                if len(feeds.entries) > 0:
                    entry = feeds.entries[0]
                    if "title" in entry.keys():
                        txt.append(nothing + ok + " title: ")
                        if len(entry["title"].split("\n")) > 1:
                            txt[-1] += entry["title"].split("\n")[0] + "..."
                        else:
                            txt[-1] += entry["title"]
                    else:
                        txt.append(nothing + notok + " title")
                    if "published_parsed" in entry.keys():
                        txt.append(nothing + ok + " published_parsed")
                    elif "published" in entry.keys():
                        txt.append(nothing + ok + " published")
                    elif "updated_parsed" in entry.keys():
                        txt.append(nothing + ok + " updated_parsed")
                    else:
                        txt.append(nothing + notok + " date")
                    if "author" in entry.keys():
                        txt.append(nothing + ok + " author: " + entry["author"])
                    else:
                        txt.append(nothing + notok + " author")
                await ctx.send("\n".join(txt))
        except Exception as e:
            await ctx.bot.get_cog("Errors").on_command_error(ctx, e)

    async def check_rss_url(self, url):
        r = await self.parse_yt_url(url)
        if r is not None:
            return True
        r = await self.parse_tw_url(url)
        if r is not None:
            return True
        r = await self.parse_twitch_url(url)
        if r is not None:
            return True
        r = await self.parse_deviant_url(url)
        if r is not None:
            return True
        try:
            f = await self.feed_parse(url, 8)
            _ = f.entries[0]
            return True
        except BaseException:
            return False

    async def parse_yt_url(self, url):
        r = r"(?:http.*://)?(?:www.)?(?:youtube.com|youtu.be)(?:(?:/channel/|/user/)(.+)|/[\w-]+$)"
        match = re.search(r, url)
        if match is None:
            return None
        else:
            return match.group(1)

    async def parse_tw_url(self, url):
        r = r"(?:http.*://)?(?:www.)?(?:twitter.com/)([^?\s]+)"
        match = re.search(r, url)
        if match is None:
            return None
        else:
            name = match.group(1)
            try:
                user = self.twitterAPI.GetUser(screen_name=name)
            except twitter.TwitterError:
                return None
            return user.id

    async def parse_twitch_url(self, url):
        r = r"(?:http.*://)?(?:www.)?(?:twitch.tv/)([^?\s]+)"
        match = re.search(r, url)
        if match is None:
            return None
        else:
            return match.group(1)

    async def parse_deviant_url(self, url):
        r = r"(?:http.*://)?(?:www.)?(?:deviantart.com/)([^?\s]+)"
        match = re.search(r, url)
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
            async with async_timeout.timeout(timeout) as cm:
                async with _session.get(url) as response:
                    html = await response.text()
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
        if cm.expired:
            # request was cancelled by timeout
            self.bot.info("[RSS] feed_parse got a timeout")
            return None
        headers = {k.decode("utf-8").lower(): v.decode("utf-8") for k, v in headers}
        return feedparser.parse(html, response_headers=headers)

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
            obj = self.rssMessage(
                bot=self.bot,
                Type="yt",
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
                obj = self.rssMessage(
                    bot=self.bot,
                    Type="yt",
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
                posts = self.twitterAPI.GetUserTimeline(
                    user_id=int(name), exclude_replies=True
                )
                username = self.twitterAPI.GetUser(user_id=int(name)).screen_name
            else:
                posts = self.twitterAPI.GetUserTimeline(
                    screen_name=name, exclude_replies=True
                )
                username = name
        except twitter.error.TwitterError as e:
            if e.message == "Not authorized.":
                return await self.bot._(channel, "rss.nothing")
            if "Unknown error" in e.message:
                return await self.bot._(channel, "rss.nothing")
            if "The twitter.Api instance must be authenticated." in e.message:
                return await self.bot._(channel, "rss.wrong-token")
            if e.message[0]["code"] == 34:
                return await self.bot._(channel, "rss.nothing")
            raise e
        if not date:
            if len(posts) == 0:
                return []
            lastpost = posts[0]
            text = html.unescape(getattr(lastpost, "full_text", lastpost.text))
            url = "https://twitter.com/{}/status/{}".format(
                username.lower(), lastpost.id
            )
            img = None
            if lastpost.media:  # if exists and is not empty
                img = lastpost.media[0].media_url_https
            obj = self.rssMessage(
                bot=self.bot,
                Type="tw",
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
                if r := re.search(r"https://t.co/([^\s]+)", text):
                    text = text.replace(r.group(0), "")
                url = "https://twitter.com/{}/status/{}".format(name.lower(), post.id)
                img = None
                if post.media:  # if exists and is not empty
                    img = post.media[0].media_url_https
                obj = self.rssMessage(
                    bot=self.bot,
                    Type="tw",
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
            r = re.search(r'<img src="([^"]+)" />', feed["summary"])
            img_url = None
            if r is not None:
                img_url = r.group(1)
            obj = self.rssMessage(
                bot=self.bot,
                Type="twitch",
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
                r = re.search(r'<img src="([^"]+)" />', feed["summary"])
                img_url = None
                if r is not None:
                    img_url = r.group(1)
                obj = self.rssMessage(
                    bot=self.bot,
                    Type="twitch",
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
                l = feed["link"]
            elif "link" in feeds.keys():
                l = feeds["link"]
            else:
                l = url
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
            r = re.search(
                r"(http(s?):)([/|.|\w|\s|-])*\.(?:jpe?g|gif|png|webp)", str(feed)
            )
            if r is not None:
                img = r.group(0)
            obj = self.rssMessage(
                bot=self.bot,
                Type="web",
                url=l,
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
                try:
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
                        l = feed["link"]
                    elif "link" in feeds.keys():
                        l = feeds["link"]
                    else:
                        l = url
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
                    r = re.search(
                        r"(http(s?):)([/|.|\w|\s|-])*\.(?:jpe?g|gif|png|webp)",
                        str(feed),
                    )
                    if r is not None:
                        img = r.group(0)
                    obj = self.rssMessage(
                        bot=self.bot,
                        Type="web",
                        url=l,
                        title=title,
                        date=datz,
                        author=author,
                        channel=feeds.feed["title"]
                        if "title" in feeds.feed.keys()
                        else "?",
                        image=img,
                    )
                    liste.append(obj)
                except BaseException:
                    pass
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
            obj = self.rssMessage(
                bot=self.bot,
                Type="deviant",
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
                obj = self.rssMessage(
                    bot=self.bot,
                    Type="deviant",
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

    async def db_get_flow(self, ID: int):
        query = f"SELECT rowid as ID, * FROM {self.table} WHERE `rowid`=?"
        liste = self.bot.db_query(query, (ID,))
        for e in range(len(liste)):
            liste[e] = await self.transform_feed(liste[e])
        return liste

    async def db_get_guild_flows(self, guildID: int):
        """Get every flow of a guild"""
        query = f"SELECT rowid as ID, * FROM {self.table} WHERE `guild`=?"
        liste = self.bot.db_query(query, (guildID,))
        for e in range(len(liste)):
            liste[e] = await self.transform_feed(liste[e])
        return liste

    async def db_add_flow(self, guildID: int, channelID: int, _type: str, link: str):
        """Add a flow in the database"""
        if _type == "mc":
            form = ""
        else:
            form = await self.bot._(guildID, "rss." + _type + "-default-flow")
        query = "INSERT INTO `{}` (`guild`,`channel`,`type`,`link`,`structure`) VALUES (:g, :c, :t, :l, :f)".format(
            self.table
        )
        ID = self.bot.db_query(
            query, {"g": guildID, "c": channelID, "t": _type, "l": link, "f": form}
        )
        return ID

    async def db_remove_flow(self, ID: int):
        """Remove a flow from the database"""
        if not isinstance(ID, int):
            raise ValueError
        query = f"DELETE FROM {self.table} WHERE rowid=?"
        self.bot.db_query(query, (ID,))
        return True

    async def db_get_all_flows(self):
        """Get every flow of the database"""
        query = "SELECT rowid as ID, * FROM `{}` WHERE `guild` in ({})".format(
            self.table, ",".join(["'{}'".format(x.id) for x in self.bot.guilds])
        )
        liste = self.bot.db_query(query, ())
        for e in range(len(liste)):
            liste[e] = await self.transform_feed(liste[e])
        return liste

    async def db_get_count(self, get_disabled: bool = False):
        """Get the number of rss feeds"""
        query = "SELECT COUNT(*) FROM `{}`".format(self.table)
        if not get_disabled:
            query += (
                " WHERE `guild` in ("
                + ",".join(["'{}'".format(x.id) for x in self.bot.guilds])
                + ")"
            )
        result = self.bot.db_query(query, (), fetchone=True)
        return result[0]

    async def db_update_flow(self, ID: int, values=[(None, None)]):
        """Update a flow in the database"""
        temp = ", ".join([f"{v[0]}=?" for v in values])
        values = [v[1] for v in values]
        query = f"UPDATE `{self.table}` SET {temp} WHERE rowid={ID}"
        self.bot.db_query(query, values)

    async def send_rss_msg(
        self, obj, channel: discord.TextChannel, roles: typing.List[str], send_stats
    ):
        if channel is not None:
            t = await obj.create_msg(await self.get_lang(channel.guild))
            mentions = list()
            for item in roles:
                if item == "":
                    continue
                role = discord.utils.get(channel.guild.roles, id=int(item))
                if role is not None:
                    mentions.append(role)
            try:
                if isinstance(t, discord.Embed):
                    await channel.send(
                        " ".join(obj.mentions),
                        embed=t,
                        allowed_mentions=discord.AllowedMentions(
                            everyone=False, roles=True
                        ),
                    )
                else:
                    await channel.send(
                        t,
                        allowed_mentions=discord.AllowedMentions(
                            everyone=False, roles=True
                        ),
                    )
                if send_stats:
                    if statscog := self.bot.get_cog("BotStats"):
                        statscog.rss_stats["messages"] += 1
            except Exception as e:
                self.bot.log.info(
                    "[send_rss_msg] Cannot send message on channel {}: {}".format(
                        channel.id, e
                    )
                )

    async def check_flow(
        self, flow: dict, session: ClientSession = None, send_stats: bool = False
    ):
        try:
            guild = self.bot.get_guild(flow["guild"])
            if flow["link"] in self.cache.keys():
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
                for o in objs:
                    guild = self.bot.get_guild(flow["guild"])
                    if guild is None:
                        self.bot.log.info(
                            "[send_rss_msg] Can not send message on server {} (unknown)".format(
                                flow["guild"]
                            )
                        )
                        return False
                    chan = guild.get_channel(flow["channel"])
                    if guild is None:
                        self.bot.log.info(
                            "[send_rss_msg] Can not send message on channel {} (unknown)".format(
                                flow["channel"]
                            )
                        )
                        return False
                    o.format = flow["structure"]
                    o.embed = bool(flow["use_embed"])
                    if o.embed:
                        o.fill_embed_data(flow)
                    await o.fill_mention(guild, flow["roles"], self.bot._)
                    await self.send_rss_msg(o, chan, flow["roles"], send_stats)
                await self.db_update_flow(
                    flow["ID"],
                    [("date", o.date)],
                )
                return True
            else:
                return True
        except Exception as e:
            await self.bot.get_cog("Errors").senf_err_msg(
                "Erreur rss sur le flux {} (type {} - salon {})".format(
                    flow["link"], flow["type"], flow["channel"]
                )
            )
            await self.bot.get_cog("Errors").on_error(e, None)
            return False

    async def main_loop(self, guildID: int = None):
        if not self.config["rss_loop_enabled"]:
            return
        t = time.time()
        if self.loop_processing:
            return
        if guildID is None:
            self.bot.log.info("Check RSS lancé")
            self.loop_processing = True
            liste = await self.db_get_all_flows()
        else:
            self.bot.log.info(f"Check RSS lancé pour le serveur {guildID}")
            liste = await self.db_get_guild_flows(guildID)
        check = 0
        errors = []
        if guildID is None:
            if statscog := self.bot.get_cog("BotStats"):
                statscog.rss_stats["messages"] = 0
        session = ClientSession()
        for flow in liste:
            try:
                if flow["type"] == "tw" and self.twitter_over_capacity:
                    continue
                if flow["type"] == "mc":
                    if MCcog := self.bot.get_cog("Minecraft"):
                        await MCcog.check_flow(flow, send_stats=(guildID is None))
                    check += 1
                else:
                    if await self.check_flow(
                        flow, session, send_stats=(guildID is None)
                    ):
                        check += 1
                    else:
                        errors.append(flow["ID"])
            except Exception as e:
                await self.bot.get_cog("Errors").on_error(e, None)
            await asyncio.sleep(self.time_between_flows_check)
        await session.close()
        if MCcog := self.bot.get_cog("Minecraft"):
            MCcog.flows = dict()
        d = [
            "**RSS loop done** in {}s ({}/{} flows)".format(
                round(time.time() - t, 3), check, len(liste)
            )
        ]
        if guildID is None:
            if statscog := self.bot.get_cog("BotStats"):
                statscog.rss_stats["checked"] = check
                statscog.rss_stats["errors"] = len(errors)
        if len(errors) > 0:
            d.append(
                "{} errors: {}".format(len(errors), " ".join([str(x) for x in errors]))
            )
        emb = discord.Embed(
            description="\n".join(d),
            color=1655066,
            timestamp=datetime.datetime.utcnow(),
        )
        emb.set_author(name=str(self.bot.user), icon_url=self.bot.user.display_avatar)
        # await self.bot.get_cog("Embeds").send([emb],url="loop")
        self.bot.log.debug(d[0])
        if len(errors) > 0:
            self.bot.log.warn("[Rss loop] " + d[1])
        if guildID is None:
            self.loop_processing = False
        self.twitter_over_capacity = False
        self.cache = dict()

    @tasks.loop(minutes=20)
    async def loop_child(self):
        self.bot.log.info(" Boucle rss commencée !")
        t1 = time.time()
        await self.bot.get_cog("Rss").main_loop()
        self.bot.log.info(
            " Boucle rss terminée en {}s!".format(round(time.time() - t1, 2))
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
                await self.loop_child.start()
            except RuntimeError:
                await ctx.send("La boucle est déjà en cours !")
            else:
                await ctx.send("Boucle rss relancée !")
        elif new_state == "stop":
            await self.loop_child.cancel()
            self.bot.log.info(" Boucle rss arrêtée de force par un admin")
            await ctx.send("Boucle rss arrêtée de force !")
        elif new_state == "once":
            if self.loop_processing:
                await ctx.send("Une boucle rss est déjà en cours !")
            else:
                await ctx.send("Et hop ! Une itération de la boucle en cours !")
                self.bot.log.info(" Boucle rss forcée")
                await self.main_loop()
        else:
            await ctx.send(
                "Option `new_start` invalide - choisissez start, stop ou once"
            )

    async def send_log(self, text: str, guild: discord.Guild):
        """Send a log to the logging channel"""
        return
        # try:
        #     emb = self.bot.get_cog("Embeds").Embed(desc="[RSS] "+text,color=5366650,footer_text=guild.name).update_timestamp().set_author(self.bot.user)
        #     await self.bot.get_cog("Embeds").send([emb])
        # except Exception as e:
        #     await self.bot.get_cog("Errors").on_error(e,None)
