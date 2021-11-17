import discord
import aiohttp
import json
import asyncio
from discord.ext import commands, tasks
import os, typing
import random
from enum import Enum


def read(config_value):
    with open('config.json', 'r') as f:
        config_data = json.load(f)
    return config_data[config_value.upper()]


class QueueIsEmpty(commands.CommandError):
    pass



class Queue:
    def __init__(self):
        self._queue = []
        self.position = 0

    @property
    def is_empty(self):
        return not self._queue

    @property
    def current_track(self):
        if not self._queue:
            raise QueueIsEmpty

        if self.position <= len(self._queue) - 1:
            return self._queue[self.position]

    @property
    def upcoming(self):
        if not self._queue:
            raise QueueIsEmpty

        return self._queue[self.position + 1:]

    @property
    def history(self):
        if not self._queue:
            raise QueueIsEmpty

        return self._queue[:self.position]

    @property
    def length(self):
        return len(self._queue)


    def get_next_track(self):
        if not self._queue:
            raise QueueIsEmpty

        self.position += 1

        if self.position < 0:
            return None
        elif self.position > len(self._queue) - 1:
            self.position = 0

        return self._queue[self.position]

    def shuffle(self):
        if not self._queue:
            raise QueueIsEmpty

        upcoming = self.upcoming
        random.shuffle(upcoming)
        self._queue = self._queue[:self.position + 1]
        self._queue.extend(upcoming)


    def empty(self):
        self._queue.clear()
        self.position = 0

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = Queue()
        self.names = ["My Jesus", "Why God", "Scars in Heaven", 'Hold on to Me', 'Bless the Lord', 'Different', 'Battle Belongs',
        'Help is on the Way']


    @commands.command()
    async def play(self, ctx):
        """Plays a file from the local filesystem"""

        

        for enum, song in enumerate(os.listdir("music_files")):
            source = os.path.join("music_files", song)
            try:
                if not self.queue._queue:
                    self.queue._queue.append({source: self.names[enum]})
            except IndexError:
                pass
        try:
            while ctx.voice_client.is_connected():
                source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(list(self.queue._queue[self.queue.position].items())[0][0], executable = "ffmpeg"))

                await ctx.send(f'Now playing: {list(self.queue._queue[self.queue.position].items())[0][1]}')

                ctx.voice_client.play(source, after=lambda e: print(f'Player error: {e}') if e else None)
                try:
                    while ctx.voice_client.is_playing:
                        await asyncio.sleep(5)
                    try:
                        self.queue.position += 1
                    
                    except IndexError:
                        self.queue.position = 0

                except Exception as e:
                    pass
        except Exception:
            pass

    @commands.command()
    async def resume(self, ctx):
        """Resumes the song if it is paused"""
        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")
        
        ctx.voice_client.resume()
        await ctx.send('Music resumed')

        while ctx.voice_client.is_playing:
            await asyncio.sleep(5)
        
        self.queue.position += 1
        
        try:
            while ctx.voice_client.is_connected():
                source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(list(self.queue._queue[self.queue.position].items())[0][0], executable = "ffmpeg"))

                await ctx.send(f'Now playing: {list(self.queue._queue[self.queue.position].items())[0][1]}')

                ctx.voice_client.play(source, after=lambda e: print(f'Player error: {e}') if e else None)
                try:
                    while ctx.voice_client.is_playing:
                        await asyncio.sleep(5)
                    try:
                        self.queue.position += 1
                    
                    except IndexError:
                        self.queue.position = 0

                except AttributeError as e:
                    pass
        except AttributeError:
            pass

    @commands.command()
    async def join(self, ctx, *, channel: typing.Optional[discord.VoiceChannel]):
        """Joins a voice channel"""

        if channel is None:
            if ctx.author.voice.channel is not None:
                await ctx.author.voice.channel.connect()
            
            else:
            
                return await ctx.send('You are not connected to a voice channel')
        else:
            if ctx.voice_client is not None:
                return await ctx.voice_client.move_to(channel)

            await channel.connect()
    
    @commands.command()
    async def volume(self, ctx, volume: int):
        """Changes the player's volume"""

        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")

        ctx.voice_client.source.volume = volume / 100
        await ctx.send(f"Changed volume to {volume}%")
    
    @commands.command()
    async def pause(self, ctx):
        """Pauses the current song being played"""
        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")
        
        ctx.voice_client.pause()
        await ctx.send('Music paused')

    @commands.command()
    async def stop(self, ctx):
        """Stops and disconnects the bot from voice. The user MUST be in the voice channel for this command to work."""

        await ctx.voice_client.disconnect()
    

    
    @commands.command(aliases = ['skip'])
    async def next(self, ctx):
        """Plays to the next song in the queue"""
        try:
            self.queue.position += 1
        except IndexError:
            self.queue.position = 0

        song = list(self.queue._queue[self.queue.position].items())[0][0]

        ctx.voice_client.stop()

        while ctx.voice_client.is_connected():
            source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(list(self.queue._queue[self.queue.position].items())[0][0], executable = "ffmpeg"))

            await ctx.send(f'Now playing: {list(self.queue._queue[self.queue.position].items())[0][1]}')

            ctx.voice_client.play(source, after=lambda e: print(f'Player error: {e}') if e else None)
            try:
                while ctx.voice_client.is_playing:
                    await asyncio.sleep(5)
                try:
                    self.queue.position += 1
                
                except IndexError:
                    self.queue.position = 0

            except Exception as e:
                print(e)
    
    @commands.command()
    async def shuffle(self, ctx):
        """Shuffles the songs in the queue"""
        self.queue.shuffle()
        queue_ = '\n'.join(list(item.items())[0][1] for item in self.queue._queue)
        await ctx.send(f'The queue has been shuffled. It is now: \n{queue_}')
    
    @commands.command()
    async def queue(self, ctx):
        """Displays the current queue"""

        queue_ = '\n'.join(list(item.items())[0][1] for item in self.queue._queue)

        await ctx.send(f"{queue_}\n```The current song is: {list(self.queue._queue[self.queue.position].items())[0][1]}```")


def setup(bot):
    bot.add_cog(Music(bot))