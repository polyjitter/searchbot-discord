# -*- coding: utf-8 -*-

# Better Logging
# Adds some better logging with utils.logging.

'''Better Logging Cog'''

import discord
from discord.ext import commands


class BetterLogging(commands.Cog):
    """Provides more logging for certain events with utils.logging."""

    def __init__(self, bot):

        # Main Stuff
        self.bot = bot
        self.request = bot.request
        self.emoji = "\U0001F4CB"

        # Loggers
        self.info = bot.logging.info
        self.warn = bot.logging.warn
        self.error = bot.logging.error
        self.debug = bot.logging.debug

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """Logs guild joining."""

        msg = f"\U0001F4C8  **Joined {guild.name}**\n\n"
        msg += f"_Owner:_ {guild.owner}\n"
        msg += f"_Member Count:_ {guild.member_count}\n\n"
        msg += f"_Guild Count now {len(self.bot.guilds)}._"

        await self.info(content=msg, name="Guild Join")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        """Logs guild leaving."""

        msg = f"**\U0001F4C9  Left {guild.name}**\n\n"
        msg += f"_Owner:_ {guild.owner}\n"
        msg += f"_Member Count:_ {guild.member_count}\n\n"
        msg += f"_Guild Count now {len(self.bot.guilds)}._"

        await self.info(content=msg, name="Guild Leave")

    @commands.Cog.listener()
    async def on_command(self, ctx):
        """Logs command calls."""

        msg = (
            f"**`{ctx.command.name}`** called by "
            f"**{ctx.author}** in _\"{ctx.guild if ctx.guild else 'DMs'}\"_."
        )

        await self.info(content=msg, name="Command Call")

    async def cog_check(self, ctx):
        return commands.is_owner()(ctx.command)


def setup(bot):
    bot.add_cog(BetterLogging(bot))
