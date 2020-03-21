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
import sys
import asyncio
import aiohttp
import rethinkdb
from typing import List, Optional


class Bot(commands.Bot):
    """Custom Bot Class that subclasses the commands.ext one"""

    def __init__(self, **options):
        """Initializes the main parts of the bot."""

        # Initializes parent class
        super().__init__(self._get_prefix_new, **options)

        # Setup
        self.extensions_list: List[str] = []

        with open('config.json') as f:
            self.config = json.load(f)

            # Info
            self.prefix: List[str] = self.config['PREFIX']
            self.version: str = self.config['VERSION']
            self.description: str = self.config['DESCRIPTION']
            self.repo: str = self.config['REPO']
            self.support_server: str = self.config['SERVER']
            self.perms: int = self.config['PERMS']
            if not self.config['CACHE']:
                self.max_messages = None

            # Toggles
            self.maintenance: bool = self.config['MAINTENANCE']
            self.case_insensitive: bool = self.config['CASE_INSENSITIVE']
            self.custom_help: bool = self.config['CUSTOM_HELP']
            self.mention_assist: bool = self.config['MENTION_ASSIST']
            self.prefixless_dms: bool = self.config['PREFIXLESS_DMS']

        # RethinkDB
        if self.config['RETHINK']['DB']:
            self.re = rethinkdb.RethinkDB()
            self.re.set_loop_type('asyncio')
            self.rdb: str = self.config['RETHINK']['DB']
            self.conn = None
            self.rtables: List[str] = []

    def _init_extensions(self):
        """Initializes extensions."""

        # Utils
        # Avoids race conditions with online
        utils_dir = os.listdir('extensions/utils')
        if 'online.py' in utils_dir:
            utils_dir.remove('online.py')
            bot.load_extension('extensions.utils.online')

        # Rest of utils
        for ext in utils_dir:
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

    async def _init_rethinkdb(self):
        """Initializes RethinkDB."""

        # Prerequisites
        dbc = self.config['RETHINK']

        # Error handling the initialization
        try:
            # Create connection
            self.conn = await self.re.connect(
                host=dbc['HOST'],
                port=dbc['PORT'],
                db=dbc['DB'],
                user=dbc['USERNAME'],
                password=dbc['PASSWORD']
            )

            # Create or get database
            dbs = await self.re.db_list().run(self.conn)
            if self.rdb not in dbs:
                print('Database not present. Creating...')
                await self.re.db_create(self.rdb).run(self.conn)

            # Append any existing tables to rtables
            tables = await self.re.db(self.rdb).table_list().run(self.conn)
            self.rtables.extend(tables)

        # Exit if fails bc bot can't run without db
        except Exception as e:
            print('RethinkDB init error!\n{}: {}'.format(type(e).__name__, e))
            sys.exit(1)

        print('RethinkDB initialisation successful.')

    async def _get_prefix_new(self, bot, msg):
        """More flexible check for prefix."""

        # Adds empty prefix if in DMs
        if isinstance(msg.channel, discord.DMChannel) and self.prefixless_dms:
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

        # Maintenance Mode
        if self.maintenance:
            await self.change_presence(
                activity=discord.Activity(
                    name="Maintenance",
                    type=discord.ActivityType.watching
                ),
                status=discord.Status.dnd
            )
        else:
            await self.change_presence(
                activity=discord.Activity(
                    name=f"@{self.user.name}",
                    type=discord.ActivityType.listening
                ),
                status=discord.Status.online
            )

        # NOTE Rethink Entry Point
        # Initializes all rethink stuff
        if hasattr(self, 'rdb') and not self.rtables:
            await self._init_rethinkdb()

        # NOTE Extension Entry Point
        # Loads core, which loads all other extensions
        if not self.extensions_list:
            self._init_extensions()

        print('Initialized.\n')

        # Logging
        msg = "ALL ENGINES GO!\n"
        msg += "-----------------------------\n"
        msg += f"ACCOUNT: {bot.user}\n"
        msg += f"OWNER: {self.appinfo.owner}\n"
        msg += "-----------------------------\n"
        print(msg)

        await self.logging.info(content=msg, name="On Ready")

    async def on_message(self, message):
        """Handles what the bot does whenever a message comes across."""

        # Prerequisites
        mentions = [self.user.mention, f'<@!{self.user.id}>']
        ctx = await self.get_context(message)

        # Avoid warnings while loading
        if not hasattr(bot, 'appinfo'):
            return

        # Handling
        # Turn away bots
        elif message.author.bot:
            return

        # Ignore blocked users
        elif message.author.id in self.config.get('BLOCKED'):
            return

        # Maintenance mode
        elif (
            self.maintenance 
            and not message.author.id == bot.appinfo.owner.id
        ):
            return

        # Empty ping for assistance
        elif message.content in mentions and self.mention_assist:
            assist_msg = (
                "**Hi there! How can I help?**\n\n"
                # Two New Lines Here
                f"You may use **{self.user.mention}** `term here` to search, "
                f"or **{self.user.mention}** `help` for assistance.")
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
    if (
        isinstance(error, commands.CommandNotFound)
        or isinstance(error, commands.CheckFailure)
    ):
        return

    # Provides a very pretty embed if something's actually a dev's fault.
    elif isinstance(error, commands.CommandInvokeError):

        # Prerequisites
        embed_fallback = (
            f"**An error occured: {type(error).__name__}. "
            f"Please contact {bot.appinfo.owner}.**"
        )
        error_embed = await bot.logging.error(
            error, ctx,
            ctx.command.cog.qualified_name if ctx.command.cog.qualified_name
            else "DMs"
        )

        # Sending
        await ctx.send(embed_fallback, embed=error_embed)

    # If anything else goes wrong, just go ahead and send it in chat.
    else:
        await bot.logging.error(
            error, ctx,
            ctx.command.cog.qualified_name if ctx.command.cog.qualified_name
            else "DMs"
        )
        await ctx.send(error)
# NOTE Bot Entry Point
# Starts the bot
print("Connecting...\n")
bot.run(bot.config['TOKEN'])