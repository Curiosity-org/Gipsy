"""
Ce programme est régi par la licence CeCILL soumise au droit français et
respectant les principes de diffusion des logiciels libres. Vous pouvez
utiliser, modifier et/ou redistribuer ce programme sous les conditions
de la licence CeCILL diffusée sur le site "http://www.cecill.info".
"""

import discord

from utils import MyContext, CheckException
from core import config


def is_bot_admin(ctx: MyContext):
    return ctx.author.id in config.get("bot.admins")


async def is_admin(ctx: MyContext):
    admin = (
        ctx.guild is None
        or ctx.author.guild_permissions.administrator
        or is_bot_admin(ctx)
    )
    if not admin:
        raise CheckException("is_admin")
    return True


async def is_server_manager(ctx: MyContext):
    g_manager = (
        ctx.guild is None
        or ctx.author.guild_permissions.manage_guild
        or is_bot_admin(ctx)
    )
    if not g_manager:
        raise CheckException("is_server_manager")
    return True


async def is_roles_manager(ctx: MyContext):
    r_manager = (
        ctx.guild is None
        or ctx.author.guild_permissions.manage_roles
        or is_bot_admin(ctx)
    )
    if not r_manager:
        raise CheckException("is_roles_manager")
    return True


async def can_group(ctx: MyContext):
    server_config = ctx.bot.server_configs[ctx.guild.id]
    if server_config["group_allowed_role"] is None:
        return True
    role = discord.utils.get(
        ctx.message.guild.roles, id=server_config["group_allowed_role"]
    )
    if role in ctx.author.roles:
        return True
