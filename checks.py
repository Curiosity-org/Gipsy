import discord
from discord.ext import commands
from utils import MyContext


def is_bot_admin(ctx: MyContext):
    return ctx.author.id in ctx.bot.config['bot_admins']


async def is_admin(ctx: MyContext):
    admin = ctx.guild is None or ctx.author.guild_permissions.administrator or is_bot_admin(ctx)
    if not admin and ctx.invoked_with != "help":
        try:
            await ctx.send("Il vous manque la permission 'Administrateur' pour faire cela")
        except discord.errors.Forbidden:
            pass
    return admin

async def is_server_manager(ctx: MyContext):
    g_manager = ctx.guild is None or ctx.author.guild_permissions.manage_guild or is_bot_admin(ctx)
    if not g_manager and ctx.invoked_with != "help":
        try:
            await ctx.send("Il vous manque la permission 'Gérer le serveur' pour faire cela")
        except discord.errors.Forbidden:
            pass
    return g_manager

async def is_roles_manager(ctx: MyContext):
    r_manager = ctx.guild is None or ctx.author.guild_permissions.manage_roles or is_bot_admin(ctx)
    if not r_manager and ctx.invoked_with != "help":
        try:
            await ctx.send("Il vous manque la permission 'Gérer le serveur' pour faire cela")
        except discord.errors.Forbidden:
            pass
    return r_manager