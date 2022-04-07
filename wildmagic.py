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

COGS = ('cogsmisc.repl', 'cogsddb.charinfo')

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

for cog in COGS:
    bot.load_extension(cog)

bot.run(config.TOKEN)
