import os
import configparser
import asyncio
from enum import Enum
from dotenv import load_dotenv
from discord.ext import commands
from discord.utils import get
from discord import Embed

from timer import Timer, TimerStatus        # Custom timer and timer status Enum

DEBUG = False
COMMAND_PREFIX = '*'
SETTING_OPTIONS = ['time', 'repeat', 'message']
TIMER_COMMANDS = ['start', 'pause', 'time', 'settime', 'setmessage', 'toggleping', 'togglerepeat']
GENERAL_COMMANDS = ['reset', 'help']

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
bot = commands.Bot(command_prefix=COMMAND_PREFIX, help_command=None)
timer = Timer()


class MsgColors(Enum):
    """Contains color values in hex for use in Discord Embeds"""
    AQUA = 0x33c6bb
    YELLOW = 0xFFD966
    RED = 0xEA3546
    PURPLE = 0x6040b1
    WHITE = 0xFFFFFF
    BLACK = 0x000000


@bot.event
async def on_ready():
    """Prints connection success in console on bot initialization."""
    print(f'{bot.user} has connected to Discord.')


@bot.command(name='start', help='Starts/resumes the timer for nagging', aliases=['resume'])
async def start_timer(ctx):
    """Starts or resumes timer countdown and repeats if specified."""
    status = timer.get_status()
    # Grabs settings and timer duration from `settings.ini`
    repeat_mode = config['CURRENT_SETTINGS']['repeat']
    time_mins = config['CURRENT_SETTINGS']['time']
    time_full = int(time_mins) * 60

    # Create role here in case user starts timer before triggering toggleping
    nag_role = get(ctx.guild.roles, name='NagMe')
    if nag_role is None:
        await ctx.guild.create_role(name='NagMe', mentionable=True, colour=MsgColors.AQUA)
        if DEBUG:
            print(f'Created NagMe role for `{ctx.guild.name}`')

    if status == TimerStatus.STOPPED:                                               # Starting timer from stopped state
        await run_timer(time_full, ctx)
        while repeat_mode == 'True' and timer.get_status() != TimerStatus.PAUSED:   # Loop if repeat mode enabled
            await run_timer(time_full, ctx)
            repeat_mode = config['CURRENT_SETTINGS']['repeat']                      # Check repeat mode is enabled
    elif status == TimerStatus.PAUSED:                                              # Resuming timer from paused state
        timer.resume()
        await run_timer(time_full, ctx)
        while repeat_mode == 'True' and timer.get_status() != TimerStatus.PAUSED:   # Loop if repeat mode enabled
            repeat_mode = config['CURRENT_SETTINGS']['repeat']                      # Check repeat mode is enabled
            await run_timer(time_full, ctx)
    else:
        em = Embed(title=':warning: Alert',
                   description='Timer is already running.',
                   color=MsgColors.YELLOW.value)
        await ctx.send(embed=em)


@bot.command(name='pause', help='Pauses/stops the timer', aliases=['stop'])
async def pause_timer(ctx):
    """Pauses the timer countdown."""
    repeat_mode = 'On' if config['CURRENT_SETTINGS']['repeat'] == 'True' else 'Off'
    if timer.pause():
        em = Embed(title=':pause_button: Paused Timer',
                   description=getFrmtTime(timer) + f'\nAuto-Repeat Mode: `{repeat_mode}`',
                   color=MsgColors.YELLOW.value)
    else:
        em = Embed(title=':warning: Alert',
                   description='Timer is already paused/stopped.\n' + getFrmtTime(timer),
                   color=MsgColors.YELLOW.value)
    await ctx.send(embed=em)


@bot.command(name='time', help='Displays remaining time and timer settings', aliases=['status', 'settings', 'timer'])
async def status(ctx):
    """Displays remaining time before ping and timer settings."""
    raw_time = timer.get_time()
    time_secs = raw_time % 60
    time_mins = int((raw_time - time_secs) / 60)
    if time_secs < 10:
        time_secs = '0' + str(time_secs)
    time_desc = f'Time Remaining: `{time_mins}:{time_secs}`\n'
    settings_desc = 'Timer Duration Setting: `' + config['CURRENT_SETTINGS']['time'] + ' minute(s)`\n'
    msg_desc = 'Ping Message: `' + config['CURRENT_SETTINGS']['message'] + '`\n'
    repeat_desc = 'Auto-Repeat Mode: `On`' if config['CURRENT_SETTINGS']['repeat'] == 'True' else 'Auto-Repeat Mode: `Off`'
    em = Embed(title=':gear: Current Settings',
               description=time_desc + settings_desc + msg_desc + repeat_desc,
               color=MsgColors.BLACK.value)
    await ctx.send(embed=em)


