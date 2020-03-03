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
    """Provides various utilities for handling BotList stuff."""

    def __init__(self, bot):

        # Main Stuff
        self.bot = bot
        self.request = bot.request
        self.emoji = "\U0001F5F3"

        # List Tokens
        self.dbl_token = bot.config['DBL']
        self.dbots_token = bot.config['DBOTS']
        self.bod_token = bot.config['BOD']
        self.dblcom_token = bot.config['DBLCOM']

        # top.gg clent
        self.dbl_client = dbl.DBLClient(
            self.bot, self.dbl_token)

    async def _update_logic(self):
        """Handles all statistic updating for various different bot lists."""

        # Prerequisites
        dbots_call = "https://discord.bots.gg/api/v1"
        bod_call = "https://bots.ondiscord.xyz/bot-api/"
        dblcom_call = "https://discordbotlist.com/api"
        responses = {}

        # Calls
        # discord.bots.gg
        if self.dbots_token != '':

            # Call Prereqs
            dbots_call += f"/bots/{self.bot.user.id}/stats"
            dbots_data = {'guildCount': len(self.bot.guilds)}
            dbots_headers = {'Authorization': self.dbots_token}

            # Call Handling
            async with self.request.post(dbots_call,
                                         json=dbots_data,
                                         headers=dbots_headers) as resp:
                resp_json = await resp.json()
                responses['dbots'] = resp_json

        # bots.ondiscord.xyz
        if self.bod_token != '':

            # Call Prereqs
            bod_call += f"/bots/{self.bot.user.id}/guilds"
            bod_data = {'guildCount': len(self.bot.guilds)}
            bod_headers = {'Authorization': self.bod_token}

            # Call Handling
            async with self.request.post(bod_call,
                                         json=bod_data,
                                         headers=bod_headers) as resp:
                resp_json = await resp.json()
                responses['bod'] = resp_json

        # discordbotlist.com
        if self.dblcom_token != '':

            # Call Prereqs
            dblcom_call += f"/bots/{self.bot.user.id}/stats"
            dblcom_data = {'guilds': len(self.bot.guilds)}
            dblcom_headers = {'Authorization': f"Bot {self.dblcom_token}"}

            # Call Handling
            async with self.request.post(dblcom_call,
                                         json=dblcom_data,
                                         headers=dblcom_headers) as resp:
                responses['dblcom'] = resp.status

        # top.gg
        if self.dbl_token != '':
            # NOTE top.gg has a lib so it gets different handling.
            try:
                resp = await self.dbl_client.post_guild_count()
                responses['dbl'] = resp
            except Exception as e:
                responses['dbl'] = e

        # Finalization
        return responses

    # TODO Move to Core, hide behind check for any existing token
    @commands.command(aliases=['review'])
    async def vote(self, ctx):
        """Review and vote for this bot on various botlists."""

        # Header
        msg = (
            "**Thank you for wanting to help us out!**\n"
            "You can find us on the following lists:\n\n"
        )

        # Links
        # XXX This is really stupidly done, I'm going to find a way to redo it.
        if self.dbots_token != '':
            msg += f"_discord.bots.gg_ <https://discord.bots.gg/bots/{self.bot.user.id}/>\n"
        if self.bod_token != '':
            msg += f"_bots.ondiscord.xyz_ <https://bots.ondiscord.xyz/bots/{self.bot.user.id}/>\n"
        if self.dblcom_token != '':
            msg += f"_discordbotlist.com_ <https://discordbotlist.com/bots/{self.bot.user.id}/>\n"
        if self.dbl_token != '':
            msg += f"_top.gg_ <https://top.gg/bot/{self.bot.user.id}/>\n"

        # Sending
        await ctx.send(msg)

    @commands.command()
    @commands.is_owner()
    async def listupdate(self, ctx):
        """Updates statistics on botlists."""

        msg = await ctx.send("<a:loading:393852367751086090> **Updating...**")
        responses = await self._update_logic()
        print(responses)  # TODO Look at responses and figure out error handling
        await msg.edit(content="**Updated!**")

    @tasks.loop(minutes=15.0)
    async def update_stats(self):
        """Automatically updates statistics every 15 minutes."""

        responses = await self._update_logic()
        print(responses)  # TODO See other todo


def setup(bot):
    """Adds the cog to the bot."""
    bot.add_cog(BotList(bot))
