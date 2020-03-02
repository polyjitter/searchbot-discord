import discord
import os
from discord.ext import commands
import time
import asyncio
import sys
import cpuinfo
import math
import psutil
import itertools


class Core(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.settings = {   
            'extensions': []
        }

        # 
        self._original_help_command = bot.help_command
        if bot.config['CUSTOM_HELP']:
            bot.help_command = HelpCommand()
        bot.help_command.cog = self

        self._init_extensions()

    def _init_extensions(self):
        """Initializes extensions."""

        for ext in os.listdir('extensions'):
            if ext.endswith('.py') and not ext.startswith('core'):
                try:
                    self.bot.load_extension(f'extensions.{ext[:-3]}')
                    self.settings['extensions'].append(
                        f'extensions.{ext[:-3]}')
                except:
                    pass

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

        msg = f"**{self.bot.description}**\n"
        msg += f"Created by **taciturasa#4365**, this instance by **{self.bot.appinfo.owner}.**\n\n"
        msg += "**Source Code:** _<https://github.com/taciturasa/searchbot-discord>_\n"
        msg += "**Support Server:** _<https://discord.gg/4BpReNV>_\n"
        msg += "_Note: Please attempt to contact the hoster of any separate instances before this server._\n\n"
        msg += f"_See **{ctx.prefix}** `help` for help, `invite` to add the bot, and `stats` for statistics._"

        await ctx.send(msg)

    @commands.command(aliases=['addbot', 'connect', 'join'])
    async def invite(self, ctx):
        """Gets a link to invite this bot to your server."""

        msg = (
            "**Thanks for checking me out!**\n\n"
            "Use the following link to add me:\n"
            f"*<https://discordapp.com/oauth2/authorize?client_id={self.bot.user.id}&scope=bot>*"
        )

        if self.bot.config['PERMS'] is not None:
            msg += f"&permissions={self.bot.config['PERMS']}"

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

    @commands.command()
    @commands.is_owner()
    async def load(self, ctx, name: str):
        """Load an extension into the bot."""
        m = await ctx.send(f'Loading {name}')
        extension_name = 'extensions.{0}'.format(name)
        if extension_name not in self.settings['extensions']:
            try:
                self.bot.load_extension(extension_name)
                self.settings['extensions'].append(extension_name)
                await m.edit(content='Extension loaded.')
            except Exception as e:
                await m.edit(
                    content=f'Error while loading {name}\n`{type(e).__name__}: {e}`')
        else:
            await m.edit(content='Extension already loaded.')

    @commands.command(aliases=["ule", "ul"])
    @commands.is_owner()
    async def unload(self, ctx, name: str):
        """Unload an extension from the bot."""

        m = await ctx.send(f'Unloading {name}')
        extension_name = 'extensions.{0}'.format(name)
        if extension_name in self.settings['extensions']:
            self.bot.unload_extension(extension_name)
            self.settings['extensions'].remove(extension_name)
            await m.edit(content='Extension unloaded.')
        else:
            await m.edit(content='Extension not found or not loaded.')

    @commands.command(aliases=["rle", "rl"])
    @commands.is_owner()
    async def reload(self, ctx, name: str):
        """Reload an extension of the bot."""

        m = await ctx.send(f'Reloading {name}')
        extension_name = 'extensions.{0}'.format(name)
        if extension_name in self.settings['extensions']:
            self.bot.unload_extension(extension_name)
            try:
                self.bot.load_extension(extension_name)
                await m.edit(content='Extension reloaded.')
            except Exception as e:
                self.settings['extensions'].remove(extension_name)
                await m.edit(
                    content=f'Failed to reload extension\n`{type(e).__name__}: {e}`')
        else:
            await m.edit(content='Extension isn\'t loaded.')

    @commands.command(aliases=['exit', 'reboot'])
    @commands.is_owner()
    async def restart(self, ctx):
        """Turns the bot off."""

        await ctx.send(':zzz: **Restarting.**')
        exit()

    def cog_unload(self):
        self.bot.help_command = self._original_help_command

class HelpCommand(commands.MinimalHelpCommand):
    def __init__(self, **options):
        super().__init__(**options)

    def add_bot_commands_formatting(self, commands, heading):
        if commands:
            self.paginator.add_line(f"**{heading}**")
            if heading == 'Main':
                self.paginator.add_line(", ".join(f"`{c.name}`" for c in commands))
            else:
                for c in commands:
                    self.paginator.add_line(f'`{c.name}` - _{c.short_doc}_')
        self.paginator.add_line()

    async def send_bot_help(self, mapping):
        ctx = self.context
        bot = ctx.bot

        if bot.description:
            self.paginator.add_line(bot.description, empty=True)

        note = self.get_opening_note()
        if note:
            self.paginator.add_line(note, empty=True)

        no_category = '\u200b{0.no_category}'.format(self)
        def get_category(command, *, no_category=no_category):
            cog = command.cog
            return cog.qualified_name if cog is not None else no_category

        filtered = await self.filter_commands(bot.commands, sort=True, key=get_category)
        to_iterate = itertools.groupby(filtered, key=get_category)

        main_cmds = []
        other_cmds = {}

        for category, commands in to_iterate:
            commands = sorted(commands, key=lambda c: c.name) if self.sort_commands else list(commands)
            if category in ['Core', 'Bot List']:
                main_cmds.extend(commands) 
            else:
                other_cmds[category] = commands
            
        self.add_bot_commands_formatting(main_cmds, 'Main')
        for category, commands in other_cmds.items():
            self.add_bot_commands_formatting(commands, category)

        note = self.get_ending_note()
        if note:
            self.paginator.add_line()
            self.paginator.add_line(note)

        await self.send_pages()



def setup(bot):
    bot.add_cog(Core(bot))
