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
    repeat_mode = config['CURRENT_SETTINGS']['repeat']
    time_mins = config['CURRENT_SETTINGS']['time']
    time_secs = '00'
    desc = f'Time Remaining: `{time_mins}:{time_secs}`'
    time_full = int(time_mins) * 60
    if DEBUG:
        time_full = 5

    if status == TimerStatus.STOPPED:
        # TODO: Add embed to ctx.send
        await ctx.send(desc)

        await master(time_full, ctx)
        while repeat_mode == 'True' and timer.get_status() != TimerStatus.PAUSED:
            if DEBUG: print('repeating, from stopped')
            await master(time_full, ctx)
            repeat_mode = config['CURRENT_SETTINGS']['repeat']  # grab latest repeat mode to check condition

        # await run_timer(time_full)
        # await time_out(ctx)
        # while repeat_mode == 'True' and timer.get_status() != TimerStatus.PAUSED:        # loop for repeat mode
        #     print('repeating')
        #     await run_timer(time_full)
        #     print('in start loop, timer status', timer.get_status())
        #     await time_out(ctx)
    elif status == TimerStatus.PAUSED:
        print('in pause')
        timer.resume()
        await master(time_full, ctx)
        while repeat_mode == 'True' and timer.get_status() != TimerStatus.PAUSED:
            repeat_mode = config['CURRENT_SETTINGS']['repeat']  # grab latest repeat mode to check condition
            if DEBUG: print('repeating, from paused')
            await master(time_full, ctx)
        # await run_timer(time_full)
        # await time_out(ctx)
    else:
        # TODO: Add embed to ctx
        await ctx.send('timer already running')


@bot.command(name='pause', help='Pauses/stops the timer', aliases=['stop'])
async def pause_timer(ctx):
    if timer.pause():
        print('timer paused)')
        await ctx.send('timer paused')
    else:
        print('timer already paused')
        await ctx.send('timer already paused')


# TODO: change command 'tr' to 'togglerepeat'
@bot.command(name='tr', help='Toggles auto-repeat mode for the timer')
async def toggle_repeat(ctx):
    repeat_mode = config['CURRENT_SETTINGS']['repeat']
    repeat_mode = 'False' if repeat_mode == 'True' else 'True'
    config.set('CURRENT_SETTINGS', 'repeat', repeat_mode)
    with open('settings.ini', 'w') as updatedConfigFile:
        config.write(updatedConfigFile)
    # TODO: add embed to ctx
    await ctx.send('Changed repeat mode to ' + repeat_mode)


# Testing Timer function
async def run_timer(duration: int):
    timer.start(duration)
    while timer.get_status() == TimerStatus.RUNNING:
        await asyncio.sleep(1)
        timer.tick()
        print('tick', timer.get_time())


async def time_out(ctx):
    if timer.get_status() == TimerStatus.STOPPED:
        # TODO: Add embed to ctx
        # TODO: Change to ping role
        print('time up')
        await ctx.send('time up')


async def master(duration: int, ctx):
    timer.start(duration)
    while timer.get_status() == TimerStatus.RUNNING:
        await asyncio.sleep(1)
        timer.tick()
        if DEBUG: print('Tick', timer.get_time())
    if timer.get_status() == TimerStatus.STOPPED:
        # TODO: Add embed to ctx
        # TODO: Change to ping role
        if DEBUG: print('time up')
        await ctx.send('time up')


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('settings.ini')
    bot.run(TOKEN)
