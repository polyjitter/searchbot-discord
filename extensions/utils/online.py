# -*- coding: utf-8 -*-

# tacibot online util
# Provides utils for various online tools.

'''Online File'''

import discord


class Online():
    """Provides various online utilities for your bot."""

    def __init__(self, bot):
        self.bot = bot
        self.request = bot.request

    async def hastebin(self, string):
        """Posts a string to hastebin."""

        url = "https://hasteb.in/documents"
        data = string.encode('utf-8')
        async with self.request.post(url=url, data=data) as haste_response:
            haste_key = (await haste_response.json())['key']
            haste_url = f"http://hasteb.in/{haste_key}"
        return haste_url

    def get_webhook(self, url: str):
        """Easily gets a webhook from a url."""

        return discord.Webhook.from_url(
            url,
            adapter=discord.AsyncWebhookAdapter(self.request)
        )


def setup(bot):
    bot.online = Online(bot)
