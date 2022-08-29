import discord
from discord.ext import commands

import random

async def execute(
    ban_plugin,
    ctx: commands.Context,
    user: discord.User,
    reason: str,
) -> bool:
    """If the ban is issued by Leirof, then Bald ban event
    """
    if ctx.author.id == 125722240896598016:
        if await ban_plugin.fake_ban(ctx, user):
            # Find and send some random message
            choice = random.randint(0, 9)
            msg = await ctx.bot._(ctx.channel, f"ban.gunivers.ban.{choice}")
            await ctx.send(msg.format(ctx.author.mention, user.mention))
            await ctx.send(
                "https://thumbs.gfycat.com/PepperyEminentIndianspinyloach-size_restricted.gif"
            )
            await ctx.send(
                "https://media.discordapp.net/attachments/791335982666481675/979052868915064862/Chauve_qui_peut_.png"
            )
        return True
    else:
        return False
