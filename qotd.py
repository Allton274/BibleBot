import discord
import aiohttp
import json
import datetime
import asyncio
from discord.ext import commands, tasks
from bs4 import BeautifulSoup


def read(config_value):
    with open('config.json', 'r') as f:
        config_data = json.load(f)
    return config_data[config_value.upper()]


async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()


class QOTD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name = 'qotd', invoke_without_command = True)
    async def _qotd(self, ctx):
        desc = '\n'.join(f'{read("PREFIX")}' + command.name for command in self.bot.get_command('qotd').commands)

        embed = discord.Embed(title = 'QOTD Commands', description = desc, color = discord.Color.green(), timestamp = ctx.message.created_at)

        await ctx.send(embed = embed)
    
    @_qotd.command()
    @commands.has_permissions(administrator = True)
    async def time(self, ctx, time):
        time = time.split(':')
        

        if len(time) != 2:

            raise ValueError('You must provide a time in standard format. ``E.g. 22:00``')

        today = datetime.datetime(datetime.datetime.now().year, datetime.datetime.now().month, datetime.datetime.now().day, int(time[0]), int(time[1]))

        if today < datetime.datetime.now():
            
            today = datetime.datetime(datetime.datetime.now().year, datetime.datetime.now().month, datetime.datetime.now().day + 1, int(time[0]), int(time[1]))

        with open('config.json', 'r') as f:
            r = json.load(f)
            r["QOTD_TIME"] = ':'.join(str(item) for item in time)

        f.close()

        with open('config.json', 'w+') as f:

            json.dump(r, f, indent = 0)

        f.close()

        embed = discord.Embed(title = 'QOTD Time', description = f'The QOTD time has been changed to ``{":".join(str(item) for item in time)}``', color = discord.Color.green(), 
        timestamp = ctx.message.created_at)

        await ctx.send(embed = embed)
        
        await asyncio.sleep(int((today-datetime.datetime.now()).total_seconds()))

        self.get_question.start()

    
    @_qotd.command()
    async def check(self, ctx):
        time = read('QOTD_TIME')

        if time == 'None':
            embed = discord.Embed(title = 'QOTD Time', description = 'There is no QOTD time set!', color = discord.Color.red(), timestamp = ctx.message.created_at)

            return await ctx.send(embed = embed)

        
        embed = discord.Embed(title = 'QOTD Time', description = f'The current QOTD time is {time}', color = discord.Color.green(), timestamp = ctx.message.created_at)
        await ctx.send(embed = embed)

    
    @_qotd.command()
    @commands.has_permissions(administrator = True)
    async def clear(self, ctx):

        with open('config.json', 'r') as f:
            r = json.load(f)
            r["QOTD_TIME"] = 'None'

        f.close()

        with open('config.json', 'w+') as f:

            json.dump(r, f, indent = 0)

        f.close()

        await ctx.send(embed = discord.Embed(title = 'QOTD Time Cleared', description = 'The QOTD Time has been cleared!', timestamp = ctx.message.created_at, color = discord.Color.green()))
        

    @_qotd.command()
    @commands.has_permissions(administrator = True)
    async def channel(self, ctx, chan: discord.TextChannel):
        """Change the channel that QOTD sends to."""

        with open('config.json', 'r') as f:
            r = json.load(f)
            r["QUESTION_CHANNEL_ID"] = chan.id

        f.close()

        with open('config.json', 'w+') as f:

            json.dump(r, f, indent = 0)

        f.close()

        await ctx.send(embed = discord.Embed(title = 'QOTD Channel changed', description = 'The QOTD channel has been changed!', timestamp = ctx.message.created_at, color = discord.Color.green()))



    @tasks.loop(hours = 24)
    async def get_question(self):

        await self.bot.wait_until_ready()

        async with aiohttp.ClientSession() as session:
            #html = await fetch(session, "https://faculty.washington.edu/ejslager/random-generator/index.html")
            html = await fetch(session, "https://www.conversationstarters.com/generator.php")
        html = BeautifulSoup(html, "html.parser")
        question = str(html.find_all(id = "random")[0])[63:-6]
        guild = self.bot.get_guild(read('guild_id'))
        
        question_channel = guild.get_channel(read('question_channel_id'))
        answer_channel = discord.utils.get(guild.text_channels, id = read('answer_CHANNEL_ID'))#self.bot.get_channel(read('answer_channel_id'))
        embed = discord.Embed(
            title='QOTD Question',
            description=f"{question}\nSend your response in {answer_channel.mention}",
            color=discord.Color.green()
        )
        qotd_role = guild.get_role(read('qotd_role_id'))
        await question_channel.send(qotd_role.mention)
        await question_channel.send(embed=embed)

    


def setup(bot):
    bot.add_cog(QOTD(bot))
