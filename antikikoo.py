import discord
from discord.ext import commands

WELCOME_MESSAGE = """(FR) Bienvenue sur GUNIVERS {user} !
Vous n'avez accès qu'au salon Lobby pour le moment. Pour débloquer l'accès au reste du Discord, lisez les instructions présentes dans le salon {channel} :wink:

(EN) Welcome to GUNIVERS {user} !
You only have access to the Lobby channel. To unlock the acess to the rest of our Discord, please follow the instructions in the {channel} channel :wink:"""

CONFIRM_MESSAGE = """{user} a lu {channel}

{user} read {channel}"""


class Antikikoo(commands.Cog):
    """Empêche les kikoos de rentrer dans le serveur"""

    def __init__(self, bot):
        self.bot = bot
        self.file = "antikikoo"


    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Called when a member joins a guild"""
        if member.guild.id != self.bot.config["main_server"]:
            return
        self.bot.log.info(f"{member} ({member.id}) joined the server")
        config = self.bot.server_configs[member.guild.id]
        verif_channel = self.bot.get_channel(config["verification_channel"])
        info_channel = "<#"+config["info_channel"]+">"
        await verif_channel.send(WELCOME_MESSAGE.format(user=member.mention, channel=info_channel))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Called for every new message
        We use it to check when someone send the verification message"""
        if message.guild == None: # si le message n'est pas dans un serveur
            return
        config = self.bot.server_configs[message.guild.id]
        if message.channel.id != config["verification_channel"]:
            return
        info_channel = "<#"+config["info_channel"]+">"
        if message.content.lower() == config["pass_message"].lower():
            emb = discord.Embed(description=CONFIRM_MESSAGE.format(
                user=message.author.mention, channel=info_channel))
            await message.channel.send(embed=emb)
            try:
                await message.delete()
            except:
                self.bot.log.exception(f"Impossible de supprimer le message de vérification")
            try:
                if config["verification_add_role"]:
                    await message.author.add_roles(self.verif_role)
                else:
                    await message.author.remove_roles(self.verif_role)
            except:
                self.bot.log.exception(f"Impossible de donner ou d'enlever le rôle de vérification au membre {message.author}")


    @commands.group(name="antikikoo", aliases=["ak", "antitroll"])
    @commands.guild_only()
    async def ak_main(self, ctx: commands.Context):
        """Configuration du filtre anti-kikoo"""
        pass

    @ak_main.command(name="channel")
    async def ak_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Modifie le salon où les membres devront se vérifier"""
        self.bot.server_configs[ctx.guild.id]["verification_channel"] =  channel.id
        await ctx.send("Le salon de vérification est maintenant {} !".format(channel.mention))


def setup(bot):
    bot.add_cog(Antikikoo(bot))
