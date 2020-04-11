import discord
from discord.ext import commands
import checks


class Contact(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.file = "contact"
    
    @commands.Cog.listener()
    async def on_message(self, message:discord.Message):
        """Called for every new message
        We use it to check when someone send a message in the contact channel"""
        if message.guild == None: # si le message n'est pas dans un serveur
            return
        if message.author.bot: # si le message a été envoyé par un bot
            return
        config = self.bot.server_configs[message.guild.id]
        if message.channel.id != config["contact_channel"]:
            return
        category = self.bot.get_channel(config["contact_category"])
        channel = discord.utils.get(category.text_channels, topic=str(message.author.id))
        if channel == None:
            channel = await category.create_text_channel(str(message.author))
            await channel.edit(topic=str(message.author.id))
        else:
            if channel.name != str(message.author):
                await channel.edit(name=str(message.author))
        await channel.send(message.content)
        await channel.set_permissions(message.author, read_messages=True,send_messages=True)
        try:
            await message.delete()
        except discord.errors.Forbidden:
            pass


def setup(bot):
    bot.add_cog(Contact(bot))
