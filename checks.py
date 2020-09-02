def is_bot_admin(ctx):
    return ctx.author.id in ctx.bot.config['bot_admins']

def is_admin(ctx):
    return ctx.guild is None or ctx.author.guild_permissions.administrator