from typing import List
import os
import sys
import json
import gspread
import io
from urllib.request import urlopen, Request
import re
import requests

headers = {
            'Authorization': "",
            'Accept': 'application/json, text/plain, */*',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
            'Content-Type': 'application/json',
            'Sec-Fetch-Site': 'same-site',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty'
          }


from utils import checks, config

import textwrap
import traceback
from contextlib import redirect_stdout

import discord
from utils.argparser import argparse
from discord.errors import Forbidden, HTTPException, InvalidArgument, NotFound
from discord.ext import commands
from discord.ext.commands.errors import CommandInvokeError
from discord.ext.commands import CheckFailure, CommandInvokeError, CommandNotFound, MemberNotFound  # Error handling imports.
from discord.ext.commands import guild_only, NoPrivateMessage, has_role, has_any_role, MissingRole, UserNotFound
from discord.ext.commands import MissingAnyRole

gc = gspread.service_account(filename="service_account.json")
sh = gc.open_by_url("https://docs.google.com/spreadsheets/d/18AfHOEBS0CMYERtO6O6fCoME8jB9wVm_Gc5FIni3ryE/edit#gid=0")

DDB_URL_RE = re.compile(r"(?:https?://)?(?:www\.dndbeyond\.com|ddb\.ac)(?:/profile/.+)?/characters/(\d+)/?")

PREFIX = "!!"
COLUMNS = ['Player' ,'Character Name' ,'Race' ,'Level' ,'Class 1' ,'Subclass 1' ,'Class 2' ,'Subclass 2' ,'Class 3' ,'Subclass 3' ,'Class 4' ,'Subclass 4' ,'URL' ,'Gender' ,'Height (Decimal Ft)']
intents = discord.Intents.all()

NEWLINE = "\n"
bot = commands.Bot(command_prefix=commands.when_mentioned_or(PREFIX), pm_help=False, case_insensitive=True, intents=intents)

# @bot.event  # This defines an event, which listens for the condition specified, and then executes.
# async def on_command_error(ctx, error):  # This event executes when the bot hears that specified exceptions are caught.
#     if isinstance(error, CommandNotFound):  # This executes if a command is not found.
#         error_msg = f"Command not found. View `{PREFIX}help` for valid commands."
#     elif isinstance(error, CommandInvokeError):  # This executes if a command is used incorrectly, or in circumstances where a command cannot finish executing properly and there is no specific handling for the error the command invokes.
#         error_msg = f"Incorrect invocation. Please re-examine the command in `{PREFIX}help`."
#     elif isinstance(error, MissingAnyRole):  # This executes if a command is being used by someone who does not have the roles required to run it.
#         error_msg = "You don't have any of the roles required to run this command."
#     await ctx.message.channel.send(f"Error: {error_msg} ({error})")  # Sends the error message in the channel where the command was
#     # invoked.
#     return

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.command(aliases=['gvar_update', 'gvar'])
@checks.role_or_permissions('DM')
async def update_gvar(ctx, *args):
  all_characters = sh.sheet1.get_all_records()
  out = [{"player": char['Player'],
          "name": char['Character Name'],
          "sheet": char['URL'],
          "gender": char['Gender']
         } for char in all_characters]

  get, getStatus = avraeREST("GET", "customizations/gvars/5e8f9f82-616b-4828-b201-f0f9ea9368af")
  newPayload = get.json()
  newPayload.update({"value":json.dumps(out)})
  post, postStatus = avraeREST("POST", "customizations/gvars/5e8f9f82-616b-4828-b201-f0f9ea9368af", json.dumps(newPayload))

  if postStatus in (200, 201):
    await ctx.send('Gvar Updated')

