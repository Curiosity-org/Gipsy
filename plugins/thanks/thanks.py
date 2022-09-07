import args
from utils import Gunibot, MyContext
from discord.ext import commands
import discord
from bot import checks
import asyncio
import datetime
from typing import Dict, List, Optional, Tuple

import sys

sys.path.append("./bot")


class Thanks(commands.Cog):
    def __init__(self, bot: Gunibot):
        self.bot = bot
        self.tasks = list()
        if bot.is_ready():
            self.schedule_tasks()
        self.config_options = ["_thanks_cmd", "thanks_duration", "thanks_allowed_roles"]

        bot.get_command("config").add_command(self.config_thanks_allowed_roles)
        bot.get_command("config").add_command(self.config_thanks_duration)
        bot.get_command("config").add_command(self.thanks_main)

    @commands.command(name="thanks_allowed_roles")
    async def config_thanks_allowed_roles(
        self, ctx: MyContext, roles: commands.Greedy[discord.Role]
    ):
        if len(roles) == 0:
            roles = None
        else:
            roles = [role.id for role in roles]
        await ctx.send(
            await self.bot.sconfig.edit_config(
                ctx.guild.id, "thanks_allowed_roles", roles
            )
        )

    @commands.command(name="thanks_duration")
    async def config_thanks_duration(
        self, ctx: MyContext, duration: commands.Greedy[args.tempdelta]
    ):
        duration = sum(duration)
        if duration == 0:
            if ctx.message.content.split(" ")[-1] != "thanks_duration":
                await ctx.send(
                    await self.bot._(ctx.guild.id, "sconfig.invalid-duration")
                )
                return
            duration = None
        x = await self.bot.sconfig.edit_config(
            ctx.guild.id, "thanks_duration", duration
        )
        await ctx.send(x)

    @commands.group(name="thanks", aliases=["thx"], enabled=False)
    async def thanks_main(self, ctx: MyContext):
        """Edit your thanks-levels settings"""
        if ctx.subcommand_passed is None:
            await ctx.send_help("config thanks")

    @thanks_main.command(name="list")
    async def thanks_list(self, ctx: MyContext):
        """List your current thanks levels"""
        await self.bot.get_cog("Thanks").thankslevels_list(ctx)

    '''
    @thanks_main.command(name="add")
    async def thanks_add(self, ctx: MyContext, amount: int, role: discord.Role):
        """Add a role to give when someone reaches a certain amount of thanks"""
        #await self.bot.get_cog("Thanks").thankslevel_add(ctx, amount, role)
        pass

    @thanks_main.command(name="reset")
    async def thanks_reset(self, ctx: MyContext, amount: int = None):
        """Remove every role given for a certain amount of thanks
        If no amount is specified, it will reset the whole configuration"""
        if amount is None:
            await self.bot.get_cog("Thanks").thankslevel_reset(ctx)
        else:
            await self.bot.get_cog("Thanks").thankslevel_remove(ctx, amount)
    '''

    @commands.Cog.listener()
    async def on_ready(self):
        self.schedule_tasks()

    def schedule_tasks(self):
        res = self.bot.db_query(
            "SELECT guild, user, timestamp FROM thanks", (), astuple=True
        )
        now = datetime.datetime.now()
        for task in res:
            task = list(task)
            task[2] = datetime.datetime.strptime(task[2], "%Y-%m-%d %H:%M:%S")
            delta = (task[2] - now).total_seconds()
            delta += self.bot.server_configs[task[0]]["thanks_duration"]
            if delta > 0:
                T = self.bot.get_cog("TimeCog").add_task(
                    delta, self.reload_roles, *task
                )
                self.tasks.append(T)

    def cog_unload(self):
        for task in self.tasks:
            task.cancel()
        if self.bot.get_cog("Sconfig"):
            self.bot.get_command("config thanks").enabled = False

    async def _create_config(
        self, ctx: MyContext, mentions: bool = False
    ) -> List[Tuple[str, str]]:
        """Create a list of (key,value) for the /config command"""
        roles: dict = self.db_get_roles(ctx.guild.id)
        result = list()
        for k, v in sorted(roles.items()):
            subroles = [ctx.guild.get_role(r) for r in v]
            if mentions:
                subroles = [r.mention for r in subroles if r is not None]
            else:
                subroles = [r.name for r in subroles if r is not None]
            result.append((f"{k} remerciements", " ".join(subroles)))
        return result

    def db_get_user(self, guildID: int, userID: int) -> Optional[dict]:
        query = "SELECT * FROM thanks WHERE guild=? AND user=?"
        res = self.bot.db_query(query, (guildID, userID))
        return res if len(res) > 0 else None

    def db_get_last(
        self, guildID: int, userID: int, authorID: int = None
    ) -> Optional[dict]:
        if authorID is None:
            res = self.db_get_user(guildID, userID)
        else:
            query = "SELECT * FROM thanks WHERE guild=? AND user=? AND author=?"
            res = self.bot.db_query(query, (guildID, userID, authorID))
        return res[-1] if len(res) > 0 else None

    def db_get_amount(self, guildID: int, userID: int, duration: int = None) -> int:
        query = "SELECT COUNT(*) as count FROM thanks WHERE guild=? AND user=?"
        if duration:
            query += f" AND timestamp >= datetime('now','-{duration} seconds')"
        res = self.bot.db_query(query, (guildID, userID), fetchone=True)
        return res["count"]

    def db_add_thanks(self, guildID: int, userID: int, authorID: int):
        query = "INSERT INTO thanks (guild,user,author) VALUES (?, ?, ?)"
        self.bot.db_query(query, (guildID, userID, authorID))

    def db_cleanup_thanks(self, guildID: int, duration: int):
        if not isinstance(duration, (int, float)):
            return
        query = f"DELETE FROM thanks WHERE guild=? AND timestamp < datetime('now','-{duration} seconds')"
        self.bot.db_query(query, (guildID,))

    def db_set_role(self, guildID: int, roleID: int, level: int):
        query = "INSERT INTO thanks_levels (guild, role, level) VALUES (?, ?, ?)"
        self.bot.db_query(query, (guildID, roleID, level))

    def db_get_roles(self, guildID: int, level: int = None):
        if level:
            query = "SELECT role, level FROM thanks_levels WHERE guild=? AND level=?"
            liste = self.bot.db_query(query, (guildID, level))
        else:
            query = "SELECT role, level FROM thanks_levels WHERE guild=?"
            liste = self.bot.db_query(query, (guildID,))
        res = dict()
        for lvl in liste:
            res[lvl["level"]] = res.get(lvl["level"], list()) + [lvl["role"]]
        return res

    def db_remove_level(self, guildID: int, level: int):
        query = "DELETE FROM thanks_levels WHERE guild=? AND level=?"
        self.bot.db_query(query, (guildID, level))

    def db_reset_level(self, guildID: int):
        query = "DELETE FROM thanks_levels WHERE guild=?"
        self.bot.db_query(query, (guildID,))

    async def has_allowed_roles(
        self, guild: discord.Guild, member: discord.Member
    ) -> bool:
        config = self.bot.server_configs[guild.id]["thanks_allowed_roles"]
        if config is None:
            return False
        roles = [guild.get_role(x) for x in config]
        for r in member.roles:
            if r in roles:
                return True
        return False

    async def give_remove_roles(
        self,
        member: discord.Member,
        roles_conf: Dict[int, List[discord.Role]] = None,
        duration: int = None,
    ) -> bool:
        """Give or remove thanks roles if needed
        Return True if roles were given/removed, else False"""
        if not member.guild.me.guild_permissions.manage_roles:
            self.bot.log.info(
                f'Module - Thanks: Missing "manage_roles" permission on guild "{member.guild.name}"'
            )
            return False
        g: discord.Guild = member.guild
        pos: int = g.me.top_role.position
        if roles_conf is None:
            roles_conf = self.db_get_roles(g.id)
        for k, v in roles_conf.items():
            if all(isinstance(x, discord.Role) for x in v):  # roles already initialized
                continue
            r = [g.get_role(x) for x in v]
            roles_conf[k] = list(
                filter(lambda x: (x is not None) and (x.position < pos), r)
            )
            if len(roles_conf[k]) == 0:
                del roles_conf[k]
        if duration is None:
            duration = self.bot.server_configs[member.guild.id]["thanks_duration"]
        amount = self.db_get_amount(member.guild.id, member.id, duration)
        gave_anything = False
        for lvl, roles in roles_conf.items():
            if amount >= lvl:  # should give roles
                roles = list(filter(lambda x: x not in member.roles, roles))
                if len(roles) > 0:
                    await member.add_roles(*roles, reason="Thanks system")
                    self.bot.log.debug(
                        "[Thanks] Rôles {0} ajoutés à {1} ({1.id})".format(
                            roles, member
                        )
                    )
                    gave_anything = True
            else:  # should remove roles
                roles = list(filter(lambda x: x in member.roles, roles))
                if len(roles) > 0:
                    await member.remove_roles(*roles, reason="Thanks system")
                    self.bot.log.debug(
                        "[Thanks] Rôles {0} enlevés à {1} ({1.id})".format(
                            roles, member
                        )
                    )
                    gave_anything = True
        return gave_anything

    async def reload_roles(self, guildID: int, memberID: int, date: datetime.datetime):
        """Remove roles if needed"""
        delta = self.bot.server_configs[guildID]["thanks_duration"]
        if (datetime.datetime.now() - date).total_seconds() < delta:
            return
        guild: discord.Guild = self.bot.get_guild(guildID)
        if guild is None:
            return
        member = guild.get_member(memberID)
        if member is None:
            return
        await self.give_remove_roles(member, duration=delta)

    @commands.command(name="thanks", aliases=["thx"])
    @commands.guild_only()
    async def thanks(self, ctx: MyContext, *, user: discord.User):
        """Thanks a user for their work.
        The user may get a special role, according to your server configuration"""
        if not await self.has_allowed_roles(ctx.guild, ctx.author):
            await ctx.send(await self.bot._(ctx.guild.id, "thanks.add.not-allowed"))
            return
        if user.bot:
            await ctx.send(await self.bot._(ctx.guild.id, "thanks.add.no-bot"))
            return
        if user == ctx.author:
            await ctx.send(await self.bot._(ctx.guild.id, "thanks.add.no-self"))
            return
        last = self.db_get_last(ctx.guild.id, user.id, ctx.author.id)
        if last:
            last_date = datetime.datetime.strptime(
                last["timestamp"], "%Y-%m-%d %H:%M:%S"
            )
            delta = datetime.datetime.utcnow() - last_date
            if delta.days < 1:
                await ctx.send(await self.bot._(ctx.guild.id, "thanks.add.too-soon"))
                return
        self.db_add_thanks(ctx.guild.id, user.id, ctx.author.id)
        duration = self.bot.server_configs[ctx.guild.id]["thanks_duration"]
        amount = self.db_get_amount(ctx.guild.id, user.id, duration)
        await ctx.send(
            await self.bot._(ctx.guild.id, "thanks.add.done", user=user, amount=amount)
        )
        T = self.bot.get_cog("TimeCog").add_task(
            duration,
            self.reload_roles,
            ctx.guild.id,
            user.id,
            datetime.datetime.utcnow(),
        )
        self.tasks.append(T)
        member = ctx.guild.get_member(user.id)
        if member is not None:
            await self.give_remove_roles(member)

    @commands.command(name="thankslist", aliases=["thanks-list", "thxlist"])
    @commands.guild_only()
    async def thanks_list(self, ctx: MyContext, *, user: discord.User = None):
        """Get the list of thanks given to a user (or you by default)"""
        you = user is None
        if you:
            user = ctx.author
        liste = self.db_get_user(ctx.guild.id, user.id)
        if liste is None:
            if you:
                txt = await self.bot._(ctx.guild.id, "thanks.list.nothing-you")
            else:
                txt = await self.bot._(ctx.guild.id, "thanks.list.nothing-them")
            await ctx.send(txt)
            return
        for e, l in enumerate(liste):
            liste[e] = [
                self.bot.get_guild(l["guild"]),
                self.bot.get_user(l["user"]),
                self.bot.get_user(l["author"]),
                datetime.datetime.strptime(l["timestamp"], "%Y-%m-%d %H:%M:%S"),
            ]
        duration = self.bot.server_configs[ctx.guild.id]["thanks_duration"]
        current = [
            x
            for x in liste
            if (datetime.datetime.utcnow() - x[3]).total_seconds() < duration
        ]
        if ctx.can_send_embed:
            _title = await self.bot._(ctx.guild.id, "thanks.list.title", user=user)
            emb = discord.Embed(title=_title)
            _active = await self.bot._(
                ctx.guild.id, "thanks.list.active", count=len(current)
            )
            if len(current) > 0:
                t = [
                    "• {} ({})".format(x[2].mention, x[3].strftime("%d/%m/%y %HH%M"))
                    for x in current
                ]
                emb.add_field(name=_active, value="\n".join(t))
            else:
                emb.add_field(name=_active, value="0")
            old = len(liste) - len(current)
            if old > 0:
                _inactive = await self.bot._(
                    ctx.guild.id, "thanks.list.inactive", count=old
                )
                emb.add_field(name="\u200b", value=_inactive, inline=False)
            await ctx.send(embed=emb)
        else:
            txt = "```md\n"
            if len(current) > 0:
                t = [
                    "- {} ({})".format(str(x[2]), x[3].strftime("%d/%m/%y %HH%M"))
                    for x in current
                ]
                _active = await self.bot._(
                    ctx.guild.id, "thanks.list.active", count=len(current)
                )
                txt += "# " + _active + "\n{}\n".format(len(current), "\n".join(t))
            old = len(liste) - len(current)
            if old > 0:
                _inactive = await self.bot._(
                    ctx.guild.id, "thanks.list.inactive", count=len(current)
                )
                txt += "\n" + _inactive + "\n"
            await ctx.send(txt + "```")

    @commands.command(name="thanksreload", aliases=["thanks-reload"])
    @commands.guild_only()
    @commands.check(checks.is_admin)
    async def thanks_reload(
        self, ctx: commands.Context, *, user: discord.Member = None
    ):
        """Reload the thanks roles for a user, or everyone"""
        users = [user] if user is not None else ctx.guild.members
        users = list(filter(lambda x: not x.bot, users))
        if len(users) == 0:
            await ctx.send(await self.bot._(ctx.guild.id, "thanks.reload.no-member"))
            return
        rolesID = self.db_get_roles(ctx.guild.id)
        roles = list()
        for r in rolesID.values():
            roles += [ctx.guild.get_role(x) for x in r]
        roles = list(filter(None, roles))
        if not roles:
            await ctx.send(await self.bot._(ctx.guild.id, "thanks.reload.no-role"))
            return
        if not ctx.guild.me.guild_permissions.manage_roles:
            await ctx.send(await self.bot._(ctx.guild.id, "thanks.reload.no-perm"))
            return
        del roles
        delta = self.bot.server_configs[ctx.guild.id]["thanks_duration"]
        i = 0
        for m in users:
            if await self.give_remove_roles(m, rolesID, delta):
                i += 1
        if i == 0:
            txt = await self.bot._(
                ctx.guild.id, "thanks.reload.nothing-done", count=len(users)
            )
        elif i == 1:
            txt = await self.bot._(
                ctx.guild.id, "thanks.reload.one-done", count=len(users)
            )
        else:
            txt = await self.bot._(ctx.guild.id, "thanks.reload.many-done", i=i)
        await ctx.send(txt)

    async def thankslevels_list(self, ctx: MyContext):
        roles: dict = self.db_get_roles(ctx.guild.id)

        async def g(k: int) -> str:
            return await self.bot._(ctx.guild.id, "thanks.thanks", count=k)

        text = "\n".join(
            [await g(k) + " ".join([f"<@&{r}>" for r in v]) for k, v in roles.items()]
        )
        if text == "":
            text = await self.bot._(ctx.guild.id, "thanks.no-role")
        _title = await self.bot._(ctx.guild.id, "thanks.roles-list")
        if ctx.can_send_embed:
            embed = discord.Embed(title=_title, description=text)
            await ctx.send(embed=embed)
        else:
            await ctx.send("__" + _title + ":__\n" + text)

    async def thankslevel_add(
        self, ctx: commands.Context, level: int, role: discord.Role
    ):
        self.db_set_role(ctx.guild.id, role.id, level)
        roles = self.db_get_roles(ctx.guild.id, level)
        if len(roles) == 0:
            await ctx.send(await self.bot._(ctx.guild.id, "thanks.went-wrong"))
            return
        roles = roles[level]
        await ctx.send(
            await self.bot._(
                ctx.guild.id, "thanks.role-added", count=len(roles), lvl=level
            )
        )

    async def thankslevel_remove(self, ctx: commands.Context, level: int):
        self.db_remove_level(ctx.guild.id, level)
        roles = self.db_get_roles(ctx.guild.id, level)
        if len(roles) == 0:
            await ctx.send(
                await self.bot._(ctx.guild.id, "thanks.roles-deleted", lvl=level)
            )
        else:
            await ctx.send(await self.bot._(ctx.guild.id, "thanks.went-wrong"))

    async def thankslevel_reset(self, ctx: commands.Context):
        roles = self.db_get_roles(ctx.guild.id)
        if len(roles) == 0:
            await ctx.send(await self.bot._(ctx.guild.id, "thanks.reload.no-role"))
            return
        msg: discord.Message = await ctx.send(
            await self.bot._(ctx.guild.id, "thanks.confirm", count=len(roles))
        )
        await msg.add_reaction("✅")

        def check(reaction, user):
            return (
                user == ctx.author
                and str(reaction.emoji) == "✅"
                and reaction.message.id == msg.id
            )

        try:
            await self.bot.wait_for("reaction_add", timeout=30.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send(await self.bot._(ctx.guild.id, "thanks.too-long"))
            return
        self.db_reset_level(ctx.guild.id)
        roles = self.db_get_roles(ctx.guild.id)
        if len(roles) == 0:
            await ctx.send(await self.bot._(ctx.guild.id, "thanks.everything-deleted"))
        else:
            await ctx.send(await self.bot._(ctx.guild.id, "thanks.went-wrong"))


config = {}
async def setup(bot:Gunibot=None, plugin_config:dict=None):
    if bot is not None:
        await bot.add_cog(Thanks(bot))
    if plugin_config is not None:
        global config
        config.update(plugin_config)

