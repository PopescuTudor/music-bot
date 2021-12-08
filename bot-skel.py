#!./.venv/bin/python
    
import discord      # base discord module
import code         # code.interact
import os           # environment variables
import inspect      # call stack inspection
import random       # dumb random number generator
import youtube_dl
    
from discord.ext import commands    # Bot class and utils
    
################################################################################
############################### HELPER FUNCTIONS ###############################
################################################################################
    
# log_msg - fancy print
#   @msg   : string to print
#   @level : log level from {'debug', 'info', 'warning', 'error'}
def log_msg(msg: str, level: str):
    # user selectable display config (prompt symbol, color)
    dsp_sel = {
        'debug'   : ('\033[34m', '-'),
        'info'    : ('\033[32m', '*'),
        'warning' : ('\033[33m', '?'),
        'error'   : ('\033[31m', '!'),
    }
    
    # internal ansi codes
    _extra_ansi = {
        'critical' : '\033[35m',
        'bold'     : '\033[1m',
        'unbold'   : '\033[2m',
        'clear'    : '\033[0m',
    }
    
    # get information about call site
    caller = inspect.stack()[1]
    
    # input sanity check
    if level not in dsp_sel:
        print('%s%s[@] %s:%d %sBad log level: "%s"%s' % \
            (_extra_ansi['critical'], _extra_ansi['bold'],
                caller.function, caller.lineno,
                _extra_ansi['unbold'], level, _extra_ansi['clear']))
        return
    
    # print the damn message already
    print('%s%s[%s] %s:%d %s%s%s' % \
        (_extra_ansi['bold'], *dsp_sel[level],
            caller.function, caller.lineno,
            _extra_ansi['unbold'], msg, _extra_ansi['clear']))
    
################################################################################
############################## BOT IMPLEMENTATION ##############################
################################################################################
    
# bot instantiation
bot = commands.Bot(command_prefix='!')
    
# on_ready - called after connection to server is established
@bot.event
async def on_ready():
    log_msg('logged on as <%s>' % bot.user, 'info')
    
# on_message - called when a new message is posted to the server
#   @msg : discord.message.Message
@bot.event
async def on_message(msg):
    # filter out our own messages
    if msg.author == bot.user:
        return
    
    log_msg('message from <%s>: "%s"' % (msg.author, msg.content), 'debug')
    
    # overriding the default on_message handler blocks commands from executing
    # manually call the bot's command processor on given message
    await bot.process_commands(msg)
    
# roll - rng chat command
#   @ctx     : command invocation context
#   @max_val : upper bound for number generation (must be at least 1)
@bot.command(brief='Generate random number between 1 and <arg>')
async def roll(ctx, max_val: int):
    # argument sanity check
    if max_val < 1:
        raise Exception('argument <max_val> must be at least 1')
    
    await ctx.send(random.randint(1, max_val))
    
# roll_error - error handler for the <roll> command
#   @ctx     : command that crashed invocation context
#   @error   : ...
@roll.error
async def roll_error(ctx, error):
    await ctx.send(str(error))
    
################################################################################
############################# PROGRAM ENTRY POINT ##############################
################################################################################
@bot.command(name='play')
async def play(ctx, url : str):
    song_there = os.path.isfile("song.mp3")
    try:
        if song_there:
            os.remove("song.mp3")
    except PermissionError:
        await ctx.send("Muzica inca este redata!")
        return
        
    voiceChannel = discord.utils.get(ctx.guild.voice_channels, name='voice_channel')
    await voiceChannel.connect()
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    for file in os.listdir("./"):
        if(file.endswith(".mp3")):
            os.rename(file, "song.mp3")
    voice.play(discord.FFmpegPCMAudio("song.mp3"))

@bot.command(name='leave')
async def leave(ctx):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice.is_connected():       
        await voice.disconnect()
    else:
        await ctx.send("Bot-ul nu e conectat la voice_channel!")

@bot.command(name='pause')
async def pause(ctx):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice.is_playing():
        voice.pause()
    else:
        await ctx.send("Bot-ul nu poate fi pus pe pauza inca!")

@bot.command(name='resume')
async def resume(ctx):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice.is_paused():
        voice.resume()
    else:
        await ctx.send("Bot-ul nu e pus pe pauza!")

@bot.command(name='stop')
async def stop(ctx):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    voice.stop()

if __name__ == '__main__':
    # check that token exists in environment
    if 'BOT_TOKEN' not in os.environ:
        log_msg('save your token in the BOT_TOKEN env variable!', 'error')
        exit(-1)
    
    # launch bot (blocking operation)
    bot.run(os.environ['BOT_TOKEN'])

