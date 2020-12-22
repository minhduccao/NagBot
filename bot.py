import os
import configparser
from dotenv import load_dotenv
from discord.ext import commands
from discord.utils import get
from discord import Embed
import asyncio
from enum import Enum

from timer import Timer, TimerStatus

DEBUG = True
COMMAND_PREFIX = '*'
SETTING_OPTIONS = ['time', 'repeat', 'message']
TIMER_COMMANDS = ['start', 'pause', 'time', 'settime', 'setmessage', 'toggleping', 'togglerepeat']
GENERAL_COMMANDS = ['reset', 'help']

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
bot = commands.Bot(command_prefix=COMMAND_PREFIX, help_command=None)
timer = Timer()


class MsgColors(Enum):
    AQUA = 0x33c6bb
    YELLOW = 0xFFD966
    RED = 0xEA3546
    PURPLE = 0x6040b1
    WHITE = 0xFFFFFF
    BLACK = 0x000000

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord.')


@bot.command(name='start', help='Starts/resumes the timer for nagging', aliases=['resume'])
async def start_timer(ctx):
    status = timer.get_status()
    repeat_mode = config['CURRENT_SETTINGS']['repeat']
    time_mins = config['CURRENT_SETTINGS']['time']
    time_full = int(time_mins) * 60
    # TODO: remove debug statement
    if DEBUG:
        time_full = 5

    # Create role here in case user starts timer before triggering toggleping
    nag_role = get(ctx.guild.roles, name='NagMe')
    if nag_role is None:
        await ctx.guild.create_role(name='NagMe', mentionable=True, colour=MsgColors.AQUA)
        if DEBUG: print(f'Created NagMe role for `{ctx.guild.name}`')

    if status == TimerStatus.STOPPED:
        await run_timer(time_full, ctx)
        while repeat_mode == 'True' and timer.get_status() != TimerStatus.PAUSED:   # Loop if repeat mode enabled
            if DEBUG: print('repeating, from stopped')
            await run_timer(time_full, ctx)
            repeat_mode = config['CURRENT_SETTINGS']['repeat']                      # Check repeat mode is enabled
    elif status == TimerStatus.PAUSED:
        timer.resume()
        await run_timer(time_full, ctx)
        while repeat_mode == 'True' and timer.get_status() != TimerStatus.PAUSED:   # Loop if repeat mode enabled
            repeat_mode = config['CURRENT_SETTINGS']['repeat']                      # Check repeat mode is enabled
            if DEBUG: print('repeating, from paused')
            await run_timer(time_full, ctx)
    else:
        em = Embed(title=':warning: Alert',
                   description='Timer is already running.',
                   color=MsgColors.YELLOW.value)
        await ctx.send(embed=em)


@bot.command(name='pause', help='Pauses/stops the timer', aliases=['stop'])
async def pause_timer(ctx):
    repeat_mode = 'On' if config['CURRENT_SETTINGS']['repeat'] == 'True' else 'Off'
    if timer.pause():
        em = Embed(title=':pause_button: Paused Timer',
                   description=getFrmtTime(timer) + f'\nAuto-Repeat Mode: `{repeat_mode}`',
                   color=MsgColors.YELLOW.value)
    else:
        em = Embed(title=':warning: Alert',
                   description='Timer is already paused/stopped.',
                   color=MsgColors.YELLOW.value)
    await ctx.send(embed=em)


@bot.command(name='togglerepeat', help='Toggles auto-repeat mode for the timer', aliases=['repeat'])
async def toggle_repeat(ctx):
    repeat_mode = config['CURRENT_SETTINGS']['repeat']
    repeat_mode = 'False' if repeat_mode == 'True' else 'True'
    config.set('CURRENT_SETTINGS', 'repeat', repeat_mode)
    with open('settings.ini', 'w') as updatedConfigFile:
        config.write(updatedConfigFile)
    repeat_desc = 'On' if config['CURRENT_SETTINGS']['repeat'] == 'True' else 'Off'
    em = Embed(title=':gear: Auto-Repeat Mode Changed',
               description=f'Auto-repeat mode has been changed to `{repeat_desc}`.',
               color=MsgColors.BLACK.value)
    await ctx.send(embed=em)


@bot.command(name='time', help='Displays remaining time and timer settings', aliases=['status', 'settings'])
async def status(ctx):
    raw_time = timer.get_time()
    time_secs = raw_time % 60
    time_mins = int((raw_time - time_secs) / 60)
    if time_secs < 10:
        time_secs = '0' + str(time_secs)
    time_desc = f'Time Remaining: `{time_mins}:{time_secs}`\n'
    settings_desc = 'Timer Duration Setting: `' + config['CURRENT_SETTINGS']['time'] + ' minute(s)`\n'
    msg_desc = 'Ping Message: `' + config['CURRENT_SETTINGS']['message'] + '`\n'
    repeat_desc = 'Auto-Repeat Mode: `On`' if config['CURRENT_SETTINGS']['repeat'] == 'True' else 'Auto_Repeat Mode: `Off`'
    em = Embed(title=':gear: Current Settings',
               description=time_desc + settings_desc + msg_desc + repeat_desc,
               color=MsgColors.BLACK.value)
    await ctx.send(embed=em)


