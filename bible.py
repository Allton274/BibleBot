import aiohttp
import discord
import json
import datetime
import asyncio
import html
import re
from bs4 import BeautifulSoup
from discord.ext import commands, tasks, menus


def read(config_value):
    with open('config.json', 'r') as f:
        config_data = json.load(f)
    return config_data[config_value.upper()]


def read_version(channel_id):

    with open('version.json', 'r') as f:

        version = json.load(f)
    
    return version[f'{channel_id}']


def purify_text(text):
    result = text.replace("“", "\"")
    result = result.replace("[", " <")
    result = result.replace("]", "> ")
    result = result.replace("”", "\"")
    result = result.replace("‘", "'")
    result = result.replace("’", "'")
    result = result.replace(",", ", ")
    result = result.replace(".", ". ")
    result = result.replace(". \"", ".\"")
    result = result.replace(". '", ".'")
    result = result.replace(" .", ".")
    result = result.replace(", \"", ",\"")
    result = result.replace(", '", ",'")
    result = result.replace("!", "! ")
    result = result.replace("! \"", "!\"")
    result = result.replace("! '", "!'")
    result = result.replace("?", "? ")
    result = result.replace("? \"", "?\"")
    result = result.replace("? '", "?'")
    result = result.replace(":", ": ")
    result = result.replace(";", "; ")
    result = result.replace("¶ ", "")
    result = result.replace("â", "\"")  # biblehub beginning smart quote
    result = result.replace(" â", "\"")  # biblehub ending smart quote
    result = result.replace("â", "-")  # biblehub dash unicode
    return re.sub(r"\s+", " ", result)


def remove_bible_title_in_search(string):
    return re.sub(r"<[^>]*>", "", string)

async def fetch_link(session, url):
    async with session.get(url) as response:
        return await response.text()


async def get_verse_embed(title):
    async with aiohttp.ClientSession() as session:
        html = await fetch_link(session, 'http://www.thywordistrue.com/verse_generator')
    html = BeautifulSoup(html, "html.parser")
    verse = html.findAll("p")[0].text
    reference = html.findAll("small")[2].text
    embed = discord.Embed(
        title=title,
        description=f"{verse}",
        color=discord.Color.green()
    )
    embed.set_footer(text=reference)
    return embed

class BibleVersions(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=1018)

    async def format_page(self, menu, entries):
        embed = discord.Embed(title = 'Bible Versions', description = entries, color = discord.Color.green())

        return embed



class SearchResultsEntry:

    def __init__(self):
        
        self.counter = 1

        self.new_result = []

    def format_entries(self, results):

        for result in results:

            self.new_result.append(results[f'result{self.counter}']['title'])

            self.new_result.append(results[f'result{self.counter}']['text'])

            self.counter += 1
        
        
        return self.new_result




class SearchResults(menus.ListPageSource):

    def __init__(self, data, id):

        self.id = id
        super().__init__(data, per_page = 10)
    
    async def format_page(self, menu, entries):

        counter = 0
        embed = discord.Embed()

        embed.title = f'{(len(self.entries))//2} Results'

        embed.set_footer(text = f'Version: {read_version(self.id)}')

        #print(entries)

        for item in entries:
            try:
                embed.add_field(name = entries[counter], value = entries[counter + 1], inline = False)
            except IndexError:
                break
            else:
                counter += 2
        
        return embed



