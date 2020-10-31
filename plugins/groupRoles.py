import discord
from discord.ext import commands
from marshal import loads, dumps
from typing import List, Union
import checks
import args


# /rolelink <grant/revoke> <role> when <get/loose> <one/all> <roles>


class ActionType(commands.Converter):
    types = ['grant', 'revoke']

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
        raise commands.errors.BadArgument("Type d'action invalide")


class TriggerType(commands.Converter):
    types = ['get-one', 'get-all', 'loose-one', 'loose-all']

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
        raise commands.errors.BadArgument("Type de déclencheur invalide")


class Action:
    def __init__(self, action: ActionType, target_role: int, trigger: TriggerType, trigger_roles: List[int], guild: int):
        self.action = action
        self.target_role = target_role
        self.trigger = trigger
        self.trigger_roles = trigger_roles
        self.b_trigger_roles = dumps(trigger_roles)
        self.guild = guild
        self.id = None


class GroupRoles(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.file = "groupRoles"

    def db_get_config(self, guildID: int) -> List[Action]:
        """Get every action of a specific guild"""
        c = self.bot.database.cursor()
        c.execute('SELECT rowid, * FROM group_roles WHERE guild=?', (guildID,))
        # comes as: (row, guild, action, target, trigger, trigger-roles)
        res = list()
        for row in list(c):
            #       Action            target_role  trigger           trigger_roles  guild
            temp = (ActionType(row[2]), row[3], TriggerType(
                row[4]), loads(row[5]), row[1])
            res.append(Action(*temp))
            res[-1].id = row[0]
        c.close()
        return res if len(res) > 0 else None

    def db_add_action(self, action: Action) -> int:
        """Add an action into a guild
        Return the inserted row ID"""
        c = self.bot.database.cursor()
        data = (action.guild, action.action.type, action.target_role,
                action.trigger.type, action.b_trigger_roles)
        c.execute(
            "INSERT INTO group_roles (guild, action, target, trigger, `trigger-roles`) VALUES (?, ?, ?, ?, ?)", data)
        self.bot.database.commit()
        rowid = c.lastrowid
        c.close()
        return rowid

    def db_delete_action(self, guildID: int, actionID: int) -> bool:
        """Delete an action from a guild, based on its row ID
        Return True if a row was deleted, False else"""
        c = self.bot.database.cursor()
        c.execute("DELETE FROM group_roles WHERE guild=? AND rowid=?",
                  (guildID, actionID))
        self.bot.database.commit()
        deleted = c.rowcount == 1
        c.close()
        return deleted

    async def filter_allowed_roles(self, guild: discord.Guild, roles: List[discord.Role]) -> List[discord.Role]:
        """Return every role that the bot is allowed to give/remove
        IE: role exists, role is under bot's highest role
        If bot doesn't have the "manage roles" perm, list will be empty"""
        if not guild.me.guild_permissions.manage_roles:
            return list()
        pos: int = guild.me.top_role.position
        roles = [guild.get_role(x) for x in roles]
        roles = list(filter(lambda x: (x is not None)
                            and (x.position < pos), roles))
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

    async def give_remove_roles(self, member: discord.Member, roles: List[discord.Role], action: ActionType):
        if not roles:  # list is empty or None
            return
        if action.type == 0:
            await member.add_roles(*roles, reason="Linked roles")
        else:
            await member.remove_roles(*roles, reason="Linked roles")

    async def check_got_roles(self, member: discord.Member, roles: List[discord.Role]):
        """Trigger actions based on granted roles"""
        actions = self.db_get_config(member.guild.id)
        for action in actions:
            if action.trigger.type == 0:  # if trigger is 'get-one'
                for r in roles:
                    if r.id in action.trigger_roles:  # if one given role triggers that action
                        alwd_roles = await self.filter_allowed_roles(member.guild, [action.target_role])
                        await self.give_remove_roles(member, alwd_roles, action.action)
                        break
            elif action.trigger.type == 1:  # if trigger is 'get-all'
                for r in roles:
                    if r.id in action.trigger_roles:  # if one given role triggers that action
                        member_roles = [x.id for x in member.roles]
                        if all([(x in member_roles) for x in action.trigger_roles]):
                            alwd_roles = await self.filter_allowed_roles(member.guild, [action.target_role])
                            await self.give_remove_roles(member, alwd_roles, action.action)
                            break

    async def check_lost_roles(self, member: discord.Member, roles: List[discord.Role]):
        """Trigger actions based on revoked roles"""
        actions = self.db_get_config(member.guild.id)
        for action in actions:
            if action.trigger.type == 2:  # if trigger is 'loose-one'
                for r in roles:
                    if r.id in action.trigger_roles:  # if one lost role triggers that action
                        alwd_roles = await self.filter_allowed_roles(member.guild, [action.target_role])
                        await self.give_remove_roles(member, alwd_roles, action.action)
                        break
            elif action.trigger.type == 3:  # if trigger is 'loose-all'
                for r in roles:
                    if r.id in action.trigger_roles:  # if one lost role triggers that action
                        member_roles = [x.id for x in member.roles]
                        if all([(x not in member_roles) for x in action.trigger_roles]):
                            alwd_roles = await self.filter_allowed_roles(member.guild, [action.target_role])
                            await self.give_remove_roles(member, alwd_roles, action.action)
                            break

    @commands.group(name="rolelink")
    @commands.guild_only()
    async def rolelink_main(self, ctx: commands.Context):
        """Manage your roles-links"""
        if ctx.subcommand_passed is None:
            await ctx.send_help('rolelink')

    @rolelink_main.command(name="create")
    async def rolelink_create(self, ctx: commands.Context, action: ActionType, target_role: discord.Role, when: args.constant('when'), trigger: TriggerType, trigger_roles: commands.Greedy[discord.Role]):
        """Create a new roles-link"""
        if not trigger_roles:
            await ctx.send("Il vous faut au moins 1 rôle déclencheur !")
            return
        action = Action(action, target_role.id, trigger, [
                        x.id for x in trigger_roles], ctx.guild.id)
        actionID = self.db_add_action(action)
        await ctx.send(f"Une nouvelle action a bien été ajoutée, avec l'ID {actionID} !")

    @rolelink_main.command(name="list")
    async def rolelink_list(self, ctx: commands.Context):
        """List your roles-links"""
        actions = self.db_get_config(ctx.guild.id)
        if not actions:
            await ctx.send("Vous n'avez aucune action de configurée pour le moment.\nUtilisez la commande `rolelink create` pour en ajouter")
            return
        txt = "**Liste de vos rôles-liaisons :**\n"
        for action in actions:
            triggers = ' '.join([f'<@&{r}>' for r in action.trigger_roles])
            target = f'<@&{action.target_role}>'
            txt += f"{action.id}. {action.action.name} {target} when {action.trigger.name.replace('-', ' ')} of {triggers}\n"
        await ctx.send(txt)

    @rolelink_main.command(name="delete")
    async def rolelink_delete(self, ctx: commands.Context, id: int):
        """Delete one of your roles-links"""
        deleted = self.db_delete_action(ctx.guild.id, id)
        if deleted:
            await ctx.send("Votre rôle-liaison a bien été supprimée !")
        else:
            await ctx.send("Impossible de trouver une rôle-liaison avec cet identifiant.\nVous pouvez obtenir l'identifiant d'une liaison avec la commande `rolelink list`")


def setup(bot):
    bot.add_cog(GroupRoles(bot))
