# -*- coding: utf-8 -*-

# Search Functionality
# Provides search results from SearX

'''Search Cog'''

import discord
from discord.ext import commands
import aiohttp
import random
import sys

class Search(commands.Cog):
    def  __init__(self, bot):
        self.bot = bot
        self.request = bot.request
        self.instances = bot.instances

    async def _search_logic(self, query: str, is_nsfw: bool = False, category: str = None):
        """Provides search logic for all search commands."""

        # WARNING - This list includes slurs.
        nono_words = [
            'tranny', 'faggot', 'fag',
            'porn', 'cock', 'dick',
            'titty', 'boob', 'penis',
            'slut', 'cum', 'jizz',
            'semen', 'cooch', 'coochie',
            'pussy', 'penis', 'fetish',
            'bdsm'
        ]
        nono_sites = [
            'xvideos', 'pornhub'
        ]

        if not is_nsfw:
            for i in nono_words:
                if i in query:
                    return (
                        "**Sorry!** That query included language "
                        "we cannot accept in a non-NSFW channel. "
                        "Please try again in an NSFW channel."
                    )

        # Choose an instance
        if self.instances == []:
            with open('searxes.txt') as f:
                self.instances = f.read().split('\n')
        instance = random.sample(self.instances, k=1)[0]
        print(f"Attempting to use {instance}")

        # Error Template
        error_msg = ("**An error occured!**\n\n"
            f"There was a problem with `{instance}`. Please try again later.\n"
            f"_If problems with this instance persist, contact`{self.bot.appinfo.owner}` to have it removed._")

        # Create the URL to make an API call to
        call = f'{instance}/search?q={query}&format=json&language=en-US'

        # If a type is provided, add that type to the call URL
        if category:
            call += f'&category={category}'

        if is_nsfw:
            call += f'&safesearch=0'
        else:
            call += f'&safesearch=1'

        # Make said API call
        try:
            async with self.request.get(call) as resp:
                response = await resp.json()
        except aiohttp.ClientError:
            return error_msg

        # Split our response data up for parsing
        # infoboxes = response['infoboxes']
        results = response['results']

        # Create message with results
        try:
            # Handle tiny result count
            if len(results) > 5:
                amt = 5
            else:
                amt = len(results)

            if not is_nsfw:
                for r in results[0:7]:
                    for n in nono_sites:
                        if n in r['url']:
                            results.remove(r)

            # Header
            msg = f"Showing **{amt}** results for `{query}`. \n\n"
            # Expanded Result
            msg += (
                f"**{results[0]['title']}** <{results[0]['url']}>\n"
                f"{results[0]['content']}\n\n")
            # Other Results
            msg += "\n".join(
                [f"**{entry['title']}** <{entry['url']}>" for entry in results[1:5]])
            # Instance Info
            msg += f"\n\n_Results retrieved from instance `{instance}`._"
        
        # Reached if error with returned results
        except (KeyError, IndexError) as e:
            # Logging
            print(f"{e} with instance {instance}, trying again.")

            self.instances.remove(instance) # Weed the instance out
            return await self._search_logic(query, is_nsfw) # Recurse until good response

        return msg
    
    @commands.command()
    async def search(self, ctx, *, query: str):
        """Search online for results."""

        # Logging
        print(f"\n\nNEW CALL: {ctx.author} from {ctx.guild}.\n")

        # Handling
        async with ctx.typing():
            msg = await self._search_logic(query, ctx.channel.is_nsfw())
            await ctx.send(msg)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Listener makes no command fallback to searching."""

        if isinstance(error, commands.CommandNotFound) or \
            isinstance(error, commands.CheckFailure):
            # Logging
            print(f"\n\nNEW CALL: {ctx.author} from {ctx.guild}.\n")

            # Handling
            async with ctx.typing():
                # Prepares term
                term = ctx.message.content.replace(ctx.prefix, '', 1)
                term = term.lstrip(' ')
                # Does search
                msg = await self._search_logic(term, ctx.channel.is_nsfw())
                # Sends result
                await ctx.send(msg)


def setup(bot):
    bot.add_cog(Search(bot))