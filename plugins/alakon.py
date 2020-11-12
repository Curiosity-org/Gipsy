import discord
import aiohttp
import random
from discord.ext import commands
import checks

# Commande /cookie

@commands.command(name="cookie")
async def cookie(self, ctx):
    """La fonction la plus complexe du bot: donne un cookie à l'utilisateur qui en demande."""
    message = f"Voilà pour vous {ctx.author}: :cookie:"
    await ctx.send(message)
