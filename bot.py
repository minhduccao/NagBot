import os
import discord
import configparser
from dotenv import load_dotenv
from discord.ext import commands
import asyncio

from timer import Timer, TimerStatus

DEBUG = True
COMMAND_PREFIX = '*'
SETTING_OPTIONS = ['time', 'repeat', 'message']

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
        await run_timer(time_full, ctx)
        while repeat_mode == 'True' and timer.get_status() != TimerStatus.PAUSED:
            if DEBUG: print('repeating, from stopped')
            await run_timer(time_full, ctx)
            repeat_mode = config['CURRENT_SETTINGS']['repeat']  # grab latest repeat mode to check condition
    elif status == TimerStatus.PAUSED:
        timer.resume()
        await run_timer(time_full, ctx)
        while repeat_mode == 'True' and timer.get_status() != TimerStatus.PAUSED:
            repeat_mode = config['CURRENT_SETTINGS']['repeat']  # grab latest repeat mode to check condition
            if DEBUG: print('repeating, from paused')
            await run_timer(time_full, ctx)
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
    # TODO: change msg to be clearer (repeat mode enabled/on)
    await ctx.send('Changed repeat mode to ' + repeat_mode)


@bot.command(name='time', help='Displays remaining time and timer settings', aliases=['status'])
async def status(ctx):
    raw_time = timer.get_time()
    time_secs = raw_time % 60
    time_mins = int((raw_time - time_secs) / 60)
    if time_secs < 10:
        time_secs = '0' + str(time_secs)
    time_desc = f'Time Remaining: `{time_mins}:{time_secs}`\n'
    settings_desc = 'Timer Duration Setting: `' + config['CURRENT_SETTINGS']['time'] + ' minutes`\n'
    msg_desc = 'Ping Message: `' + config['CURRENT_SETTINGS']['message'] + '`'
    # TODO: Add embed to ctx
    await ctx.send(time_desc + settings_desc + msg_desc)


@bot.command(name='reset', help='Resets bot settings to default settings')
async def reset(ctx, confirm=''):
    if confirm.lower() != 'confirm':
        await ctx.send('Are you sure you want to reset the settings? \nEnter `reset confirm` to confirm resetting settings.')
    else:
        for option in SETTING_OPTIONS:
            config.set('CURRENT_SETTINGS', option, config['DEFAULT'][option])
        with open('settings.ini', 'w') as configFile:
            config.write(configFile)
        await ctx.send('Bot settings have been reset to default values.')


@bot.command(name='settime', help='Sets the timer duration (in minutes)', aliases=['set'])
async def set_time(ctx, time: int):
    if time <= 0:
        await ctx.send('Invalid timer duration. Duration must be 1+ minutes. \nFormat: `settime #`')
    else:
        config.set('CURRENT_SETTINGS', 'time', str(time))
        with open('settings.ini', 'w') as configFile:
            config.write(configFile)
        await ctx.send('Timer duration has been set to `' + str(time) + ' minutes`.')


@bot.command(name='setmessage', help='Sets the ping message', aliases=['setmsg'])
async def set_message(ctx, message: str):
    config.set('CURRENT_SETTINGS', 'message', message)
    with open('settings.ini', 'w') as configFile:
        config.write(configFile)
    await ctx.send('Ping message has been set to `' + message + '`.')


async def run_timer(duration: int, ctx):
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


@set_time.error
async def set_time_error(ctx, error):
    if DEBUG: print(f'caught *settime error: {ctx.message.content} \n  {ctx.message}\n')

    if isinstance(error, commands.errors.MissingRequiredArgument):
        msg = 'Specify a timer duration (in minutes). \nFormat: `settime #`'
        with open('error.log', 'a') as errorLog:
            errorLog.write(f'Unhandled `settime` message: {ctx.message.content} \n  {ctx.message}\n')
    elif isinstance(error, commands.errors.BadArgument):
        msg = 'Specify a valid # for the timer duration. \nFormat: `settime #`'
    else:
        with open('error.log', 'a') as errorLog:
            errorLog.write(f'Unhandled `settime` message: {ctx.message.content} \n  {ctx.message}\n')
        msg = 'Unhandled `settime` error has occurred. See `error.log` for more information.'
    await ctx.send(msg)


@set_message.error
async def set_message_error(ctx, error):
    if DEBUG: print(f'caught *setmsg error: {ctx.message.content} \n  {ctx.message}\n')

    if isinstance(error, commands.errors.MissingRequiredArgument):
        msg = 'Specify a message for pinging. \nFormat: `setmessage your_message_here`'
    else:
        with open('error.log', 'a') as errorLog:
            errorLog.write(f'Unhandled `setmessage` message: {ctx.message.content} \n  {ctx.message}\n')
        msg = 'Unhandled `setmessage` error has occurred. See `error.log` for more information.'
    await ctx.send(msg)

if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('settings.ini')
    bot.run(TOKEN)
