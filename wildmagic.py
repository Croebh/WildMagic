from typing import List
import os
import sys
import json
import io
from urllib.request import urlopen, Request
import re
import requests

from utils import checks, config
from utils.utils import feet_and_inches, avraeREST, Dropdown, DropdownView

import textwrap
import traceback
from contextlib import redirect_stdout

import discord
from utils.argparser import argparse
from discord.errors import Forbidden, HTTPException, InvalidArgument, NotFound
from discord.ext import commands
from discord.ext.commands.errors import CommandInvokeError
from discord.ext.commands import CheckFailure, CommandInvokeError, CommandNotFound, MemberNotFound
from discord.ext.commands import guild_only, NoPrivateMessage, has_role, has_any_role, MissingRole, UserNotFound
from discord.ext.commands import MissingAnyRole

COGS =  ('cogsmisc.repl', 'cogschar.char', 'cogspoll.poll', 'w4rcogs.reactrole')

PREFIX = "!!"
NEWLINE = "\n"

intents = discord.Intents.all()

bot = commands.Bot(command_prefix=commands.when_mentioned_or(PREFIX),
                   pm_help=False,
                   case_insensitive=True,
                   intents=intents,
                   owner_id=config.OWNER_ID)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        error_msg = f"Command not found. View `{PREFIX}help` for valid commands."
    elif isinstance(error, CommandInvokeError):
        error_msg = f"Incorrect invocation. Please re-examine the command in `{PREFIX}help`."
    elif isinstance(error, MissingAnyRole):
        error_msg = "You don't have any of the roles required to run this command."
    await ctx.message.channel.send(f"Error: {error_msg} ({error})")
    return

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.command()
@checks.is_owner()
async def restart(ctx):
  await ctx.send("Restarting...")
  print("Restarting...")
  os.execv(sys.executable, ['python'] + sys.argv)

for cog in COGS:
  bot.load_extension(cog)

bot.run(config.TOKEN)
