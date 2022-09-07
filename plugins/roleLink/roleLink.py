from utils import Gunibot
from discord.ext import commands
import discord
from bot import checks
import args
import asyncio
from marshal import dumps, loads
from typing import List, Union

import sys

sys.path.append("./bot")
sys.path.append("./bot")

# /rolelink <grant/revoke> <role> when <get/loose> <one/all> <roles>


class ActionType(commands.Converter):
    types = ["grant", "revoke"]

    def __init__(self, action: Union[str, int] = None):
        if isinstance(action, str):
            self.type = self.types.index(action)
        elif isinstance(action, int):
            self.type = action
        else:
            return
        self.name = self.types[self.type]

    async def convert(self, ctx: commands.Context, argument: str):
        if argument in self.types:
            return ActionType(argument)
        raise commands.errors.BadArgument("Unknown dependency action type")


class TriggerType(commands.Converter):
    types = ["get-one", "get-all", "loose-one", "loose-all"]

    def __init__(self, trigger: Union[str, int] = None):
        if isinstance(trigger, str):
            self.type = self.types.index(trigger)
        elif isinstance(trigger, int):
            self.type = trigger
        else:
            return
        self.name = self.types[self.type]

    async def convert(self, ctx: commands.Context, argument: str):
        if argument in self.types:
            return TriggerType(argument)
        raise commands.errors.BadArgument("Unknown dependency trigger type")


class Dependency:
    def __init__(
        self,
        action: ActionType,
        target_role: int,
        trigger: TriggerType,
        trigger_roles: List[int],
        guild: int,
    ):
        self.action = action
        self.target_role = target_role
        self.trigger = trigger
        self.trigger_roles = trigger_roles
        self.b_trigger_roles = dumps(trigger_roles)
        self.guild = guild
        self.id = None

    def to_str(self, useID: bool = True) -> str:
        triggers = " ".join([f"<@&{r}>" for r in self.trigger_roles])
        target = f"<@&{self.target_role}>"
        ID = f"{self.id}. " if useID else ""
        return f"{ID}{self.action.name} {target} when {self.trigger.name.replace('-', ' ')} of {triggers}"


class ConflictingCyclicDependencyError(Exception):
    """Used when a loop is found when analyzing a role dependencies system"""

    pass


