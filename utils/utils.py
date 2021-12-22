import discord
from urllib.request import urlopen, Request
import re
import requests
from utils import config

headers = {
            'Authorization': "",
            'Accept': 'application/json, text/plain, */*',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
            'Content-Type': 'application/json',
            'Sec-Fetch-Site': 'same-site',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty'
          }

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

  request = requests.request(type.upper(), url , headers=headers, data = payload)
  requestStatus = request.status_code

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

def get_positivity(string):
    if isinstance(string, bool):  # oi!
        return string
    lowered = string.lower()
    if lowered in ('yes', 'y', 'true', 't', '1', 'enable', 'on'):
        return True
    elif lowered in ('no', 'n', 'false', 'f', '0', 'disable', 'off'):
        return False
    else:
        return None

async def confirm(ctx, message, delete_msgs=False, response_check=get_positivity):
    """
    Confirms whether a user wants to take an action.

    :rtype: bool|None
    :param ctx: The current Context.
    :param message: The message for the user to confirm.
    :param delete_msgs: Whether to delete the messages.
    :param response_check: A function (str) -> bool that returns whether a given reply is a valid response.
    :type response_check: (str) -> bool
    :return: Whether the user confirmed or not. None if no reply was recieved
    """
    msg = await ctx.channel.send(message)
    try:
        reply = await ctx.bot.wait_for('message', timeout=30, check=auth_and_chan(ctx))
    except asyncio.TimeoutError:
        return None
    reply_bool = response_check(reply.content) if reply is not None else None
    if delete_msgs:
        try:
            await msg.delete()
            await reply.delete()
        except:
            pass
    return reply_bool

def auth_and_chan(ctx):
    """Message check: same author and channel"""

    def chk(msg):
        return msg.author == ctx.author and msg.channel == ctx.channel

    return chk

