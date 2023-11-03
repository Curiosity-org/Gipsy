"""
Ce programme est régi par la licence CeCILL soumise au droit français et
respectant les principes de diffusion des logiciels libres. Vous pouvez
utiliser, modifier et/ou redistribuer ce programme sous les conditions
de la licence CeCILL diffusée sur le site "http://www.cecill.info".
"""

import discord
from discord.ext import commands

from utils import Gunibot, MyContext
# pylint: disable=relative-beyond-top-level
from .abbreviations import abbreviations


async def setup(bot: Gunibot = None):
    await bot.add_cog(Abbrev(bot))


class Abbrev(commands.Cog):
    def __init__(self, bot: Gunibot):
        self.bot = bot
        self.file = "abbreviationExplainer"
        self.cache = {}

        self.bot.get_command("config").add_command(self.config_enable_abbreviation_explainer)

    @commands.command(name="enable_abbreviation_explainer")
    async def config_enable_abbreviation_explainer(self, ctx: MyContext, value: bool):
        """Enable or disable the XP system in your server"""
        await ctx.send(
            await self.bot.sconfig.edit_config(ctx.guild.id, "enable_abbreviation_explainer", value)
        )


    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # check if server has enabled the abbreviation explainer
        if not self.bot.server_configs[message.guild.id].get("enable_abbreviation_explainer", False):
            return

        # check if message is not from a bot
        if message.author.bot:
            return

        # retrieve a list of all abbreviations in the message
        words = message.content.split()
        abbreviations_lang = abbreviations.keys()
        abbreviations_in_message = {lang: [] for lang in abbreviations_lang}
        for word in words:
            for lang in abbreviations_lang:
                if word.lower() in abbreviations[lang]:
                    abbreviations_in_message[lang].append(word.lower())

        # don't do anything if there are no abbreviations in the message
        if not any(abbreviations_in_message.values()):
            return

        buttons = discord.ui.View()
        for lang in abbreviations_in_message:
            for word in abbreviations_in_message[lang]:
                label = f"{word} : {abbreviations[lang][word]}"
                buttons.add_item(discord.ui.Button(label=label, style=discord.ButtonStyle.blurple, disabled=True))

        # create a webhook to send the message
        webhook = await message.channel.create_webhook(name="Abbreviation Explainer")

        # if the message is a reply, create a reply embed
        embed = None
        if message.reference:
            reference = await message.channel.fetch_message(message.reference.message_id)
            embed = discord.Embed(
                                    description=await self.bot._(
                                        message.guild.id,
                                        "wormhole.reply_to",
                                        link=reference.jump_url,
                                    ),
                                    colour=0x2F3136,  # 2F3136
                                ).set_footer(
                                    text=reference.content, icon_url=reference.author.display_avatar
                                )

        # resend the message with the abbreviations explained
        await webhook.send(
            message.content,
            username=message.author.display_name,
            avatar_url=message.author.avatar.url if message.author.avatar else None,
            view=buttons,
            wait=True,
            embed=embed
        )

        # delete the original message
        await message.delete()

        # delete the webhook
        await webhook.delete()

