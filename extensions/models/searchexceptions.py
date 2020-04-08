# -*- coding: utf-8 -*-

# search exceptions
# Provides custom exceptions for the search cog.

"""Search Exceptions File"""

from discord.ext import commands


class SafesearchFail(commands.CommandError):
    """Thrown when a query contains NSFW content."""
    pass


def setup(bot):
    pass
