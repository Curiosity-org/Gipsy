import discord
from discord.ext import commands


def is_bot_admin(ctx: commands.Context):
    return ctx.author.id in ctx.bot.config['bot_admins']


async def is_admin(ctx: commands.Context):
    admin = ctx.guild is None or ctx.author.guild_permissions.administrator or is_bot_admin(ctx)
    if not admin and ctx.invoked_with != "help":
        try:
            await ctx.send("Il vous manque la permission 'Administrateur' pour faire cela")
        except discord.errors.Forbidden:
            pass
    return admin
