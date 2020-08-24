import discord
from discord.ext import commands
from discord.utils import snowflake_time
from datetime import datetime, timedelta
import checks


class Contact(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.file = "contact"
    
    @commands.Cog.listener()
    async def on_message(self, message:discord.Message):
        """Called for every new message
        We use it to check when someone send a message in the contact channel"""
        if message.guild is None: # si le message n'est pas dans un serveur
            return
        if message.author.bot: # si le message a été envoyé par un bot
            return
        config = self.bot.server_configs[message.guild.id]
        if message.channel.id != config["contact_channel"]:
            return
        category = self.bot.get_channel(config["contact_category"])
        channel = discord.utils.get(category.text_channels, topic=str(message.author.id))
        if channel is None:
            try:
                channel = await category.create_text_channel(str(message.author))
                await channel.edit(topic=str(message.author.id))
            except discord.errors.Forbidden as e:
                await self.bot.get_cog("Errors").on_error(e, await self.bot.get_context(message))
                return
        else:
            if channel.name != str(message.author):
                await channel.edit(name=str(message.author))
        await channel.send(message.content)
        await channel.set_permissions(message.author, read_messages=True,send_messages=True)
        try:
            await message.delete()
        except discord.errors.Forbidden:
            pass

    @commands.command(name="contact-clear", aliases=["ctc", "ct-clear"])
    @commands.guild_only()
    async def ct_clear(self, ctx: commands.Context, days: int=15):
        """Nettoie tous les salons inutilisés depuix X jours"""
        categ_id = self.bot.server_configs[ctx.guild.id]["contact_category"]
        if categ_id is None:
            await ctx.send("Aucune catégorie de contact n'a été créée !")
            return
        categ = ctx.guild.get_channel(categ_id)
        if categ is None:
            await ctx.send("Impossible de trouver la catégorie de contact ! Vérifiez votre configuration")
            return
        i = 0 # compteur de suppressions
        errors = list() # liste des éventuelles erreurs
        max_date = datetime.now()-timedelta(days=days)
        for chan in categ.text_channels:
            if snowflake_time(chan.last_message_id) < max_date: # si la date du dernier message est trop ancienne
                try:
                    await chan.delete(reason="channel too old")
                    i += 1
                except discord.DiscordException as e:
                    errors.append(str(e))
        answer = "" if i==0 else f"{i} salons ont été supprimés !"
        if len(errors) > 0:
            answer += "\n{} salons n'ont pu être supprimés :\n • {}".format(len(errors), "\n • ".join(errors))
        if len(answer) == 0: # si aucun salon n'a eu besoin d'être supprimé
            answer = "Aucun salon n'est aussi vieux !"
        await ctx.send(answer)

def setup(bot):
    bot.add_cog(Contact(bot))
