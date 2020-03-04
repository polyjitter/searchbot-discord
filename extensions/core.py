# -*- coding: utf-8 -*-

# tacibot core
# Handles all important main features of any bot.

'''Core File'''

import discord
import os
from discord.ext import commands
import time
import asyncio
import sys
import cpuinfo
import math
import psutil
from extensions.models.help import TaciHelpCommand


class Core(commands.Cog):
    """Provides all core features of a bot."""

    def __init__(self, bot):

        # Main Stuff
        self.bot = bot
        self.extensions_list = bot.extensions_list
        self.emoji = "\U0001F4E6"

        # Help Command
        self._original_help_command = bot.help_command
        if bot.config['CUSTOM_HELP']:
            bot.help_command = TaciHelpCommand()
        bot.help_command.cog = self

    def _humanbytes(self, B) -> str:  # function lifted from StackOverflow
        """Return the given bytes as a human friendly KB, MB, GB, or TB string."""

        B = float(B)
        KB = float(1024)
        MB = float(KB ** 2)  # 1,048,576
        GB = float(KB ** 3)  # 1,073,741,824
        TB = float(KB ** 4)  # 1,099,511,627,776

        if B < KB:
            return '{0} {1}'.format(
                B, 'Bytes' if 0 == B > 1 else 'Byte')
        elif KB <= B < MB:
            return '{0:.2f} KB'.format(B/KB)
        elif MB <= B < GB:
            return '{0:.2f} MB'.format(B/MB)
        elif GB <= B < TB:
            return '{0:.2f} GB'.format(B/GB)
        elif TB <= B:
            return '{0:.2f} TB'.format(B/TB)

    @commands.command(aliases=['info', 'source', 'server'])
    async def about(self, ctx):
        """Returns information about this bot."""

        msg = f"__**{self.bot.user.name}**__ - _{self.bot.description}_\n\n"
        msg += f"This instance by **{self.bot.appinfo.owner}.**\n\n"
        if self.bot.config['REPO']:
            msg += f"**Source Code:** _<{self.bot.config['REPO']}>_\n"
        if self.bot.config['SERVER:']:
            msg += f"**Support Server:** _<{self.bot.config['SERVER']}>_\n\n"
        msg += "_Note: Please attempt to contact the hoster of any separate instances before this server._\n"
        msg += f"_See **{ctx.prefix}**`help` for help, `invite` to add the bot, and `stats` for statistics._"

        await ctx.send(msg)

    @commands.command(aliases=['addbot', 'connect', 'join'])
    async def invite(self, ctx):
        """Gets a link to invite this bot to your server."""

        msg = (
            "**Thanks for checking me out!**\n\n"
            "Use the following link to add me:\n"
            f"*<https://discordapp.com/oauth2/authorize?client_id={self.bot.user.id}&scope=bot"
        )

        if self.bot.config['PERMS'] is not None:
            msg += f"&permissions={self.bot.config['PERMS']}>*"
        else:
            msg += ">*"

        await ctx.send(msg)

    @commands.command()
    async def stats(self, ctx):
        """Provides statistics on the bot itself."""

        mem = psutil.virtual_memory()
        currproc = psutil.Process(os.getpid())
        total_ram = self._humanbytes(mem[0])
        available_ram = self._humanbytes(mem[1])
        usage = self._humanbytes(currproc.memory_info().rss)
        msg = f"""
```
Total RAM: {total_ram}
Available RAM: {available_ram}
RAM used by bot: {usage}
Number of bot commands: {len(ctx.bot.commands)}
Number of extensions present: {len(ctx.bot.cogs)}
```
"""
        await ctx.send(msg)

    @commands.command()
    async def ping(self, ctx):
        """Checks the ping of the bot."""

        before = time.monotonic()
        pong = await ctx.send("...")
        after = time.monotonic()
        ping = (after - before) * 1000
        await pong.edit(content="`PING discordapp.com {}ms`".format(int(ping)))

    @commands.group(aliases=['extensions', 'ext'], 
                    invoke_without_command=True)
    @commands.is_owner()
    async def extend(self, ctx, name:str = None):
        """Provides status of extensions and lets you hotswap extensions."""

        # Provides status of extension
        if name is not None:
            status = "is" if name in self.extensions_list else "is not"
            msg = f"**{name}** {status} currently loaded and/or existent."

        # Handles empty calls
        else:
            msg = (
                "**Nothing was provided!**\n\n"
                "Please provide an extension name for status, "
                "or provide a subcommand."
            )

        # Sends completed message
        await ctx.send(msg)

    @extend.command(aliases=['le', 'l'])
    @commands.is_owner()
    async def load(self, ctx, name: str):
        """Load an extension into the bot."""
        m = await ctx.send(f'Loading {name}')
        extension_name = f'extensions.{name}'
        if extension_name not in self.extensions_list:
            try:
                self.bot.load_extension(extension_name)
                self.extensions_list.append(extension_name)
                await m.edit(content='Extension loaded.')
            except Exception as e:
                await m.edit(
                    content=f'Error while loading {name}\n`{type(e).__name__}: {e}`')
        else:
            await m.edit(content='Extension already loaded.')

    @extend.command(aliases=["ule", "ul"])
    @commands.is_owner()
    async def unload(self, ctx, name: str):
        """Unload an extension from the bot."""

        m = await ctx.send(f'Unloading {name}')
        extension_name = f'extensions.{name}'
        if extension_name in self.extensions_list:
            self.bot.unload_extension(extension_name)
            self.extensions_list.remove(extension_name)
            await m.edit(content='Extension unloaded.')
        else:
            await m.edit(content='Extension not found or not loaded.')

    @extend.command(aliases=["rle", "rl"])
    @commands.is_owner()
    async def reload(self, ctx, name: str):
        """Reload an extension of the bot."""

        m = await ctx.send(f'Reloading {name}')
        extension_name = f'extensions.{name}'
        if extension_name in self.extensions_list:
            self.bot.unload_extension(extension_name)
            try:
                self.bot.load_extension(extension_name)
                await m.edit(content='Extension reloaded.')
            except Exception as e:
                self.extensions_list.remove(extension_name)
                await m.edit(
                    content=f'Failed to reload extension\n`{type(e).__name__}: {e}`')
        else:
            await m.edit(content='Extension isn\'t loaded.')

    @extend.command(name='list')
    async def list_cmd(self, ctx):
        """Lists all extensions loaded by the bot."""

        # Message Construction
        msg = "**Loaded Extensions**\n\n"
        msg += '\n'.join(f'`{e}`' for e in self.extensions_list)
        msg += "\n\n_See the other subcommands of this command to manage them._"

        # Message Sending
        await ctx.send(msg)

    @commands.command(aliases=['exit', 'reboot'])
    @commands.is_owner()
    async def restart(self, ctx):
        """Turns the bot off."""

        await ctx.send(":zzz: **Restarting...**")
        exit()

    @commands.command()
    @commands.is_owner()
    async def leave(self, ctx):
        """Makes the bot leave the server this was called in."""
        
        if ctx.guild:
            await ctx.send(
                "\U0001F4A8 **Leaving server.** "
                "_If you want me back, add me or get an admin to._")
            await ctx.guild.leave()
        else:
            await ctx.send(
                "**Can't leave!** _This channel is not inside a guild._")

    def cog_unload(self):
        self.bot.help_command = self._original_help_command


def setup(bot):
    bot.add_cog(Core(bot))