@bot.command(aliases=['char', 'lookup_char'])
async def char_lookup(ctx, name:str):
  char   = name
  if char:
    all_characters = sh.sheet1.get_all_records()
    possible = []
    for i, character in enumerate(all_characters, 1):
      if character['Character Name'].lower() == char.lower():
        possible = [(i, character)]
        break
      if char.lower() in character['Character Name'].lower():
        possible.append((i, character))
    else:
      if not possible:
        await ctx.send(f"Error: Unable to find a character named: `{char}`")
        return
  if len(possible) > 1:
    options = [discord.SelectOption(label=char[1]['Character Name'],
                                    description=char[1]['Player'],
                                    value=str(i))
               for i, char in enumerate(possible[:25])]
    view = DropdownView(options=options)
    await ctx.send('Multiple Matches Found', view=view)
    await view.wait()
    i, character = possible[int(view.value)]
  else:
    i, character = possible[0]
  embed = discord.Embed(title       = f"{character['Character Name']} ({character['Player']})", 
                        url         = character['URL'])
  embed.add_field(name = 'Race', value=character['Race'] or 'Not Set')
  classes = [f"""{x}: {character[x]} {f"({character['Sub'+x.lower()]})" if character.get('Sub'+x.lower()) else ''}""" for x in ['Class 1', 'Class 2', 'Class 3', 'Class 4'] if character.get(x)]
  embed.add_field(name = 'Levels', value=f"""Level: {character['Level'] or 'Not Set'}\n{NEWLINE.join(classes)}""")
  embed.add_field(name = 'Details', value=f"""Height: {feet_and_inches(character.get('Height (Decimal Ft)')) or 'Not Set'}\nGender: {character.get('Gender')  or 'Not Set'}""")
  #if beyond_match := DDB_URL_RE.match(character['URL']):
  #  req = Request(f"""https://www.dndbeyond.com/character/{beyond_match.group(1)}/json""")
  #  req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:59.0) Gecko/20100101 Firefox/59.0')
  #  response = urlopen(req)
  #  
  #  char_json = json.loads(response.read())

  await ctx.send(embed=embed)

@bot.command()
async def height(ctx):
  all_characters = sh.sheet1.get_all_records()
  all_characters = [i for i in all_characters if i['Height (Decimal Ft)']]
  all_characters.sort(key = lambda t: float(t['Height (Decimal Ft)']))
  tall = [f"{i['Character Name']} ({i['Player']}):** {feet_and_inches(i['Height (Decimal Ft)'])}" for i in all_characters[-5:]]
  tall.reverse()
  tall = [f"**{i}. {t}" for i, t in enumerate(tall, 1)]
  short = [f"{i['Character Name']} ({i['Player']}):** {feet_and_inches(i['Height (Decimal Ft)'])}" for i in all_characters[:5]]
  short = [f"**{i}. {t}" for i, t in enumerate(short, 1)]
  embed = discord.Embed(title="Big and Small, we like em all!")
  embed.add_field(name="Tallest", value="\n".join(tall))
  embed.add_field(name="Shortest", value="\n".join(short))
  await ctx.send(embed=embed)

