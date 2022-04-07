import os
import sys
import json
import re
import requests

from utils import checks, config, utils

import disnake
from disnake.ext import commands
from disnake.ext.commands import (
    CommandInvokeError,
    CommandNotFound,
    MissingRequiredArgument
)
from disnake.ext.commands import MissingAnyRole

COGS = ('cogsmisc.repl',)

PREFIX = "??"
NEWLINE = "\n"

intents = disnake.Intents.all()


class CustomHelp(commands.DefaultHelpCommand):

    async def send_pages(self):
        destination = self.get_destination()
        for page in self.paginator.pages:
            embed = disnake.Embed(description=page)
            await destination.send(embed=embed)

    def add_indented_commands(self, commands, *, heading, max_size=None):
        if not commands:
            return

        self.paginator.add_line(heading)
        max_size = max_size or self.get_max_size(commands)

        for command in commands:
            name = command.name
            params = [f"" for param in command.clean_params]
            entry = f'`{PREFIX}{name} {command.signature}` - {command.short_doc}'
            self.paginator.add_line(entry)

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or(PREFIX),
    pm_help=False,
    case_insensitive=True,
    intents=intents,
    owner_id=config.OWNER_ID,
    help_command=CustomHelp(sort_commands=False,
                            width=1000,
                            paginator=commands.Paginator(prefix=None, suffix=None),
                            no_category="Uncategorized")
)


@bot.event
async def on_command_error(ctx, error):
    error_msg = "You done goofed?"
    if isinstance(error, CommandNotFound):
        error_msg = f"Command not found. View `{PREFIX}help` for valid commands."
    elif isinstance(error, (CommandInvokeError, MissingRequiredArgument)):
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


@bot.command(hidden=True)
@checks.is_owner()
async def restart(ctx):
    """Restarts the bot"""
    await ctx.send("Restarting...")
    print("Restarting...")
    os.execv(sys.executable, ["python"] + sys.argv)


@bot.command()
async def get_bags(ctx, url):
    """Generates a command to set up the `!bag` alias, given a provided DDB character sheet."""
    await utils.try_delete(ctx.message)
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
        json_data = json.loads(resp.content)['data']
        for item in json_data["inventory"]:
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
    else:
        await ctx.send("Unable to find a valid DDB character link.")


@bot.command()
async def get_desc(ctx, url):
    """Generates a command to set up your characters description, given a provided DDB character sheet."""
    await utils.try_delete(ctx.message)
    regex = r"^.*characters\/(\d+)\/?"
    match = re.search(regex, url)

    alignments = ["LG", "NG", "CG",
                  "LN", "TN", "CN",
                  "LE", "NE", "CE"]

    if match:
        url = f"https://character-service.dndbeyond.com/character/v3/character/{match.group(1)}"
        resp = requests.get(url)
        json_data = json.loads(resp.content)['data']
        classes = []
        for _class in json_data['classes']:
            cur_class = _class['definition']['name']
            if _class['subclassDefinition']:
                cur_class += f" ({_class['subclassDefinition']['name']})"
            classes.append(cur_class)
        out = {
            "height": json_data["height"] or "height",
            "weight": f'{json_data["weight"]} lb.' or "weight",
            "race": json_data['race']['fullName'] or "race",
            "class": '/'.join(classes) or "class",
            "appearance": json_data['traits']["appearance"] or "Write a bit about attitude, appearance, and background here.",
            "traits": json_data['traits']["personalityTraits"] or "Enter your dndbeyond rolled trait(s) here\nEnter your dndbeyond rolled trait(s) here",
            "ideals": json_data['traits']["ideals"] or "Enter your dndbeyond rolled ideal(s) here",
            "bonds": json_data['traits']["bonds"] or "Enter your dndbeyond rolled bond(s) here",
            "flaws": json_data['traits']["flaws"] or "Enter your dndbeyond rolled flaw(s) here",
            "alignment": alignments[json_data['alignmentId']-1]if json_data['alignmentId'] else "Enter your alignment"
        }
        desc_out = f""""""
        await ctx.send(f"""```md\n!desc update __**{out['height']} | {out['weight']} | {out['race']} | {out['class']}**__
> {out["appearance"]}
**Personality Traits**
{out["traits"]}
**Ideals**
{out["ideals"]}
**Bonds**
{out["bonds"]}
**Flaws**
{out["flaws"]}
**Alignment**
{out["alignment"]}\n```""")
    else:
        await ctx.send("Unable to find a valid DDB character link.")


@bot.command()
async def get_tools(ctx, url):
    """Generates a command to set up your tool proficiencies for `!tool`, given a provided DDB character sheet."""
    await utils.try_delete(ctx.message)
    regex = r"^.*characters\/(\d+)\/?"
    match = re.search(regex, url)

    if match:
        url = f"https://character-service.dndbeyond.com/character/v3/character/{match.group(1)}"
        resp = requests.get(url)
        json_data = json.loads(resp.content)['data']
        profs = []
        expertise = []
        for _type in json_data['modifiers']:
            for modifier in json_data['modifiers'][_type]:
                if modifier['entityTypeId'] == 2103445194:
                    if modifier['type'] == 'proficiency':
                        profs.append(modifier['friendlySubtypeName'])
                    if modifier['type'] == 'expertise':
                        expertise.append(modifier['friendlySubtypeName'])
        out = []
        if profs:
            out.append(f"""`!cvar pTools {', '.join(profs)}`""")
        if expertise:
            out.append(f"""`!cvar eTools {', '.join(expertise)}`""")
        await ctx.send('\n'.join(out) or "No tool proficiencies found.")
    else:
        await ctx.send("Unable to find a valid DDB character link.")


@bot.command()
async def new_char(ctx, url):
    """Runs the various commands that assist with creating new characters, given a provided DDB character sheet."""
    _commands = ['get_desc', 'get_bags', 'get_tools']
    for command in _commands:
        command = bot.get_command(command)
        await ctx.invoke(command, url=url)

for cog in COGS:
    bot.load_extension(cog)

bot.run(config.TOKEN)
