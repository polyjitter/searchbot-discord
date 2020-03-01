# -*- coding: utf-8 -*-

# Botlist Reporting
# Reports statistics to various botlists.
# Not useful for redist instances.

'''Botlist Cog'''

import discord
import aiohttp
from discord.ext import commands, tasks
import dbl


class Botlist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.request = bot.request
        self.dbl_token = bot.config['DBL']
        self.dbots_token = bot.config['DBOTS']
        self.bod_token = bot.config['BOD']
        self.dblcom_token = bot.config['DBLCOM']
        self.dbl_client = dbl.DBLClient(
            self.bot, self.dbots_token)

    async def _update_logic(self):
        """Handles all statistic updating for various different bot lists."""

        dbots_call = "https://discord.bots.gg/api/v1"
        bod_call = "https://bots.ondiscord.xyz/bot-api/"
        dblcom_call = "https://discordbotlist.com/api"
        responses = {}

        # bots.discord.gg
        if self.dbots_token != '':
            dbots_call += f"/bots/{self.bot.user.id}/stats"
            dbots_data = {'guildCount': len(self.bot.guilds)}
            dbots_headers = {'Authorization': self.dbots_token}
            async with self.request.post(dbots_call, 
                                         json=dbots_data, 
                                         headers=dbots_headers) as resp:
                resp_json = await resp.json()
                print(resp_json)
                responses['dbots'] = resp_json

        # bots.ondiscord.xyz
        if self.bod_token != '':
            bod_call += f"/bots/{self.bot.user.id}/guilds"
            bod_data = {'guildCount': len(self.bot.guilds)}
            bod_headers = {'Authorization': self.bod_token}
            async with self.request.post(bod_call, 
                                         json=bod_data,
                                         headers=bod_headers) as resp:
                resp_json = await resp.json()
                print(resp_json)
                responses['bod'] = resp_json

        # discordbotlist.com
        if self.dblcom_token != '':
            dblcom_call += f"/bots/{self.bot.user.id}/stats"
            dblcom_data = {'guilds': len(self.bot.guilds)}
            dblcom_headers = {'Authorization': self.dblcom_token}
            async with self.request.post(dblcom_call, 
                                         json=dblcom_data,
                                         headers=dblcom_headers) as resp:
                resp_json = await resp.json()
                print(resp_json)
                responses['dblcom'] = resp_json

        # top.gg
        if self.dbl_token != '':
            try:
                resp = await self.dbl_client.post_guild_count()
                responses['dbl'] = resp
            except Exception as e:
                responses['dbl'] = e

        # Finishing up
        return responses

    @commands.command()
    async def listupdate(self, ctx):
        """Updates statistics on botlists."""

        msg = await ctx.send("<a:loading:393852367751086090> **Updating...**")
        responses = await self._update_logic()
        print(responses)
        await msg.edit(content="**Updated!**")

    @tasks.loop(minutes=15.0)
    async def update_stats(self):
        responses = await self._update_logic()
        print(responses)

    async def cog_check(self, ctx):
        return (ctx.author.id == self.bot.appinfo.owner.id)


def setup(bot):
    bot.add_cog(Botlist(bot))
