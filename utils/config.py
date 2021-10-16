from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
AVRAE_TOKEN = os.getenv('AVRAE_TOKEN')
DICECLOUD_USER = os.getenv('DICECLOUD_USER')
DICECLOUD_PASS = os.getenv('DICECLOUD_PASS')
DICECLOUD_TOKEN = os.getenv('DICECLOUD_TOKEN')
OWNER_ID = 164249546073964544