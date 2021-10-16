import io
import textwrap
import traceback
import json
import gspread
import discord

from contextlib import redirect_stdout
from utils import checks, config
from utils.utils import avraeREST, feet_and_inches, Dropdown, DropdownView
from utils.argparser import argparse

from discord.ext import commands


COLUMNS = ['Player' ,'Character Name' ,'Race' ,'Level' ,'Class 1' ,'Subclass 1' ,'Class 2' ,'Subclass 2' ,'Class 3' ,'Subclass 3' ,'Class 4' ,'Subclass 4' ,'URL' ,'Gender' ,'Height (Decimal Ft)']

gc = gspread.service_account(filename="service_account.json")
sh = gc.open_by_url("https://docs.google.com/spreadsheets/d/18AfHOEBS0CMYERtO6O6fCoME8jB9wVm_Gc5FIni3ryE/edit#gid=0")
NEWLINE = "\n"

class CHAR(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
      
  @commands.command(aliases=['gvar_update', 'gvar'])
  @checks.role_or_permissions('DM')
  async def update_gvar(self, ctx, *args):
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

  @commands.command(aliases=['char', 'lookup_char'])
  async def char_lookup(self, ctx, name:str):
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
    if len(possible) > 1:
      options = [discord.SelectOption(label=name[1]['Character Name'],
                                      description=name[1]['Player'],
                                      value=str(i))
                 for i, name in enumerate(possible[:25])]
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

    await ctx.send(embed=embed)

  @commands.command()
  async def height(self, ctx):
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

  @commands.command(aliases=['newchar'])
  @checks.role_or_permissions('DM')
  async def new_char(self, ctx, *args):
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

  @commands.command(aliases=['char_edit', 'edit'])
  @checks.role_or_permissions('DM')
  async def edit_char(self, ctx, *args):
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

def setup(bot):
    bot.add_cog(CHAR(bot))