@bot.command(name='reset', help='Resets bot settings to default settings')
async def reset(ctx, confirm=''):
    if confirm.lower() != 'confirm':
        em = Embed(title=':warning: Confirm Reset',
                   description='Are you sure you want to reset the settings? \nEnter `reset confirm` to confirm resetting settings.',
                   color=MsgColors.YELLOW.value)
        await ctx.send(embed=em)
    else:
        for option in SETTING_OPTIONS:
            config.set('CURRENT_SETTINGS', option, config['DEFAULT'][option])
        with open('settings.ini', 'w') as configFile:
            config.write(configFile)
        em = Embed(title='gear: Settings Changed',
                   description='Bot settings have been reset to default values.',
                   color=MsgColors.BLACK.value)
        await ctx.send(embed=em)


@bot.command(name='settime', help='Sets the timer duration (in minutes)', aliases=['set'])
async def set_time(ctx, time: int):
    if time <= 0:
        em = Embed(title=':warning: Invalid `settime` Command Usage',
                   description='Invalid timer duration. Duration must be 1+ minutes. \nFormat: `settime #`',
                   color=MsgColors.YELLOW.value)
    else:
        config.set('CURRENT_SETTINGS', 'time', str(time))
        with open('settings.ini', 'w') as configFile:
            config.write(configFile)
        em = Embed(title=':gear: Timer Duration Changed',
                   description='Timer duration has been set to `' + str(time) + ' minute(s)`.',
                   color=MsgColors.BLACK.value)
    await ctx.send(embed=em)


@bot.command(name='setmessage', help='Sets the ping message', aliases=['setmsg'])
async def set_message(ctx, message: str):
    config.set('CURRENT_SETTINGS', 'message', message)
    with open('settings.ini', 'w') as configFile:
        config.write(configFile)
    em = Embed(title=':gear: Ping Message Changed',
               description=f'Ping message has been set to `{message}`.',
               color=MsgColors.BLACK.value)
    await ctx.send(embed=em)


@bot.command(name='toggleping', help='Toggles the bot from pinging you', aliases=['ping'])
async def toggle_ping(ctx):
    nag_role = get(ctx.guild.roles, name='NagMe')
    if nag_role is None:
        await ctx.guild.create_role(name='NagMe', mentionable=True, colour=MsgColors.AQUA)
        if DEBUG: print(f'Created NagMe role for `{ctx.guild.name}`')
        nag_role = get(ctx.guild.roles, name='NagMe')
    if nag_role not in ctx.author.roles:
        await ctx.author.add_roles(nag_role)
        em = Embed(title=':bell: Ping Notification Enabled',
                   description='You will be pinged by the bot whenever the timer goes off. \nPress on the react buttons or use `toggleping` to disable bot pings.',
                   color=MsgColors.BLACK.value)
    else:
        await ctx.author.remove_roles(nag_role)
        em = Embed(title=':no_bell: Ping Notification Disabled',
                   description='You won\'t be pinged by the bot anymore. \nPress on the react buttons or use `toggleping` to enable bot pings.',
                   color=MsgColors.BLACK.value)
    msg = await ctx.send(embed=em)
    await msg.add_reaction('🔔')
    await msg.add_reaction('🔕')


@bot.command(name='help', help='Describes all bot commands')
async def help(ctx):
    help_commands = dict()
    for command in bot.commands:
        help_commands[command.name] = command.help

    desc = 'The prefix for this bot is `' + COMMAND_PREFIX + '`\n'  # Prints ordered list of timer commands
    desc += f'\n**Timer Commands | {len(TIMER_COMMANDS)}**\n'
    for command in TIMER_COMMANDS:
        desc += '`{:12s}` {}\n'.format(command, help_commands[command])

    desc += f'\n**General Commands | {len(GENERAL_COMMANDS)}**\n'  # Prints ordered list of general commands
    for command in GENERAL_COMMANDS:
        desc += '`{:12s}` {}\n'.format(command, help_commands[command])

    desc += f'\n**Other**\n'
    desc += 'Pressing on the bell icons will enable/disable bot pings\nwhenever the timer runs out.'

    em = Embed(title='Bot Commands',
               description=desc,
               color=MsgColors.PURPLE.value)
    msg = await ctx.send(embed=em)
    await msg.add_reaction('🔔')
    await msg.add_reaction('🔕')


@bot.event
async def on_reaction_add(reaction, user):
    if not user.bot:                                    # Prevents bot from adding/removing roles to itself
        nag_role = get(user.guild.roles, name='NagMe')
        if reaction.emoji == '🔔':
            await user.add_roles(nag_role)
            em = Embed(title=':bell: Ping Notification Enabled',
                       description='You will be pinged by the bot whenever the timer goes off.',
                       color=MsgColors.BLACK.value)
        elif reaction.emoji == '🔕':
            await user.remove_roles(nag_role)
            em = Embed(title=':bell: Ping Notification Enabled',
                       description='You won\'t be pinged by the bot anymore.',
                       color=MsgColors.BLACK.value)
        await user.send(embed=em)


