from typing import Union

import discord
from discord import ui

from utils import Gunibot


class GiveawayView(ui.View):
    "Public message allowing people to enter a giveaway"

    def __init__(self, bot: Gunibot, button_label: str, custom_id: str):
        super().__init__(timeout=None)
        self.bot = bot
        enter_btn = discord.ui.Button(label=button_label,
                                      style=discord.ButtonStyle.green,
                                      emoji="🎉",
                                      custom_id=custom_id)
        self.add_item(enter_btn)

    async def stop_giveaway(self, interaction: Union[discord.Message, discord.Interaction]):
        "Disable the view button and edit the message to show the giveaway is over"
        for child in self.children:
            child.disabled = True
        if isinstance(interaction, discord.Interaction):
            await interaction.followup.edit_message(
                interaction.message.id,
                content=interaction.message.content,
                embed=interaction.message.embeds[0],
                view=self
            )
        else:
            await interaction.edit(
                content=interaction.content,
                embed=interaction.embeds[0],
                view=self
            )
        super().stop()
