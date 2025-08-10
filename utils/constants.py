import os

TOKEN = os.getenv("DISCORD_TOKEN")
OWNER_ID = 164249546073964544

BEARER_TOKEN = os.getenv("BEARER_TOKEN")
AVRAE_TOKEN = os.getenv("AVRAE_TOKEN")

GUILD_IDS = [1031055347319832666]  # NLP server
DB_URI = os.getenv("DB_URI", f"sqlite+aiosqlite:///data/nlp.db")
MAGIC_ITEM_SHEET_ID = "170QfzpDrxE9vHDtjzvb1GmZ1L-dCXnm7qlZS9Vx7hdE"

SUBCLASS_REPLACEMENTS = [
    "Path of the ",    # Barbarian
    "Path of ",
    "College of ",     # Bard
    " Domain",         # Cleric
    "Circle of the ",  # Druid
    "Circle of ",
    "Way of the ",     # Monk
    "Way of ",
    "Warrior of the ",
    "Oath of the ",    # Paladin
    "Oath of ",
    "The ",            # Warlock
    "School of ",      # Wizard
    "Order of the",    # Bloodhunter
    r" \(.+?\)",       # 2014 Subclasses on 2024 Classes add the book tag. We don't care.
]