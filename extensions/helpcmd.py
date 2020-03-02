# -*- coding: utf-8 -*-

# tacibot helpcmd
# Provides a new custom help command with some pretty formatting

'''HelpCmd File'''

import discord
from discord.ext import commands
import itertools

class TaciHelpCommand(commands.MinimalHelpCommand):
    def __init__(self, **options):

        # Main Stuff
        super().__init__(**options)
        self.command_attrs['help'] = "Find more assistance on this bot."
        self.subcommands_heading = "Subcommands"

    def get_opening_note(self):
        """Provides the header for all help commands."""

        # Prerequisites
        bot = self.context.bot

        # __**name v0.0**__ - _description_
        return f"__**{bot.user.name} v{bot.config['VERSION']}**__ - _{bot.description}_"

    def get_ending_note(self):
        """Provides the footer for all help commands."""

        # Prerequisites
        command_name = self.invoked_with

        return (
            "_For more info, see "
            # `prefix!command [category/command/subcommand]`
            f"`{self.clean_prefix}{command_name} [category/command/subcommand]`._"
        )

    def get_command_signature(self, command):
        """Gets the syntax string for a command."""

        # **`prefix!command [parameters]`**
        return f"**`{self.clean_prefix}{command.qualified_name} {command.signature}`**"

    def add_aliases_formatting(self, aliases):
        """Adds a listing of aliases to a command help."""

        # _Aliases: `alias1`, `alias2`, `alias3`_
        self.paginator.add_line(
            f"_{self.aliases_heading} {','.join(f'`{a}`' for a in aliases)}_"
        )

    def add_command_formatting(self, command):
        """Creates the help for the main command in a command help."""

        # Usually unused
        if command.description:
            self.paginator.add_line(command.description, empty=True)

        # **`prefix!command [parameters]`**
        signature = self.get_command_signature(command)

        # _Aliases: `alias1`, `alias2`, `alias3`_
        if command.aliases:
            self.paginator.add_line(signature)
            self.add_aliases_formatting(command.aliases)
        else:
            self.paginator.add_line(signature, empty=True)

        # Anything from the help, which is usually from the command's docstring
        if command.help:
            try:
                self.paginator.add_line(command.help, empty=True)
            except RuntimeError:
                for line in command.help.splitlines():
                    self.paginator.add_line(line)
                self.paginator.add_line()

    def add_subcommand_formatting(self, command):
        """Adds the entry for each subcommand under a cog or group."""

        # `command` - description OR `command`
        if command.short_doc:
            line = f"`{command.qualified_name}` - {command.short_doc}"
        else:
            line = f"`{command.qualified_name}`"
        self.paginator.add_line(line)

    def add_bot_commands_formatting(self, commands, heading):
        """Adds the entry for each cog and command in the main help."""

        if commands:
            # **Cog Name**
            self.paginator.add_line(f"**{heading}**")

            # TODO Make the Core Dynamic
            if heading == '\U0001F4E6  Core':
                # `command1`, `command2`, `command3`
                # On Same Line
                self.paginator.add_line(", ".join(f"`{c.name}`" for c in commands))
            else:
                # `command` - description
                # On new lines
                for c in commands:
                    self.paginator.add_line(f"`{c.name}` - {c.short_doc}")
            
            # New Line
            self.paginator.add_line()

    async def send_bot_help(self, mapping):
        """Sends the entire help for the bot."""

        # Prerequisites
        ctx = self.context
        bot = ctx.bot
        main_cmds = []
        other_cmds = {}

        # Adds the header if there
        note = self.get_opening_note()
        if note:
            self.paginator.add_line(note, empty=True)

        # Gets the category for each command in the bot
        no_category = '\u200b{0.no_category}'.format(self)
        def get_category(command, *, no_category=no_category):
            cog = command.cog
            if cog is not None:
                return f"{cog.emoji}  {cog.qualified_name}" if cog.emoji else cog.qualified_name
            else:
                return no_category

        # Gets all commands and categories to iterate over
        filtered = await self.filter_commands(bot.commands, sort=True, key=get_category)
        to_iterate = itertools.groupby(filtered, key=get_category)

        # Splits Bot List and Core commands out of the others
        for category, commands in to_iterate:
            commands = sorted(commands, key=lambda c: c.name) if self.sort_commands else list(commands)
            if category in ['\U0001F4E6  Core', '\U0001F5F3  Bot List']:
                main_cmds.extend(commands) 
            else:
                other_cmds[category] = commands
        
        # Core/Bot List commands become compacted
        self.add_bot_commands_formatting(main_cmds, '\U0001F4E6  Core')

        # Everything else is normal
        for category, commands in other_cmds.items():
            self.add_bot_commands_formatting(commands, category)

        # Adds the footer if there
        note = self.get_ending_note()
        if note:
            self.paginator.add_line(note)

        # Sends the completed help output
        await self.send_pages()

    async def send_cog_help(self, cog):
        """Sends the help for a cog."""

        # Adds the header if there
        note = self.get_opening_note()
        if note:
            self.paginator.add_line(note, empty=True)
            # New Line

        # **Cog Name**
        self.paginator.add_line(
            f"{cog.emoji}  **{cog.qualified_name}**" if cog.emoji else f"{cog.qualified_name}")

        # _Description if there_
        if cog.description:
            self.paginator.add_line(f"_{cog.description}_", empty=True)

        # Lists all commands in the cog
        filtered = await self.filter_commands(cog.get_commands(), sort=self.sort_commands)
        if filtered:
            for command in filtered:
                self.add_subcommand_formatting(command)

        # Adds the footer if there
        note = self.get_ending_note()
        if note:
            self.paginator.add_line()  # New Line
            self.paginator.add_line(note)

        # Sends the completed help output
        await self.send_pages()

    async def send_group_help(self, group):      
        """Sends the help for a command group."""

        # Adds the header if there
        note = self.get_opening_note()
        if note:
            self.paginator.add_line(note, empty=True)
            # New Line

        # Adds the formatting for the main group command 
        self.add_command_formatting(group)

        # Adds any subcommands
        filtered = await self.filter_commands(group.commands, sort=self.sort_commands)
        if filtered:
            # **Subcommands** (or subcommands_heading)
            self.paginator.add_line(f"**{self.subcommands_heading}**")
            # Adds each subcommand entry
            for command in filtered:
                self.add_subcommand_formatting(command)

        # Adds the footer if there 
        note = self.get_ending_note()
        if note:
            self.paginator.add_line()  # New Line
            self.paginator.add_line(note)

        # Sends the completed help output
        await self.send_pages()

    async def send_command_help(self, command):
        """Sends the help for a single command."""

        # Adds the header if there
        note = self.get_opening_note()
        if note:
            self.paginator.add_line(note, empty=True)
            # New Line

        # Adds the formatting for the command
        self.add_command_formatting(command)

        # Adds the footer if there
        note = self.get_ending_note()
        if note:
            self.paginator.add_line(note)

        # Sends the completed help output.
        self.paginator.close_page()  # TODO What does this do?
        await self.send_pages()