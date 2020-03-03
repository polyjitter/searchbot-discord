# -*- coding: utf-8 -*-

# tacibot logging util
# Provides utils for logging via webhooks.

'''Online File'''

import discord
from discord.ext.commands import Context
import traceback
from typing import Optional


class Logging():
    """Provides logging utilities for bots."""

    def __init__(self, bot):
        self.bot = bot
        self.request = bot.request
        self.online = bot.online
        self.maintenance = bot.maintenance

        # Sets info hook first
        self.info_hook = self.online.get_webhook(
            bot.config['INFO_HOOK'] if bot.config['INFO_HOOK']
            else None
        )

        # Sets other hooks or defaults them
        if self.info_hook:
            self.warn_hook = self.online.get_webhook(
                bot.config['WARN_HOOK'] if bot.config['WARN_HOOK']
                else self.info_hook
            )
            self.error_hook = self.online.get_webhook(
                bot.config['ERROR_HOOK'] if bot.config['ERROR_HOOK']
                else self.info_hook
            )
            self.debug_hook = self.online.get_webhook(
                bot.config['DEBUG_HOOK'] if bot.config['DEBUG_HOOK']
                else self.info_hook
            )

        # If no hooks, nothing is there
        else:
            self.warn_hook = self.error_hook = self.debug_hook = None

    async def _create_error_embed(self, error: Exception, ctx: Context):
        """Creates a new basic error embed."""

        # Prerequisites
        formatted_tb = traceback.format_tb(error.__traceback__)
        formatted_tb = ''.join(formatted_tb)
        original_exc = traceback.format_exception(
            type(error), error, error.__traceback__)

        # Hastebins Traceback
        try:
            url = await self.online.hastebin(
                ''.join(original_exc))
        except Exception as e:
            url = None
            print(e)

        # Embed Building
        error_embed = discord.Embed(
            title=(
                f"{type(error).__name__} "
                f"{'(Click for Hastebin)' if url else ''}"
            ),
            url=url if url else None,
            color=0xFF0000
        )

        # Formats Traceback
        trace_content = (
            "```py\n\nTraceback (most recent call last):"
            "\n{}{}: {}```").format(
                formatted_tb,
                type(error).__name__,
                error)

        # Adds Traceback
        error_embed.add_field(
            name=(
                f"`{type(error).__name__}` in "
                f"command `{ctx.command.qualified_name}`"
            ),
            value=(trace_content[:1018] + '...```')
            if len(trace_content) > 1024
            else trace_content
        )

        # Provides completed embed
        return error_embed

    async def info(self, content: str, 
                   embed: Optional[discord.Embed] = None, 
                   name: Optional[str] = None):
        """Logs info and sends it to the appropriate places."""

        if self.info_hook:
            return await self.info_hook.send(
                content=content,
                username=f"{self.bot.user.name} - {name if name else 'unknown'}",
                avatar_url=str(self.bot.user.avatar_url),
                embed=embed
            )
        else:
            return

    async def warn(self, content: str, 
                    embed: Optional[discord.Embed] = None, 
                    name: Optional[str] = None):
        """Logs warnings and sends them to the appropriate places."""

        if self.warn_hook:
            return await self.warn_hook.send(
                content=content,
                username=f"{self.bot.user.name} - {name if name else 'unknown'}",
                avatar_url=str(self.bot.user.avatar_url),
                embed=embed
            )
        else:
            return

    async def error(self, error: Exception, ctx: Context, name: Optional[str]):
        """Logs errors and sends them to the appropriate places."""

        # Prerequisites
        error_embed = await self._create_error_embed(error, ctx)

        # Log and say so
        if self.error_hook:

            # Log
            fallback = (
                f"**{ctx.author}** encountered a(n) "
                f"`{type(error).__name__}` when attempting to use "
                f"`{ctx.command}`."
            )
            await self.error_hook.send(
                content=fallback,
                username=f"{self.bot.user.name} - {name if name else 'unknown'}",
                avatar_url=str(self.bot.user.avatar_url),
                embed=error_embed
            )

            # Say so
            is_reported = "has been automatically reported, but"

        # Say hasn't been logged
        else:
            is_reported = "has not been automatically reported, so"

        # Added reported info and return
        error_embed.description = (
            f"This is (probably) a bug. This {is_reported} "
            f"please give **{self.bot.appinfo.owner}** a heads-up in DMs."
        )
        return error_embed

    async def debug(self, content: str, 
                    embed: Optional[discord.Embed] = None, 
                    name: Optional[str] = None):
        """Logs warnings and sends them to the appropriate places."""

        if self.debug_hook and self.maintenance:
            return await self.debug_hook.send(
                content=content,
                username=f"{self.bot.user.name} - {name if name else 'unknown'}",
                avatar_url=str(self.bot.user.avatar_url),
                embed=embed
            )
        else:
            return


def setup(bot):
    bot.logging = Logging(bot)
