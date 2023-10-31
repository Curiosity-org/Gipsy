"""
Ce programme est régi par la licence CeCILL soumise au droit français et
respectant les principes de diffusion des logiciels libres. Vous pouvez
utiliser, modifier et/ou redistribuer ce programme sous les conditions
de la licence CeCILL diffusée sur le site "http://www.cecill.info".
"""

import discord
from discord.ext import commands
import re
from urllib.parse import urlparse, parse_qs

from utils import Gunibot, MyContext


async def setup(bot: Gunibot = None):
    await bot.add_cog(YoutubeTrackingRemover(bot))


class YoutubeTrackingRemover(commands.Cog):
    def __init__(self, bot: Gunibot):
        self.bot = bot
        self.file = "youtubeTrackingRemover"
        self.cache = {}
        self.bot.get_command("config").add_command(self.config_enable_youtube_tracking_remover)

    @commands.command(name="enable_youtube_tracking_remover")
    async def config_enable_youtube_tracking_remover(self, ctx: MyContext, value: bool):
        """Enable or disable the YouTube tracking remover"""
        await ctx.send(
            await self.bot.sconfig.edit_config(ctx.guild.id, "enable_youtube_tracking_remover", value)
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # obviously, not in DMs
        if not message.guild:
            return

        # check if server has enabled the youtube tracking remover
        if not self.bot.server_configs[message.guild.id].get("enable_youtube_tracking_remover", False):
            print("not enabled")
            return

        # check if message is not from a bot
        if message.author.bot:
            return

        # check if message contains a youtube.com link
        regex = r'(https?://(?:www\.)?youtube\.com/watch\?[^\s]+)'
        matches = re.findall(regex, message.content)

        content = message.content
        for match in matches:
            parsed_url = urlparse(match)
            query_params = parse_qs(parsed_url.query)
            new_match = match

            # replace the link with a link with only the video id
            if 'v' in query_params:
                video_id = query_params['v'][0]
                new_match = f'https://www.youtube.com/watch?v={video_id}'

            # re-add `time` and `t` parameters
            if 't' in query_params:
                time = query_params['t'][0]
                new_match = new_match + f'&t={time}'
            elif 'time' in query_params:
                time = query_params['time'][0]
                new_match = new_match + f'&time={time}'

            content = content.replace(match, f'{new_match}')

        # check for youtu.be links
        regex = r'(https?://(?:www\.)?youtu\.be/[^\s]+)'
        matches = re.findall(regex, message.content)

        for match in matches:
            parsed_url = urlparse(match)
            query_params = parse_qs(parsed_url.query)

            # remove every parameters
            new_match = match.split('?')[0]

            # re-add `time` and `t` parameters
            if 't' in query_params:
                time = query_params['t'][0]
                new_match = new_match + f'?t={time}'
            elif 'time' in query_params:
                time = query_params['time'][0]
                new_match = new_match + f'?time={time}'

            content = content.replace(match, f'{new_match}')

        if content == message.content:
            # no need to send a message if it will be the same
            return

        # create a webhook
        webhook = await message.channel.create_webhook(name="Youtube Tracking Remover")

        # send the message with the replaced links
        webhook_message = await webhook.send(content,
                                             username=message.author.display_name,
                                             avatar_url=message.author.display_avatar.url,
                                             files=[await attachment.to_file() for attachment in message.attachments],
                                             wait=True)

        # add the view
        await webhook_message.edit(view=YoutubeTrackingRemoverView(self.bot, webhook_message, webhook, message.author.id))

        # delete the original message
        await message.delete()


class YoutubeTrackingRemoverView(discord.ui.View):
    def __init__(self, bot: Gunibot, message: discord.WebhookMessage, webhook: discord.Webhook, original_user_id: int):
        super().__init__(timeout=300)
        self.bot = bot
        self.message = message
        self.webhook = webhook
        self.original_user_id = original_user_id

    # pylint: disable=unused-argument
    @discord.ui.button(emoji='❓', style=discord.ButtonStyle.green)
    async def button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            await self.bot._(interaction.guild_id, "youtube_tracking_remover.message"),
            ephemeral=True)

    # pylint: disable=unused-argument
    @discord.ui.button(emoji='🗑️', style=discord.ButtonStyle.red)
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        # check if the user is the author of the message
        if interaction.user.id != self.original_user_id:
            return await interaction.response.send_message(
                await self.bot._(interaction.guild_id, "youtube_tracking_remover.not_author"),
                ephemeral=True)
        else:
            await interaction.message.delete()

    async def on_timeout(self):
        try:
            await self.message.edit(view=None)
            await self.webhook.delete()
        except discord.NotFound:
            pass
