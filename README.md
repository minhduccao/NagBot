# NagBot
NagBot is a Discord bot written in Python using the discord.py API wrapper to remind users of water and posture checks. At the moment, it is intended to run on a single Discord server per bot instance.

See a [list of all commands here](https://github.com/minhduccao/NagBot/wiki/Bot-Command-Reference).

# Features
1. Timer to remind users every x minutes with options to disable repeating pings
2. Adjustable timer duration and ping message
3. Easily add or remove self from bot pings via emoji reactions or bot command
4. Ability to reset settings to default
5. Logs errors to a separate file

# Dependencies
```
discord.py
discord
python-dotenv
```

# Installation (Self-Hosting)
1. Clone the NagBot repository
2. Install all dependencies from `requirements.txt`
3. Create a Discord developer account and create an application
4. Copy the application token into the `.env` file 
5. Generate an OAuth2 URL with `bot` scope and `Administrator` permission
6. Use the URL to add the bot to the specified Discord server and run `bot.py`

# File Breakdown
```
bot.py        | Code for NagBot and its functions
timer.py      | Custom timer class with countdown and timer states
settings.ini  | Settings for timer duration, repeating timer mode, ping message
.env          | Discord application token for bot
```



