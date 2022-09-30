import discord
from discord.ext import commands

import random


async def execute(
    ban_plugin,
    ctx: commands.Context,
    user: discord.User,
    reason: str,
) -> bool:
    """Normally ban the user, with a little goodbye message"""
    if await ban_plugin.fake_ban(ctx, user):
        # Find and send some random message
        choice = random.randint(0, 9)
        msg = await ctx.bot._(ctx.channel, f"ban.gunivers.ban.{choice}")
        await ctx.send(msg.format(ctx.author.mention, user.mention))
        await ctx.send(
            "https://thumbs.gfycat.com/PepperyEminentIndianspinyloach-size_restricted.gif"
        )
