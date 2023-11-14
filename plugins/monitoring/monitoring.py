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
            try:
                request = requests.get(self.config["monitoring_push_url"], timeout=5)
                if (request.status_code != 200 or request.json()["ok"] != False):
                    raise requests.exceptions.RequestException("URL returned an error")
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Error while sending heartbeat to monitoring: {e}")
                self.logger.warning(
                    "Monitoring disabled for this session: an error occured while sending the heartbeat to the monitoring server.\n"
                    "Error : %s",
                    e,
                )
                return
            #pylint: disable=no-member
            self.ping_monitoring.start()
            self.logger.info(
                "Monitoring enabled successfully for %s", self.config["monitoring_push_url"]
            )

    @tasks.loop(seconds=20)
    async def ping_monitoring(self):
        try:
            requests.get(self.config["monitoring_push_url"], timeout=5)
        except requests.exceptions.RequestException as e:
            self.logger.error("Error while sending heartbeat to monitoring: %s", e)

    @ping_monitoring.before_loop
    async def before_ping_monitoring(self):
        await self.bot.wait_until_ready()
