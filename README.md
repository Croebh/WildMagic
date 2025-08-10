# Wildmagic Bot
A multiuse Discord bot, with some utility commands for my personal use, and a variety of commands for the Northern Lights Province Discord server.

## Setting up the bot
There are a few things that need to be set up before you can run/use this bot:
1. A Google service account (``service_account.json``)
2. A Discord token, Avrae token, and DDB Bearer Token, saved into ``docker\env``

## Docker Setup
1. Create a `docker\env` file with real credentials (Reference the example below).
2. Run `docker-compose up --build`.
3. Wait for the bot to start up and join your server.
4. Stop the bot by pressing `Ctrl+C` in the terminal.
5. Run `docker-compose down -v` to remove the containers and volumes.

```env
AVRAE_TOKEN=
BEARER_TOKEN=
DISCORD_TOKEN=
```

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
6. In ``docker\env``, paste the token after the ``AVRAE_TOKEN=`` key.

### Discord Token
You'll also need to have a valid Discord bot token.

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications/)
2. Select your bot/application
3. On the left, select 'Bot'
4. Under Build-A-Bot, select 'Copy Token'
5. In ``docker\env``, paste the token after ``DISCORD_TOKEN=``

### DDB Bearer Token
If you want to grab sheet data, you'll want your DDB Bearer token

1. Go to [D&D Beyond](https://www.dndbeyond.com/)
2. Press F12 to open the DevTools
3. Go to the 'Application' tab
4. On the left, select 'https://www.dndbeyond.com/' under 'Cookies'
5. Copy the 'Value' next to the 'cobalt-token' key
6. In ``docker\env``, paste the token after the ``BEARER_TOKEN=`` key.