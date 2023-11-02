"""
Ce programme est régi par la licence CeCILL soumise au droit français et
respectant les principes de diffusion des logiciels libres. Vous pouvez
utiliser, modifier et/ou redistribuer ce programme sous les conditions
de la licence CeCILL diffusée sur le site "http://www.cecill.info".
"""

from discord.ext import tasks, commands

from utils import Gunibot


class Gunivers(commands.Cog):
    def __init__(self, bot: Gunibot):
        self.bot = bot
        self.file = "gunivers"
        self.update_loop.start()  # pylint: disable=no-member

    async def cog_unload(self):
        self.update_loop.cancel()  # pylint: disable=no-member

    @tasks.loop(minutes=60.0 * 24.0)
    async def update_loop(self):
        channel = self.bot.get_channel(757879277776535664)  # Round Table
        if channel is not None:
            await channel.send("Bon, qu'est-ce qu'on peut poster aujourd'hui ?")


async def setup(bot: Gunibot = None):
    await bot.add_cog(Gunivers(bot))
