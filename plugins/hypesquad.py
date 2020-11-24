import discord
import time
from discord.ext import commands, tasks
from utils import Gunibot


class Hypesquad(commands.Cog):

    def __init__(self, bot: Gunibot):
        self.bot = bot
        self.file = "hypesquad"

    def cog_unload(self):
        self.roles_loop.cancel()

    @tasks.loop(hours=12)
    async def roles_loop(self):
        """Check every 12h the members roles"""
        t1 = time.time()
        self.bot.log.debug("[hypesquad] Started roles check")
        count = 0 # count of edited members
        for g in self.bot.guilds:
            try:
                roles = await self.get_roles(g)
                if any(roles.values): # if at least a role is set
                    for member in g.members:
                        count += await self.edit_roles(member, roles)
            except discord.errors.Forbidden:
                # missing a perm
                self.bot.log.warn(f'[hypesquad] Unable to give roles in guild {g.id} ({g.name})')
        delta = round(time.time()-t1, 2)
        self.bot.log.info(f"[hypesquad] Finished roles check in {delta}s")

    @roles_loop.before_loop
    async def before_roles_loop(self):
        """Waiting until the bot is ready"""
        await self.bot.wait_until_ready()

    async def edit_roles(self, member: discord.Member, roles: dict[str, discord.Role]) -> bool:
        """Add or remove roles to a member based on their hypesquad
        Returns True if a role has been given/removed"""
        roles_list = list(member.roles)
        unwanted = list()
        if member.public_flags.hypesquad_bravery and roles['bravery']:
            if roles['bravery'] not in member.roles:
                # add bravery
                roles_list.append(roles['bravery'])
            # remove brilliance balance none
            unwanted = (roles['brilliance'], roles['balance'], roles['none'])
        elif member.public_flags.hypesquad_brilliance and roles['brilliance']:
            if roles['brilliance'] not in member.roles:
                # add brilliance
                roles_list.append(roles['brilliance'])
            # remove bravery balance none
            unwanted = (roles['bravery'], roles['balance'], roles['none'])
        elif member.public_flags.hypesquad_balance and roles['balance']:
            # add balance
            if roles['balance'] not in member.roles:
                roles_list.append(roles['balance'])
            # remove brilliance bravery none
            unwanted = (roles['brilliance'], roles['bravery'], roles['none'])
        elif roles['none']:
            if roles['none'] not in member.roles:
                # add none
                roles_list.append(roles['none'])
            # remove brilliance balance bravery
            unwanted = (roles['brilliance'], roles['balance'], roles['bravery'])
        roles_list = [r for r in roles_list if r not in unwanted] # we remove unwanted roles
        roles_list = list(set(roles_list)) # we remove duplicates
        if roles_list != member.roles:
            # if changes were applied
            await member.edit(roles=roles_list, reason="Hypesquad roles")
            return True
        return False
    
    async def get_roles(self, guild: discord.Guild) -> dict[str, discord.Role]:
        """Get the hypesquads roles according to the guild config"""
        config = self.bot.server_configs[guild.id]
        result = dict()
        for k in ('hs_bravery_role', 'hs_brilliance_role', 'hs_balance_role', 'hs_none_role'):
            if config[k] is None:
                result[k] = None
            else:
                result[k] = guild.get_role(config[k])
        return result

def setup(bot):
    bot.add_cog(Hypesquad(bot))
