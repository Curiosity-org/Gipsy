from discord.ext import commands

def is_bot_admin(ctx: commands.Context):
    return ctx.author.id in ctx.bot.config['bot_admins']

async def is_admin(ctx: commands.Context):
    admin = ctx.guild is None or ctx.author.guild_permissions.administrator or is_bot_admin(ctx)
    if not admin:
        try:
            await ctx.send("Il vous manque la permission 'Administrateur' sur le serveur pour faire cela/vous n'etes pas un administrateur du bot")
        except discord.errors.Forbidden:
            pass
    return admin