@bot.command(aliases=['newchar'])
@checks.role_or_permissions('DM')
async def new_char(ctx, *args):
  """Adds a new character to the spreadsheet. 
  Requires `-player`, `-name`, and `-url`, everything else is optional.

  `-player <player>` - The characters player
  `-name <name>` - The characters name
  `-url <url>` - The characters url

  `-race [race]` - The characters race
  `-level [level]` - The characters level
  `-class1 [class1]` - The characters first class
  `-subclass1 [subclass1]` - The characters first subclass
  `-class2 [class2]` - The characters second class
  `-subclass2 [subclass2]` - The characters second subclass
  `-class3 [class3]` - The characters third class
  `-subclass3 [subclass3]` - The characters third subclass
  `-class4 [class4]` - The characters fourth class
  `-subclass4 [subclass4]` - The characters fourth subclass
  `-gender [gender]` - The characters gender
  `-height [height]` - The characters height in decimal feet
  """
  parsed = argparse(args)
  player    = parsed.last("player", "")
  name      = parsed.last("name")
  race      = parsed.last("race", "")
  level     = parsed.last("level", "")
  class1    = parsed.last("class1", "")
  subclass1 = parsed.last("subclass1", "")
  class2    = parsed.last("class2", "")
  subclass2 = parsed.last("subclass2", "")
  class3    = parsed.last("class3", "")
  subclass3 = parsed.last("subclass3", "")
  class4    = parsed.last("class4", "")
  subclass4 = parsed.last("subclass4", "")
  url       = parsed.last("url")
  gender    = parsed.last("gender", "")
  height    = parsed.last("height", "")
  if name and player and url:
    all_characters = sh.sheet1.get_all_records()
    new_row  = len(all_characters) + 2 # Account for header and then add 1
    new_char = {'Player': player ,
                'Character Name': name ,
                'Race': race ,
                'Level': level ,
                'Class 1': class1 ,
                'Subclass 1': subclass1 ,
                'Class 2': class2 ,
                'Subclass 2': subclass2 ,
                'Class 3': class3 ,
                'Subclass 3': subclass3 ,
                'Class 4': class4 ,
                'Subclass 4': subclass4 ,
                'URL': url ,
                'Gender': gender ,
                'Height (Decimal Ft)': height}
    letter = "ABCDEFGHIJKLMNO"
    for i, col in enumerate(COLUMNS):
      if new_char[col]:
        sh.sheet1.update(f"{letter[i]}{new_row}", new_char[col])
    character = sh.sheet1.get_all_records()[new_row-2]
    embed = discord.Embed(title       = f"{character['Character Name']} ({character['Player']})",
                              url         = character['URL'])
    embed.add_field(name = 'Race', value=character['Race'] or 'Not Set')
    classes = [f"""{x}: {character[x]} {f"({character['Sub'+x.lower()]})" if character.get('Sub'+x.lower()) else ''}""" for x in ['Class 1', 'Class 2', 'Class 3', 'Class 4'] if character.get(x)]
    embed.add_field(name = 'Levels', value=f"""Level: {character['Level'] or 'Not Set'}\n{NEWLINE.join(classes)}""")
    embed.add_field(name = 'Details', value=f"""Height: {feet_and_inches(character.get('Height (Decimal Ft)'))  or 'Not Set'}\nGender: {character.get('Gender')  or 'Not Set'}""")
    await ctx.send(embed=embed)

@bot.command(aliases=['vote'])
@checks.role_or_permissions('DM')
async def poll(ctx: commands.Context, title: str, desc: str, url: str=None, notes: str=None, image: str=None):
  """Generates an embed with a given title and description, and tallies positive and negative reactions, allowing easy voting.
  
  Also creates a thread and silently adds the entire DM team to it."""
  embed = discord.Embed(title       = title, 
                        description = desc,
                        url         = url or "")
  if notes:
    embed.add_field(name='Notes', value=notes, inline=False
      )
  embed.add_field(name='Yes - ✅', value="0", inline=True)
  embed.add_field(name='No - ❎',  value="0", inline=True)
  message = await ctx.send(embed=embed)
  await message.add_reaction("❓")
  await message.add_reaction("✅")
  await message.add_reaction("❎")
  # thread  = await ctx.channel.create_thread(name=title, message=message)
  # thread_message = await thread.send('Time to vote!')
  # await thread_message.edit('Time to Vote, <@&692769572675125310>!')
  # await thread_message.pin()

