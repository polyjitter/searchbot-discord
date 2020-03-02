# -*- coding: utf-8 -*-

# search - a tiny little search utility bot for discord.
# All original work by taciturasa, with some code by ry00001.
# Used and modified with permission.
# See LICENSE for license information.

'''Main File'''

import discord
from discord.ext import commands
import traceback
import json
import os
import asyncio
import aiohttp
import random


class Bot(commands.Bot):
    """Custom Bot Class that subclasses the commands.ext one"""

    def __init__(self, **options):
        """Initializes the main parts of the bot."""

        # Logging
        print('Initializing...\n')

        # Initializes parent class
        super().__init__(self._get_prefix_new, **options)

        # Setup
        self.extensions_list = []
        with open('config.json') as f:
            self.config = json.load(f)
            self.prefix = self.config['PREFIX']
            self.version = self.config['VERSION']
            self.maintenance = self.config['MAINTENANCE']
            self.description = self.config['DESCRIPTION']
            self.case_insensitive = self.config['CASE_INSENSITIVE']

        # Get Instances
        with open('searxes.txt') as f:
            self.instances = f.read().split('\n')

        # Logging

    def _init_extensions(self):
        """Initializes extensions."""

        # Utils
        for ext in os.listdir('extensions/utils'):
            if ext.endswith('.py'):
                try:
                    bot.load_extension(f'extensions.utils.{ext[:-3]}')
                    self.extensions_list.append(
                        f'extensions.utils.{ext[:-3]}')
                except Exception as e:
                    print(e)

        # Models
        for ext in os.listdir('extensions/models'):
            if ext.endswith('.py'):
                try:
                    bot.load_extension(f'extensions.models.{ext[:-3]}')
                    self.extensions_list.append(
                        f'extensions.models.{ext[:-3]}')
                except Exception as e:
                    print(e)

        # Extensions
        for ext in os.listdir('extensions'):
            if ext.endswith('.py'):
                try:
                    bot.load_extension(f'extensions.{ext[:-3]}')
                    self.extensions_list.append(
                        f'extensions.{ext[:-3]}')
                except Exception as e:
                    print(e)
        

    async def _get_prefix_new(self, bot, msg):
        """More flexible check for prefix."""

        # Adds empty prefix if in DMs
        if isinstance(msg.channel, discord.DMChannel) and self.config['PREFIXLESS_DMS']:
            plus_empty = self.prefix.copy()
            plus_empty.append('')
            return commands.when_mentioned_or(*plus_empty)(bot, msg)
        # Keeps regular if not
        else:
            return commands.when_mentioned_or(*self.prefix)(bot, msg)

    async def on_ready(self):
        """Initializes the main portion of the bot once it has connected."""

        print('Connected.\n')

        # Prerequisites
        if not hasattr(self, 'request'):
            self.request = aiohttp.ClientSession()
        if not hasattr(self, 'appinfo'):
            self.appinfo = await self.application_info()
        if self.description == '':
            self.description = self.appinfo.description

        # NOTE Extension Entry Point
        # Loads core, which loads all other extensions
        if self.extensions_list == []:
            self._init_extensions()

        print('Initialized.\n')

        # Logging
        msg = "ALL ENGINES GO!\n"
        msg += "-----------------------------\n"
        msg += f"ACCOUNT: {bot.user}\n"
        msg += f"OWNER: {self.appinfo.owner}\n"
        msg += "-----------------------------\n"
        print(msg)

    async def on_message(self, message):
        """Handles what the bot does whenever a message comes across."""

        # Prerequisites
        mentions = [self.user.mention, f'<@!{self.user.id}>']
        ctx = await self.get_context(message)

        # Handling
        # Turn away bots
        if message.author.bot:
            return

        # Ignore blocked users
        elif message.author.id in self.config.get('BLOCKED'):
            return

        # Maintenance mode
        elif self.maintenance and not message.author.is_owner():
            return

        # Empty ping for assistance
        elif message.content in mentions and self.config.get('MENTION_ASSIST'):
            assist_msg = (
                "**Hi there! How can I help?**\n\n"
                # Two New Lines Here
                f"You may use **{self.user.mention} `term here`** to search, "
                f"or **{self.user.mention} `help`** for assistance.")
            await ctx.send(assist_msg)

        # Move on to command handling
        else:
            await self.process_commands(message)


# Creates Bot object
bot = Bot()


@bot.listen()
async def on_command_error(ctx, error):
    """Handles all errors stemming from ext.commands."""

    # Lets other cogs handle CommandNotFound.
    # Change this if you want command not found handling
    if isinstance(error, commands.CommandNotFound):
        return

    # Provides a very pretty embed if something's actually a dev's fault.
    elif isinstance(error, commands.CommandInvokeError):

        # Prerequisites
        original_error = error.original
        traceback_orig = traceback.format_tb(original_error.__traceback__)
        traceback_orig = ''.join(traceback_orig)
        appinfo = await bot.application_info()
        original_exc = traceback.format_exception(
            type(original_error), original_error, original_error.__traceback__)
        print(original_exc)

        # Main Message
        embed_fallback = f"**An error occured: {type(original_error).__name__}. Please contact {appinfo.owner}.**"

        # Hastebins Traceback
        try:
            url = await bot.online.hastebin(
                ''.join(original_exc))
        except Exception as e:
            url = None
            print(e)

        # Embed Building
        error_embed = discord.Embed(
            title=(
                f"{type(original_error).__name__} "
                f"{'(Click for Hastebin)' if url else ''}"
            ),
            url=url if url else None,
            color=0xFF0000,
            description=(  # TODO Change if has logging
                "This is (probably) a bug. This has not been automatically "
                f"reported, so please give **{appinfo.owner}** a heads-up in DMs.")
        )

        # Formats Traceback
        trace_content = (
            "```py\n\nTraceback (most recent call last):"
            "\n{}{}: {}```").format(
                traceback_orig,
                type(original_error).__name__,
                original_error)

        # Adds Traceback
        error_embed.add_field(
            name=(
                f"`{type(original_error).__name__}` in "
                f"command `{ctx.command.qualified_name}`"
            ),
            value=(trace_content[:1018] + '...```')
            if len(trace_content) > 1024
            else trace_content
        )

        # Sending
        await ctx.send(embed_fallback, embed=error_embed)

    # If anything else goes wrong, just go ahead and send it in chat.
    else:
        original_error = error
        original_exc = traceback.format_exception(
            type(original_error), original_error, original_error.__traceback__)
        print(''.join(original_exc))
        await ctx.send(error)
# NOTE Bot Entry Point
# Starts the bot
print("Connecting...\n")
bot.run(bot.config['TOKEN'])
