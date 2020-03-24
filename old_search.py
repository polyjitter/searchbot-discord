# This is the old search logic for reference purposes 
 
    async def _old_search_logic(self, query: str, is_nsfw: bool = False,
                                category: str = None) -> str:
        """Provides search logic for all search commands."""

        # NSFW Filtering
        # WARNING - This list includes slurs.
        nono_words = [
            'tranny', 'faggot', 'fag',
            'porn', 'cock', 'dick',
            'titty', 'boob', 'penis',
            'slut', 'cum', 'jizz',
            'semen', 'cooch', 'coochie',
            'pussy', 'penis', 'fetish',
            'bdsm', 'sexy', 'xxx',
            'orgasm', 'masturbation',
            'erotic', 'creampie',
            'fap', 'nude', 'orgasm',
            'squirting', 'yiff',
            'e621'
        ]
        nono_sites = [
            'xvideos', 'pornhub',
            'xhamster', 'xnxx',
            'youporn', 'xxx',
            'freexcafe', 'sex.com',
            'e621', 'nhentai'
        ]

        if not is_nsfw:
            for i in nono_words:
                if i in query.replace(" ", ""):
                    return (
                        "**Sorry!** That query included language "
                        "we cannot accept in a non-NSFW channel. "
                        "Please try again in an NSFW channel."
                    )

        # Choose an instance
        if self.instances == []:
            with open('searxes.txt') as f:
                self.instances = f.read().split('\n')
        instance = random.sample(self.instances, k=1)[0]

        # Error Template
        error_msg = (
            "**An error occured!**\n\n"
            f"There was a problem with `{instance}`. Please try again later.\n"
            f"_If problems with this instance persist, "
            f"contact`{self.bot.appinfo.owner}` to have it removed._"
        )

        # Create the URL to make an API call to
        call = f'{instance}search?q={query}&format=json&language=en-US'

        # If a type is provided, add that type to the call URL
        if category:
            call += f'&categories={category}'

        if is_nsfw:
            call += '&safesearch=0'
        else:
            call += '&safesearch=1'

        # Figure out engines for different categories to get decent results.
        if category == 'videos':
            call += '&engines=bing+videos,google+videos'
        # Make said API call
        try:
            async with self.request.get(call) as resp:
                response = await resp.json()
        except aiohttp.ClientError:
            return error_msg

        # Split our response data up for parsing
        # infoboxes = response['infoboxes']
        results = response['results']

        # Create message with results
        try:
            # Handle tiny result count
            if len(results) > 5:
                amt = 5
            else:
                amt = len(results)

            # Remove no-no sites
            if not is_nsfw:
                for r in results[0:7]:
                    for n in nono_sites:
                        if n in r['url']:
                            results.remove(r)

            # Escape stuff
            query = discord.utils.escape_mentions(query)
            query = discord.utils.escape_markdown(query)

            # Header
            msg = f"Showing **{amt}** results for `{query}`. \n\n"
            # Expanded Result
            msg += (
                f"**{results[0]['title']}** <{results[0]['url']}>\n"
                f"{results[0]['content']}\n\n")
            # Other Results
            msg += "\n".join(
                [f"**{entry['title']}** <{entry['url']}>" for entry in results[1:5]])
            # Instance Info
            msg += f"\n\n_Results retrieved from instance `{instance}`._"

            return msg

        # Reached if error with returned results
        except (KeyError, IndexError) as e:
            # Logging
            await self.warn(
                f"A user encountered a(n) `{e}` with <{instance}> when searching for `{query}`. "
                "Consider removing it or looking into it.",
                name="Failed Instance"
            )

            self.instances.remove(instance)  # Weed the instance out
            # Recurse until good response
            return await self._old_search_logic(query, is_nsfw)

    async def _instance_check(self, instance: str, content: dict) -> bool:
        """Checks the quality of an instance."""

        # Makes sure proper values exist
        if 'error' in content:
            return False
        if not ('engines' in content and 'initial' in content['timing']):
            return False
        if not ('google' in content['engines'] and 'enabled' in content['engines']['google']):
            return False

        # Makes sure google is enabled
        if not content['engines']['google']['enabled']:
            return False

        # Makes sure is not Tor
        if content['network_type'] != 'normal':
            return False

        # Only picks instances that are fast enough
        timing = int(content['timing']['initial'])
        if timing > 0.20:
            return False

        # Check for Google captcha
        test_search = f'{instance}/search?q=test&format=json&lang=en-US'
        try:
            async with self.request.get(test_search) as resp:
                response = await resp.json()
            response['results'][0]['content']
        except (aiohttp.ClientError, KeyError, IndexError):
            return False

        # Reached if passes all checks
        return True

            @commands.command()
    @commands.is_owner()
    async def rejson(self, ctx):
        """Refreshes the list of instances for searx."""

        msg = await ctx.send('<a:updating:403035325242540032> Refreshing instance list...\n\n'
                             '(Due to extensive quality checks, this may take a bit.)')
        plausible: List[str] = []

        # Get, parse, and quality check all instances
        async with self.request.get('https://searx.space/data/instances.json') as r:
            # Parsing
            searx_json = await r.json()
            instances = searx_json['instances']

            # Quality Check
            for i in instances:
                content = instances.get(i)
                is_good: bool = await self._instance_check(i, content)
                if is_good:
                    plausible.append(i)

        # Save new list
        self.instances = plausible
        with open('searxes.txt', 'w') as f:
            f.write('\n'.join(plausible))

        await msg.edit(content='Instances refreshed!')

            async def _old_basic_search(self, ctx, query: str,
                                category: str = None):
        """Base search message generation."""

        async with ctx.typing():
            is_nsfw = (
                ctx.channel.is_nsfw() if hasattr(ctx.channel, 'is_nsfw')
                else False
            )

            msg = await self._old_search_logic(query, is_nsfw, category)
            await ctx.send(msg)

            await self.info(
                content=(
                    f"**{ctx.author}** searched for `{query}` "
                    f"in \"{ctx.guild}\" and got this:"
                    f"\n\n{msg}"
                ),
                name="Search Results"
            )