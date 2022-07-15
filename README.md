# WildMagic Bot
A Discord bot for use on the Maritime Monsters Discord server.

## Setting up the bot
There are a few things that need to be set up before you can run/use this bot:
1. A Google service account (``service_account.json``)
2. A Discord token and Avrae token, saved into ``utils\.env``
   * It should follow this format:
     ```env
     DISCORD_TOKEN=
     AVRAE_TOKEN=
     ```
3. Add your Discord id to the ``utils\config.py`` file

### Google Service Account
You'll need to create a Google Drive Service Account. You can find instructions on how to do this [here](https://docs.gspread.org/en/latest/oauth2.html#using-signed-credentials).

Follow steps 1-3 in the Signed Credentials portion. Rename the JSON ``service_account.json`` and put it in the project root.

### Avrae Token
In order for this plugin to have your permissions to grab and update your GVAR.

1. Go to [Avrae](https://avrae.io) and log in to the dashboard
2. Press F12 to open the DevTools
3. Go to the 'Application' tab
4. On the left, select 'https://avrae.io' under 'Local Storage'
5. Copy the 'Value' next to the 'avrae-token' key
6. In ``utils\.env``, paste the token after the ``AVRAE_TOKEN=`` key.

### Discord Token
You'll also need to have a valid Discord bot token.

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications/)
2. Select your bot/application
3. On the left, select 'Bot'
4. Under Build-A-Bot, select 'Copy Token'
5. In ``utils\.env``, paste the token after ``DISCORD_TOKEN=``

### Discord User ID
In order for the bot to recognize you as the owner, you'll need to add your Discord user ID to the ``utils\config.py`` file.

1. In Discord, enable Developer Mode
  1. [Try This Link](discord://-/settings/advanced)
  2. If that doesn't work, go into your user settings, then, under App Settings, click Advanced
2. Right click your profile picture and select Copy ID
3. In ``utils\config.py``, replace the existing number after ``OWNERID=`` with your own ID

## Running the bot
Simply run ``start.bat`` and it will start up. You can use the ``!!restart`` comman