async def run_timer(duration: int, ctx):
    timer.start(duration)
    repeat_mode = 'On' if config['CURRENT_SETTINGS']['repeat'] == 'True' else 'Off'

    em = Embed(title=':timer: Timer Running',
               description=getFrmtTime(timer) + f'\nAuto-Repeat Mode: `{repeat_mode}`',
               color=MsgColors.AQUA.value)
    msg = await ctx.send(embed=em)
    await msg.add_reaction('🔔')
    await msg.add_reaction('🔕')

    while timer.get_status() == TimerStatus.RUNNING:
        await asyncio.sleep(1)
        timer.tick()
        if DEBUG: print('Tick', timer.get_time())
    if timer.get_status() == TimerStatus.STOPPED:
        if DEBUG: print('Time up')
        nag_role = get(ctx.guild.roles, name='NagMe')
        ping_message = config['CURRENT_SETTINGS']['message']
        em = Embed(title=':timer: Time Up',
                   description=f'{nag_role.mention} \n{ping_message}',
                   color=MsgColors.AQUA.value)
        msg = await ctx.send(embed=em)
        await msg.add_reaction('🔔')
        await msg.add_reaction('🔕')


# ------------ UTILITY FUNCTIONS -------------------
def getFrmtTime(clock: Timer):
    time_secs = clock.get_time() % 60
    time_mins = int((clock.get_time() - time_secs) / 60)
    if time_secs < 10:  # Formats seconds if <10 seconds left
        time_secs = '0' + str(time_secs)

    return f'Time Remaining: `{time_mins}:{time_secs}`'


# ------------ ERROR HANDLING --------------
@set_time.error
async def set_time_error(ctx, error):
    if DEBUG: print(f'Caught `settime` error: {ctx.message.content}\n  {ctx.message}\n  {error.args[0]}\n')

    if isinstance(error, commands.errors.MissingRequiredArgument):
        em = Embed(title=':warning: Invalid `settime` Command Usage',
                   description='Specify a timer duration (in minutes). \nFormat: `settime #`',
                   color=MsgColors.YELLOW.value)
    elif isinstance(error, commands.errors.BadArgument):
        em = Embed(title=':warning: Invalid `settime` Command Usage',
                   description='Specify a valid # for the timer duration. \nFormat: `settime #`',
                   color=MsgColors.YELLOW.value)
    else:
        with open('error.log', 'a') as errorLog:
            errorLog.write(f'Unhandled `settime` message: {ctx.message.content}\n  {ctx.message}\n  {error.args[0]}\n')
        em = Embed(title=':x: Unhandled `settime` Error',
                   description=f'Unhandled `settime` error has occurred.\n{error.logs[0]} See `error.log` for more information.',
                   color=MsgColors.RED.value)
    await ctx.send(embed=em)


@set_message.error
async def set_message_error(ctx, error):
    if DEBUG: print(f'Caught `setmessage` error: {ctx.message.content}\n  {ctx.message}\n  {error.args[0]}\n')

    if isinstance(error, commands.errors.MissingRequiredArgument):
        em = Embed(title=':warning: Invalid `setmessage` Command Usage',
                   description='Specify a message for pinging. \nFormat: `setmessage your_message_here`',
                   color=MsgColors.YELLOW.value)
    else:
        with open('error.log', 'a') as errorLog:
            errorLog.write(f'Unhandled `setmessage` message: {ctx.message.content}\n  {ctx.message}\n  {error.args[0]}\n')
        em = Embed(title=':x: Unhandled `setmessage` Error',
                   description=f'Unhandled `setmessage` error has occurred. \n{error.args[0]} \nSee `error.log` for more information.',
                   color=MsgColors.RED.value)
    await ctx.send(embed=em)


@toggle_ping.error
async def toggle_ping_error(ctx, error):
    if DEBUG: print(f'Caught `toggleping` error: {ctx.message.content}\n  {ctx.message}\n  {error.args[0]}\n')

    if 'Missing Permissions' in error.args[0]:
        em = Embed(title=':x: Invalid `toggleping` Command Usage',
                   description='Bot has no permissions to create roles. Ensure that the bot has the `Manage Roles` permission',
                   color=MsgColors.RED.value)
    else:
        with open('error.log', 'a') as errorLog:
            errorLog.write(f'Unhandled `toggleping` message: {ctx.message.content}\n  {ctx.message}\n  {error.args[0]}\n')
        em = Embed(title=':x: Unhandled `toggleping` Error',
                   description=f'Unhandled `toggleping` error has occurred. \n{error.args[0]} \nSee `error.log` for more information.',
                   color=MsgColors.RED.value)
    await ctx.send(embed=em)


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('settings.ini')
    bot.run(TOKEN)