@bot.command(aliases=['char_edit', 'edit'])
@checks.role_or_permissions('DM')
async def edit_char(ctx, *args):
  """Edits a character on the spreadsheet. 
  Requires `-name`, everything else is optional.

  `-player <player>` - The characters player
  `-name <name>` - The characters name
  `-url <url>` - The characters url

  `-race [race]` - The characters race
  `-level [level]` - The characters level
  `-class1 [class1]` - The characters first class
  `-subclass1 [subclass1]` - The characters first subclass
  `-class2 [class2]` - The characters second class
  `-subclass2 [subclass2]` - The characters second subclass
  `-class3 [class3]` - The characters third class
  `-subclass3 [subclass3]` - The characters third subclass
  `-class4 [class4]` - The characters fourth class
  `-subclass4 [subclass4]` - The characters fourth subclass
  `-gender [gender]` - The characters gender
  `-height [height]` - The characters height in decimal feet
  """
  parsed = argparse(args)
  player    = parsed.last("player", "")
  name      = parsed.last("name")
  new_name  = parsed.last("newname")
  race      = parsed.last("race", "")
  level     = parsed.last("level", "")
  class1    = parsed.last("class1", "")
  subclass1 = parsed.last("subclass1", "")
  class2    = parsed.last("class2", "")
  subclass2 = parsed.last("subclass2", "")
  class3    = parsed.last("class3", "")
  subclass3 = parsed.last("subclass3", "")
  class4    = parsed.last("class4", "")
  subclass4 = parsed.last("subclass4", "")
  url       = parsed.last("url")
  gender    = parsed.last("gender", "")
  height    = parsed.last("height", "")
  if name:
    all_characters = sh.sheet1.get_all_records()
    possible = []
    for i, character in enumerate(all_characters, 1):
      if character['Character Name'].lower() == name.lower():
        possible = [(i, character)]
        break
      if name.lower() in character['Character Name'].lower():
        possible.append((i, character))
    else:
      if not possible:
        await ctx.send(f"Error: Unable to find a character named: `{name}`")
        return
    row, character = possible[0]
    new_char = {'Player': player ,
                'Character Name': new_name or character['Character Name'],
                'Race': race ,
                'Level': level ,
                'Class 1': class1 ,
                'Subclass 1': subclass1 ,
                'Class 2': class2 ,
                'Subclass 2': subclass2 ,
                'Class 3': class3 ,
                'Subclass 3': subclass3 ,
                'Class 4': class4 ,
                'Subclass 4': subclass4 ,
                'URL': url ,
                'Gender': gender ,
                'Height (Decimal Ft)': height}
    letter = "ABCDEFGHIJKLMNO"
    for i, col in enumerate(COLUMNS):
      if new_char[col]:
        sh.sheet1.update(f"{letter[i]}{row+1}", new_char[col])
    character = sh.sheet1.get_all_records()[row-1]
    updated = [i[0] for i in new_char.items() if i[1] and not (i[0] == 'Character Name' and i[1] == character['Character Name'])]
    embed = discord.Embed(title       = f"{character['Character Name']} ({character['Player']})",
                          description = f"**Updated:** {', '.join(updated)}",
                          url         = character['URL'])
    embed.add_field(name = 'Race', value=character['Race'] or 'Not Set')
    classes = [f"""{x}: {character[x]} {f"({character['Sub'+x.lower()]})" if character.get('Sub'+x.lower()) else ''}""" for x in ['Class 1', 'Class 2', 'Class 3', 'Class 4'] if character.get(x)]
    embed.add_field(name = 'Levels', value=f"""Level: {character['Level'] or 'Not Set'}\n{NEWLINE.join(classes)}""")
    embed.add_field(name = 'Details', value=f"""Height: {feet_and_inches(character.get('Height (Decimal Ft)'))  or 'Not Set'}\nGender: {character.get('Gender')  or 'Not Set'}""")
    await ctx.send(embed=embed)

@bot.command(aliases=['json_poll'])
@checks.is_owner()
async def poll_json(ctx, json_name):
  if json_name:
    # Trim off the end if necessary
    if json_name.endswith('.json'):
      json_name = json_name[:-5]

    # Grab the file and open it as a json
    with open(f'{json_name}.json', encoding='UTF-8') as f:
      items = json.load(f)

    # Loop over each item in the json and create the poll
    for item in items:
      name  = item['name']
      desc  = item['desc']
      url   = item['url'] or ""
      notes = item.get('notes', '')

      embed = discord.Embed(title       = name, 
                            description = desc,
                            url         = url)
      
      if notes:
        embed.add_field(name='Notes', value=notes, inline=False
          )
      embed.add_field(name='Yes - ✅', value="0", inline=True)
      embed.add_field(name='No - ❎',  value="0", inline=True)

      message = await ctx.send(embed=embed)

      await message.add_reaction("❓")
      await message.add_reaction("✅")
      await message.add_reaction("❎")

      thread  = await ctx.channel.create_thread(name=name, message=message)

      thread_message = await thread.send('Time to vote!')
      await thread_message.edit('Time to Vote, <@&692769572675125310>!')
      await thread_message.pin()

