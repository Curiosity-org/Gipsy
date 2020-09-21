import discord
import re
from discord.ext import commands


class tempdelta(commands.Converter):
    def __init__(self):
        pass

    async def convert(self, ctx: commands.Context, argument) -> int:
        d = 0
        found = False
        # ctx.invoked_with
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
