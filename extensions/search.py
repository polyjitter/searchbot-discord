# -*- coding: utf-8 -*-

# Search Functionality
# Provides search results from Qwant

'''Search Cog'''

from typing import List

import discord
from discord.ext import commands
import html2text
import re
from urllib.parse import quote_plus

from extensions.models import searchexceptions
from extensions.models.regex import nono_re


class Search(commands.Cog, name="Basic"):
    """Searches the web for a variety of different resources."""

    def __init__(self, bot):

        # Main Stuff
        self.bot = bot
        self.info = bot.logging.info
        self.warn = bot.logging.warn
        self.debug = bot.logging.debug
        self.request = bot.request
        self.emoji = "\U0001F50D"
        self.scrape_token = bot.config['SCRAPESTACK']

        # Markdown converter
        self.tomd = html2text.HTML2Text()
        self.tomd.ignore_links = True
        self.tomd.ignore_images = True
        self.tomd.ignore_tables = True
        self.tomd.ignore_emphasis = True
        self.tomd.body_width = 0

    async def _search_logic(self, query: str, is_nsfw: bool = False,
                            category: str = 'web', count: int = 5) -> list:
        """Uses scrapestack and the Qwant API to find search results."""

        # Typing
        base: str
        safesearch: str

        # NSFW Filtering
        if nono_re.match(query) and not is_nsfw:
            raise searchexceptions.SafesearchFail('Query had NSFW.')

        base = "https://api.qwant.com/api"

        # Safesearch
        if is_nsfw:
            safesearch = "0"
        else:
            safesearch = "2"

        # Search URL Building
        # api.qwant.com/api/search/web?count=5&q=test&safesearch=2&...
        # XXX Find out why quote_plus wasn't working
        query_with_plus = query.replace(' ', '+')
        search_url = (
            f"{base}/search/{category}"
            f"?count={count}"
            f"&q={query_with_plus}"
            f"&safesearch={safesearch}"
            "&t=web"
            "&locale=en_US"
            "&uiv=4"
        )

        # Scrape or not
        if self.scrape_token != '':
            search_url = (
                "http://api.scrapestack.com/scrape"
                f"?access_key={self.scrape_token}"
                f"&url={quote_plus(search_url)}"
            )

        self.debug(search_url, name="_search_logic")

        # Searching
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:74.0)'
                ' Gecko/20100101 Firefox/74.0'
            )
        }
        async with self.request.get(search_url, headers=headers) as resp:
            to_parse = await resp.json()

            # Sends results
            return to_parse['data']['result']['items']

    async def _basic_search(self, ctx, query: str, category: str = 'web'):
        """Basic search formatting."""

        # NOTE Customizable count not yet implemented.
        count: int = 5

        # Safesearch variable
        is_nsfw = (
            ctx.channel.is_nsfw() if hasattr(ctx.channel, 'is_nsfw')
            else False
        )

        # Handling
        async with ctx.typing():

            # Searches
            results = await self._search_logic(query, is_nsfw, category)
            count = len(results)

            # Escapes all nasties for displaying
            query_display = discord.utils.escape_mentions(query)
            query_display = discord.utils.escape_markdown(query_display)

            # Return if no results
            try:
                results[0]
            except IndexError:
                return await ctx.send(
                    f"No results found for `{query_display}`."
                )

            # Gets the first entry's stuff
            first_title = self.tomd.handle(results[0]['title']).rstrip('\n')
            first_url = results[0]['url']
            first_desc = self.tomd.handle(results[0]['desc']).rstrip('\n')

            # Builds the substring for each of the other results.
            other_results: List[str] = []
            for r in results[1:count]:
                title = self.tomd.handle(r['title']).rstrip('\n')
                url = r['url']
                other_results.append(f"**{title}** {url}")
            other_msg: str = "\n".join(other_results)

            # Builds message
            msg = (
                f"Showing **{count}** results for `{query_display}`.\n\n"
                f"**{first_title}** {first_url}\n{first_desc}\n\n"
                f"{other_msg}\n\n_Powered by Qwant._"
            )

            msg = re.sub(
                r'(https?://(?:www\.)?[-a-zA-Z0-9@:%._+~#=]+\.'
                r'[a-zA-Z0-9()]+\b[-a-zA-Z0-9()@:%_+.~#?&/=]*)',
                r'<\1>',
                msg
            )


            # Sends message
            self.info(
                f"**New Search** - `{ctx.author}` in `{ctx.guild}`\n\n{msg}",
                name="New Search"
            )
            await ctx.send(msg)

    @commands.command()
    async def search(self, ctx, *, query: str):
        """Search online for general results."""

        await self._basic_search(ctx, query)

    # @commands.command(aliases=['video'])
    # async def videos(self, ctx, *, query: str):
    #     """Search online for videos."""

    #     await self._basic_search(ctx, query, 'videos')

    # @commands.command()
    # async def music(self, ctx, *, query: str):
    #     """Search online for music."""

    #     await self._basic_search(ctx, query, 'music')

    # @commands.command(aliases=['file'])
    # async def files(self, ctx, *, query: str):
    #     """Search online for files."""

    #     await self._basic_search(ctx, query, 'files')

    # @commands.command(aliases=['image'])
    # async def images(self, ctx, *, query: str):
    #     """Search online for images."""

    #     await self._basic_search(ctx, query, 'images')

    # @commands.command()
    # async def it(self, ctx, *, query: str):
    #     """Search online for IT-related information."""

    #     await self._basic_search(ctx, query, 'it')

    # @commands.command(aliases=['map'])
    # async def maps(self, ctx, *, query: str):
    #     """Search online for map information."""

    #     await self._basic_search(ctx, query, 'maps')

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Listener makes no command fallback to searching."""

        fallback = (commands.CommandNotFound, commands.CheckFailure)

        if isinstance(error, fallback):
            try:
                await self._basic_search(
                    ctx, ctx.message.content[len(ctx.prefix):]
                )
            except searchexceptions.SafesearchFail:
                await ctx.send(
                    "**Sorry!** That query included language "
                    "we cannot accept in a non-NSFW channel. "
                    "Please try again in an NSFW channel."
                )


def setup(bot):

    bot.add_cog(Search(bot))
