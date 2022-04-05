import os
import sys
import json
import re
import requests

from utils import checks, config

import disnake
from disnake.ext import commands
from disnake.ext.commands import (
    CommandInvokeError,
    CommandNotFound,
)
from disnake.ext.commands import MissingAnyRole

COGS = ('cogsmisc.repl',)

PREFIX = "??"
NEWLINE = "\n"

intents = disnake.Intents.all()

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or(PREFIX),
    pm_help=False,
    case_insensitive=True,
    intents=intents,
    owner_id=config.OWNER_ID,
)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        error_msg = f"Command not found. View `{PREFIX}help` for valid commands."
    elif isinstance(error, CommandInvokeError):
        error_msg = (
            f"Incorrect invocation. Please re-examine the command in `{PREFIX}help`."
        )
    elif isinstance(error, MissingAnyRole):
        error_msg = "You don't have any of the roles required to run this command."
    await ctx.message.channel.send(f"Error: {error_msg} ({error})")
    return


@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")


@bot.command()
@checks.is_owner()
async def restart(ctx):
    await ctx.send("Restarting...")
    print("Restarting...")
    os.execv(sys.executable, ["python"] + sys.argv)


@bot.command()
async def get_bags(ctx, url):
    regex = r"^.*characters\/(\d+)\/?"
    match = re.search(regex, url)
    if match:
        out = {
            "Backpack": {},
            "Equipment": {},
            "Magical Items": {},
            "Consumables": {},
            "Harvest": {},
        }
        url = f"https://character-service.dndbeyond.com/character/v3/character/{match.group(1)}"
        resp = requests.get(url)
        json_data = json.loads(resp.content)
        for item in json_data["data"]["inventory"]:
            bag_name = "Backpack"
            if item["definition"]["magic"]:
                bag_name = "Magical Items"
            elif item["definition"]["canEquip"]:
                bag_name = "Equipment"
            elif item["definition"]["isConsumable"]:
                bag_name = "Consumables"
            item_name = item["definition"]["name"]
            quantity = item["quantity"]
            out[bag_name][item_name] = out[bag_name].get(item_name, 0) + quantity
        await ctx.send(f"""```json\n!cvar bags {json.dumps(list(out.items()))}\n```""")


for cog in COGS:
    bot.load_extension(cog)

bot.run(config.TOKEN)
