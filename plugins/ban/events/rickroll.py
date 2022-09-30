import discord
from discord.ext import commands


async def execute(
    ban_plugin,
    ctx: commands.Context,
    user: discord.User,
    reason: str,
) -> bool:
    """Just send a rickroll"""
    await ctx.bot._(ctx.channel, f"ban.gunivers.rickroll")
    await ctx.send(
        "Never gonna give you up,\nnever gonna let you down,\nnever gonna run around and ban you :musical_note:"
    )
    await ctx.send(
        "https://thumbs.gfycat.com/VengefulDesertedHalibut-size_restricted.gif"
    )
    return
