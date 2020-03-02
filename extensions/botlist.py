# -*- coding: utf-8 -*-

# Botlist Reporting
# Reports statistics to various botlists.
# Not useful for redist instances.

'''Botlist Cog'''

import discord
import aiohttp
from discord.ext import commands, tasks
import dbl


class BotList(commands.Cog, name='Bot List'):
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

    @commands.command(aliases=['review'])
    async def vote(self, ctx):
        """Review and vote for us on various botlists!"""

        msg = (
            "**Thank you for wanting to help us out!**\n"
            "You can find us on the following lists:\n\n"
        )
        if self.dbots_token != '':
            msg += f"_bots.discord.gg_ <https://bots.discord.gg/bots/{self.bot.user.id}/>\n"
        if self.bod_token != '':
            msg += f"_bots.ondiscord.xyz_ <https://bots.ondiscord.xyz/bots/{self.bot.user.id}/>\n"
        if self.dblcom_token != '':
            msg += f"_discordbotlist.com_ <https://discordbotlist.com/bots/{self.bot.user.id}/>\n"
        if self.dbl_token != '':
            msg += f"_top.gg_ <https://top.gg/bot/{self.bot.user.id}/>\n"

        await ctx.send(msg)

    @commands.command()
    @commands.is_owner()
    async def listupdate(self, ctx):
        """Updates statistics on botlists."""

        msg = await ctx.send("<a:loading:393852367751086090> **Updating...**")
        responses = await self._update_logic()
        print(responses)
        await msg.edit(content="**Updated!**")

    @tasks.loop(minutes=15.0)
    async def update_stats(self):
        """Automatically updates statistics every 15 minutes."""
        
        responses = await self._update_logic()
        print(responses)


def setup(bot):
    bot.add_cog(BotList(bot))
