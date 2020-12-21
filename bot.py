import os
import discord
import configparser
from dotenv import load_dotenv
from discord.ext import commands
import asyncio

from timer import Timer, TimerStatus

DEBUG = True
COMMAND_PREFIX = '*'

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
bot = commands.Bot(command_prefix=COMMAND_PREFIX, help_command=None)
timer = Timer()


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord.')


# TODO: Remove debug command
@bot.command(name='d', help='DEBUG command')
async def debug(ctx):
    await ctx.send('hi')


@bot.command(name='start', help='Starts/resumes the timer for nagging', aliases=['resume'])
async def start_timer(ctx):
    status = timer.get_status()
    if status == TimerStatus.STOPPED:
        time_mins = config['CURRENT_SETTINGS']['time']
        time_secs = '00'
        desc = f'Time Remaining: `{time_mins}:{time_secs}`'
        # TODO: Add embed to ctx.send
        await ctx.send(desc)

        time_full = int(time_mins) * 60
        timer.start(time_full)
        while timer.get_status() == TimerStatus.RUNNING:
            await asyncio.sleep(1)
            timer.tick()
        if timer.get_status() == TimerStatus.STOPPED:
            # TODO: Add embed to ctx
            # TODO: Change to ping role
            await ctx.send('Time up')
    elif status == TimerStatus.PAUSED:
        timer.resume()
        while timer.get_status() == TimerStatus.RUNNING:
            await asyncio.sleep(1)
            timer.tick()
        if timer.get_status() == TimerStatus.STOPPED:
            # TODO: Add embed to ctx
            # TODO: Change to ping role
            await ctx.send('time up')
    else:
        # TODO: Add embed to ctx
        await ctx.send('timer already running')


@bot.command(name='stop', help='Stops/pauses the Pomodoro timer', aliases=['pause'])
async def stop_timer(ctx):
    pass


@bot.command(name='tr', help='Toggles auto-repeat mode for the timer')
async def toggle_repeat(ctx):
    mode = config['CURRENT_SETTINGS']['repeat']
    mode = 'False' if mode == 'True' else 'True'
    config.set('CURRENT_SETTINGS', 'repeat', mode)
    with open('settings.ini', 'w') as updatedConfigFile:
        config.write(updatedConfigFile)
    await ctx.send('Changed repeat mode to ' + mode)


# Testing Timer function
# async def runTimer():
#     while timer.get_status() == TimerStatus.RUNNING:
#         await asyncio.sleep(1)
#         timer.tick()


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('settings.ini')
    bot.run(TOKEN)
