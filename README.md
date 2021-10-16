# WildMagic Bot
A Discord bot for use on the Waifus & Warriors Discord server.

## Creating Support Files
You'll need to create a Google Drive Service Account. You can find instructions on how to do this [here](https://docs.gspread.org/en/latest/oauth2.html#using-signed-credentials).

Follow steps 1-3 in the Signed Credentials portion. Rename the JSON ``service_account.json`` and put it in the project root.

## Avrae Token
In order for this plugin to have your permissions to grab and update your GVARs, Workshop Aliases, or Workshop Snippets, you need to give it your token.

1. Go to [Avrae](https://avrae.io) and log in to the dashboard
2. Press F12 to open the DevTools
3. Go to the 'Application' tab
4. On the left, select 'https://avrae.io' under 'Local Storage'
5. Copy the 'Value' next to the 'avrae-token' key
6. In `\utils\.env`, paste the token after the `AVRAE_TOKEN=` key.
7. Be sure to update your Discord token while you're in there!
