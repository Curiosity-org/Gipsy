import discord
from discord.ext import commands

import random


async def execute(
    ban_plugin,
    ctx: commands.Context,
    user: discord.User,
    reason: str,
) -> bool:
    """Ban both the executor and the targeted user."""
    if await ban_plugin.fake_ban(ctx, user):
        if await ban_plugin.fake_ban(ctx, ctx.author, False):
            # If there's no error, find a random message and send
            # it.
            choice = random.randint(0, 3)
            msg = await ctx.bot._(ctx.channel, f"ban.gunivers.bothban.{choice}")
            await ctx.send(msg.format(ctx.author.mention, user.mention))
            await ctx.send(
                "https://thumbs.gfycat.com/BackInsignificantAfricanaugurbuzzard-size_restricted.gif"
            )
            return
        else:
            # we cannot ban the author, so we act as if it was a one-way ban
            choice = random.randint(0, 9)
            msg = await ctx.bot._(ctx.channel, f"ban.gunivers.ban.{choice}")
            await ctx.send(msg.format(ctx.author.mention, user.mention))
            await ctx.send(
                "https://thumbs.gfycat.com/PepperyEminentIndianspinyloach-size_restricted.gif"
            )
