# -*- coding: utf-8 -*-

# Speciality Search
# Provides search for specific sites.
# Developed by source#5843.

'''Search Cog'''

import aiohttp
import discord
from discord.ext import commands
from urllib import parse


class SpecialtySearch(commands.Cog, name="Specialty"):
    """Provides specialty search tools for various different specific sites."""

    def __init__(self, bot):

        # Main Stuff
        self.bot = bot
        self.info = bot.logging.info
        self.warn = bot.logging.warn
        self.request = bot.request
        self.emoji = "\u2728"

    @commands.command(aliases=['urban', 'ud'])
    async def urbandictionary(self, ctx, *, query: str):
        """Look up terms on Urban Dictionary."""

        # Handling
        async with ctx.typing():

            number = 1

            if " | " in query:
                query, number = query.rsplit(" | ", 1)
            search = parse.quote(query)

            async with self.request.get(f"http://api.urbandictionary.com/v0/define?term={search}") as resp:

                resp = await resp.json()

                query = discord.utils.escape_mentions(query)
                query = discord.utils.escape_markdown(query)

                if not resp["list"]:
                    await ctx.send(f"`{query}`` couldn't be found on Urban Dictionary.")
                else:
                    try:
                        top_result = resp["list"][int(number) - 1]
                        embed = discord.Embed(
                            title=top_result["word"],
                            description=top_result["definition"][0:425] + "...",
                            url=top_result["permalink"],
                            color=ctx.author.color
                        )
                        if top_result["example"]:
                            embed.add_field(name="Example:",
                                            value=top_result["example"][0:100] + "...", inline=False)
                        embed.add_field(
                            name="👍", value=top_result["thumbs_up"])
                        embed.add_field(
                            name="👎", value=top_result["thumbs_down"])

                        embed.set_author(name=top_result["author"],
                                         icon_url="https://apprecs.org/gp/images/app-icons/300/2f/info.tuohuang.urbandict.jpg")
                        number = str(int(number) + 1)
                        embed.set_footer(text=str(len(
                            resp["list"])) + f" results were found. To see a different result, use {ctx.prefix}ud {query} | {number}.")
                        try:

                            await ctx.send(
                                f"**{top_result['word']}** - "
                                f"<{top_result['permalink']}>",
                                embed=embed
                            )

                        except Exception:
                            await ctx.send(top_result["definition"])
                    except Exception as e:
                        print(e)

    @commands.command()
    async def anime(self, ctx, *, query: str):
        """Look up anime information."""
        base = "https://kitsu.io/api/edge/"

        # Handling
        async with ctx.typing():
            async with self.request.get(base + "anime", params={"filter[text]": query}) as resp:

                resp = await resp.json()
                resp = resp['data']

                query = discord.utils.escape_mentions(query)
                query = discord.utils.escape_markdown(query)

                if not resp:
                    return await ctx.send(f"No results for `{query}`.")

                anime = resp[0]
                title = f'{anime["attributes"]["canonicalTitle"]}'
                anime_id = anime["id"]
                url = f"https://kitsu.io/anime/{anime_id}"
                thing = '' if not anime['attributes'][
                    'endDate'] else f' to {anime["attributes"]["endDate"]}'

                embed = discord.Embed(
                    title=f"{title}",
                    color=ctx.author.color,
                    rl=url
                )
                embed.description = anime["attributes"]["synopsis"][0:425] + "..."
                embed.add_field(name="Average Rating",
                                value=anime["attributes"]["averageRating"])
                embed.add_field(name="Popularity Rank",
                                value=anime["attributes"]["popularityRank"])
                embed.add_field(name="Age Rating",
                                value=anime["attributes"]["ageRating"])
                embed.add_field(
                    name="Status", value=anime["attributes"]["status"])

                embed.add_field(
                    name="Aired", value=f"{anime['attributes']['startDate']}{thing}")
                embed.add_field(name="Episodes",
                                value=anime['attributes']["episodeCount"])
                embed.add_field(
                    name="Type", value=anime['attributes']["showType"])
                embed.set_thumbnail(
                    url=anime['attributes']["posterImage"]["original"])
                embed.set_footer(
                    text=f"Requested by {ctx.author.name} | Powered by kitsu.io", icon_url=ctx.author.avatar_url_as(format="png"))
                try:

                    await ctx.send(f"**{title}** - <{url}>", embed=embed)

                except:
                    aired = f"{anime['attributes']['startDate']}{thing}"
                    template = f"""
url: {url}
Title: {title}
Average Rating: {anime["attributes"]["averageRating"]}
Popularity Rank: {anime["attributes"]["popularityRank"]}
Age Rating: {anime["attributes"]["ageRating"]}
Status: {anime["attributes"]["status"]}
Aired: {aired}
Type: {anime['attributes']["showType"]}


Powered by kitsu.io"""
                    await ctx.send(template)

    @commands.command()
    async def manga(self, ctx, *, query: str):
        """Look up manga information."""

        base = "https://kitsu.io/api/edge/"

        # Handling
        async with ctx.typing():
            async with self.request.get(base + "manga", params={"filter[text]": query}) as resp:

                resp = await resp.json()
                resp = resp['data']

                query = discord.utils.escape_mentions(query)
                query = discord.utils.escape_markdown(query)

                if not resp:
                    return await ctx.send(f"No results for `{query}`.")

                manga = resp[0]
                title = f'{manga["attributes"]["canonicalTitle"]}'
                manga_id = manga["id"]
                url = f"https://kitsu.io/manga/{manga_id}"

                embed = discord.Embed(
                    title=f"{title}", color=ctx.author.color, url=url)
                embed.description = manga["attributes"]["synopsis"][0:425] + "..."
                if manga["attributes"]["averageRating"]:
                    embed.add_field(name="Average Rating",
                                    value=manga["attributes"]["averageRating"])
                embed.add_field(name="Popularity Rank",
                                value=manga["attributes"]["popularityRank"])
                if manga["attributes"]["ageRating"]:
                    embed.add_field(name="Age Rating",
                                    value=manga["attributes"]["ageRating"])
                embed.add_field(
                    name="Status", value=manga["attributes"]["status"])
                thing = '' if not manga['attributes'][
                    'endDate'] else f' to {manga["attributes"]["endDate"]}'
                embed.add_field(
                    name="Published", value=f"{manga['attributes']['startDate']}{thing}")
                if manga['attributes']['chapterCount']:
                    embed.add_field(name="Chapters",
                                    value=manga['attributes']["chapterCount"])
                embed.add_field(
                    name="Type", value=manga['attributes']["mangaType"])
                embed.set_thumbnail(
                    url=manga['attributes']["posterImage"]["original"])

                try:

                    await ctx.send(f"**{title}** - <{url}>", embed=embed)

                except Exception :

                    aired = f"{manga['attributes']['startDate']}{thing}"
                    template = f"""
url: {url}
Title: {title}
Average Rating: {manga["attributes"]["averageRating"]}
Popularity Rank: {manga["attributes"]["popularityRank"]}
Age Rating: {manga["attributes"]["ageRating"]}
Status: {manga["attributes"]["status"]}
Aired: {aired}
Type: {manga['attributes']["showType"]}


Powered by kitsu.io"""
                    await ctx.send(template)


def setup(bot):
    bot.add_cog(SpecialtySearch(bot))