@bot.command()
@checks.is_owner()
async def restart(ctx):
  await ctx.send("Restarting...")
  print("Restarting...")
  os.execv(sys.executable, ['python'] + sys.argv)

@bot.event
async def on_raw_reaction_add(event):
  await poll_voting(event)

@bot.event
async def on_raw_reaction_remove(event):
  await poll_voting(event)

async def poll_voting(event):
  server    = bot.get_guild(event.guild_id)
  msg_id    = event.message_id
  channel   = bot.get_channel(event.channel_id)
  emoji     = event.emoji
  user_id   = event.user_id
  user      = server.get_member(user_id)

  message   = await channel.fetch_message(msg_id)

  # Is the message one of the bots?
  if message.author.id == bot.user.id and user_id != bot.user.id:
    embed     = message.embeds[0]
    embedDict = embed.to_dict()
    all_dms = server.get_role(692769572675125310).members
    all_dms = [member.id for member in all_dms]
    # Gather the user ids for those who reacted
    for reaction in message.reactions:
      if str(reaction.emoji) == "✅":
        pos_reactions = reaction.count
        pos_reactions_user = [member.id for member in await reaction.users().flatten()]
      if str(reaction.emoji) == "❎":
        neg_reactions = reaction.count
        neg_reactions_user = [member.id for member in await reaction.users().flatten()]

    if event.event_type == "REACTION_ADD":
      if str(emoji) == "✅":
        # Remove the opposing reaction if existing
        if user_id in neg_reactions_user and event.channel_id != 889751624967393300:
          await message.remove_reaction("❎", user)
      if str(emoji) == "❎":
        # Remove the opposing reaction if existing
        if user_id in pos_reactions_user and event.channel_id != 889751624967393300:
          await message.remove_reaction("✅", user)
      if str(emoji) == "❓":
        # Tell me who in the DM role didn't vote yet
        total_votes = list(set(neg_reactions_user + pos_reactions_user))
        missing = [(await server.fetch_member(i)).nick for i in all_dms if i not in total_votes]
        missing = [nick[:nick.index('[') if '[' in nick else nick.index(' ') if ' ' in nick else None].strip() for nick in missing]
        await user.send(f"Checking the votes on **{embedDict['title']}**:\n" + 
                        (f" - {len(missing)} DM{'s have' if len(missing)>1 else ' has'} not voted: {', '.join(missing)}" if missing else 'Everyone voted!'))
        # If not in the space time emporium, remove the users react
        if event.channel_id != 889751624967393300:
          await message.remove_reaction("❓", user)

    # thread = bot.get_channel(msg_id)
    # threadName = thread.name.split(' | ')[0]
    # await thread.edit(name=f"{threadName} | {pos_reactions-1}|{neg_reactions-1}|{len(all_dms)-neg_reactions-pos_reactions+2}")

    embedDict['fields'][-2]['value'] = str(pos_reactions - 1)
    embedDict['fields'][-1]['value'] = str(neg_reactions - 1)

    await message.edit(embed=discord.Embed().from_dict(embedDict))

def feet_and_inches(decimal_feet):
  if decimal_feet:
    feet = int(decimal_feet)
    inches = int((decimal_feet - feet) * 12)
    return f"{feet}′ {f'{inches}″' if inches else ''}"

def avraeREST(type: str, endpoint: str, payload: str = None):
  if payload is None:
    payload = ""
  token = config.AVRAE_TOKEN
  headers['Authorization'] = token
  url = '/'.join(["https://api.avrae.io", endpoint]).strip('/')

  try:
    request = requests.request(type.upper(), url , headers=headers, data = payload)
    requestStatus = request.status_code
  except:
    if requestStatus==403:
      print("Unsuccessfully {}: {} - Double check your token".format(type.upper(), endpoint), requestStatus)
    if requestStatus==404:
      print("Unsuccessfully {}: {} - Invalid endpoint".format(type.upper(), endpoint), requestStatus)

  if requestStatus in (200, 201):
    print("Successfully {}: {}".format(type.upper(), endpoint), requestStatus)

  return request, requestStatus

