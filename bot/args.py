"""
Ce programme est régi par la licence CeCILL soumise au droit français et
respectant les principes de diffusion des logiciels libres. Vous pouvez
utiliser, modifier et/ou redistribuer ce programme sous les conditions
de la licence CeCILL diffusée sur le site "http://www.cecill.info".
"""

import re

from discord.ext import commands

from utils import MyContext


class tempdelta(commands.Converter): # pylint: disable=invalid-name
    async def convert(self, ctx: MyContext, argument: str) -> int: # pylint: disable=unused-argument
        time = 0
        found = False
        for time_spec in [
            ("y", 86400 * 365),
            ("w", 604800),
            ("d", 86400),
            ("h", 3600),
            ("m", 60),
            ("min", 60),
        ]:
            pattern = re.search(r"^(\d+)" + time_spec[0] + "$", argument)
            if pattern is not None:
                time += int(pattern.group(1)) * time_spec[1]
                found = True
        pattern = re.search(r"^(\d+)h(\d+)m?$", argument)
        if pattern is not None:
            time += int(pattern.group(1)) * 3600 + int(pattern.group(2)) * 60
            found = True
        if not found:
            raise commands.errors.BadArgument("Invalid duration: " + argument)
        return time


class moderatorFlag(commands.Converter): # pylint: disable=invalid-name
    async def convert(self, ctx: MyContext, argument: str) -> str:
        logs_flags = ctx.bot.get_cog("ConfigCog").LogsFlags.FLAGS
        if argument not in logs_flags.values():
            raise commands.errors.BadArgument("Invalid moderation flag: " + argument)
        return argument


def constant(word: str):
    class Constant(commands.Converter):
        w = word

        async def convert(self, ctx: MyContext, arg: str): # pylint: disable=unused-argument
            if arg != self.w:
                raise commands.errors.BadArgument("Unknown argument")

    return Constant


class arguments(commands.Converter): # pylint: disable=invalid-name
    async def convert(self, ctx: MyContext, argument: str) -> dict: # pylint: disable=unused-argument
        answer = dict()
        for result in re.finditer(r"(\w+) ?= ?\"((?:[^\"\\]|\\\"|\\)+)\"", argument):
            answer[result.group(1)] = result.group(2).replace('\\"', '"')
        return answer
