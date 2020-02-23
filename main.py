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
    '''Custom Bot Class that overrides the commands.ext one'''

    def __init__(self, **options):
        super().__init__(self.get_prefix_new, **options)
        print('Performing initialization...\n')

        # Get Config Values
        with open('config.json') as f:
            self.config = json.load(f)
            self.prefix = self.config.get('PREFIX')
            self.version = self.config.get('VERSION')
            self.maintenance = self.config.get('MAINTENANCE')

        # Get Instances
        with open('searxes.txt') as f:
            self.instances = f.read().split('\n')

        print('Initialization complete.\n\n')

    async def get_prefix_new(self, bot, msg):
        if isinstance(msg.channel, discord.DMChannel) and self.config['PREFIXLESS_DMS']:
            plus_none = self.prefix.copy()
            plus_none.append('')
            return commands.when_mentioned_or(*plus_none)(bot, msg)
        else:
            return commands.when_mentioned_or(*self.prefix)(bot, msg)

    def init_extensions(self):
        for ext in os.listdir('extensions'):
            if ext.endswith('.py'):
                self.load_extension(f'extensions.{ext[:-3]}')

    async def start(self, *args, **kwargs):
        async with aiohttp.ClientSession() as self.request:
            self.init_extensions()
            await super().start(*args, **kwargs)

    async def on_ready(self):
        appinfo = await self.application_info()

        msg = "CONNECTED!\n"
        msg += "-----------------------------\n"
        msg += f"ACCOUNT: {bot.user}\n"
        msg += f"OWNER: {appinfo.owner}\n"
        msg += "-----------------------------\n"

        print(msg)

    async def on_message(self, message):
        mentions = [self.user.mention, f'<@!{self.user.id}>']
        ctx = await self.get_context(message)

        if message.author.bot:
            return
        elif message.author.id in self.config.get('BLOCKED'):
            return
        elif self.maintenance and not message.author.is_owner():
            return
        elif message.content in mentions:
            assist_msg = (
                "**Hi there! How can I help?**\n\n"
                # Two New Lines Here
                f"You may use **{self.user.mention} `term here`** to search,"
                f"or **{self.user.mention} `help`** for assistance.")
            await ctx.send(assist_msg)
        else:
            await self.process_commands(message)


bot = Bot(
    description='search - a tiny little search utility bot for discord.',
    case_insensitive=True)


@bot.listen()
async def on_command_error(ctx, error):

    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.CommandInvokeError):
        # TODO Ensure old code functions

        error = error.original
        _traceback = traceback.format_tb(error.__traceback__)
        _traceback = ''.join(_traceback)
        appinfo = await bot.application_info()

        embed_fallback = f"**An error occured: {type(error).__name__}. Please contact {appinfo.owner}.**"

        error_embed = discord.Embed(
            title=f"{type(error).__name__}",
            color=0xFF0000,
            description=(
                "This is (probably) a bug. This has been not been automatically "
                f"reported, so please give **{appinfo.owner}** a heads-up in DMs.")
        )

        trace_content = (
            "```py\n\nTraceback (most recent call last):"
            "\n{}{}: {}```").format(
                _traceback,
                type(error).__name__,
                error)

        error_embed.add_field(
            name="`{}` in command `{}`".format(
                type(error).__name__, ctx.command.qualified_name),
            value=(trace_content[:1018] + '...```')
            if len(trace_content) > 1024
            else trace_content)
        await ctx.send(embed_fallback, embed=error_embed)
    else:
        await ctx.send(error)

bot.run(bot.config['TOKEN'])
