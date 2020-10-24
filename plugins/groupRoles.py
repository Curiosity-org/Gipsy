import discord
from discord.ext import commands
from marshal import loads, dumps
from typing import Union
import checks

# /rolelink grant/revoke [role] revoke/grant/have-all [roles]


class ActionType(commands.Converter):
    types = ['grant', 'revoke']

    def __init__(self, action: Union[str, int] = None):
        if isinstance(action, str):
            self.type = self.types.index(action)
        elif isinstance(action, int):
            self.type = action
        self.name = self.types[self.type]

    async def convert(self, ctx: commands.Context, argument: str):
        if argument in self.types:
            return ActionType(argument)
        raise commands.errors.BadArgument("Type d'action invalide")


class TriggerType(commands.Converter):
    types = ['grant', 'revoke', 'have-all']

    def __init__(self, trigger: Union[str, int] = None):
        if isinstance(trigger, str):
            self.type = self.types.index(trigger)
        elif isinstance(trigger, int):
            self.type = trigger
        self.name = self.types[self.type]

    async def convert(self, ctx: commands.Context, argument: str):
        if argument in self.types:
            return TriggerType(argument)
        raise commands.errors.BadArgument("Type de déclencheur invalide")


class Action:
    def __init__(self, action: ActionType, target_role: int, trigger: TriggerType, trigger_roles: [int], guild: int):
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

    def db_get_config(self, guildID: int) -> [Action]:
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

    @commands.group(name="rolelink")
    @commands.guild_only()
    async def rolelink_main(self, ctx: commands.Context):
        """Manage your roles-links"""
        if ctx.subcommand_passed is None:
            await ctx.send_help('rolelink')

    @rolelink_main.command(name="create")
    async def rolelink_create(self, ctx: commands.Context, action: ActionType, target_role: discord.Role, trigger: TriggerType, trigger_roles: commands.Greedy[discord.Role]):
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
            txt += f"{action.id}. {action.action.name} {target} when {action.trigger.name} {triggers}\n"
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