class Bible(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        async with aiohttp.ClientSession() as session:
            async with session.get('https://biblegateway.com/passage/?search=' + message.content + "&version=kjv") as response:

                try:

                    response = await response.text()

                    soup = BeautifulSoup(response, features = 'html.parser')

                    lines = soup.find_all('meta')

                    text = str(lines[13])

                    text = text[15:-29]
                    
                    verse_embed = discord.Embed(
                        title=message.content.title(),
                        description=text.replace("&amp;#39;", "'"),
                        color=discord.Color.green())

                    await message.channel.send(embed = verse_embed)
                
                except IndexError:
                    return
            
            
            
    
    @commands.group(name = 'VOTD', invoke_without_command = True, aliases = ['votd', 'verse-of-the-day', 'verseoftheday'])
    async def _votd(self, ctx):
        """Commands to manage the Verse of the Day feature. The bot will send a message every 24 hours from the set time.
        """


        desc = '\n'.join(f'{read("PREFIX")}' + command.name for command in self.bot.get_command('votd').commands)

        embed = discord.Embed(title = 'QOTD Commands', description = desc, color = discord.Color.green(), timestamp = ctx.message.created_at)

        await ctx.send(embed = embed)
    
    @_votd.command()
    @commands.has_permissions(administrator = True)
    async def time(self, ctx, time):
        """Change the time the bot should send a verse. __If you would like it in the PM, you will need to use military time, and include a colon.__
        
        E.g.: ``!votd time 18:30`` to set the time for 6:30 PM."""

        time = time.split(':')
        

        if len(time) != 2:

            raise ValueError('You must provide a time in standard format. ``E.g. 22:00``')

        today = datetime.datetime(datetime.datetime.now().year, datetime.datetime.now().month, datetime.datetime.now().day, int(time[0]), int(time[1]))

        if today < datetime.datetime.now():
            
            today = datetime.datetime(datetime.datetime.now().year, datetime.datetime.now().month, datetime.datetime.now().day + 1, int(time[0]), int(time[1]))

        with open('config.json', 'r') as f:
            r = json.load(f)
            r["VOTD_TIME"] = ':'.join(str(item) for item in time)

        f.close()

        with open('config.json', 'w+') as f:

            json.dump(r, f, indent = 0)

        f.close()

        embed = discord.Embed(title = 'VOTD Time', description = f'The VOTD time has been changed to ``{":".join(str(item) for item in time)}``', color = discord.Color.green(), 
        timestamp = ctx.message.created_at)

        await ctx.send(embed = embed)
        
        await asyncio.sleep(int((today-datetime.datetime.now()).total_seconds()))

        self.daily_verse.start()

    
    @_votd.command()
    async def check(self, ctx):

        """Check what time the Verse of the Day is set for."""

        time = read('VOTD_TIME')

        if time == 'None':
            embed = discord.Embed(title = 'VOTD Time', description = 'There is no VOTD time set!', color = discord.Color.red(), timestamp = ctx.message.created_at)

            return await ctx.send(embed = embed)

        
        embed = discord.Embed(title = 'VOTD Time', description = f'The current VOTD time is {time}', color = discord.Color.green(), timestamp = ctx.message.created_at)
        await ctx.send(embed = embed)

    
    @_votd.command()
    @commands.has_permissions(administrator = True)
    async def clear(self, ctx):

        """Clear the time previously set for Verse of the Day. The bot will stop sending verses until a new time is set."""

        with open('config.json', 'r') as f:
            r = json.load(f)
            r["VOTD_TIME"] = 'None'

        f.close()

        with open('config.json', 'w+') as f:

            json.dump(r, f, indent = 0)

        f.close()

        await ctx.send(embed = discord.Embed(title = 'VOTD Time Cleared', description = 'The VOTD Time has been cleared!', timestamp = ctx.message.created_at, color = discord.Color.green()))

    @_votd.command()
    @commands.has_permissions(administrator = True)
    async def channel(self, ctx, chan: discord.TextChannel):
        """Change the channel that VOTD sends to."""
        with open('config.json', 'r') as f:
            r = json.load(f)
            r["VOTD_CHANNEL_ID"] = chan.id

        f.close()

        with open('config.json', 'w+') as f:

            json.dump(r, f, indent = 0)

        f.close()

        await ctx.send(embed = discord.Embed(title = 'VOTD Channel changed', description = 'The VOTD channel has been changed!', timestamp = ctx.message.created_at, color = discord.Color.green()))


    @tasks.loop(hours=24)
    async def daily_verse(self):
        await self.bot.wait_until_ready()
        embed = await get_verse_embed('VOTD')
        guild = self.bot.get_guild(read('guild_id'))
        
        verse_channel = self.bot.get_channel(read('votd_channel_id'))
        votd_role = guild.get_role(read('votd_role_id'))
        await verse_channel.send(votd_role.mention)
        await verse_channel.send(embed=embed)

    @commands.command()
    async def random(self, ctx):
        """Send a random Bible verse into the channel."""

        embed = await get_verse_embed('Random Verse')
        await ctx.channel.send(embed=embed)

    
    @commands.command()
    async def versions(self, ctx):

        """Versions of the Bible supported by this bot. Use the abbrevation when chaning the version."""

        bibles = '''21st Century King James Version (KJ21)
                    American Standard Version (ASV)
                    Amplified Bible (AMP)
                    Amplified Bible, Classic Edition (AMPC)
                    BRG Bible (BRG)
                    Christian Standard Bible (CSB)	
                    Common English Bible (CEB)
                    Complete Jewish Bible (CJB)
                    Contemporary English Version (CEV)
                    Darby Translation (DARBY)
                    Disciples’ Literal New Testament (DLNT)
                    Douay-Rheims 1899 American Edition (DRA)
                    Easy-to-Read Version (ERV)
                    Evangelical Heritage Version (EHV)
                    English Standard Version (ESV)	
                    English Standard Version Anglicised (ESVUK)
                    Expanded Bible (EXB)
                    1599 Geneva Bible (GNV)	
                    GOD’S WORD Translation (GW)
                    Good News Translation (GNT)
                    Holman Christian Standard Bible (HCSB)	
                    International Children’s Bible (ICB)
                    International Standard Version (ISV)
                    J.B. Phillips New Testament (PHILLIPS)
                    Jubilee Bible 2000 (JUB)
                    King James Version (KJV)	
                    Authorized (King James) Version (AKJV)
                    Lexham English Bible (LEB)	
                    Living Bible (TLB)
                    The Message (MSG)	
                    Modern English Version (MEV)
                    Mounce Reverse Interlinear New Testament (MOUNCE)
                    Names of God Bible (NOG)
                    New American Bible (Revised Edition) (NABRE)
                    New American Standard Bible (NASB)	
                    New American Standard Bible 1995 (NASB1995)	
                    New Century Version (NCV)
                    New English Translation (NET Bible)
                    New International Reader's Version (NIRV)
                    New International Version (NIV)	
                    New International Version - UK (NIVUK)	
                    New King James Version (NKJV)	
                    New Life Version (NLV)
                    New Living Translation (NLT)	
                    New Matthew Bible (NMB)	
                    New Revised Standard Version (NRSV)
                    New Revised Standard Version, Anglicised (NRSVA)
                    New Revised Standard Version, Anglicised Catholic Edition (NRSVACE)
                    New Revised Standard Version Catholic Edition (NRSVCE)
                    New Testament for Everyone (NTE)
                    Orthodox Jewish Bible (OJB)
                    The Passion Translation (TPT)
                    Revised Geneva Translation (RGT)
                    Revised Standard Version (RSV)
                    Revised Standard Version Catholic Edition (RSVCE)
                    Tree of Life Version (TLV)
                    The Voice (VOICE)               
                    World English Bible (WEB)
                    Worldwide English (New Testament) (WE)
                    Wycliffe Bible (WYC)
                    Young's Literal Translation (YLT)'''

                 
       

    

        pages = menus.MenuPages(source=BibleVersions(bibles), clear_reactions_after=True)
        await pages.start(ctx)


    
    @commands.command()
    async def search(self, ctx, *, query):

        """Search for all verses that contain the query you input in the Bible version that is currently set for the channel."""

        #query = html.escape(query)

        query = query.split(' ')

        if len(query) > 1:


            query = '+'.join(item for item in query)

            url = f"https://www.biblegateway.com/quicksearch/?search={query}" + \
                f"&version={read_version(ctx.channel.id)}&searchtype=all&limit=50000&interface=print"

        
        
        else:
            url = f"https://www.biblegateway.com/quicksearch/?search={query[0]}" + \
                f"&version={read_version(ctx.channel.id)}&searchtype=all&limit=50000&interface=print"

        search_results = {}
        length = 0

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp is not None:
                    soup = BeautifulSoup(await resp.text(), features = "html.parser")

                    for row in soup.find_all(True, {"class": "row"}):
                        result = {}

                        for extra in row.find_all(True, {"class": "bible-item-extras"}):
                            extra.decompose()

                        result["title"] = row.find(True, {"class": "bible-item-title"})
                        result["text"] = row.find(True, {"class": "bible-item-text"})

                        if result["title"] is not None:
                            if result["text"] is not None:
                                result["title"] = result["title"].getText()
                                result["text"] = remove_bible_title_in_search(
                                    purify_text(
                                        result["text"].get_text()[0:-1]))

                                length += 1
                                search_results["result" + str(length)] = result
                    
                    pages = menus.MenuPages(source = SearchResults(SearchResultsEntry().format_entries(search_results), ctx.channel.id), clear_reactions_after= True)

                    await pages.start(ctx)
                
                else:

                    return await ctx.send('Something went wrong!')


    
    @commands.group(invoke_without_command = True)
    async def version(self, ctx):

        """Commands to manage the Bible version for the whole server or specific channels. Use the command by itself to check the current Bible version in use for the channel."""
        
        version = read_version(ctx.channel.id)

        embed = discord.Embed(title = f'{ctx.channel.name} Version', description = f'The current Bible version in this channel is: ``{version.upper()}``', color = discord.Color.green())

        await ctx.send(embed = embed)

    
    @version.command()
    @commands.has_permissions(administrator = True)
    async def set(self, ctx, version):

        """Set the Bible version for the current channel, __using the abbreviated name of the version__."""

        search_results = {}
        length = 0

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://www.biblegateway.com/quicksearch/?search=holy+spirit&version={version}&searchtype=all&limit=50000&interface=print") as resp:

                

                soup = BeautifulSoup(await resp.text(), "html.parser")

                

                for row in soup.find_all(True, {"class": "row"}):
                    result = {}

                    for extra in row.find_all(True, {"class": "bible-item-extras"}):
                        extra.decompose()

                    result["title"] = row.find(True, {"class": "bible-item-title"})
                    result["text"] = row.find(True, {"class": "bible-item-text"})

                    if result["title"] is not None:
                            if result["text"] is not None:
                                result["title"] = result["title"].getText()
                                result["text"] = remove_bible_title_in_search(
                                    purify_text(
                                        result["text"].get_text()[0:-1]))

                                length += 1
                                search_results["result" + str(length)] = result


        if len(search_results) < 1:

            embed = discord.Embed(title = 'Error', description = 'This version is not recognized!', color = discord.Color.red())

            return await ctx.send(embed = embed)

        
        else:
            with open('version.json', 'r') as f:
            
                r = json.load(f)

                r[f'{ctx.channel.id}'] = version

            f.close()

            with open('version.json', 'w+') as f:

                json.dump(r, f, indent = 0)

            embed = discord.Embed(title = 'Success', description = f'The Bible version for this channel has been set to ``{version.upper()}``')

            await ctx.send(embed = embed)

    
    @version.command()
    @commands.has_permissions(administrator = True)
    async def guild(self, ctx, version):

        """Set a Bible version for the entire server. __Use the abbreviated name of the version.__"""
        
        search_results = {}
        length = 0

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://www.biblegateway.com/quicksearch/?search=holy+spirit&version={version}&searchtype=all&limit=50000&interface=print") as resp:

                

                soup = BeautifulSoup(await resp.text(), "lxml")

                

                for row in soup.find_all(True, {"class": "row"}):
                    result = {}

                    result["title"] = row.find(True, {"class": "bible-item-title"})
                    result["text"] = row.find(True, {"class": "bible-item-text"})

                    if result["title"] is not None:
                            if result["text"] is not None:
                                result["title"] = result["title"].getText()
                                result["text"] = remove_bible_title_in_search(
                                    purify_text(
                                        result["text"].get_text()[0:-1]))

                                length += 1
                                search_results["result" + str(length)] = result


        if len(search_results) < 1:

            embed = discord.Embed(title = 'Error', description = 'This version is not recognized!', color = discord.Color.red())

            return await ctx.send(embed = embed)

        
        with open('version.json', 'r') as f:
            r = json.load(f)

        f.close()

        for channel in ctx.guild.text_channels:

            r[f'{channel.id}'] = version
    
        with open('version.json', 'w+') as f:

            json.dump(r, f, indent = 0)

        await ctx.send(embed = discord.Embed(title = 'Success', description = f'All channels have been changed to ``{version.upper()}``', color = discord.Color.green(), timestamp = ctx.message.created_at))


        



        




def setup(bot):
    bot.add_cog(Bible(bot))
