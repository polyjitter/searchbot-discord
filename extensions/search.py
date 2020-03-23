# -*- coding: utf-8 -*-

# Search Functionality
# Provides search results from SearX

'''Search Cog'''

import discord
from discord.ext import commands
import aiohttp
import random
import sys
from typing import List


class Search(commands.Cog):
    """Searches the web for a variety of different resources."""

    def __init__(self, bot):

        # Main Stuff
        self.bot = bot
        self.info = bot.logging.info
        self.warn = bot.logging.warn
        self.request = bot.request
        self.emoji = "\U0001F50D"

        # Get Instances
        with open('searxes.txt') as f:
            self.instances = f.read().split('\n')


    async def _search_logic(self, query: str, is_nsfw: bool = False,
                            category: str = None) -> str:
        """Provides search logic for all search commands."""

        # NSFW Filtering
        # WARNING - This list includes slurs.
        nono_words = [
            'tranny', 'faggot', 'fag',
            'porn', 'cock', 'dick',
            'titty', 'boob', 'penis',
            'slut', 'cum', 'jizz',
            'semen', 'cooch', 'coochie',
            'pussy', 'penis', 'fetish',
            'bdsm', 'sexy', 'xxx',
            'orgasm', 'masturbation',
            'erotic', 'creampie',
            'fap', 'nude', 'orgasm',
            'squirting', 'yiff',
            'e621'
        ]
        nono_sites = [
            'xvideos', 'pornhub',
            'xhamster', 'xnxx',
            'youporn', 'xxx',
            'freexcafe', 'sex.com',
            'e621'
        ]

        if not is_nsfw:
            for i in nono_words:
                if i in query.replace(" ", ""):
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

        # Error Template
        error_msg = (
            "**An error occured!**\n\n"
            f"There was a problem with `{instance}`. Please try again later.\n"
            f"_If problems with this instance persist, contact`{self.bot.appinfo.owner}` to have it removed._"
        )

        # Create the URL to make an API call to
        call = f'{instance}search?q={query}&format=json&language=en-US'

        # If a type is provided, add that type to the call URL
        if category:
            call += f'&categories={category}'

        if is_nsfw:
            call += '&safesearch=0'
        else:
            call += '&safesearch=1'

        # Figure out engines for different categories to get decent results.
        if category == 'videos':
            call += '&engines=bing+videos,google+videos'
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

            query = discord.utils.escape_mentions(query)
            query = discord.utils.escape_markdown(query)

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

            return msg

        # Reached if error with returned results
        except (KeyError, IndexError) as e:
            # Logging
            await self.warn(
                f"A user encountered a(n) `{e}` with <{instance}> when searching for `{query}`. "
                "Consider removing it or looking into it.",
                name="Failed Instance"
            )

            self.instances.remove(instance)  # Weed the instance out
            # Recurse until good response
            return await self._search_logic(query, is_nsfw)

    async def _instance_check(self, instance: str, content: dict) -> bool:
        """Checks the quality of an instance."""

        # Makes sure proper values exist
        if 'error' in content:
            return False
        if not ('engines' in content and 'initial' in content['timing']):
            return False
        if not ('google' in content['engines'] and 'enabled' in content['engines']['google']):
            return False

        # Makes sure google is enabled
        if not content['engines']['google']['enabled']:
            return False

        # Makes sure is not Tor
        if content['network_type'] != 'normal':
            return False

        # Only picks instances that are fast enough
        timing = int(content['timing']['initial'])
        if timing > 0.20:
            return False

        # Check for Google captcha
        test_search = f'{instance}/search?q=test&format=json&lang=en-US'
        try:
            async with self.request.get(test_search) as resp:
                response = await resp.json()
            response['results'][0]['content']
        except (aiohttp.ClientError, KeyError, IndexError):
            return False

        # Reached if passes all checks
        return True

    @commands.command()
    async def search(self, ctx, *, query: str):
        """Search online for general results."""

        async with ctx.typing():
            msg = await self._search_logic(query, ctx.channel.is_nsfw())
            await self.info(
                content=f"**{ctx.author}** searched for `{query}` in \"{ctx.guild}\" and got this:"
                f"\n\n{msg}",
                name="Search Results"
            )
            await ctx.send(msg)

    @commands.command(aliases=['video'])
    async def videos(self, ctx, *, query: str):
        """Search online for videos."""

        async with ctx.typing():
            msg = await self._search_logic(query, ctx.channel.is_nsfw(), 'videos')
            await self.info(
                content=f"**{ctx.author}** searched for `{query}` videos in \"{ctx.guild}\" and got this:"
                f"\n\n{msg}",
                name="Search Results"
            )
            await ctx.send(msg)

    @commands.command()
    async def music(self, ctx, *, query: str):
        """Search online for music."""

        async with ctx.typing():
            msg = await self._search_logic(query, ctx.channel.is_nsfw(), 'music')
            await self.info(
                content=f"**{ctx.author}** searched for `{query}` music in \"{ctx.guild}\" and got this:"
                f"\n\n{msg}",
                name="Search Results"
            )
            await ctx.send(msg)

    @commands.command(aliases=['file'])
    async def files(self, ctx, *, query: str):
        """Search online for files."""

        async with ctx.typing():
            msg = await self._search_logic(query, ctx.channel.is_nsfw(), 'files')
            await self.info(
                content=f"**{ctx.author}** searched for `{query}` files in \"{ctx.guild}\" and got this:"
                f"\n\n{msg}",
                name="Search Results"
            )
            await ctx.send(msg)

    @commands.command(aliases=['image'])
    async def images(self, ctx, *, query: str):
        """Search online for images."""

        # Handling
        async with ctx.typing():
            msg = await self._search_logic(query, ctx.channel.is_nsfw(), 'images')
            await self.info(
                content=f"**{ctx.author}** searched for `{query}` images in \"{ctx.guild}\" and got this:"
                f"\n\n{msg}",
                name="Search Results"
            )
            await ctx.send(msg)

    @commands.command()
    async def it(self, ctx, *, query: str):
        """Search online for IT-related information."""

        # Handling
        async with ctx.typing():
            msg = await self._search_logic(query, ctx.channel.is_nsfw(), 'it')
            await self.info(
                content=f"**{ctx.author}** searched for `{query}` IT in \"{ctx.guild}\" and got this:"
                f"\n\n{msg}",
                name="Search Results"
            )
            await ctx.send(msg)

    @commands.command(aliases=['map'])
    async def maps(self, ctx, *, query: str):
        """Search online for map information."""

        # Handling
        async with ctx.typing():
            msg = await self._search_logic(query, ctx.channel.is_nsfw(), 'map')
            await self.info(
                content=f"**{ctx.author}** searched for `{query}` maps in \"{ctx.guild}\" and got this:"
                f"\n\n{msg}",
                name="Search Results"
            )
            await ctx.send(msg)

    @commands.command()
    @commands.is_owner()
    async def rejson(self, ctx):
        """Refreshes the list of instances for searx."""

        msg = await ctx.send('<a:updating:403035325242540032> Refreshing instance list...\n\n'
                             '(Due to extensive quality checks, this may take a bit.)')
        plausible: List[str] = []

        # Get, parse, and quality check all instances
        async with self.request.get('https://searx.space/data/instances.json') as r:
            # Parsing
            searx_json = await r.json()
            instances = searx_json['instances']

            # Quality Check
            for i in instances:
                content = instances.get(i)
                is_good: bool = await self._instance_check(i, content)
                if is_good:
                    plausible.append(i)

        # Save new list
        self.instances = plausible
        with open('searxes.txt', 'w') as f:
            f.write('\n'.join(plausible))

        await msg.edit(content='Instances refreshed!')

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Listener makes no command fallback to searching."""

        if isinstance(error, commands.CommandNotFound) or \
                isinstance(error, commands.CheckFailure):

            # Handling
            async with ctx.typing():
                # Prepares term
                term = ctx.message.content.replace(ctx.prefix, '', 1)
                term = term.lstrip(' ')
                # Does search
                is_nsfw = ctx.channel.is_nsfw() if hasattr(ctx.channel, 'is_nsfw') else False
                msg = await self._search_logic(term, is_nsfw)

                # Logging
                await self.info(
                    content=f"**{ctx.author}** searched for `{term}` in \"{ctx.guild}\" and got this:"
                    f"\n\n{msg}",
                    name="Search Results"
                )


                # Sends result
                await ctx.send(msg)


def setup(bot):
    bot.add_cog(Search(bot))
