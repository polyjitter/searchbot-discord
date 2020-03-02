# -*- coding: utf-8 -*-

# tacibot online util
# Provides utils for various online tools.

'''Online File'''

class Online():
    def __init__(self, bot):
        self.bot = bot
        self.request = bot.request

    async def hastebin(self, string):
        """Posts a string to hastebin."""

        url = "https://hastebin.com/documents"
        data = string.encode('utf-8')
        async with self.request.post(url=url, data=data) as haste_response:
            haste_key = (await haste_response.json())['key']
            haste_url = f"http://hastebin.com/{haste_key}"
        # data = {'sprunge': ''}
        # data['sprunge'] = string
        # haste_url = await self.aioclient.post(url='http://sprunge.us',
        # data=data)
        return haste_url

def setup(bot):
    bot.online = Online(bot)
