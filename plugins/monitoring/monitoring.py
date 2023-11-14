"""
Ce programme est régi par la licence CeCILL soumise au droit français et
respectant les principes de diffusion des logiciels libres. Vous pouvez
utiliser, modifier et/ou redistribuer ce programme sous les conditions
de la licence CeCILL diffusée sur le site "http://www.cecill.info".
"""

# pylint: disable=unused-import
from discord.ext import tasks, commands

import requests

from utils import Gunibot, MyContext
import core


async def setup(bot: Gunibot = None):
    await bot.add_cog(Monitoring(bot))


class Monitoring(commands.Cog):
    def __init__(self, bot: Gunibot):
        self.bot = bot
        self.file = "monitoring"
        self.logger = core.setup_logger(self.file)
        self.config = core.config.get(self.file)
        if self.config["monitoring_enabled"]:
            # test if the url is valid
            if requests.get(self.config["monitoring_push_url"]).status_code == 200:
                self.ping_monitoring.start()
                self.logger.info(
                    f"Monitoring enabled successfully for {self.config['monitoring_push_url']}"
                )
            else:
                self.logger.warning(
                    f"Monitoring disabled for this time: {self.config['monitoring_push_url']} is not valid or reachable"
                )

    @tasks.loop(seconds=20)
    async def ping_monitoring(self):
        requests.get(self.config["monitoring_push_url"])

    @ping_monitoring.before_loop
    async def before_ping_monitoring(self):
        await self.bot.wait_until_ready()
