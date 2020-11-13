import discord
from discord.ext import commands, tasks
import random
import traceback
import re
import time
import datetime
from marshal import loads, dumps
import checks, args


class Giveaways(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.file = "giveaways"
        self.internal_task.start()

    def db_add_giveaway(self, channel: discord.TextChannel, name: str, message: int, max_entries: int, ends_at: datetime.datetime = None) -> int:
        """
        Add a giveaway into the database
        channel: the channel where the giveaway started
        message: the ID of the sent message
        max_entries: the max amount of participants
        ends_at: the end date of the giveaway (null for a manual end)
        Returns: the row ID of the giveaway
        """
        c = self.bot.database.cursor()
        data = (channel.guild.id, channel.id, name[:64], max_entries, ends_at, message, dumps(list()))
        c.execute(
            "INSERT INTO giveaways (guild, channel, name, max_entries, ends_at, message, users) VALUES (?, ?, ?, ?, ?, ?, ?)", data)
        self.bot.database.commit()
        rowid = c.lastrowid
        c.close()
        return rowid

    def db_get_giveaways(self, guildID: int) -> [dict]:
        """
        Get giveaways attached to a server
        guildID: the guild (server) ID
        Returns: a list of dicts containing the giveaways info
        """
        c = self.bot.database.cursor()
        c.execute("SELECT rowid, * FROM giveaways WHERE guild=?", (guildID,))
        res = [{c.description[e][0]: value for e, value in enumerate(row)} for row in list(c)]
        for r in res:
            r['users'] = loads(r['users'])
            r['ends_at'] = datetime.datetime.strptime(r['ends_at'], '%Y-%m-%d %H:%M:%S')
        c.close()
        return res
    
    def db_get_expired_giveaways(self) -> [dict]:
        """
        Get every running giveaway
        Returns: a list of dicts containing the giveaways info
        """
        c = self.bot.database.cursor()
        c.execute("SELECT rowid, * FROM giveaways WHERE ends_at <= ? AND running = 1", (datetime.datetime.now(),))
        res = [{c.description[e][0]: value for e,value in enumerate(row)} for row in list(c)]
        for r in res:
            r['users'] = loads(r['users'])
            r['ends_at'] = datetime.datetime.strptime(r['ends_at'], '%Y-%m-%d %H:%M:%S')
        c.close()
        return res

    def db_get_users(self, rowID: int) -> [int]:
        """
        Get the users participating into a giveaway via command
        rowID: the ID of the giveaway to edit
        Returns: list of users IDs
        """
        c = self.bot.database.cursor()
        c.execute("SELECT users FROM giveaways WHERE rowid=?", (rowID,))
        res = list(c)
        c.close()
        if len(res) == 0:
            return None
        return loads(res[0][0])

    def db_add_participant(self, rowID: int, userID: int) -> bool:
        """
        Add a participant to a giveaway
        rowID: the ID of the giveaway to edit
        userID: the participant ID
        Returns: if the operation succeed
        """
        current_participants = self.db_get_users(rowID)
        if current_participants is None:
            # means that the giveaway doesn't exist
            return False
        current_participants = dumps(current_participants+[userID])
        c = self.bot.database.cursor()
        c.execute("UPDATE giveaways SET users=? WHERE rowid=?",
                  (current_participants, rowID))
        self.bot.database.commit()
        updated = c.rowcount == 1
        c.close()
        return updated

    def db_stop_giveaway(self, rowID: int) -> bool:
        """
        Stop a giveaway
        rowID: the ID of the giveaway to stop
        Returns: if the giveaway has successfully been stopped
        """
        c = self.bot.database.cursor()
        c.execute("UPDATE giveaways SET running=0 WHERE rowid=?", (rowID,))
        self.bot.database.commit()
        updated = c.rowcount == 1
        c.close()
        return updated

    def db_delete_giveaway(self, rowID: int) -> bool:
        """
        Delete a giveaway from the database
        rowID: the ID of the giveaway to delete
        Returns: if the giveaway has successfully been deleted
        """
        c = self.bot.database.cursor()
        c.execute("DELETE FROM giveaways WHERE rowid=?", (rowID,))
        self.bot.database.commit()
        deleted = c.rowcount == 1
        c.close()
        return deleted

    @commands.group(pass_context=True, aliases=["gaw", "giveaways"])
    async def giveaway(self, ctx):
        """Start or stop giveaways."""
        if ctx.subcommand_passed is None:
            await ctx.send_help('giveaways')

    @giveaway.command(pass_context=True)
    @commands.check(checks.is_admin)
    async def start(self, ctx, *, settings):
        """Start a giveaway
        Usage"
        [p]giveaway start name: <Giveaway  name>; length: <Time length>; entries: [winners count]; channel: [channel mention]
        Giveaway name is mandatory.
        Length is mandatory.
        Winners count is optional (default 1).
        Channel is optional (default current channel).

        Example:
        [p]giveaway start name: Minecraft account; length: 3d;
        [p]giveaway start name: Minecraft account; length: 2h; channel: #announcements
        [p]giveaway start name: Minecraft account; length: 5h 3min; entries: 5"""
        i_settings = settings.split("; ")
        existing_giveaways = self.db_get_giveaways(ctx.guild.id)
        existing_giveaways = [x['name'] for x in existing_giveaways]


        # Setting all of the settings.
        settings = {"name": "", "length": -1, "channel": ctx.channel, "entries": 1}
        for setting in i_settings:
            if setting.startswith("name: "):
                if setting[6:] in existing_giveaways:
                    await ctx.send("Il y a déjà un giveaway en cours avec ce nom !")
                    return
                else:
                    settings['name'] = setting[6:].strip()
            elif setting.startswith("entries: "):
                entries = setting.replace("entries: ", "").strip()
                if (not entries.isnumeric()) or (entries == "0"):
                    await ctx.send("Le nombre de gagnants doit être un nombre entier")
                    return
                settings['entries'] = int(entries)
            elif setting.startswith("length: "):
                total = 0
                for elem in setting[7:].split():
                    total += await args.tempdelta().convert(ctx, elem)
                if total > 0:
                    settings['length'] = total
            elif setting.startswith("channel: "):
                try:
                    channel = await commands.TextChannelConverter().convert(ctx, setting.replace('channel: ', ''))
                except:
                    await ctx.send("Le paramètre 'salon' n'est pas un salon valide")
                    return
                perms = channel.permissions_for(ctx.guild.me)
                if not (perms.send_messages or perms.embed_links):
                    await ctx.send("Je ne peux pas envoyer d'embeds dans le salon spécifié")
                    return
                settings['channel'] = channel
        # Checking if mandatory settings are there.
        if settings['name'] == "":
            await ctx.send("Le paramètre 'nom' ne peut pas être vide")
            return
        if settings['length'] == -1:
            await ctx.send("Le paramètre 'length' ne peut pas être vide")
            return
        settings['ends_at'] = datetime.datetime.fromtimestamp(round(time.time()) + settings['length'])
        # Send embed now
        try:
            emb = discord.Embed(title="New giveaway!", description=settings["name"], timestamp=datetime.datetime.utcnow(
            )+datetime.timedelta(seconds=settings['length']), color=random.randint(0, 16777215)).set_footer(text="Finit à")
            msg = await settings['channel'].send(embed=emb)
            settings['message'] = msg.id
        except discord.HTTPException as e:
            await self.bot.get_cog("Errors").on_error(e, ctx) # send error logs
            await ctx.send("Impossible d'envoyer de message dans " + settings['channel'].mention)
            return
        # Save settings in database
        rowid = self.db_add_giveaway(
            settings['channel'], settings['name'], settings['message'], settings['entries'], settings['ends_at'])
        if rowid:
            await ctx.send("J'ai correctement créé le giveaway **{}** avec l'ID {}".format(settings['name'], rowid))
        else:
            await ctx.send("Oups, quelque chose s'est mal passé !")

    @giveaway.command(pass_context=True)
    @commands.check(checks.is_admin)
    async def stop(self, ctx, *, giveaway):
        """Stops a giveaway early so you can pick a winner
        Example:
        [p]giveaway stop Minecraft account"""
        giveaways = self.db_get_giveaways(ctx.guild.id)
        if len(giveaways) == 0:
            await ctx.send("Il n'y a aucun giveaway dans ce serveur")
            return
        giveaway = [x for x in giveaways if x['name']
                    == giveaway or str(x['rowid']) == giveaway]
        if len(giveaway) == 0:
            await ctx.send("Ce n'est pas un giveaway existant, pour voir tous les giveaways vous pouvez utiliser `{}giveaway list`".format(ctx.prefix))
            return
        giveaway = giveaway[0]
        if not giveaway['running']:
            await ctx.send("Ce giveaway est déjà arrêté")
            return
        self.db_stop_giveaway(giveaway['rowid'])
        await self.send_results(giveaway, await self.pick_winners(ctx.guild, giveaway))
    
    @giveaway.command(pass_context=True)
    @commands.check(checks.is_admin)
    async def delete(self, ctx, *, giveaway):
        """
        Delete a giveaway from the database
        """
        giveaways = self.db_get_giveaways(ctx.guild.id)
        if len(giveaways) == 0:
            await ctx.send("Il n'y a aucun giveaway dans ce serveur")
            return
        giveaway = [x for x in giveaways if x['name'] == giveaway or str(x['rowid']) == giveaway]
        if len(giveaway) == 0:
            await ctx.send("Ce n'est pas un giveaway existant, pour voir tous les giveaways vous pouvez utiliser `{}giveaway list`".format(ctx.prefix))
            return
        giveaway = giveaway[0]
        if self.db_delete_giveaway(giveaway['rowid']):
            await ctx.send("Le giveaway a bien été supprimé !")
        else:
            await ctx.send("Oups, un problème est survenu :confused:")

    @giveaway.command(pass_context=True)
    @commands.check(checks.is_admin)
    async def pick(self, ctx, *, giveaway):
        """Picks winners for the giveaway, which usually should be 1
        Example:
        [p]giveaway pick Minecraft account (This will pick winners from all the people who entered the Minecraft account giveaway)"""
        giveaways = self.db_get_giveaways(ctx.guild.id)
        if len(giveaways) == 0:
            await ctx.send("Il n'y a aucun giveaway dans ce serveur")
            return
        giveaway = [x for x in giveaways if x['name'] == giveaway or str(x['rowid']) == giveaway]
        if len(giveaway) == 0:
            await ctx.send("Ce n'est pas un giveaway existant")
            return
        giveaway = giveaway[0]
        if giveaway['running']:
            await ctx.send("Ce giveaway est toujours d'actualité, vous pouvez l'arrêter avec `{}giveaway stop {}`".format(ctx.prefix, giveaway['rowid']))
            return
        users = set(giveaway['users']) | await self.get_users(giveaway['channel'], giveaway['message'])
        if len(users) == 0:
            await ctx.send("Personne n'a participé à ce concours ! Je vais le détruire")
            self.db_delete_giveaway(giveaway['rowid'])
        else:
            amount = min(giveaway['max_entries'], len(users))
            status = await ctx.send("Choix des gagnants...")
            winners = []
            trials = 0
            users = list(users)
            while len(winners) < amount and trials < 20:
                w = discord.utils.get(
                    ctx.guild.members, id=random.choice(users))
                if w != None:
                    winners.append(w.mention)
                else:
                    trials += 1
            self.db_delete_giveaway(giveaway['rowid'])
            if amount == 1:
                await status.edit(content="Le gagnant est : {} ! Félicitations, vous avez gagné {} !".format(" ".join(winners), giveaway))
            else:
                await status.edit(content="Les gagnants sont : {} ! Félicitations, vous avez gagné {} !".format(" ".join(winners), giveaway))

    @giveaway.command(pass_context=True)
    async def enter(self, ctx, *, giveaway):
        """Enter a giveaway.
        Example:
        [p]giveaway enter Minecraft account"""
        if ctx.author.bot:
            await ctx.send("Les bots ne peuvent pas participer à un giveaway !")
            return
        server = ctx.message.guild
        author = ctx.message.author

        giveaways = self.db_get_giveaways(ctx.guild.id)
        if len(giveaways) == 0:
            await ctx.send("Il n'y a aucun giveaway dans ce serveur")
            return
        giveaways = [x for x in giveaways if x['name'] == giveaway or str(x['rowid']) == giveaway]
        if len(giveaways) == 0:
            await ctx.send("Ce n'est pas un giveaway existant")
            return
        ga = giveaways[0]
        if author.id in ga['users']:
            await ctx.send("Vous participez déjà à ce giveaway")
        elif not ga['running']:
            await ctx.send("Ce giveaway a été arrêté")
        else:
            if self.db_add_participant(ga['rowid'], author.id):
                await ctx.send("Vous participez maintenant au giveaway **{}**, bonne chance !".format(ga['name']))
            else:
                await ctx.send("Oups, quelque chose s'est mal passé pendant l'ajout :confused:")

    @giveaway.command(pass_context=True)
    async def list(self, ctx):
        """Lists all giveaways running in this server"""
        server = ctx.message.guild
        giveaways = self.db_get_giveaways(server.id)
        if len(giveaways) == 0:
            await ctx.send("Il n'y a aucun giveaway dans ce serveur")
            return
        else:
            running = [f"{x['rowid']}. {x['name']}" for x in giveaways if x['running']]
            stopped = [f"{x['rowid']}. {x['name']}" for x in giveaways if not x['running']]
            text = ""
            if len(running) > 0:
                text += "Les giveaways actuellement actifs :\n\t{}".format("\n\t".join(running))
            if len(stopped) > 0:
                text += "\n\n" if len(text) > 0 else ""
                text += "Les giveaways déjà terminés :\n\t{}".format("\n\t".join(stopped))
            if len(text) == 0:
                text = "Il n'y a aucun giveaway dans ce serveur"
            await ctx.send(text)

    @giveaway.command(pass_context=True)
    async def info(self, ctx, *, giveaway):
        """Get information for a giveaway
        Example:
        [p]giveaway info Minecraft account"""
        server = ctx.message.guild
        giveaways = self.db_get_giveaways(ctx.guild.id)
        if len(giveaways) == 0:
            await ctx.send("Il n'y a aucun giveaway dans ce serveur")
            return
        giveaway = [x for x in giveaways if x['name'] == giveaway or str(x['rowid']) == giveaway]
        if len(giveaway) == 0:
            await ctx.send("Ce n'est pas un giveaway existant")
            return
        giveaway = giveaway[0]
        entries = len(set(giveaway['users']) | await self.get_users(giveaway['channel'], giveaway['message']))
        d1, d2 = datetime.datetime.now(), giveaway['ends_at']
        if d1 < d2:
            time_left = await self.bot.get_cog("TimeCog").time_delta(d2, d1, 'fr', precision=0)
        elif d1 == d2:
            time_left = "Imminent"
        else:
            time_left = "Déjà terminé"
        name = giveaway['name']
        await ctx.send("Nom : **{}**\nTemps restant : **{}**\nEntrées : **{}**\nSalon : <#{}>".format(name, time_left, entries, giveaway['channel']))

    def cog_unload(self):
        self.internal_task.cancel()

    @tasks.loop(seconds=2.0)
    async def internal_task(self):
        for giveaway in self.db_get_expired_giveaways():
            if giveaway['running']:
                try:
                    serv = self.bot.get_guild(giveaway['guild'])
                    winners = await self.pick_winners(serv, giveaway)
                    await self.send_results(giveaway, winners)
                    self.db_stop_giveaway(giveaway['rowid'])
                except Exception as e:
                    await self.bot.get_cog('Errors').on_error(e)
                    self.db_stop_giveaway(giveaway['rowid'])

    async def get_users(self, channel: int, message: int):
        """Get users who reacted to a message"""
        channel: discord.TextChannel = self.bot.get_channel(channel)
        if channel is None:
            return []
        message: discord.Message = await channel.fetch_message(message)
        if message is None or message.author != self.bot.user:
            return []
        users = set()
        for react in message.reactions:
            async for user in react.users():
                if not user.bot:
                    users.add(user.id)
        return users

    async def edit_embed(self, channel: discord.TextChannel, message: int, winners: [discord.Member]) -> int:
        """Edit the embed to display results
        Returns the embed color if the embed was found, None else"""
        message: discord.Message = await channel.fetch_message(message)
        if message is None or message.author != self.bot.user:
            return None
        if len(message.embeds) == 0 or message.embeds[0].title != "New giveaway!":
            return None
        emb: discord.Embed = message.embeds[0]
        emb.set_footer(text="Ended at")
        emb.description = "Price: {}\nWon by: {}".format(
            emb.description, " ".join([x.mention for x in winners]))
        await message.edit(embed=emb)
        return emb.color

    async def pick_winners(self, guild: discord.Guild, giveaway: dict) -> [discord.Member]:
        """Select the winner of a giveaway, from both participants using the command and using the message reactions
        Returns a list of members"""
        users = set(giveaway['users']) | await self.get_users(giveaway['channel'], giveaway['message'])
        if len(users) == 0:
            return list()
        else:
            amount = min(giveaway['max_entries'], len(users))
            winners = list()
            trials = 0
            users = list(users)
            while len(winners) < amount and trials < 20:
                w = discord.utils.get(guild.members, id=random.choice(users))
                if w != None:
                    winners.append(w)
                else:
                    trials += 1
        return winners

    async def send_results(self, giveaway: dict, winners: [discord.Member]):
        """Send the giveaway results in a new embed"""
        self.bot.log.info(f"Giveaway '{giveaway['name']}' has stopped")
        channel: discord.TextChannel = self.bot.get_channel(giveaway['channel'])
        if channel is None:
            return None
        emb_color = await self.edit_embed(channel, giveaway['message'], winners)
        if emb_color is None:
            # old embed wasn't found, we select a new color
            emb_color = random.randint(0, 16777215)
        if len(winners) == 0:
            win = "Il n'y a eu aucun participant :confused:"
        else:
            win = "Le gagnant est" if len(winners) == 1 else "Les gagnants sont"
        emb = discord.Embed(title="Giveaway is over!", description="Price: {}\n\n{} {}".format(
            giveaway['name'], win, " ".join([x.mention for x in winners])), color=emb_color)
        await channel.send(embed=emb)
        self.db_delete_giveaway(giveaway['rowid'])


def setup(bot):
    bot.add_cog(Giveaways(bot))
