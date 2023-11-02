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
    """Reverse the ban, uno reverse card
    The command executor is banned instead of the targeted user.
    """
    if await ban_plugin.fake_ban(ctx, ctx.author, False):
        # Find and send some random message
        choice = random.randint(0, 3)
        msg = await ctx.bot._(ctx.channel, f"ban.gunivers.selfban.{choice}")
        await ctx.send(msg.format(ctx.author.mention, user.mention))
        await ctx.send(
            "https://tenor.com/view/self-ban-brooklyn99-brooklyn-nine-nine-pepperdrop-ban-gif-25644700"
        )
    else:
        # fallback to a normal ban
        if await ban_plugin.fake_ban(ctx, user):
            choice = random.randint(0, 9)
            msg = await ctx.bot._(ctx.channel, f"ban.gunivers.ban.{choice}")
            await ctx.send(msg.format(ctx.author.mention, user.mention))
            await ctx.send(
                "https://tenor.com/view/bongocat-banhammer-ban-hammer-bongo-gif-18219363"
            )
