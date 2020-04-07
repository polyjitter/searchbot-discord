# -*- coding: utf-8 -*-

# search source
# Provides paginator sources for the search cog.

"""Search Source File"""

from typing import Callable, List, Tuple, Optional, Any

import discord
from discord.ext import menus
import html2text
import re

FetcherArgs = Tuple[Any]
Fetcher = Callable[..., List]

# Markdown converter
tomd = html2text.HTML2Text()
tomd.ignore_links = True
tomd.ignore_images = True
tomd.ignore_tables = True
tomd.ignore_emphasis = True
tomd.body_width = 0


# TODO Change around value names, make it general
class Result:
    """A class that holds the general data for a search result.

    Parameters:

    title (str): Title of the content.

    url (str): The direct link to the content.

    desc (str): The content's description.

    source (Optional[str]): The source site. Defaults to url. 

    image (Optional[str]): The content's image.
    """

    def __init__(self, title: str, url: str,
                 desc: str = "No description provided.",
                 source: Optional[str] = None,  image: Optional[str] = None):
        self.url = url
        if title in [None, ""]:
            self.title = "Unknown"
        else:
            self.title = title
        self.desc = desc
        self.source = source
        self.image = image

    def __repr__(self):
        fmt = f'<Image url={self.url} title={self.title} source={self.source}>'
        return fmt


class NormalSource(menus.AsyncIteratorPageSource):
    def __init__(self, query: str, fetcher: FetcherArgs, per_page: int,
                 header: str = "", footer: str = ""):
        self.header = header
        self.footer = footer
        self.query = query

        super().__init__(self._generate(fetcher), per_page=per_page)

    async def _generate(self, fetcher: Fetcher):
        offset = 0
        per_request = 10
        # TODO put the generation in the fetcher itself
        # Qwant: image - media, source - url, title - title
        while results := await fetcher(
                offset, per_request, self.query
            ):
            results
            for r in results:
                yield r
            offset += per_request

    async def format_page(self, menu, entries):
        start = menu.current_page * self.per_page

        # Escapes all nasties for displaying
        query_display = discord.utils.escape_mentions(self.query)
        query_display = discord.utils.escape_markdown(query_display)

        # Return if no results
        try:
            entries[0]
        except IndexError:
            return f"No results found for `{query_display}`."

        # Gets the first entry's stuff
        first_title = tomd.handle(entries[0].title).rstrip('\n')
        first_url = entries[0].url
        if start == 0:
            first_desc = tomd.handle(entries[0].desc).rstrip('\n')
            first = f"**{first_title}** {first_url}\n{first_desc}\n\n"
        else:
            first =  f"**{first_title}** {first_url}\n"

        # Builds the substring for each of the other results.
        other_results: List[str] = []

        for e in entries[1:5]:
            title = tomd.handle(e.title).rstrip('\n')
            url = e.url
            other_results.append(f"**{title}** {url}")

        other_msg = "\n".join(other_results)

        # Builds message
        msg = f"{first}{other_msg}"
        msg = re.sub(
            r'(https?://(?:www\.)?[-a-zA-Z0-9@:%._+~#=]+\.'
            r'[a-zA-Z0-9()]+\b[-a-zA-Z0-9()@:%_+.~#?&/=]*)',
            r'<\1>',
            msg
        )

        content = (
            f"{self.header}\n\n"
            f"Showing results *{start} - {start + 5}* "
            f"for `{self.query}`.\n\n"
            f"{msg}\n\n"
            f"{self.footer}"
        )

        return content


class ImageSource(menus.AsyncIteratorPageSource):
    def __init__(self, query: str, fetcher: FetcherArgs, args: FetcherArgs,
                 header: str = "", footer: str = ""):
        self.header = header
        self.footer = footer
        self.query = query
        super().__init__(self._generate(fetcher, args), per_page=1)

    async def _generate(self, fetcher: Fetcher, fetch_args: FetcherArgs):
        offset = 0
        per_request = 10
        # TODO put the generation in the fetcher itself
        # Qwant: image - media, source - url, title - title
        while results := await fetcher(
                offset, per_request, self.query, *fetch_args
            ):
            results
            for r in results:
                yield r
            offset += per_request

    async def format_page(self, menu, entry):
        start = menu.current_page * self.per_page

        content = (
            f"{self.header}\n\n"
            f"Showing image result `{start}` for `{self.query}``.\n\n"
            f"<{entry.image}>"
            f"{self.footer}\n\n"
        )

        embed = discord.Embed(
            title=entry.title,
            url=entry.image,
            description=entry.source
        )
        embed.set_image(url=entry.image)

        return {
            "content": content,
            "embed": embed
        }
