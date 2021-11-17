import discord
import json
from discord.ext import commands
import sys
import aiohttp
import bs4
# Import Cogs
from qotd import QOTD
from bs4 import BeautifulSoup
from bible import Bible
from help import PaginatedHelpCommand
from discord.ext.commands import when_mentioned_or

def get_prefix(*args):
    with open("config.json", "r") as f:
        f = json.load(f)
        return f["PREFIX"]


def token():
    with open("config.json", "r") as f:
        f = json.load(f)
        return f["TOKEN"]


bot = commands.Bot(command_prefix=when_mentioned_or(get_prefix()))
bot.help_command = PaginatedHelpCommand()


@bot.event
async def on_ready():
    print('Logged on\nClient User:', bot.user.id)


@bot.command()
@commands.has_permissions(administrator = True)
async def prefix(ctx, new_prefix):

    """Change the prefix of the bot."""

    with open('config.json', 'r') as f:
            r = json.load(f)
            r["PREFIX"] = new_prefix

    f.close()

    with open('config.json', 'w+') as f:

            json.dump(r, f, indent = 0)
    f.close()

    embed = discord.Embed(title = 'Prefix Changed', description = f'This server\'s prefix has been changed to ``{new_prefix}``', color = discord.Color.green())

    await ctx.send(embed = embed)

@bot.group(invoke_without_command = True)
async def setup(ctx):
    """View the configurable options for QOTD and VOTD settings."""

    embed = discord.Embed(title = 'Setup Commands:',
    description = f'``{get_prefix()}setup qotd`` - Set a channel for QOTD\n``{get_prefix()}setup votd`` - Set a channel for VOTD')

    await ctx.send(embed = embed)

@setup.command(case_insensitive = True)
@commands.has_permissions(administrator = True)
async def qotd(ctx, channel: discord.TextChannel):

    """Set the channel for the QOTD to send to."""

    with open('config.json', 'r') as f:
            r = json.load(f)
            r["QUESTION_CHANNEL_ID"] = channel.id

    f.close()

    with open('config.json', 'w+') as f:

            json.dump(r, f)
    f.close()

    embed = discord.Embed(title = 'Channel Set', description = f'The channel {channel.mention} has been set as the QOTD channel!')

    await ctx.send(embed = embed)

@setup.command(case_insensitive = True)
@commands.has_permissions(administrator = True)
async def votd(ctx, channel: discord.TextChannel):

    """Set the channel for the VOTD to send to."""

    with open('config.json', 'r') as f:
            r = json.load(f)
            r["VOTD_CHANNEL_ID"] = channel.id

    f.close()

    with open('config.json', 'w+') as f:

            json.dump(r, f, indent = 0)
    f.close()  

    embed = discord.Embed(title = 'Channel Set', description = f'The channel {channel.mention} has been set as the VOTD channel!')

    await ctx.send(embed = embed)

@bot.command(hidden = True)
async def init(ctx):
    with open('version.json', 'r') as f:
        r = json.load(f)

    f.close()

    for channel in ctx.guild.text_channels:

        r[f'{channel.id}'] = 'kjv'
    
    with open('version.json', 'w+') as f:

        json.dump(r, f, indent = 0)
    await ctx.send('channels initalized')

@bot.command(hidden = True)
async def shutdown(ctx):
    sys.exit(0)

        

# Load Cogs
bot.load_extension("qotd")
bot.load_extension("bible")
bot.load_extension("music2")


bot.run(token())