class GroupRoles(commands.Cog):
    def __init__(self, bot: Gunibot):
        self.bot = bot
        self.file = ""

    def db_get_config(self, guildID: int) -> List[Dependency]:
        """Get every dependencies of a specific guild"""
        query = "SELECT rowid, * FROM group_roles WHERE guild=?"
        # comes as: (rowid, guild, action, target, trigger, trigger-roles)
        res = list()
        liste = self.bot.db_query(query, (guildID,))
        for row in liste:
            temp = (
                ActionType(row["action"]),
                row["target"],
                TriggerType(row["trigger"]),
                loads(row["trigger-roles"]),
                row["guild"],
            )
            res.append(Dependency(*temp))
            res[-1].id = row["rowid"]
        return res if len(res) > 0 else None

    def db_add_action(self, action: Dependency) -> int:
        """Add an action into a guild
        Return the inserted row ID"""
        data = (
            action.guild,
            action.action.type,
            action.target_role,
            action.trigger.type,
            action.b_trigger_roles,
        )
        query = "INSERT INTO group_roles (guild, action, target, trigger, `trigger-roles`) VALUES (?, ?, ?, ?, ?)"
        lastrowid = self.bot.db_query(query, data)
        return lastrowid

    def db_delete_action(self, guildID: int, actionID: int) -> bool:
        """Delete an action from a guild, based on its row ID
        Return True if a row was deleted, False else"""
        query = "DELETE FROM group_roles WHERE guild=? AND rowid=?"
        rowcount = self.bot.db_query(query, (guildID, actionID))
        return rowcount == 1

    async def filter_allowed_roles(
        self, guild: discord.Guild, roles: List[discord.Role]
    ) -> List[discord.Role]:
        """Return every role that the bot is allowed to give/remove
        IE: role exists, role is under bot's highest role
        If bot doesn't have the "manage roles" perm, list will be empty"""
        if not guild.me.guild_permissions.manage_roles:
            return list()
        pos: int = guild.me.top_role.position
        roles = [guild.get_role(x) for x in roles]
        roles = list(filter(lambda x: (x is not None) and (x.position < pos), roles))
        return roles

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """Check if a member got/lost a role"""
        if before.roles == after.roles:
            # we don't care about other changes
            return
        got = [r for r in after.roles if r not in before.roles]
        lost = [r for r in before.roles if r not in after.roles]
        if got:
            await self.check_got_roles(after, got)
        if lost:
            await self.check_lost_roles(after, lost)

    async def give_remove_roles(
        self, member: discord.Member, roles: List[discord.Role], action: ActionType
    ):
        if not roles:  # list is empty or None
            return
        names = [x.name for x in roles]
        if action.type == 0:
            self.bot.log.debug(f"Giving {names} to {member}")
            await member.add_roles(*roles, reason="Linked roles")
        else:
            self.bot.log.debug(f"Removing {names} to {member}")
            await member.remove_roles(*roles, reason="Linked roles")

    async def check_got_roles(self, member: discord.Member, roles: List[discord.Role]):
        """Trigger dependencies based on granted roles"""
        actions = self.db_get_config(member.guild.id)
        if actions is None:
            return
        for action in actions:
            if action.trigger.type == 0:  # if trigger is 'get-one'
                for r in roles:
                    if (
                        r.id in action.trigger_roles
                    ):  # if one given role triggers that action
                        alwd_roles = await self.filter_allowed_roles(
                            member.guild, [action.target_role]
                        )
                        await self.give_remove_roles(member, alwd_roles, action.action)
                        break
            elif action.trigger.type == 1:  # if trigger is 'get-all'
                for r in roles:
                    if (
                        r.id in action.trigger_roles
                    ):  # if one given role triggers that action
                        member_roles = [x.id for x in member.roles]
                        if all([(x in member_roles) for x in action.trigger_roles]):
                            alwd_roles = await self.filter_allowed_roles(
                                member.guild, [action.target_role]
                            )
                            await self.give_remove_roles(
                                member, alwd_roles, action.action
                            )
                            break

    async def check_lost_roles(self, member: discord.Member, roles: List[discord.Role]):
        """Trigger dependencies based on revoked roles"""
        actions = self.db_get_config(member.guild.id)
        if actions is None:
            return
        for action in actions:
            if action.trigger.type == 2:  # if trigger is 'loose-one'
                for r in roles:
                    if (
                        r.id in action.trigger_roles
                    ):  # if one lost role triggers that action
                        alwd_roles = await self.filter_allowed_roles(
                            member.guild, [action.target_role]
                        )
                        await self.give_remove_roles(member, alwd_roles, action.action)
                        break
            elif action.trigger.type == 3:  # if trigger is 'loose-all'
                for r in roles:
                    if (
                        r.id in action.trigger_roles
                    ):  # if one lost role triggers that action
                        member_roles = [x.id for x in member.roles]
                        if all([(x not in member_roles) for x in action.trigger_roles]):
                            alwd_roles = await self.filter_allowed_roles(
                                member.guild, [action.target_role]
                            )
                            await self.give_remove_roles(
                                member, alwd_roles, action.action
                            )
                            break

    async def get_triggers(
        self, action: Dependency, actions: List[Dependency]
    ) -> List[Dependency]:
        """Get every dependency which will directly trigger a selected action"""
        triggers = list()
        unwanted_action = 0 if action.trigger.type <= 1 else 1
        for a in actions:
            if a.id == action.id:
                continue
            # if a will trigger action
            if (
                a.action.type == unwanted_action
                and a.target_role in action.trigger_roles
            ):
                triggers.append(a)
        if action.trigger.type in (1, 3):  # get-all or loose-all
            roles = list(action.trigger_roles)
            for a in triggers:
                if a in roles:
                    roles.remove(a)
            if len(roles) > 0:
                return triggers
        return triggers

    async def compute_actions(
        self, action: Dependency, actions_done: list, all_actions: list
    ):
        """Check if a list of dependencies may contain a loop"""
        for target_action in await self.get_triggers(action, all_actions):
            already_noted = target_action in actions_done
            if already_noted:
                raise ConflictingCyclicDependencyError(target_action)
            actions_done.append(target_action)
            await self.compute_actions(target_action, actions_done, all_actions)

    @commands.group(name="rolelink")
    @commands.guild_only()
    async def rolelink_main(self, ctx: commands.Context):
        """Manage your roles-links"""
        if ctx.subcommand_passed is None:
            await ctx.send_help("rolelink")

    @rolelink_main.command(name="add")
    @commands.check(checks.is_server_manager)
    async def rolelink_create(
        self,
        ctx: commands.Context,
        action: ActionType,
        target_role: discord.Role,
        when: args.constant("when"),
        trigger: TriggerType,
        trigger_roles: commands.Greedy[discord.Role],
    ):
        """Create a new roles-link
        Actions can be either grant or revoke
        Trigger can be either get-one, get-all, loose-one or loose-all"""
        if not trigger_roles:
            await ctx.send("Il vous faut au moins 1 rôle déclencheur !")
            return
        action = Dependency(
            action, target_role.id, trigger, [x.id for x in trigger_roles], ctx.guild.id
        )
        try:
            all_actions = self.db_get_config(ctx.guild.id)
            if all_actions is not None:
                await self.compute_actions(action, list(), all_actions + [action])
        except ConflictingCyclicDependencyError as e:
            timeout = 20
            await ctx.send(
                await self.bot._(
                    ctx.guild.id,
                    "grouproles.infinite",
                    dep=e.args[0].to_str(False),
                    t=timeout,
                )
            )

            def check(m: discord.Message):
                return (
                    m.author == ctx.author
                    and m.channel == ctx.channel
                    and m.content.lower() in ("oui", "yes")
                )

            try:
                await self.bot.wait_for("message", check=check, timeout=timeout)
            except asyncio.TimeoutError:
                return
        actionID = self.db_add_action(action)
        await ctx.send(
            await self.bot._(ctx.guild.id, "grouproles.dep-added", id=actionID)
        )

    @rolelink_main.command(name="list")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def rolelink_list(self, ctx: commands.Context):
        """List your roles-links"""
        actions = self.db_get_config(ctx.guild.id)
        if not actions:
            await ctx.send(
                await self.bot._(ctx.guild.id, "grouproles.no-dep", p=ctx.prefix)
            )
            return
        txt = "**" + await self.bot._(ctx.guild.id, "grouproles.list") + "**\n"
        for action in actions:
            txt += action.to_str() + "\n"
        await ctx.send(txt)

    @rolelink_main.command(name="remove")
    @commands.check(checks.is_server_manager)
    async def rolelink_delete(self, ctx: commands.Context, id: int):
        """Delete one of your roles-links"""
        deleted = self.db_delete_action(ctx.guild.id, id)
        if deleted:
            await ctx.send(await self.bot._(ctx.guild.id, "grouproles.dep-deleted"))
        else:
            await ctx.send(
                await self.bot._(ctx.guild.id, "grouproles.dep-notfound", p=ctx.prefix)
            )


config = {}
async def setup(bot:Gunibot=None, plugin_config:dict=None):
    if bot is not None:
        await bot.add_cog(GroupRoles(bot))
    if plugin_config is not None:
        global config
        config.update(plugin_config)