@bot.command(name='settime', help='Sets the timer duration (in minutes)', aliases=['set'])
async def set_time(ctx, time: int):
    """Configures the timer countdown duration."""
    if time <= 0:                                                           # Force duration to be 1 minute or longer
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
    """Configures the timer ping message."""
    config.set('CURRENT_SETTINGS', 'message', message)
    with open('settings.ini', 'w') as configFile:
        config.write(configFile)
    em = Embed(title=':gear: Ping Message Changed',
               description=f'Ping message has been set to `{message}`.',
               color=MsgColors.BLACK.value)
    await ctx.send(embed=em)


@bot.command(name='toggleping', help='Toggles the bot from pinging you', aliases=['ping'])
async def toggle_ping(ctx):
    """Removes/adds a role to a user to toggle pings from the bot."""
    # Checks if the `NagMe` role already exists for pings
    nag_role = get(ctx.guild.roles, name='NagMe')
    if nag_role is None:
        await ctx.guild.create_role(name='NagMe', mentionable=True, colour=MsgColors.AQUA)
        if DEBUG:
            print(f'Created NagMe role for `{ctx.guild.name}`')
        nag_role = get(ctx.guild.roles, name='NagMe')
    # Checks if the user has the role; assign the user the role if not, else remove the role
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
    # Add 'bell' and 'crossed bell' emojis for `on_reaction_add` event
    await msg.add_reaction('🔔')
    await msg.add_reaction('🔕')


@bot.command(name='togglerepeat', help='Toggles auto-repeat mode for the timer', aliases=['repeat'])
async def toggle_repeat(ctx):
    """Configures if the timer automatically repeats after countdown finishes."""
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


@bot.command(name='reset', help='Resets bot settings to default settings')
async def reset(ctx, confirm=''):
    """Resets bot configuration to default settings."""
    # Force user to enter `*reset confirm` to confirm resetting settings to defaults
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
        em = Embed(title=':gear: Settings Reset',
                   description='Bot settings have been reset to default values.',
                   color=MsgColors.BLACK.value)
        await ctx.send(embed=em)


@bot.command(name='help', help='Describes all bot commands')
async def help(ctx):
    """Displays all commands and their associated descriptions to the user."""
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
    # Add 'bell' and 'crossed bell' emojis for `on_reaction_add` event
    await msg.add_reaction('🔔')
    await msg.add_reaction('🔕')


@bot.event
async def on_reaction_add(reaction, user):
    """Removes/adds a role to a user to toggle pings from the bot based on emoji reactions."""
    if not user.bot:                                    # Prevents bot from adding/removing roles to itself
        nag_role = get(user.guild.roles, name='NagMe')
        if reaction.emoji == '🔔':                       # `bell` emoji adds ping role to user
            await user.add_roles(nag_role)
            em = Embed(title=':bell: Ping Notification Enabled',
                       description='You will be pinged by the bot whenever the timer goes off.',
                       color=MsgColors.BLACK.value)
            await user.send(embed=em)
        elif reaction.emoji == '🔕':                     # `crossed out bell` emoji removes ping role from user
            await user.remove_roles(nag_role)
            em = Embed(title=':bell: Ping Notification Enabled',
                       description='You won\'t be pinged by the bot anymore.',
                       color=MsgColors.BLACK.value)
            await user.send(embed=em)


# --------------- HELPER / UTILITY FUNCTIONS ---------------
async def run_timer(duration: int, ctx):
    """Runs timer countdown and pings users when countdown ends.

    Args:
        duration : int
            Timer duration to countdown in seconds
        ctx : discord.ext.commands.context.Context
            Context for the command being executed
    Returns:
        n/a
    """
    timer.start(duration)
    repeat_mode = 'On' if config['CURRENT_SETTINGS']['repeat'] == 'True' else 'Off'

    em = Embed(title=':timer: Timer Running',
               description=getFrmtTime(timer) + f'\nAuto-Repeat Mode: `{repeat_mode}`',
               color=MsgColors.AQUA.value)
    msg = await ctx.send(embed=em)
    # Add 'bell' and 'crossed bell' emojis for `on_reaction_add` event
    await msg.add_reaction('🔔')
    await msg.add_reaction('🔕')

    while timer.get_status() == TimerStatus.RUNNING:
        await asyncio.sleep(1)
        timer.tick()
    if timer.get_status() == TimerStatus.STOPPED:
        nag_role = get(ctx.guild.roles, name='NagMe')
        ping_message = config['CURRENT_SETTINGS']['message']
        await ctx.send(nag_role.mention)                    # Send ping separately from embed (embed doesn't trigger ping)
        em = Embed(title=':timer: Time Up',
                   description=ping_message,
                   color=MsgColors.AQUA.value)
        msg = await ctx.send(embed=em)
        await msg.add_reaction('🔔')
        await msg.add_reaction('🔕')


