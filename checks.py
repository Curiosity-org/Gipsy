def is_bot_admin(ctx):
    return ctx.author.id in ctx.bot.config['bot_admins']