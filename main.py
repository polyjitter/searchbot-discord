# -*- coding: utf-8 -*-

# search - a tiny little search utility bot for discord
# Used and modified with permission
# All original work by taciturasa, with some code by ry00001.

'''Main File'''

import discord
from discord.ext import commands
import json
import aiohttp
import random


class Bot(commands.Bot):
    '''Custom Bot Class that overrides the commands.ext one'''

    def __init__(self, **options):
        super().__init__(self.get_prefix_new, **options)
        print('Performing initialization...\n')
        with open('config.json') as f:
            self.config = json.load(f)
            self.prefix = self.config.get('PREFIX')
            self.version = self.config.get('VERSION')
            self.maintenance = self.config.get('MAINTENANCE')
        print('Initialization complete.\n\n')
    
    async def get_prefix_new(self, bot, msg):
        return commands.when_mentioned_or(*self.prefix)(bot, msg)
    
    async def on_ready(self):
        self.appinfo = await bot.application_info()
        self.session = aiohttp.ClientSession()

        msg = "CONNECTED!\n"
        msg += "-----------------------------\n"
        msg += f"ACCOUNT: {bot.user}\n"
        msg += f"OWNER: {self.appinfo.owner}\n"
        msg += "-----------------------------\n"

        print(msg)

    async def on_message(self, message):
        if message.author.bot:
            return
        if message.author.id in self.config.get('BLOCKED'):
            return
        if (self.maintenance):
            return
        await self.get_context(message)
        await self.process_commands(message)

bot = Bot(
    description='search - a tiny little search utility bot for discord.',
    case_insensitive=True)

@bot.command()
async def search(ctx, *, query: str):
    """Search online for results."""
    async with ctx.typing():
        msg = search_logic(query)
        ctx.send(msg)

@bot.command()
@commands.is_owner()
async def rejson(ctx):
    '''Refreshes the list of instances for searx.'''

    msg = await ctx.send('Refreshing instance list...\n\n(Due to extensive quality checks, this may take a bit.)')
    plausible = []

    async with bot.session.get('https://searx.space/data/instances.json') as r:

        searx_json = await r.json()
        instances = searx_json['instances']

        for i in instances:
            info = instances.get(i)
            is_good = await instance_check(i, info)
            if is_good:
                plausible.append(i)

    with open('searxes.txt', 'w') as f:
        f.write('\n'.join(plausible))

    await msg.edit(content='Instances refreshed!')

async def search_logic(query: str):

    # Choose an instance
    with open('searxes.txt') as instances:
        instance = random.sample(instances.read().split('\n'), k=1)
        print(instance)

    error_msg = (f"There was a problem with `{instance[0]}`. Please contact "
            f"**{bot.appinfo.owner}** to have it removed.")

    # Create the URL to make an API call to
    call = f'{instance[0]}/search?q={query}&format=json&language=en-US'

    # Make said API call
    try:
        async with bot.session.get(call) as resp:
            response = await resp.json()
    except aiohttp.ClientError:
        return error_msg

    # Split our response data up for parsing
    # infoboxes = response['infoboxes']
    results = response['results']

    # Create message with results
    try:
        msg = f"Showing **5** results for `{query}`. \n\n"
        msg += (f"**{results[0]['title']}** <{results[0]['url']}>\n"
                f"{results[0]['content']}\n\n")
        msg += "\n".join(
            [f"**{entry['title']}** <{entry['url']}>" for entry in results[1:5]])
        msg += f"\n\n_Results retrieved from instance `{instance[0]}`._"
    except (KeyError, IndexError):
        print(response['results'])
        return error_msg

    # Send message
    return msg

async def instance_check(instance, info):
    '''Checks the quality of an instance.'''

    if 'error' in info:
        return False

    if not ('engines' in info and 'initial' in info['timing']):
        return False

    if not ('google' in info['engines'] and 'enabled' in info['engines']['google']):
        return False

    if not info['engines']['google']['enabled']:
        return False

    if info['network_type'] != 'normal':
        return False

    timing = int(info['timing']['initial'])
    if timing > 0.25:
        return False

    test_search = f'{instance}/search?q=test&format=json&language=en-US'

    # Check for Google captcha
    try:
        async with bot.session.get(test_search) as resp:
            response = await resp.json()
        response['results'][0]['content']
    except (aiohttp.ClientError, KeyError, IndexError):
        return False

    return True

@bot.listen("on_command_error")
async def on_command_error(ctx, error):

    if isinstance(error, commands.CommandNotFound):
        print(ctx.args)
        async with ctx.typing():
            term = ctx.message.content.replace(ctx.prefix, '', 1)
            term = term.lstrip(' ')
            msg = await search_logic(term)
            await ctx.send(msg)

    # elif isinstance(error, commands.CommandInvokeError):
    #     error = error.original
    #     _traceback = traceback.format_tb(error.__traceback__)
    #     _traceback = ''.join(_traceback)
    #     embed_fallback = "**ERROR: <@97788939196182528>**"

    #     error_embed = discord.Embed(
    #         title="An error has occurred.",
    #         color=0xFF0000,
    #         description=(
    #             "This is (probably) a bug. This has been automatically "
    #             f"reported, but give **{bot.appinfo.owner}** a heads-up in DMs.")
    #     )

    #     trace_content = (
    #         "```py\n\nTraceback (most recent call last):"
    #         "\n{}{}: {}```").format(
    #             _traceback,
    #             type(error).__name__,
    #             error)

    #     error_embed.add_field(
    #         name="`{}` in command `{}`".format(
    #             type(error).__name__, ctx.command.qualified_name),
    #         value=(trace_content[:1018] + '...```')
    #                if len(trace_content) > 1024
    #                else trace_content)
    #     await ctx.send(embed_fallback, embed=error_embed)

    else:
        await ctx.send(error)

bot.run(bot.config['TOKEN'])

