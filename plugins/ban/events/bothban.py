"""
Ce programme est régi par la licence CeCILL soumise au droit français et
respectant les principes de diffusion des logiciels libres. Vous pouvez
utiliser, modifier et/ou redistribuer ce programme sous les conditions
de la licence CeCILL diffusée sur le site "http://www.cecill.info".
"""

import random

import discord
from discord.ext import commands


async def execute(
    ban_plugin,
    ctx: commands.Context,
    user: discord.User,
    reason: str,  # pylint: disable=unused-argument
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
                "https://tenor.com/view/max-fosh-uno-reverse-uno-uno-reverse-card-football-gif-15997104819716648222"
            )
            return
        else:
            # we cannot ban the author, so we act as if it was a one-way ban
            choice = random.randint(0, 9)
            msg = await ctx.bot._(ctx.channel, f"ban.gunivers.ban.{choice}")
            await ctx.send(msg.format(ctx.author.mention, user.mention))
            await ctx.send(
                "https://tenor.com/view/bongocat-banhammer-ban-hammer-bongo-gif-18219363"
            )
