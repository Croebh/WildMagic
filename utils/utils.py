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