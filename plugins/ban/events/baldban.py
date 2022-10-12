import discord
from discord.ext import commands

import random


async def execute(
    ban_plugin,
    ctx: commands.Context,
    user: discord.User,
    reason: str,
) -> bool:
    """If the ban is issued by Leirof, then Bald ban event"""
    if ctx.author.id == 125722240896598016:
        await ctx.send(
            "https://media.discordapp.net/attachments/791335982666481675/979052868915064862/Chauve_qui_peut_.png"
        )

    return False  # allow Leirof to also get reverse ban and other fun things