class Dropdown(discord.ui.Select):
    def __init__(self, options):

        super().__init__(
            placeholder="Choose the character...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.message.delete()
        self.view.value = self.values[0]
        self.view.stop()

class DropdownView(discord.ui.View):
    def __init__(self, options):
        super().__init__()
        self.value = None

        # Adds the dropdown to our view object.
        self.add_item(Dropdown(options=options))

# Defines a custom button that contains the logic of the game.
# The ['TicTacToe'] bit is for type hinting purposes to tell your IDE or linter
# what the type of `self.view` is. It is not required.
class TicTacToeButton(discord.ui.Button["TicTacToe"]):
    def __init__(self, x: int, y: int):
        # A label is required, but we don't need one so a zero-width space is used
        # The row parameter tells the View which row to place the button under.
        # A View can only contain up to 5 rows -- each row can only have 5 buttons.
        # Since a Tic Tac Toe grid is 3x3 that means we have 3 rows and 3 columns.
        super().__init__(style=discord.ButtonStyle.secondary, label="\u200b", row=y)
        self.x = x
        self.y = y

    # This function is called whenever this particular button is pressed
    # This is part of the "meat" of the game logic
    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        view: TicTacToe = self.view
        state = view.board[self.y][self.x]
        if state in (view.X, view.O):
            return

        if view.current_player == view.X:
            self.style = discord.ButtonStyle.danger
            self.label = "X"
            self.disabled = True
            view.board[self.y][self.x] = view.X
            view.current_player = view.O
            content = "It is now O's turn"
        else:
            self.style = discord.ButtonStyle.success
            self.label = "O"
            self.disabled = True
            view.board[self.y][self.x] = view.O
            view.current_player = view.X
            content = "It is now X's turn"

        winner = view.check_board_winner()
        if winner is not None:
            if winner == view.X:
                content = "X won!"
            elif winner == view.O:
                content = "O won!"
            else:
                content = "It's a tie!"

            for child in view.children:
                child.disabled = True

            view.stop()

        await interaction.response.edit_message(content=content, view=view)


# This is our actual board View
class TicTacToe(discord.ui.View):
    # This tells the IDE or linter that all our children will be TicTacToeButtons
    # This is not required
    children: List[TicTacToeButton]
    X = -1
    O = 1
    Tie = 2

    def __init__(self):
        super().__init__()
        self.current_player = self.X
        self.board = [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]

        # Our board is made up of 3 by 3 TicTacToeButtons
        # The TicTacToeButton maintains the callbacks and helps steer
        # the actual game.
        for x in range(3):
            for y in range(3):
                self.add_item(TicTacToeButton(x, y))

    # This method checks for the board winner -- it is used by the TicTacToeButton
    def check_board_winner(self):
        for across in self.board:
            value = sum(across)
            if value == 3:
                return self.O
            elif value == -3:
                return self.X

        # Check vertical
        for line in range(3):
            value = self.board[0][line] + self.board[1][line] + self.board[2][line]
            if value == 3:
                return self.O
            elif value == -3:
                return self.X

        # Check diagonals
        diag = self.board[0][2] + self.board[1][1] + self.board[2][0]
        if diag == 3:
            return self.O
        elif diag == -3:
            return self.X

        diag = self.board[0][0] + self.board[1][1] + self.board[2][2]
        if diag == 3:
            return self.O
        elif diag == -3:
            return self.X

        # If we're here, we need to check if a tie was made
        if all(i != 0 for row in self.board for i in row):
            return self.Tie

        return None


@bot.command()
async def tic(ctx: commands.Context):
    """Starts a tic-tac-toe game with yourself."""
    await ctx.send("Tic Tac Toe: X goes first", view=TicTacToe())

bot.load_extension('cogsmisc.repl')
bot.run(config.TOKEN)


