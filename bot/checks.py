import nextcord
from utils import MyContext, CheckException


def is_bot_admin(ctx: MyContext):
    return ctx.author.id in ctx.bot.config['bot_admins']

async def is_admin(ctx: MyContext):
    admin = ctx.guild is None or ctx.author.guild_permissions.administrator or is_bot_admin(ctx)
    if not admin:
        raise CheckException('is_admin')
    return True

async def is_server_manager(ctx: MyContext):
    g_manager = ctx.guild is None or ctx.author.guild_permissions.manage_guild or is_bot_admin(ctx)
    if not g_manager:
        raise CheckException('is_server_manager')
    return True

async def is_roles_manager(ctx: MyContext):
    r_manager = ctx.guild is None or ctx.author.guild_permissions.manage_roles or is_bot_admin(ctx)
    if not r_manager:
        raise CheckException('is_roles_manager')
    return True

async def can_group(ctx: MyContext):
    config = ctx.bot.server_configs[ctx.guild.id]
    if config["group_allowed_role"] is None:
        return True
    role = nextcord.utils.get(ctx.message.guild.roles, id=config["group_allowed_role"])
    if role in ctx.author.roles:
        return True
