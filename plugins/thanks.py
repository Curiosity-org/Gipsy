import discord
import datetime
import asyncio
from discord.ext import commands
import checks


class Thanks(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.file = "thanks"
        self.tasks = list()
        self.schedule_tasks()
        if bot.get_cog("Sconfig"):
            bot.get_command("config thanks").enabled = True

    def schedule_tasks(self):
        c = self.bot.database.cursor()
        c.execute('SELECT guild, user, timestamp FROM thanks')
        res = list(c)
        c.close()
        now = datetime.datetime.now()
        for task in res:
            task = list(task)
            task[2] = datetime.datetime.strptime(task[2], "%Y-%m-%d %H:%M:%S")
            delta = (task[2] - now).total_seconds()
            delta += self.bot.server_configs[task[0]]['thanks_duration']
            if delta > 0:
                T = self.bot.get_cog("TimeCog").add_task(
                    delta, self.reload_roles, *task)
                self.tasks.append(T)

    def cog_unload(self):
        for task in self.tasks:
            task.cancel()
        if self.bot.get_cog("Sconfig"):
            self.bot.get_command("config thanks").enabled = False

    def db_get_user(self, guildID: int, userID: int):
        c = self.bot.database.cursor()
        c.execute('SELECT * FROM thanks WHERE guild=? AND user=?',
                  (guildID, userID))
        res = list(c)
        c.close()
        return res if len(res) > 0 else None

    def db_get_last(self, guildID: int, userID: int, authorID: int = None):
        if authorID is None:
            res = self.db_get_user(guildID, userID)
        else:
            c = self.bot.database.cursor()
            c.execute('SELECT * FROM thanks WHERE guild=? AND user=? AND author=?',
                      (guildID, userID, authorID))
            res = list(c)
            c.close()
        return res[-1] if len(res) > 0 else None

    def db_get_amount(self, guildID: int, userID: int, duration: int = None) -> int:
        c = self.bot.database.cursor()
        q = f" AND timestamp >= datetime('now','-{duration} seconds')" if duration else ""
        c.execute(
            'SELECT COUNT(*) FROM thanks WHERE guild=? AND user=?'+q, (guildID, userID))
        res = c.fetchone()
        c.close()
        return res[0]

    def db_add_thanks(self, guildID: int, userID: int, authorID: int):
        c = self.bot.database.cursor()
        c.execute("INSERT INTO thanks (guild,user,author) VALUES (?, ?, ?)",
                  (guildID, userID, authorID))
        self.bot.database.commit()
        c.close()

    def db_cleanup_thanks(self, guildID: int, duration: int):
        if not isinstance(duration, (int, float)):
            return
        c = self.bot.database.cursor()
        c.execute(
            f"DELETE FROM thanks WHERE guild=? AND timestamp < datetime('now','-{duration} seconds')", (guildID,))
        self.bot.database.commit()
        c.close()

    def db_set_role(self, guildID: int, roleID: int, level: int):
        c = self.bot.database.cursor()
        c.execute("INSERT INTO thanks_levels (guild, role, level) VALUES (?, ?, ?)",
                  (guildID, roleID, level))
        self.bot.database.commit()
        c.close()

    def db_get_roles(self, guildID: int, level: int = None):
        c = self.bot.database.cursor()
        if level:
            c.execute(
                "SELECT * FROM thanks_levels WHERE guild=? AND level=?", (guildID, level))
        else:
            c.execute("SELECT * FROM thanks_levels WHERE guild=?", (guildID,))
        res = dict()
        for lvl in list(c):
            res[lvl[2]] = res.get(lvl[2], list()) + [lvl[1]]
        c.close()
        return res

    def db_remove_level(self, guildID: int, level: int):
        c = self.bot.database.cursor()
        c.execute(
            "DELETE FROM thanks_levels WHERE guild=? AND level=?", (guildID, level))
        self.bot.database.commit()
        c.close()

    def db_reset_level(self, guildID: int):
        c = self.bot.database.cursor()
        c.execute(
            "DELETE FROM thanks_levels WHERE guild=?", (guildID,))
        self.bot.database.commit()
        c.close()

    async def has_allowed_roles(self, guild: discord.Guild, member: discord.Member) -> bool:
        config = self.bot.server_configs[guild.id]['thanks_allowed_roles']
        if config is None:
            return False
        roles = [guild.get_role(x) for x in config]
        for r in member.roles:
            if r in roles:
                return True
        return False

    async def give_remove_roles(self, member: discord.Member, roles_conf: {int: [discord.Role]} = None, duration: int = None) -> bool:
        """Give or remove thanks roles if needed
        Return True if roles were given/removed, else False"""
        if not member.guild.me.guild_permissions.manage_roles:
            return False
        g = member.guild
        pos = g.me.top_role.position
        if roles_conf is None:
            roles_conf = self.db_get_roles(g.id)
        for k, v in roles_conf.items():
            if all(isinstance(x, discord.Role) for x in v):  # roles already initialized
                continue
            r = [g.get_role(x) for x in v]
            roles_conf[k] = list(
                filter(lambda x: (x is not None) and (x.position < pos), r))
            if len(roles_conf[k]) == 0:
                del roles_conf[k]
        if duration is None:
            duration = self.bot.server_configs[member.guild.id]['thanks_duration']
        amount = self.db_get_amount(member.guild.id, member.id, duration)
        gave_anything = False
        for lvl, roles in roles_conf.items():
            if amount >= lvl:  # should give roles
                roles = list(filter(lambda x: x not in member.roles, roles))
                if len(roles) > 0:
                    await member.add_roles(*roles, reason="Thanks system")
                    gave_anything = True
            else:  # should remove roles
                roles = list(filter(lambda x: x in member.roles, roles))
                if len(roles) > 0:
                    await member.remove_roles(*roles, reason="Thanks system")
                    gave_anything = True
        return gave_anything

    async def reload_roles(self, guildID: int, memberID: int, date: datetime.datetime):
        """Remove roles if needed"""
        delta = self.bot.server_configs[guildID]['thanks_duration']
        if (datetime.datetime.now() - date).total_seconds() < delta:
            return
        guild = self.bot.get_guild(guildID)
        if guild is None:
            return
        member = guild.get_member(memberID)
        if member is None:
            return
        await self.give_remove_roles(member, duration=delta)

    @commands.command(name="thanks", aliases=['thx'])
    @commands.guild_only()
    async def thanks(self, ctx: commands.Context, *, user: discord.User):
        """Thanks a user for their work.
        The user may get a special role, according to your server configuration"""
        if not await self.has_allowed_roles(ctx.guild, ctx.author):
            await ctx.send("Vous n'avez pas l'autorisation de faire cela")
            return
        if user.bot:
            await ctx.send("Les bots ne peuvent pas être remerciés !")
            return
        if user == ctx.author:
            await ctx.send("Vous ne pouvez pas vous remercier vous-même !")
            return
        last = self.db_get_last(ctx.guild.id, user.id, ctx.author.id)
        if last:
            last_date = datetime.datetime.strptime(
                last[3], "%Y-%m-%d %H:%M:%S")
            delta = datetime.datetime.utcnow() - last_date
            if delta.days < 1:
                await ctx.send("Vous avez déjà remercié cet utilisateur il y a moins d'un jour !")
                return
        self.db_add_thanks(ctx.guild.id, user.id, ctx.author.id)
        duration = self.bot.server_configs[ctx.guild.id]['thanks_duration']
        amount = self.db_get_amount(ctx.guild.id, user.id, duration)
        await ctx.send(f"{user} a bien reçu votre remerciement. Il a maintenant {amount} remerciements actifs !")
        T = self.bot.get_cog("TimeCog").add_task(
            duration, self.reload_roles, ctx.guild.id, user.id, datetime.datetime.utcnow())
        self.tasks.append(T)
        member = ctx.guild.get_member(user.id)
        if member is not None:
            await self.give_remove_roles(member)

    @commands.command(name="thankslist", aliases=['thanks-list', 'thxlist'])
    @commands.guild_only()
    async def thanks_list(self, ctx: commands.Context, *, user: discord.User = None):
        """Get the list of thanks given to a user (or you by default)"""
        you = user is None
        if you:
            user = ctx.author
        liste = self.db_get_user(ctx.guild.id, user.id)
        if liste is None:
            await ctx.send(("Vous n'avez" if you else "Cet utilisateur n'a") + " jamais reçu de remerciement")
            return
        for e, l in enumerate(liste):
            liste[e] = [self.bot.get_guild(l[0]), self.bot.get_user(l[1]), self.bot.get_user(
                l[2]), datetime.datetime.strptime(l[3], "%Y-%m-%d %H:%M:%S")]
        duration = self.bot.server_configs[ctx.guild.id]['thanks_duration']
        current = [x for x in liste if (datetime.datetime.utcnow() -
                                        x[3]).total_seconds() < duration]
        if ctx.channel.permissions_for(ctx.guild.me).embed_links:
            emb = discord.Embed(title=f"Remerciements à {user}")
            if len(current) > 0:
                t = ["• {} ({})".format(x[2].mention, x[3].strftime("%d/%m/%y %HH%M"))
                     for x in current]
                a = len(current)
                emb.add_field(
                    name=f"Remerciements actifs ({a})", value="\n".join(t))
            old = len(liste) - len(current)
            if old > 0:
                emb.add_field(name="\u200b", value=f"et {old} inactifs")
            await ctx.send(embed=emb)
        else:
            txt = "```md\n"
            if len(current) > 0:
                t = ["- {} ({})".format(str(x[2]), x[3].strftime("%d/%m/%y %HH%M"))
                     for x in current]
                txt += "# Remerciements actifs ({})\n{}\n".format(
                    len(current), "\n".join(t))
            old = len(liste) - len(current)
            if old > 0:
                txt += f"\net {old} inactifs\n"
            await ctx.send(txt+"```")

    @commands.command(name="thanksreload", aliases=['thanks-reload'])
    @commands.guild_only()
    @commands.check(checks.is_admin)
    async def thanks_reload(self, ctx: commands.Context, *, user: discord.Member = None):
        """Reload the thanks roles for a user, or everyone"""
        users = [user] if user is not None else ctx.guild.members
        users = list(filter(lambda x: not x.bot, users))
        if len(users) == 0:
            await ctx.send("Aucun membre sélectionné")
            return
        rolesID = self.db_get_roles(ctx.guild.id)
        roles = list()
        for r in rolesID.values():
            roles += [ctx.guild.get_role(x) for x in r]
        roles = list(filter(None, roles))
        if not roles:
            await ctx.send("Aucun rôle n'a été configuré")
            return
        if not ctx.guild.me.guild_permissions.manage_roles:
            await ctx.send("Il me manque la permission de Gérer les rôles")
            return
        del roles, r
        delta = self.bot.server_configs[ctx.guild.id]['thanks_duration']
        i = 0
        for m in users:
            if await self.give_remove_roles(m, rolesID, delta):
                i += 1
        if i == 0:
            if len(users) == 1:
                await ctx.send("Ce membre n'avait pas besoin de recharger ses rôles")
            else:
                await ctx.send("Aucun membre n'avait besoin de recharger ses rôles")
        elif i == 1:
            if len(users) == 1:
                await ctx.send("Les rôles de ce membre ont bien été recalculés !")
            else:
                await ctx.send("Les rôles d'un membre ont bien été recalculés !")
        else:
            await ctx.send(f"Les rôles de {i} membres ont bien été recalculés !")

    async def thankslevels_list(self, ctx: commands.Context):
        roles: dict = self.db_get_roles(ctx.guild.id)
        text = "\n".join(
            [f"{k} remerciements : "+" ".join([f"<@&{r}>" for r in v]) for k, v in roles.items()])
        if text == "":
            text = "Vous n'avez aucun rôle-remerciement configuré"
        if ctx.channel.permissions_for(ctx.guild.me).embed_links:
            embed = discord.Embed(
                title="Liste de vos rôles-remerciements", description=text)
            await ctx.send(embed=embed)
        else:
            await ctx.send("__Liste de vos rôles-remerciements :__\n" + text)

    async def thankslevel_add(self, ctx: commands.Context, level: int, role: discord.Role):
        self.db_set_role(ctx.guild.id, role.id, level)
        roles = self.db_get_roles(ctx.guild.id, level)
        if len(roles) == 0:
            await ctx.send("Oups, il semble que quelque chose se soit mal passé :confused:")
            return
        roles = roles[level]
        if len(roles) == 1:
            await ctx.send(f"Ce rôle a bien été configuré. Vous avez maintenant 1 rôle configuré pour le niveau {level}")
        else:
            await ctx.send(f"Ce rôle a bien été configuré. Vous avez maintenant {len(roles)} rôles configurés pour le niveau {level}")

    async def thankslevel_remove(self, ctx: commands.Context, level: int):
        self.db_remove_level(ctx.guild.id, level)
        roles = self.db_get_roles(ctx.guild.id, level)
        if len(roles) == 0:
            await ctx.send(f"Rôles du niveau {level} supprimés avec succès !")
        else:
            await ctx.send("Oups, il semble que quelque chose se soit mal passé :confused:")

    async def thankslevel_reset(self, ctx: commands.Context):
        roles = self.db_get_roles(ctx.guild.id)
        if len(roles) == 0:
            await ctx.send("Vous n'avez aucun rôle-remerciement configuré")
            return
        msg = await ctx.send("Êtes-vous sûr de vouloir effacer votre configuration ? Cela empêchera les rôles de {} seuils actuellement configurés d'être donnés".format(len(roles)))
        await msg.add_reaction("✅")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) == "✅" and reaction.message.id == msg.id
        try:
            await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send('Trop long ! Abandon de la procédure')
            return
        self.db_reset_level(ctx.guild.id)
        roles = self.db_get_roles(ctx.guild.id)
        if len(roles) == 0:
            await ctx.send(f"Tous les seuils ont bien été effacés !")
        else:
            await ctx.send("Oups, il semble que quelque chose se soit mal passé :confused:")


def setup(bot):
    bot.add_cog(Thanks(bot))