def getFrmtTime(clock: Timer):
    """Returns formatted time in hrs:mins for custom timer class"""
    time_secs = clock.get_time() % 60
    time_mins = int((clock.get_time() - time_secs) / 60)
    if time_secs < 10:  # Formats seconds if <10 seconds left
        time_secs = '0' + str(time_secs)

    return f'Time Remaining: `{time_mins}:{time_secs}`'


# --------------- ERROR HANDLING ---------------
@set_time.error
async def set_time_error(ctx, error):
    """Catches *settime command errors and logs unhandled errors.

    Args:
        ctx : discord.ext.commands.context.Context
            Context for the command being executed
        error : discord.ext.commands.errors
            Error object from raising exception
    Returns:
        n/a
    """
    if DEBUG:
        print(f'Caught `settime` error: {ctx.message.content}\n  {ctx.message}\n  {error.args[0]}\n')

    if isinstance(error, commands.errors.MissingRequiredArgument):              # Missing duration argument
        em = Embed(title=':warning: Invalid `settime` Command Usage',
                   description='Specify a timer duration (in minutes). \nFormat: `settime #`',
                   color=MsgColors.YELLOW.value)
    elif isinstance(error, commands.errors.BadArgument):                        # Duration amount isn't a valid int
        em = Embed(title=':warning: Invalid `settime` Command Usage',
                   description='Specify a valid # for the timer duration. \nFormat: `settime #`',
                   color=MsgColors.YELLOW.value)
    else:                                                                       # Unhandled exception
        with open('error.log', 'a') as errorLog:
            errorLog.write(f'Unhandled `settime` message: {ctx.message.content}\n  {ctx.message}\n  {error.args[0]}\n')
        em = Embed(title=':x: Unhandled `settime` Error',
                   description=f'Unhandled `settime` error has occurred.\n{error.logs[0]} See `error.log` for more information.',
                   color=MsgColors.RED.value)
    await ctx.send(embed=em)


@set_message.error
async def set_message_error(ctx, error):
    """Catches *setmessage command errors and logs unhandled errors.

        Args:
            ctx : discord.ext.commands.context.Context
                Context for the command being executed
            error : discord.ext.commands.errors
                Error object from raising exception
        Returns:
            n/a
        """
    if DEBUG:
        print(f'Caught `setmessage` error: {ctx.message.content}\n  {ctx.message}\n  {error.args[0]}\n')

    if isinstance(error, commands.errors.MissingRequiredArgument):              # Missing message argument
        em = Embed(title=':warning: Invalid `setmessage` Command Usage',
                   description='Specify a message for pinging. \nFormat: `setmessage your_message_here`',
                   color=MsgColors.YELLOW.value)
    else:                                                                       # Unhandled exception
        with open('error.log', 'a') as errorLog:
            errorLog.write(f'Unhandled `setmessage` message: {ctx.message.content}\n  {ctx.message}\n  {error.args[0]}\n')
        em = Embed(title=':x: Unhandled `setmessage` Error',
                   description=f'Unhandled `setmessage` error has occurred. \n{error.args[0]} \nSee `error.log` for more information.',
                   color=MsgColors.RED.value)
    await ctx.send(embed=em)


@toggle_ping.error
async def toggle_ping_error(ctx, error):
    """Catches *toggleping command errors and logs unhandled errors.

        Args:
            ctx : discord.ext.commands.context.Context
                Context for the command being executed
            error : discord.ext.commands.errors
                Error object from raising exception
        Returns:
            n/a
        """
    if DEBUG:
        print(f'Caught `toggleping` error: {ctx.message.content}\n  {ctx.message}\n  {error.args[0]}\n')

    if 'Missing Permissions' in error.args[0]:                              # Bot is missing permissions to create a ping role
        em = Embed(title=':x: Invalid `toggleping` Command Usage',
                   description='Bot has no permissions to create roles. Ensure that the bot has the `Manage Roles` permission',
                   color=MsgColors.RED.value)
    else:                                                                   # Unhandled exception
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
