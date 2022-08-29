import discord
from discord.ext import commands

import random

async def execute(
    ban_plugin,
    ctx: commands.Context,
    user: discord.User,
    reason: str,
) -> bool:
    """Reverse the ban, uno reverse card
    The command executor is banned instead of the targeted user.
    """
    if await ban_plugin.fake_ban(ctx, ctx.author):
        # Find and send some random message
        choice = random.randint(0, 3)
        msg = await ctx.bot._(
            ctx.channel, f"ban.gunivers.selfban.{choice}"
        )
        await ctx.send(msg.format(ctx.author.mention, user.mention))
        await ctx.send(
            "https://thumbs.gfycat.com/BackInsignificantAfricanaugurbuzzard-size_restricted.gif"
        )
