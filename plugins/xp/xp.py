"""
Ce programme est régi par la licence CeCILL soumise au droit français et
respectant les principes de diffusion des logiciels libres. Vous pouvez
utiliser, modifier et/ou redistribuer ce programme sous les conditions
de la licence CeCILL diffusée sur le site "http://www.cecill.info".
"""

from typing import Dict, List, Tuple, Union
import asyncio
import re
import string
import time
import typing
from math import ceil

import discord
import emoji
from discord.ext import commands, tasks

from utils import Gunibot, MyContext

from core import setup_logger

class XP(commands.Cog):
    def __init__(self, bot: Gunibot):
        self.bot = bot
        self.logger = setup_logger('xp')

        self.cooldown = 30
        self.minimal_size = 5
        self.spam_rate = 0.20
        self.xp_per_char = 0.115
        self.max_xp_per_msg = 70
        self.cache: Dict[Dict[int, int]] = dict()  # xp cache
        self.levels = [0]  # xp required per level
        self.xp_channels_cache = dict()  # no-xp channels
        self.embed_color = discord.Colour(0xFFCF50)

        self.config_options = [
            "enable_xp",
            "noxp_channels",
            "xp_reduction",
            "levelup_channel",
            "levelup_message",
            "levelup_reaction",
            "reaction_emoji",
        ]
        bot.get_command("config").add_command(self.config_enable_xp)
        bot.get_command("config").add_command(self.config_noxp_channels)
        bot.get_command("config").add_command(self.config_xp_reduction)
        bot.get_command("config").add_command(self.config_levelup_channel)
        bot.get_command("config").add_command(self.config_levelup_message)
        bot.get_command("config").add_command(self.config_levelup_reaction)
        bot.get_command("config").add_command(self.config_levelup_reaction_emoji)

        self.xp_reduction.start() # pylint: disable=no-member

    @commands.command(name="enable_xp")
    async def config_enable_xp(self, ctx: MyContext, value: bool):
        """Enable or disable the XP system in your server"""
        await ctx.send(
            await self.bot.sconfig.edit_config(ctx.guild.id, "enable_xp", value)
        )

    @commands.command(name="noxp_channels")
    async def config_noxp_channels(
        self, ctx: MyContext, channels: commands.Greedy[discord.abc.GuildChannel]
    ):
        """Select in which channels your members should not get any xp"""
        if len(channels) == 0:
            channels = None
        else:
            channels = [channel.id for channel in channels]
        noxp_channels = await self.bot.sconfig.edit_config(ctx.guild.id, "noxp_channels", channels)
        self.xp_channels_cache[ctx.guild.id] = channels if channels is not None else []
        await ctx.send(noxp_channels)

    @commands.command(name="xp_reduction")
    async def config_xp_reduction(self, ctx: MyContext, enabled:bool):
        """Enable or disable the xp reduction system"""
        await ctx.send(
            await self.bot.sconfig.edit_config(ctx.guild.id, "xp_reduction", enabled)
        )

    @commands.command(name="levelup_channel")
    async def config_levelup_channel(self, ctx: MyContext, *, channel):
        """Select in which channel the levelup messages should be sent
        None for no levelup message, any for any channel"""
        if channel.lower() == "none":
            channel = "none"
        elif channel.lower() == "any":
            channel = "any"
        else:
            channel = await commands.TextChannelConverter().convert(ctx, channel)
            channel = channel.id
        await ctx.send(
            await self.bot.sconfig.edit_config(ctx.guild.id, "levelup_channel", channel)
        )
        self.xp_channels_cache.pop(ctx.guild.id, None)

    @commands.command(name="levelup_message")
    async def config_levelup_message(self, ctx: MyContext, *, message=None):
        """Message sent when a member reaches a new level
        Use {level} for the new level, {user} for the user mention and {username} for the user name
        Set to None to reset it"""
        await ctx.send(
            await self.bot.sconfig.edit_config(ctx.guild.id, "levelup_message", message)
        )

    @commands.command(name="levelup_reaction")
    async def config_levelup_reaction(self, ctx: MyContext, *, enabled: bool = None):
        """If the bot add a reaction to the message or send a message
        Set to True for the reaction, False for the message"""
        await ctx.send(
            await self.bot.sconfig.edit_config(ctx.guild.id, "levelup_reaction", enabled)
        )

    @commands.command(name="reaction_emoji")
    async def config_levelup_reaction_emoji(
        self, ctx: MyContext, emote: Union[discord.Emoji, str] = None
    ):
        """Set the emoji wich one the bot will react to message when levelup"""
        # check if emoji is valid
        emote = (
            emote
            if isinstance(emote, discord.Emoji) or emoji.is_emoji(emote)
            else False
        )
        # if emojis was invalid (couldn't be converted)
        if not emote:
            await ctx.send(await self.bot._(ctx.guild.id, "sconfig.invalid-emoji"))
            return
        # convert discord emoji to ID if needed
        emote = str(emote.id) if isinstance(emote, discord.Emoji) else emote
        # save result
        await ctx.send(
            await self.bot.sconfig.edit_config(ctx.guild.id, "reaction_emoji", emote)
        )

    async def _create_config(
        self, ctx: MyContext, mentions: bool = False
    ) -> List[Tuple[str, str]]:
        """Create a list of (key,value) for the /config command"""
        roles = await self.rr_list_role(ctx.guild.id)
        sorted_dict = {}
        for role in roles:
            if role := ctx.guild.get_role(role["role"]):
                if role["level"] in sorted_dict:
                    sorted_dict[role["level"]].append(role)
                else:
                    sorted_dict[role["level"]] = [role]
        if len(sorted_dict) == 0:
            return []
        _lvl = await self.bot._(ctx.guild.id, "xp.card.level")
        result = []
        for key, value in sorted(sorted_dict.items()):
            if mentions:
                subroles = [r.mention for r in value]
            else:
                subroles = [r.name for r in value]
            result.append((f"{_lvl} {key}", " ".join(subroles)))
        return result


    ################
    # XP reduction #
    ################

    @tasks.loop(hours=24*7)
    async def xp_reduction(self):
        """Reduce the xp of all members each week"""

        # Compute the XP to remove each week
        xp_to_remove = await self.calc_xp("""Vous savez, moi je ne crois pas qu’il y ait de bonne ou
de mauvaise situation. Moi, si je devais résumer ma vie aujourd’hui avec vous, je dirais que c’est
d’abord des rencontres. Des gens qui m’ont tendu la main, peut-être à un moment où je ne pouvais
pas, où j’étais seul chez moi. Et c’est assez curieux de se dire que les hasards, les rencontres
forgent une destinée... Parce que quand on a le goût de la chose, quand on a le goût de la chose
bien faite, le beau geste, parfois on ne trouve pas l’interlocuteur en face je dirais, le miroir qui
vous aide à avancer. Alors ça n’est pas mon cas, comme je disais là, puisque moi au contraire, j’ai
pu ; et je dis merci à la vie, je lui dis merci, je chante la vie, je danse la vie... je ne suis
qu’amour ! Et finalement, quand des gens me disent « Mais comment fais-tu pour avoir cette
humanité ? », je leur réponds très simplement que c’est ce goût de l’amour, ce goût donc qui m’a
poussé aujourd’hui à entreprendre une construction mécanique... mais demain qui sait ? Peut-être
simplement à me mettre au service de la communauté, à faire le don, le don de soi.""")

        # xp_to_remove *= 1
        for guild in self.bot.guilds:
            if self.bot.server_configs[guild.id]["xp_reduction"]:
                for member in guild.members:
                    await self.bdd_set_xp(
                        user_id=member.id,
                        points=xp_to_remove,
                        action_type="remove",
                        guild=guild.id,
                    )



    async def get_lvlup_chan(self, msg: discord.Message):
        value = self.bot.server_configs[msg.guild.id]["levelup_channel"]
        if value is None or value == "none":
            return None
        if value == "any":
            return msg.channel
        try:
            chan = msg.guild.get_channel(int(value))
            return chan
        except discord.errors.NotFound:
            return None

    async def check_noxp(self, message: discord.Message):
        """Check if this channel/user can get xp"""
        if message.guild is None:
            return False
        
        # get the channel ID (or parent channel id for thread)
        channel_id = message.channel.parent.id if isinstance(message.channel, discord.Thread) else message.channel.id
        # get the category
        category_id = message.channel.category.id if message.channel.category is not None else 0 # dumb ID

        if message.guild.id in self.xp_channels_cache:
            if channel_id in self.xp_channels_cache[message.guild.id]:
                return False
            if category_id in self.xp_channels_cache[message.guild.id]:
                return False
        else: # load cache
            channels = self.bot.server_configs[message.guild.id]["noxp_channels"]
            if channels is not None:
                # convert to a list even if there's only one item
                channels = [channels] if isinstance(channels, str) else channels
                channels = [int(x) for x in channels]
                
                self.xp_channels_cache[message.guild.id] = channels

                if channel_id in channels or category_id in channels:
                    return False
            else:
                self.xp_channels_cache[message.guild.id] = []
        
        return True

    async def check_cmd(self, msg: discord.Message):
        """Checks if a message is a command"""
        prefix = await self.bot.get_prefix(msg)
        return any([msg.content.startswith(p) for p in prefix])

    async def check_spam(self, text: str):
        """Checks if a text contains spam"""
        # check for usual bots prefixes
        if len(text) > 0 and (
            text[0] in string.punctuation or text[1] in string.punctuation
        ):
            return True
        chars = {}
        # count frequency of letters in the message
        for char in text:
            if char in chars:
                chars[char] += 1
            else:
                chars[char] = 1
        for value in chars.values():
            # if frequency is too high: spam detected
            if value / len(text) > self.spam_rate:
                return True
        return False

    @commands.Cog.listener("on_message")
    async def add_xp(self, msg: discord.Message):
        """Assigns a certain amount of xp to a message"""
        # check if it's a bot or sent in DM
        if msg.author.bot or msg.guild is None:
            return
        # check if it's in a no-xp channel or if xp is disabled in the server
        if not (
            await self.check_noxp(msg)
            and self.bot.server_configs[msg.guild.id]["enable_xp"]
        ):
            return
        
        # if xp of that guild is not in cache yet
        if msg.guild.id not in self.cache or len(self.cache[msg.guild.id]) == 0:
            await self.bdd_load_cache(msg.guild.id)
        # if xp of that member is in cache
        if msg.author.id in self.cache[msg.guild.id].keys():
            # we check cooldown
            if time.time() - self.cache[msg.guild.id][msg.author.id][0] < self.cooldown:
                return
        content = msg.clean_content
        # if content is too short or is spammy or is a command
        if (
            len(content) < self.minimal_size
            or await self.check_spam(content)
            or await self.check_cmd(msg)
        ):
            return
        # we calcul xp amount
        giv_points = await self.calc_xp(msg)
        # we check in the cache for the previous xp
        if msg.author.id in self.cache[msg.guild.id].keys():
            prev_points = self.cache[msg.guild.id][msg.author.id][1]
        else:
            # we check in the database for the previous xp
            prev_points = await self.bdd_get_xp(msg.author.id, msg.guild.id)
            if len(prev_points) > 0:
                prev_points = prev_points[0]["xp"]
            else:
                # if user not in database, it's their first message
                prev_points = 0
        # we update database with the new xp amount
        await self.bdd_set_xp(msg.author.id, giv_points, "add", msg.guild.id)
        # we update cache with the new xp amount
        self.cache.get(msg.guild.id)[msg.author.id] = [
            round(time.time()),
            prev_points + giv_points,
        ]
        # calcul of the new level
        new_lvl = await self.calc_level(self.cache[msg.guild.id][msg.author.id][1])
        # if new level is higher than previous level higher than 0
        if 0 < (await self.calc_level(prev_points))[0] < new_lvl[0]:
            # we send levelup message
            await self.send_levelup(msg, new_lvl)
            # refresh roles rewards for that user
            await self.give_rr(
                msg.author, new_lvl[0], await self.rr_list_role(msg.guild.id)
            )

    async def calc_xp(self, msg: discord.Message | str):
        """Calculates the xp amount corresponding to a message"""
        if isinstance(msg, str):
            content = msg
        else:
            content: str = msg.clean_content
        # we replace custom emojis by their names
        matches = re.finditer(r"<a?(:\w+:)\d+>", content, re.MULTILINE)
        for _, match in enumerate(matches, start=1):
            content = content.replace(match.group(0), match.group(1))
        # we remove links
        matches = re.finditer(r"((?:http|www)[^\s]+)", content, re.MULTILINE)
        for _, match in enumerate(matches, start=1):
            content = content.replace(match.group(0), "")
        return min(round(len(content) * self.xp_per_char), self.max_xp_per_msg)

    async def calc_level(self, xp: int): # pylint: disable=invalid-name
        """Calculates the level corresponding to a xp amount
        Returns: Current level, Total XP for the next level, Total XP for the current level

        Maths:
        - current lvl = ceil(0.056*current_xp^0.65)
        - xp needed for a level: ceil(((lvl-1)*125/7)^(20/13))"""
        if xp == 0:
            return [0, ceil((1 * 125 / 7) ** (20 / 13)), 0]
        lvl = ceil(0.056 * xp**0.65)
        next_step = ceil((lvl * 125 / 7) ** (20 / 13))
        # next_step = xp
        # while ceil(0.056*next_step**0.65) == lvl:
        #     next_step += 1
        return [lvl, next_step, ceil(((lvl - 1) * 125 / 7) ** (20 / 13))]

    async def send_levelup(self, msg: discord.Message, lvl: int):
        """Send the levelup message or react with the reaction"""
        config = self.bot.server_configs[msg.guild.id]
        if config["levelup_reaction"]:
            if config["reaction_emoji"] is None:
                await msg.add_reaction("💫")
            else:

                def emojis_convert(
                    s_emoji: str, bot_emojis: List[discord.Emoji]
                ) -> Union[str, discord.Emoji]:
                    if s_emoji.isnumeric():
                        d_em = discord.utils.get(bot_emojis, id=int(s_emoji))
                        if d_em is not None:
                            return d_em
                    return emoji.emojize(s_emoji, language="alias")

                await msg.add_reaction(
                    emojis_convert(config["reaction_emoji"], self.bot.emojis)
                )
        else:
            destination = await self.get_lvlup_chan(msg)
            # if no channel or not enough permissions: abort
            if destination is None or (
                not msg.channel.permissions_for(msg.guild.me).send_messages
            ):
                return
            text = config["levelup_message"]
            if text is None or len(text) == 0:
                text = await self.bot._(msg.channel, "xp.default_levelup")
            await destination.send(
                text.format_map(
                    self.bot.SafeDict(
                        user=msg.author.mention,
                        level=lvl[0],
                        username=msg.author.display_name,
                    )
                )
            )

    async def give_rr(
        self,
        member: discord.Member,
        level: int,
        rr_list: List[Dict[str, int]],
        remove: bool = False,
    ) -> int:
        """Give (and remove?) roles rewards to a member
        rr_list is a list of dictionnaries containing level and role id
        put remove as True if you want to remove unneeded roles rewards too"""
        counter = 0
        # List of roles IDs owned by user
        has_roles = [role.id for role in member.roles]
        # for each role that should be given and not already owned by user
        for role in [
            role_reward for role_reward in rr_list\
            if role_reward["level"] <= level and role_reward["role"] not in has_roles
        ]:
            try:
                member_role = member.guild.get_role(role["role"])
                if member_role is None:
                    continue
                # finally add the role, with a reason
                await member.add_roles(
                    member_role, reason=f"Role reward (lvl {role['level']})"
                )
                counter += 1
            except Exception as exc: # pylint: disable=broad-exception-caught
                await self.bot.get_cog("Errors").on_error(exc)
        # if we don't have to remove roles: stop
        if not remove:
            return counter
        # for each role that should be removed and owned by user
        for role in [
            x for x in rr_list if x["level"] > level and x["role"] in has_roles
        ]:
            try:
                member_role = member.guild.get_role(role["role"])
                if member_role is None:
                    continue
                # finally remove the role, with a reason
                await member.remove_roles(
                    member_role, reason=f"Role reward (lvl {role['level']})"
                )
                counter += 1
            except Exception as exc: # pylint: disable=broad-exception-caught
                await self.bot.get_cog("Errors").on_error(exc)
        return counter

    async def bdd_set_xp(
        self, user_id: int, points: int, action_type: str = "add", guild: int = None
    ):
        """Add/reset xp to a user in the database
        Set guild=None for global leaderboard"""
        try:
            try:
                xp = await self.bdd_get_xp(user_id, guild) # pylint: disable=invalid-name
                xp = xp[0]["xp"] # pylint: disable=invalid-name
            except IndexError:
                xp = 0 # pylint: disable=invalid-name
            if points < 0:
                raise ValueError("You cannot add nor set negative xp")
            if action_type == "add":
                query = "INSERT INTO xp (`guild`, `userid`,`xp`) VALUES (:g, :u, :p)"\
                    "ON CONFLICT(guild, userid) DO UPDATE SET xp = (xp + :p);"
            elif action_type == "remove":
                if xp < points:
                    query = "INSERT INTO xp (`guild`, `userid`,`xp`) VALUES"\
                        "(:g, :u, :p) ON CONFLICT(guild, userid) DO UPDATE SET xp = 0;"
                else:
                    query = "INSERT INTO xp (`guild`, `userid`,`xp`) VALUES (:g, :u, :p)"\
                        "ON CONFLICT(guild, userid) DO UPDATE SET xp = (xp - :p);"
            else:
                query = "INSERT INTO xp (`guild`, `userid`,`xp`) VALUES (:g, :u, :p)"\
                    "ON CONFLICT(guild, userid) DO UPDATE SET xp = :p;"

            self.bot.db_query(query, {"g": guild, "u": user_id, "p": points})
            return True
        except Exception as exc: # pylint: disable=broad-exception-caught
            await self.bot.get_cog("Errors").on_error(exc)
            return False

    async def bdd_get_xp(self, user_id: int, guild: int = None):
        """Get the xp amount of a user in a guild
        Set guild=None for global leaderboard"""
        try:
            query = "SELECT `xp` FROM `xp` WHERE `userid` = :u AND `guild` = :g"
            liste = self.bot.db_query(query, {"u": user_id, "g": guild})
            if len(liste) == 1:
                if user_id in self.cache[guild].keys():
                    self.cache[guild][user_id][1] = liste[0]["xp"]
                else:
                    self.cache[guild][user_id] = [
                        round(time.time()) - 60,
                        liste[0]["xp"],
                    ]
            return liste
        except Exception as exc: # pylint: disable=broad-exception-caught
            await self.bot.get_cog("Errors").on_error(exc)
            return list()

    async def bdd_get_nber(self, guild: int = None):
        """Get the number of ranked users in a guild
        Set guild=None for global leaderboard"""
        try:
            query = "SELECT COUNT(*) as count FROM xp WHERE `guild` = :g"
            liste = self.bot.db_query(query, {"g": guild})
            if liste is not None and len(liste) == 1:
                return liste[0]["count"]
            return 0
        except Exception as exc: # pylint: disable=broad-exception-caught
            await self.bot.get_cog("Errors").on_error(exc)
            return 0

    async def bdd_load_cache(self, guild: int = None):
        """Load the xp cache for a specific guild
        Set guild=None for global leaderboard"""
        try:
            self.logger.info("Loading XP cache (guild %s)", repr(guild))
            query = "SELECT `userid`,`xp` FROM xp WHERE `guild` = ?"
            liste = self.bot.db_query(query, (guild,))
            if guild not in self.cache:
                self.cache[guild] = {}
            for user_data in liste:
                self.cache[guild][user_data["userid"]] = [
                    round(time.time()) - 60, int(user_data["xp"])
                ]
        except Exception as exc: # pylint: disable=broad-exception-caught
            await self.bot.get_cog("Errors").on_error(exc)

    async def bdd_get_rank(self, user_id: int, guild: discord.Guild = None):
        """Get the rank of a user
        Set guild=None for global leaderboard"""
        try:
            query = "SELECT `userid`,`xp` FROM xp WHERE guild = ? ORDER BY xp desc;"
            liste = self.bot.db_query(query, (guild.id if guild else None,))
            userdata = {}
            i = 0
            users = []
            if guild is not None:
                users = [member.id for member in guild.members]
            for user_data in liste:
                if guild is None or (guild is not None and user_data["userid"] in users):
                    i += 1
                if user_data["userid"] == user_id:
                    userdata = dict(user_data)
                    userdata["rank"] = i
                    break
            return userdata
        except Exception as exc: # pylint: disable=broad-exception-caught
            await self.bot.get_cog("Errors").on_error(exc)

    async def bdd_get_top(self, top: int = None, guild: discord.Guild = None):
        """"""
        try:
            query = "SELECT userid, xp FROM xp WHERE guild = ? ORDER BY `xp` DESC"
            if top is not None:
                query += f" LIMIT {top}"
            return self.bot.db_query(query, (guild.id if guild else None,))
        except Exception as exc: # pylint: disable=broad-exception-caught
            await self.bot.get_cog("Errors").on_error(exc)

    async def get_xp(self, user: discord.User, guild_id: int = None):
        """Get the xp amount of a user in a guild"""
        xp = await self.bdd_get_xp(user.id, guild_id) # pylint: disable=invalid-name
        if xp is None or (isinstance(xp, list) and len(xp) == 0):
            return
        return xp[0]["xp"]

    async def send_embed(
        self,
        ctx: MyContext,
        user: discord.User,
        xp, # pylint: disable=invalid-name
        rank,
        ranks_nb,
        levels_info,
    ):
        """Send the !rank command as an embed"""
        level_field_name = await self.bot._(ctx.channel, "xp.card.level")
        rank_field_name = await self.bot._(ctx.channel, "xp.card.rank")

        if levels_info is None:
            levels_info = await self.calc_level(xp)
        emb = discord.Embed(color=self.embed_color)
        emb.set_author(name=str(user), icon_url=user.display_avatar)
        emb.add_field(name="XP", value=f"{xp}/{levels_info[1]}")
        emb.add_field(name=level_field_name, value=levels_info[0])
        emb.add_field(name=rank_field_name, value=f"{rank}/{ranks_nb}")

        await ctx.send(embed=emb)

    async def send_txt(
        self,
        ctx: MyContext,
        user: discord.User,
        xp, # pylint: disable=invalid-name
        rank,
        ranks_nb,
        levels_info,
    ):
        """Send the !rank command as a plain text"""
        level_field_name = await self.bot._(ctx.channel, "xp.card.level")
        rank_field_name = await self.bot._(ctx.channel, "xp.card.rank")
        if levels_info is None:
            levels_info = await self.calc_level(xp)
        msg = f"""__**{user.name}**__
**XP** {xp}/{levels_info[1]}
**{level_field_name}** {levels_info[0]}
**{rank_field_name}** {rank}/{ranks_nb}"""
        await ctx.send(msg)

    @commands.command(name="rank")
    @commands.guild_only()
    @commands.bot_has_permissions(send_messages=True)
    @commands.cooldown(3, 10, commands.BucketType.user)
    async def rank(self, ctx: MyContext, *, user: discord.User = None):
        """Display a user XP.
        If you don't target any user, I'll display your own XP"""
        if user is None:
            user = ctx.author
        # if user is a bot
        if user.bot:
            return await ctx.send(await self.bot._(ctx.channel, "xp.bot-rank"))
        # if xp is disabled
        if not self.bot.server_configs[ctx.guild.id]["enable_xp"]:
            return await ctx.send(await self.bot._(ctx.guild.id, "xp.xp-disabled"))
        # if guild cache not done yet
        if ctx.guild.id not in self.cache:
            await self.bdd_load_cache(ctx.guild.id)
        xp = await self.get_xp(user, ctx.guild.id) # pylint: disable=invalid-name
        if xp is None:
            if ctx.author == user:
                return await ctx.send(await self.bot._(ctx.channel, "xp.no-xp-author"))
            return await ctx.send(await self.bot._(ctx.channel, "xp.no-xp-user"))
        levels_info = None
        ranks_nb = await self.bdd_get_nber(ctx.guild.id)
        try:
            rank = (await self.bdd_get_rank(user.id, ctx.guild))["rank"]
        except KeyError:
            rank = "?"
        if isinstance(rank, float):
            rank = int(rank)
        if ctx.can_send_embed:
            await self.send_embed(ctx, user, xp, rank, ranks_nb, levels_info)
        else:
            await self.send_txt(ctx, user, xp, rank, ranks_nb, levels_info)

    async def create_top_main(
        self, ranks: List[Dict[str, int]], nbr: int, page: int, ctx: MyContext
    ):
        """Create the !top page
        ranks: data pulled from the database
        nbr: number of users to show
        page: page number to show"""
        txt = []
        i = (page - 1) * 20
        for user_data in ranks[:nbr]:
            i += 1
            user = self.bot.get_user(user_data["userid"])
            if user is None:
                try:
                    user = await self.bot.fetch_user(user_data["userid"])
                except discord.NotFound:
                    user = await self.bot._(ctx.channel, "xp.del-user")
            if isinstance(user, discord.User):
                user_name = discord.utils.escape_markdown(user.name)
                if len(user_name) > 18:
                    user_name = user_name[:15] + "..."
            else:
                user_name = user
            level_data = await self.calc_level(user_data["xp"])
            txt.append(
                "{} • **{} |** `lvl {}` **|** `xp {}`".format( # pylint: disable=consider-using-f-string
                    i,
                    "__" + user_name + "__" if user == ctx.author else user_name,
                    level_data[0],
                    user_data["xp"],
                )
            )
        return txt, i

    @commands.command(name="top")
    @commands.guild_only()
    @commands.bot_has_permissions(send_messages=True)
    @commands.cooldown(5, 60, commands.BucketType.user)
    async def top(self, ctx: MyContext, page: typing.Optional[int] = 1):
        """Get the list of the highest levels
        Each page has 20 users"""
        # if xp is disabled
        if not self.bot.server_configs[ctx.guild.id]["enable_xp"]:
            return await ctx.send(await self.bot._(ctx.guild.id, "xp.xp-disabled"))
        # if guild cache not done yet
        if ctx.guild.id not in self.cache:
            await self.bdd_load_cache(ctx.guild.id)
        # get user ranks from db
        ranks = [
            {"userid": key, "xp": value[1]}
            for key, value in self.cache[ctx.guild.id].items()
        ]
        ranks = sorted(ranks, key=lambda x: x["xp"], reverse=True)
        # cal max page and check the argument
        max_page = ceil(len(ranks) / 20)
        if page < 1:
            return await ctx.send(await self.bot._(ctx.channel, "xp.top.low-page"))
        elif page > max_page:
            return await ctx.send(await self.bot._(ctx.channel, "xp.top.high-page"))
        # limit to the amount of users we neeed
        ranks = ranks[(page - 1) * 20 :]
        # create leaderboard field while making sure the text fits in it (1024
        # char)
        nbr = 20
        txt, i = await self.create_top_main(ranks, nbr, page, ctx)
        while len("\n".join(txt)) > 1000 and nbr > 0:
            nbr -= 1
            txt, i = await self.create_top_main(ranks, nbr, page, ctx)
            # wait a bit to not overload the bot
            await asyncio.sleep(0.2)
        f_name = await self.bot._(
            ctx.channel,
            "xp.top.name",
            min=(page - 1) * 20 + 1,
            max=i,
            page=page,
            pmax=max_page,
        )
        # author
        rank = await self.bdd_get_rank(ctx.author.id, ctx.guild)
        if len(rank) == 0:
            # user has no xp yet
            your_rank = {
                "name": "__" + await self.bot._(ctx.channel, "xp.top.your") + "__",
                "value": await self.bot._(ctx.guild, "xp.no-xp-author"),
            }
        else:
            lvl = await self.calc_level(rank["xp"])
            lvl = lvl[0]
            your_rank = {
                "name": "__" + await self.bot._(ctx.channel, "xp.top.your") + "__",
                "value": "**#{} |** `lvl {}` **|** `xp {}`".format( # pylint: disable=consider-using-f-string
                    rank["rank"] if "rank" in rank.keys() else "?", lvl, rank["xp"]
                ),
            }
        # title
        top_title = await self.bot._(ctx.channel, "xp.top.title")
        # final embed
        if ctx.can_send_embed:
            emb = discord.Embed(title=top_title, color=self.embed_color)
            emb.set_author(
                name=self.bot.user.name, icon_url=self.bot.user.display_avatar
            )
            emb.add_field(name=f_name, value="\n".join(txt), inline=False)
            emb.add_field(**your_rank)
            await ctx.send(embed=emb)
        else:
            await ctx.send(f_name + "\n\n" + "\n".join(txt))

    async def rr_add_role(self, guild_id: int, role_id: int, level: int):
        """Add a role reward in the database"""
        query = (
            "INSERT INTO `roles_levels` (`guild`,`role`,`level`) VALUES (:g, :r, :l);"
        )
        self.bot.db_query(query, {"g": guild_id, "r": role_id, "l": level})
        return True

    async def rr_list_role(self, guild: int, level: int = -1) -> List[dict]:
        """List role rewards in the database"""
        if level < 0:
            query = "SELECT rowid AS id, * FROM `roles_levels` WHERE guild = :g ORDER BY level;"
        else:
            query = "SELECT rowid AS id, * FROM `roles_levels` WHERE guild=:g"\
                "AND level=:l ORDER BY level;"
        liste = self.bot.db_query(query, {"g": guild, "l": level})
        return liste

    async def rr_remove_role(self, role_id: int):
        """Remove a role reward from the database"""
        query = "DELETE FROM `roles_levels` WHERE rowid = ?;"
        self.bot.db_query(query, (role_id,))
        return True

    @commands.group(name="roles_levels")
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def rr_main(self, ctx: MyContext):
        """Manage your roles rewards like a boss"""
        if ctx.subcommand_passed is None:
            await ctx.send_help("roles_levels")

    @rr_main.command(name="add")
    @commands.has_permissions(manage_guild=True)
    async def rr_add(self, ctx: MyContext, level: int, *, role: discord.Role):
        """Add a role reward
        This role will be given to every member who reaches the specified level"""
        try:
            if role.name == "@everyone":
                raise commands.BadArgument(f'Role "{role.name}" not found')
            role_rewards = await self.rr_list_role(ctx.guild.id)
            if len([x for x in role_rewards if x["level"] == level]) > 0:
                return await ctx.send(
                    await self.bot._(ctx.guild.id, "xp.rr.already-exist")
                )
            await self.rr_add_role(ctx.guild.id, role.id, level)
        except Exception as exc: # pylint: disable=broad-exception-caught
            await self.bot.get_cog("Errors").on_command_error(ctx, exc)
        else:
            await ctx.send(
                await self.bot._(
                    ctx.guild.id, "xp.rr.added", name=role.name, level=level
                )
            )

    @rr_main.command(name="list")
    async def rr_list(self, ctx: MyContext):
        """List every roles rewards of your server"""
        if not ctx.can_send_embed:
            return await ctx.send(await self.bot._(ctx.guild.id, "xp.cant-send-embed"))
        try:
            role_rewards = await self.rr_list_role(ctx.guild.id)
        except Exception as exc: # pylint: disable=broad-exception-caught
            await self.bot.get_cog("Errors").on_command_error(ctx, exc)
        else:
            level_field_name = await self.bot._(ctx.guild.id, "xp.card.level")
            desc = "\n".join(
                [f"• <@&{x['role']}> : {level_field_name} {x['level']}" for x in role_rewards]
            )
            if len(desc) == 0:
                desc = await self.bot._(ctx.guild.id, "xp.rr.no-rr-2")
            title = await self.bot._(ctx.guild.id, "xp.rr.list-title", nbr=len(role_rewards))
            emb = discord.Embed(title=title, description=desc)
            await ctx.send(embed=emb)

    @rr_main.command(name="remove")
    @commands.has_permissions(manage_guild=True)
    async def rr_remove(self, ctx: MyContext, level: int):
        """Remove a role reward
        When a member reaches this level, no role will be given anymore"""
        try:
            roles = await self.rr_list_role(ctx.guild.id, level)
            if len(roles) == 0:
                return await ctx.send(await self.bot._(ctx.guild.id, "xp.rr.no-rr"))
            await self.rr_remove_role(roles[0]["id"])
        except Exception as exc: # pylint: disable=broad-exception-caught
            await self.bot.get_cog("Errors").on_command_error(ctx, exc)
        else:
            await ctx.send(await self.bot._(ctx.guild.id, "xp.rr.removed", level=level))

    @rr_main.command(name="reload")
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(1, 300, commands.BucketType.guild)
    async def rr_reload(self, ctx: MyContext):
        """Refresh roles rewards for the whole server"""
        try:
            if not ctx.guild.me.guild_permissions.manage_roles:
                return await ctx.send(
                    await self.bot._(ctx.guild.id, "xp.cant-manage-roles")
                )
            counter = 0
            rr_list = await self.rr_list_role(ctx.guild.id)
            if len(rr_list) == 0:
                await ctx.send(await self.bot._(ctx.guild, "xp.rr.no-rr-2"))
                return
            xps = [
                {"user": x["userid"], "xp": x["xp"]}
                for x in await self.bdd_get_top(top=None, guild=ctx.guild)
            ]
            for member in xps:
                discord_member = ctx.guild.get_member(member["user"])
                if discord_member is not None:
                    level = (await self.calc_level(member["xp"]))[0]
                    counter += await self.give_rr(discord_member, level, rr_list, remove=True)
            await ctx.send(
                await self.bot._(
                    ctx.guild.id,
                    "xp.rr.reload",
                    count=counter,
                    members=ctx.guild.member_count,
                )
            )
        except Exception as exc: # pylint: disable=broad-exception-caught
            await self.bot.get_cog("Errors").on_command_error(ctx, exc)

    async def cog_unload(self):
        self.xp_reduction.cancel() # pylint: disable=no-member


async def setup(bot:Gunibot=None):
    if bot is not None:
        await bot.add_cog(XP(bot), icon="🪙")
