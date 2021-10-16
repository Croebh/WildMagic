import io
import textwrap
import traceback
import json
import gspread
import discord
from typing import Union, Tuple, List

from contextlib import redirect_stdout
from utils import checks, config
from utils.utils import avraeREST, feet_and_inches, Dropdown, DropdownView
from utils.argparser import argparse

from discord.ext import commands

class POLL(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  @commands.command(aliases=['vote'])
  @checks.role_or_permissions('DM')
  async def poll(self, ctx: commands.Context, name: str, desc: str, url: str=None, notes: str=None):
    """Generates an embed with a given title and description, and tallies positive and negative reactions, allowing easy voting.
    
    Also creates a thread and silently adds the entire DM team to it."""

    await self.generate_poll(ctx, name, desc, url, notes)

  @commands.command(aliases=['json_poll'])
  @checks.is_owner()
  async def poll_json(self, ctx, json_name):
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

        await self.generate_poll(ctx, name, desc, url, notes)

  @commands.Cog.listener()
  async def on_raw_reaction_add(self, event):
    await self.poll_voting(event)

  @commands.Cog.listener()
  async def on_raw_reaction_remove(self, event):
    await self.poll_voting(event)

  async def poll_voting(self, event):
    server    = self.bot.get_guild(event.guild_id)
    msg_id    = event.message_id
    channel   = self.bot.get_channel(event.channel_id)
    emoji     = event.emoji
    user_id   = event.user_id
    user      = server.get_member(user_id)

    message   = await channel.fetch_message(msg_id)

    # Is the message one of the bots?
    if message.author.id == self.bot.user.id and user_id != self.bot.user.id:
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
          if user_id in neg_reactions_user:
            await message.remove_reaction("❎", user)
        if str(emoji) == "❎":
          # Remove the opposing reaction if existing
          if user_id in pos_reactions_user:
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

      # thread = self.bot.get_channel(msg_id)
      # threadName = thread.name.split(' | ')[0]
      # await thread.edit(name=f"{threadName} | {pos_reactions-1}|{neg_reactions-1}|{len(all_dms)-neg_reactions-pos_reactions+2}")

      embedDict['fields'][-2]['value'] = str(pos_reactions - 1)
      embedDict['fields'][-1]['value'] = str(neg_reactions - 1)

      await message.edit(embed=discord.Embed().from_dict(embedDict))

  async def generate_poll(self, ctx: commands.Context, name:str, desc:str, url:str = None, notes:str = None, reactions: List[Tuple[str, str]] = None):

    if not url:
      url = ""
    if not reactions:
      reactions = [('Yes', "✅"), ('No', "❎")]

    embed = discord.Embed(title       = name, 
                          description = desc,
                          url         = url)

    if notes:
      embed.add_field(name='Notes', value=notes, inline=False)

    for r_desc, r_emote in reactions:
      embed.add_field(name=f'{r_desc} - {r_emote}', value="0", inline=True)

    message = await ctx.send(embed=embed)

    await message.add_reaction("❓")
    for _, reaction in reactions:
      await message.add_reaction(reaction)

    # thread  = await ctx.channel.create_thread(name=name, message=message)
    # thread_message = await thread.send('Time to vote!')
    # await thread_message.edit('Time to Vote, <@&692769572675125310>!')
    # await thread_message.pin()

def setup(bot):
    bot.add_cog(POLL(bot))