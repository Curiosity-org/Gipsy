"""
Ce programme est régi par la licence CeCILL soumise au droit français et
respectant les principes de diffusion des logiciels libres. Vous pouvez
utiliser, modifier et/ou redistribuer ce programme sous les conditions
de la licence CeCILL diffusée sur le site "http://www.cecill.info".
"""
import time

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
            for i in range(5):
                if self.ping_monitoring():
                    self.logger.info("Monitoring test ping successful")
                    self.logger.info("Monitoring enabled")
                    self.loop.start()
                    return
                else:
                    self.logger.warning(f"Monitoring ping failed {i+1} times")
                    time.sleep(5)
            self.logger.error("Monitoring disabled due to ping failure")


    def ping_monitoring(self):
        # retrieve Discord Ping
        ping = round(self.bot.latency*1000, 0)
        # build URL
        url = (self.config["monitoring_push_url"] +
               self.config["monitoring_push_monitor"] +
               "?status=up&msg=OK&ping=" + str(ping))
        # send request
        try:
            request = requests.get(url, timeout=5)
            if (request.status_code != 200 or request.json()["ok"] != True):
                raise requests.exceptions.RequestException(request.json()["msg"])
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error while sending heartbeat to monitoring: {e}")
            return False
        return True


    @tasks.loop(seconds=20)
    async def loop(self):
        self.ping_monitoring()

    @loop.before_loop
    async def before_ping_monitoring(self):
        await self.bot.wait_until_ready()
