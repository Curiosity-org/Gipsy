import nextcord
import re
from nextcord.ext import commands
from utils import MyContext


class tempdelta(commands.Converter):
    async def convert(self, ctx: MyContext, argument: str) -> int:
        d = 0
        found = False
        for x in [('y', 86400*365), ('w', 604800), ('d', 86400), ('h', 3600), ('m', 60), ('min', 60)]:
            r = re.search(r'^(\d+)'+x[0]+'$', argument)
            if r is not None:
                d += int(r.group(1))*x[1]
                found = True
        r = re.search(r'^(\d+)h(\d+)m?$', argument)
        if r is not None:
            d += int(r.group(1))*3600 + int(r.group(2))*60
            found = True
        if not found:
            raise commands.errors.BadArgument('Invalid duration: '+argument)
        return d


class moderatorFlag(commands.Converter):
    async def convert(self, ctx: MyContext, argument: str) -> str:
        LogsFlags = ctx.bot.get_cog('ConfigCog').LogsFlags.FLAGS
        if argument not in LogsFlags.values():
            raise commands.errors.BadArgument(
                'Invalid moderation flag: '+argument)
        return argument


def constant(word: str):
    class Constant(commands.Converter):
        w = word

        async def convert(self, ctx: MyContext, arg: str):
            if arg != self.w:
                raise commands.errors.BadArgument('Unknown argument')
    return Constant

class arguments(commands.Converter):
    async def convert(self, ctx: MyContext, argument: str) -> dict:
        answer = dict()
        for result in re.finditer(r'(\w+) ?= ?\"((?:[^\"\\]|\\\"|\\)+)\"', argument):
            answer[result.group(1)] = result.group(2).replace('\\"', '"')
        return answer