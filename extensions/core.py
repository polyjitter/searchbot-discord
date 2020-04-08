# -*- coding: utf-8 -*-

# tacibot core
# Handles all important main features of any bot.

'''Core File'''

import math
import os
import sys
import time
from typing import List, Optional

import asyncio
import cpuinfo
import discord
from discord.ext import commands
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
        if bot.custom_help:
            bot.help_command = TaciHelpCommand()
        bot.help_command.cog = self

    def _create_tutorial(self, guild) -> str:
        """Creates the tutorial message."""

        prefixes: str = f"`@{self.bot.user.name}`"
        if self.bot.prefix:
            others: str = ', '.join(f'`{p}`' for p in self.bot.prefix)
            prefixes += f', {others}'

        msg: str = (
            f"**Hi!** Thanks for adding me to `{guild.name}`.\n\n"
            f"I'm **{self.bot.user.name}** - _{self.bot.description}_\n\n"
            f"My prefix{'es are' if self.bot.prefix else ' is'}: "
            f"{prefixes}.\n\n"
            "You may find more information with `help`.\n\n"
            "You may also find our support server and repo with `about`"
        )

        if 'extensions.botlist' in self.extensions_list:
            msg += ", or vote and review this bot with `vote`.\n\n"
        else:
            msg += ".\n\n"

        msg += (
            "_Please note that this bot may log errors, guild names, "
            "command calls/contents, and the names of command users "
            "for debug and maintenance purposes. "
            "These logs are shared with nobody "
            "other than those who help develop this bot. "
            "If you do not agree to this, please remove this bot._\n\n"
            "_You may recall this message at any time with `tutorial`._"
        )

        return msg

    # function lifted from StackOverflow
    def _humanbytes(self, B) -> str:
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
        else:
            return 'ERROR'

    @commands.command(aliases=['info', 'source', 'server'])
    async def about(self, ctx):
        """Returns information about this bot."""

        # Header
        msg = (
            f"__**{self.bot.user.name}**__ - _{self.bot.description}_\n"
            "Written in `discord.py`.\n\n"
            f"This instance by **{self.bot.appinfo.owner}.**\n\n"
        )

        # Repo and support server
        if self.bot.repo:
            msg += f"**Source Code:** _<{self.bot.repo}>_\n"
        if self.bot.support_server:
            msg += f"**Support Server:** _<{self.bot.support_server}>_\n\n"

        # Properly handle blank prefixes
        if ctx.prefix == '':
            prefix: str = ''
        else:
            prefix: str = f"**{ctx.prefix}**"

        # Footer
        msg += (
            f"_See {prefix}`help` for help, `invite` to add the bot, "
            "and `stats` for statistics._"
        )

        # Sending
        await ctx.send(msg)

    @commands.command(aliases=['addbot', 'connect', 'join'])
    async def invite(self, ctx):
        """Gets a link to invite this bot to your server."""

        msg = (
            "**Thanks for checking me out!**\n\n"
            "Use the following link to add me:\n"
            "*<https://discordapp.com/oauth2/authorize"
            f"?client_id={self.bot.user.id}&scope=bot"
        )

        if self.bot.perms:
            msg += f"&permissions={self.bot.perms}>*"
        else:
            msg += ">*"

        await ctx.send(msg)

    @commands.command()
    async def tutorial(self, ctx):
        """Resends the tutorial message."""
        if ctx.guild:
            msg: str = self._create_tutorial(ctx.guild)
        else:
            msg: str = "**Cannot send tutorial in DMs!**"

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
Number of bot commands: {len(self.bot.commands)}
Number of extensions present: {len(self.bot.cogs)}
Guild count: {len(self.bot.guilds)}
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
    async def extend(self, ctx, name: str = None):
        """Provides status of extensions & hotswaps extensions."""

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

    @commands.command()
    @commands.is_owner()
    async def toggle_debug(self, ctx):
        """Toggles debug while running."""

        self.bot.debug_toggle = not self.bot.debug_toggle
        await ctx.send(f"Set debug mode to `{self.bot.debug_toggle}`.")

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
                "_If you want me back, add me or get an admin to._"
            )
            await ctx.guild.leave()
        else:
            await ctx.send(
                "**Can't leave!** _This channel is not inside a guild._"
            )

    def cog_unload(self):
        self.bot.help_command = self._original_help_command

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """Sends owner notification and guild tutorial."""

        # Prerequisites
        guild_msg: str = self._create_tutorial(guild)
        channel: Optional[discord.TextChannel] = None
        owner: discord.Member = guild.owner

        # Tutorial Message
        # Get text channels
        text_channels = []
        for c in guild.channels:
            if type(c) is discord.TextChannel:
                text_channels.append(c)

        # Sets channel to general if it exists
        for c in guild.channels:
            if c.name == 'general':
                channel = c

        # XXX This looks like garbage
        # Else posts in first open channel
        if not channel:
            for c in guild.channels:
                if c.permissions_for(guild.me).send_messages:
                    channel = c

        # Send tutorial message
        if channel:
            await channel.send(guild_msg)
        else:
            guild_msg += (
                "\n\n_I am sending this message to you as there were no "
                "channels I could send messages to in your server. "
                "Please give me send message permissions in the channels "
                "You wish to use me in!_"
            )

            await owner.send(guild_msg)
            return  # Ends here if there are no good channels to send to

        # Owner Disclosure
        # Message Building
        owner_msg = (
            "**Hi there!**\n\n"
            f"I am **{self.bot.user.name}** - _{self.bot.description}_\n\n"
            "I am messaging you to inform you I was added to your server, "
            f"`{guild.name}`, by someone "
            "with **Manage Server** permissions.\n\n"
            f"I have sent a tutorial message to `{channel.name}` "
            "describing how I may be used.\n\n"
            "If you do not wish to have me there, "
            "simply kick me from the server.\n\n"
            "_Thanks for your time!_"
        )

        # Send owner disclosure
        await owner.send(owner_msg)


def setup(bot):
    bot.add_cog(Core(bot))
