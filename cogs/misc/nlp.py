import copy
import gspread

from utils import constants
from utils.avrae_api import AvraeClient

import json
import logging
import time
from collections import Counter
import re
from datetime import datetime, timedelta
from datetime import time as dt_time
from textwrap import dedent

import aiohttp

import disnake
from disnake import ApplicationCommandInteraction

from disnake.ext import commands, tasks
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound

import db
from utils.ddbclient import DDBClient
from utils.constants import GUILD_IDS, BEARER_TOKEN, MAGIC_ITEM_SHEET_ID

from models import Character, User
from utils.functions import (
    get_character_data,
    split_arg,
    natural_join,
    pluralize,
    get_classes,
    get_invocations,
    get_feats,
    get_stats,
    char_disp,
)

logger = logging.getLogger(__name__)


class ProvideUserModal(disnake.ui.Modal):
    def __init__(self, custom_id):
        components = [
            disnake.ui.TextInput(
                label="User ID",
                placeholder="",
                custom_id="userid",
                style=disnake.TextInputStyle.long,
                required=False,
                max_length=500,
            )
        ]
        super().__init__(title="User ID", custom_id=custom_id, components=components)

    async def callback(self, inter: disnake.ModalInteraction) -> None:
        await inter.response.defer(with_message=False)

    async def on_error(self, error: Exception, inter: disnake.ModalInteraction) -> None:
        await inter.response.send_message("Oops, something went wrong.", ephemeral=True)


class NLPCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.avrae_client = AvraeClient(
            aiohttp.ClientSession(loop=bot.loop), constants.AVRAE_TOKEN
        )
        self.client = DDBClient(aiohttp.ClientSession(loop=bot.loop), BEARER_TOKEN)
        self.nlp_update_stats.start()

    @tasks.loop(time=dt_time(hour=12))
    async def nlp_update_stats(self):
        """Collect the recent activity and update character data, once a week."""
        if datetime.now().weekday != 6:  # Only run on Sundays
            return

        server = self.bot.get_guild(GUILD_IDS[0])
        log_channel = server.get_channel(1045800666095943772)
        log_message = await log_channel.send(
            "Automatically getting the active members for the last 7 days, and updating character data"
        )
        await self.nlp_get_active(server=server, days=8, response=log_message)
        await self.nlp_update_character(inter=log_message)

    # noinspection PyTypeChecker
    @commands.slash_command(name="nlp_update_magic_items")
    async def update_magic_items(self, inter: ApplicationCommandInteraction):
        """Update the magic items GVAR from the GSheet"""
        await inter.response.defer()

        gc = gspread.service_account()
        sh = gc.open_by_key(MAGIC_ITEM_SHEET_ID)

        errors = []

        def split(string):
            return (
                string.replace(", or ", ", ")
                .replace(" or ", ", ")
                .replace(", and ", ", ")
                .replace(" and ", ", ")
                .strip(".")
                .split(", ")
            )

        def convert_component(comp: str) -> list[dict[str, int]]:
            split_comp = split(comp)
            c_out = []
            if split_comp[0][0].isdigit():
                for t in split_comp:
                    num, *type_ = t.split()
                    if num and not type_:
                        c_out[-1]["type_"].append(num)
                    else:
                        c_out.append({"type_": [" ".join(type_)], "num": int(num)})
            else:
                c_out = [{"type_": split_comp, "num": 1}]
            if comp and not c_out:
                errors.append(f"> Error processing components: {comp}")

            return c_out

        RARITIES = (
            ("common", 50, 5),
            ("uncommon", 250, 10),
            ("rare", 2000, 20),
            ("very rare", 9000, 30),
        )

        data_out = []

        for rarity, cost, time in RARITIES:
            worksheet = sh.worksheet(rarity.title())
            data_in = list(worksheet.get_all_records())

            for i, current_item in enumerate(data_in):
                current_item: dict = {k.lower(): v for k, v in current_item.items()}
                if not current_item.get("item"):
                    continue

                # replace keys `Cost (default 9000gp)`  `Time (default 30 days)` with `cost` and `time`
                current_item["cost"] = int(
                    current_item.pop(f"cost (default {cost}gp)") or cost
                )
                current_item["days"] = int(
                    current_item.pop(f"time (default {time} days)") or time
                )

                current_item["component creature type"]: list[dict[str, int]] | None = (
                    current_item.get("component creature type", None)
                )
                if current_item.get("component creature type"):
                    current_item["component creature type"] = convert_component(
                        current_item["component creature type"].lower()
                    )

                current_item["component cr"] = current_item.get("component cr", None)
                if current_item["component cr"]:
                    try:
                        current_item["component cr"] = int(current_item["component cr"])
                    except ValueError:
                        if "/" in current_item["component cr"]:
                            current_item["component cr"] = 1 / int(
                                current_item["component cr"].split("/")[-1]
                            )
                current_item["restrictions"] = (
                    None
                    if current_item["restrictions"] in ("Community Goal", "")
                    else current_item["restrictions"]
                )

                current_item["components"]: dict[str, int | float | str] | None = None
                if current_item["component cr"]:
                    current_item["components"] = {
                        "cr": current_item["component cr"],
                        "amt": current_item["component creature type"],
                    }

                current_item["name"] = current_item["item"]
                current_item["comment"] = current_item.pop("comments").strip()
                current_item["rarity"] = rarity

                keys_to_keep = [
                    "cost",
                    "restrictions",
                    "components",
                    "name",
                    "days",
                    "comment",
                    "rarity",
                ]
                current_item = {
                    key: value
                    for key, value in current_item.items()
                    if key in keys_to_keep and value
                }

                data_in[i] = current_item

                if "Alternative Crafting:" in current_item.get("comment", ""):
                    nm_name = (
                        current_item.get("comment", "")
                        .split("Alternative Crafting:")[1]
                        .strip()
                        .lower()
                    )

                    if nm_name.lower() == "unknown":
                        continue
                    # make a deep copy
                    nm_item = copy.deepcopy(current_item)
                    nm_item["name"] += " (NM)"
                    nm_item["components"] = {
                        "cr": "*",
                        "amt": [{"type_": split(nm_name), "num": 1}],
                    }
                    nm_item["days"] //= 2
                    nm_item["cost"] //= 2
                    data_out.append(nm_item)

            data_out.extend(data_in)

        out = [
            i
            for i in data_out
            if i.get("restrictions", "").lower()
            not in ("banned", "restricted", "restricted, see below")
            and i.get("name")
        ]

        gvar = []
        key_mapping = {
            "name": "n",
            "days": "d",
            "cost": "c",
            "comment": "N",
            "rarity": "r",
            "components": "C",
            "restrictions": "R",
        }

        for d in out:
            new_dict = {}
            for key, value in d.items():
                new_key = key_mapping.get(
                    key, key
                )  # Use the mapped key if it exists, otherwise keep the original key
                new_dict[new_key] = value
            gvar.append(new_dict)

        data_out = json.dumps(gvar, separators=(",", ":"))

        if errors:
            errors = "\n".join(errors)
            await inter.edit_original_response(f"Error processing items: \n{errors}")

        if len(data_out) > 100_000:
            await inter.edit_original_response(
                f"Error: GVAR length is over 100k ({len(data_out):,}). Ping Croebh!"
            )
            return
        with open(
            r"H:\Avrae\Avrae-Customizations\Collections\NLP\3. Magic Items - 80bc25ba-6299-4171-a575-fd7928e42d39.gvar",
            "w",
        ) as f:
            json.dump(gvar, f, separators=(",", ":"))

        old_data = await self.avrae_client.get_gvar(
            "80bc25ba-6299-4171-a575-fd7928e42d39"
        )
        old_data_items = json.loads(old_data.value)

        delta_char = len(data_out) - len(old_data.value)
        delta_items = len(gvar) - len(old_data_items)

        await self.avrae_client.set_gvar(
            "80bc25ba-6299-4171-a575-fd7928e42d39", data_out
        )
        await inter.edit_original_response(
            f"GVAR updated! There are now {len(gvar):,}{f' ({delta_items:+,})' if delta_items else ''} items, and the length of the gvar is {len(data_out):,}{f' ({delta_char:+,})' if delta_char else ''}"
        )

    @commands.Cog.listener("on_message")
    async def ping_for_review(self, message: disnake.Message):
        """Sometimes people like to repeatedly ping for review. This way, they get a response immediately."""
        if "<@&1061605761932853291>" not in message.content:
            return
        if (
            isinstance(message.channel, disnake.Thread)
            and message.channel.parent_id == 1049146029569753119
        ):
            await message.reply(
                "Thank you! A character reviewer will be with you as soon as they can!"
            )

    @commands.slash_command(guild_ids=GUILD_IDS, name="nlp_get_active")
    @commands.max_concurrency(1)
    @commands.is_owner()
    async def nlp_get_active_command(
        self,
        inter: ApplicationCommandInteraction,
        days: int = 90,
        channel: disnake.TextChannel = None,
    ):
        """[ADMIN ONLY] Get the active members from the last X days in OOC channels"""
        await inter.response.defer()

        server = self.bot.get_guild(inter.guild_id)
        response = await inter.followup.send(
            f"Beginning search for active characters for the last {days} days"
        )

        await self.nlp_get_active(server, response, days, channel)

    @commands.slash_command(guild_ids=GUILD_IDS, name="nlp_get_jsons")
    @commands.is_owner()
    async def nlp_get_jsons_command(
        self,
        inter: disnake.ApplicationCommandInteraction = None,
        active_only: bool = True,
        user_ids: str = None,
        valid_only: bool = True,
    ):
        """[ADMIN ONLY] Gets the character data from DDB API, and saves the character for each"""
        try:
            await inter.response.defer()
        except disnake.errors.InteractionException:
            pass

        user_ids = [int(id_) for id_ in user_ids.split(",")] if user_ids else None

        response = await self.nlp_update_character(
            active_only, inter=inter, valid_only=valid_only, user_ids=user_ids
        )

        if response:
            await response.edit(f"{response.content}\n\nDone updating JSONs!")

    @commands.slash_command(name="nlp_fix_character", guild_ids=GUILD_IDS)
    async def nlp_fix_link(
        self,
        inter: ApplicationCommandInteraction,
        user: disnake.User,
        character_link: str,
    ):
        """[ADMIN ONLY] Fix what character a user has. Useful for if they swap accounts."""
        await inter.response.defer(ephemeral=True)

        user_id = user.id
        async with db.async_session() as session:
            try:
                stmt = select(User).where(User.id == user_id)
                user_objs = await session.scalars(stmt)
                user_obj = user_objs.one()
            except NoResultFound:
                # User has left the server or has no validated character
                user_obj = User(id=user_id)

            try:
                stmt = select(Character).where(Character.user_id == user_id)
                old_chars = await session.scalars(stmt)
                old_char = old_chars.one()
                old_char.user_id = None
            except NoResultFound:
                ...

            character = Character(
                name="",
                url=character_link,
                level=1,
                race="",
                classes=[],
                subclasses=[],
                stats={},
                feats=[],
                invocations=[],
                valid=True,
            )
            character.user = user_obj

            session.add(character)
            await session.commit()

        await self.nlp_update_character(
            user_ids=[user.id], active_only=False, valid_only=False
        )

        await inter.send(
            f"Added {user.mention} with character link {character_link}",
            allowed_mentions=disnake.AllowedMentions().none(),
        )

    @commands.user_command(name="Get Character", guild_ids=GUILD_IDS)
    async def nlp_get_user_character(
        self, inter: disnake.ApplicationCommandInteraction
    ):
        """Gets and displays a users character"""

        async with db.async_session() as session:
            try:
                stmt = select(Character).where(Character.user_id == inter.target.id)
                results = await session.scalars(stmt)
                character = results.one()
            except NoResultFound:
                await inter.send(
                    "No character found",
                    ephemeral=True,
                    allowed_mentions=disnake.AllowedMentions().none(),
                )
                return

        embed = disnake.Embed(title="NLP Character")
        level_out = " / ".join(
            [
                f"{clas} {lvl}"
                if clas not in character.subclasses
                else f"{clas} ({character.subclasses[clas]}) {lvl}"
                for clas, lvl in character.classes.items()
            ]
        )
        embed.add_field(
            name=inter.target.display_name,
            value=f"{character.name} • [Sheet URL]({character.url})\n{character.race} • {level_out}",
            inline=False,
        )

        await inter.send(
            embed=embed,
            ephemeral=True,
            allowed_mentions=disnake.AllowedMentions().none(),
        )

    @commands.message_command(name="Add Validated Character", guild_ids=GUILD_IDS)
    async def nlp_add_validated(self, inter: disnake.ApplicationCommandInteraction):
        """Adds a validated character to the database"""
        await inter.response.defer(ephemeral=True)

        message = inter.target

        if not (
            message.author.name == "Avrae"
            and message.embeds
            and message.embeds[0].footer.text == "!validate_sheet"
        ):
            await inter.send("No valid message found", ephemeral=True)
            return

        embed = message.embeds[0].to_dict()
        misc = embed["fields"][0]["value"].splitlines()

        name = embed["title"][22:]
        race = misc[8][10:]

        classes = {}
        total_level = 0
        for class_ in misc[10][13:].split(", "):
            clas, lvl = class_.split(maxsplit=1)
            lvl = int(lvl.lower().strip(" *()abcdefghijklmnopqrstuvwxyz-"))
            classes[clas] = lvl
            total_level += lvl

        stats_ = (misc[0] + " " + misc[1]).replace(" *", "\n").replace("*", "")
        stats = {}
        for stat in stats_.splitlines():
            stat, values = stat.split(": ")
            value, mod = values.split()
            stats[stat] = int(value)

        sheet_link = misc[-1][15:-3]

        owner_name = embed["author"]["name"]

        try:
            owner = message.guild.get_member(
                int(embed["thumbnail"]["url"].split("author_id=")[1].strip("&"))
            )
        except IndexError:
            owner = message.guild.get_member_named(owner_name)

        if not owner:
            randomized_id = f"alert-{inter.id}"
            await inter.response.send_modal(
                modal=ProvideUserModal(custom_id=randomized_id)
            )
            modal = await self.bot.wait_for(
                "modal_submit",
                check=lambda modal_inter: modal_inter.custom_id == randomized_id
                and modal_inter.author == inter.author,
            )
            user_id = modal.text_values["userid"]
            owner = message.guild.get_member(int(user_id))
            if not owner:
                await inter.send(
                    f"No valid owner found for the name `{owner_name}` or ID `{user_id}`.",
                    ephemeral=True,
                )
                return

        async with db.async_session() as session:
            stmt = select(User).where(User.id == owner.id)
            users = await session.scalars(stmt)
            try:
                user = users.one()
                user.name = owner.global_name
                user.nickname = owner.display_name
                user.lastActive = datetime.now()
                user.onServer = True
            except NoResultFound:
                user = User(
                    id=owner.id,
                    name=owner.global_name,
                    nickname=owner.display_name,
                    lastActive=datetime.now(),
                    onServer=True,
                )
                session.add(user)
            char = Character(
                name=name,
                url=sheet_link,
                race=race,
                level=total_level,
                stats=stats,
                classes=classes,
                subclasses=[],
                feats=[],
                invocations=[],
                valid=True,
            )
            char.user = user

            session.add(char)
            await session.commit()

        await self.nlp_update_character(user_ids=[owner.id])

        await inter.send(
            f"Added {owner.mention} as {name}, approved at <t:{int(datetime.now().timestamp())}:R>",
            ephemeral=True,
            allowed_mentions=disnake.AllowedMentions().none(),
        )

        if not inter.channel.name.startswith("[Approved"):
            await inter.channel.edit(name=f"[Approved] {name}")

        if total_level == 5:
            roles = [
                disnake.utils.get(inter.guild.roles, name=role)
                for role in ("Player", "Looking for Tier 2", "Looking for RP", "Tier 1")
            ]
            await owner.add_roles(*roles, reason="Character approved")
            await inter.send(
                f"Roles added to {owner.mention}: `@Player`, `@Tier 1`, `@Looking for Tier 2`, and `@Looking for RP`",
                allowed_mentions=disnake.AllowedMentions().none(),
            )

        await message.add_reaction("👍")

    @commands.message_command(name="List Characters", guild_ids=GUILD_IDS)
    async def nlp_list_characters(self, inter: disnake.ApplicationCommandInteraction):
        """Lists all the characters for the users mentioned in the message"""
        users = []
        for user in inter.target.mentions:
            users.append(user.id)

        if not users:
            await inter.send("No users mentioned", ephemeral=True)
            return

        characters = []
        async with db.async_session() as session:
            stmt = select(Character).filter(Character.user_id.in_(users))
            characters = await session.scalars(stmt)

        if not characters:
            await inter.send("No characters found", ephemeral=True)
            return

        embed = disnake.Embed(title="NLP Characters")
        for character in characters:
            level_out = " / ".join(
                [
                    f"{clas} {lvl}"
                    if clas not in character.subclasses
                    else f"{clas} ({character.subclasses[clas]}) {lvl}"
                    for clas, lvl in character.classes.items()
                ]
            )
            embed.add_field(
                name=character.name,
                value=f"<@{character.user.id}> • [Sheet URL]({character.url})\n{character.race} • {level_out}",
                inline=False,
            )

        await inter.send(embed=embed, allowed_mentions=disnake.AllowedMentions().none())

    # todo: look into a better way to do this, because... not great
    @commands.slash_command(name="nlp_character_lookup", guild_ids=GUILD_IDS)
    async def nlp_character_lookup_multiple(
        self,
        inter: disnake.ApplicationCommandInteraction,
        name_1: str = commands.param(description="The first character"),
        name_2: str = commands.param(description="The second character", default=None),
        name_3: str = commands.param(description="The third character", default=None),
        name_4: str = commands.param(description="The fourth character", default=None),
        name_5: str = commands.param(description="The fifth character", default=None),
        name_6: str = commands.param(description="The sixth character", default=None),
        extended: bool = True,
    ):
        """
        Looks up 1-6 characters, returning a brief overview of them and a link to their sheets.
        """
        embed = disnake.Embed(title="Character Lookup")
        names = [
            name for name in [name_1, name_2, name_3, name_4, name_5, name_6] if name
        ]

        async with db.async_session() as session:
            stmt = (
                select(Character)
                .join(User)
                .where(User.onServer)
                .filter(User.nickname.in_(names))
            )
            characters = await session.scalars(stmt)

        for character in characters:
            title, value = char_disp(character, extended=extended)
            embed.add_field(name=title, value=value, inline=True)

        if not characters:
            await inter.send("No characters found", ephemeral=True)
            return

        await inter.send(embed=embed, allowed_mentions=disnake.AllowedMentions().none())

    # todo: look into a better way to do this, because... not great
    @nlp_character_lookup_multiple.autocomplete("name_1")
    @nlp_character_lookup_multiple.autocomplete("name_2")
    @nlp_character_lookup_multiple.autocomplete("name_3")
    @nlp_character_lookup_multiple.autocomplete("name_4")
    @nlp_character_lookup_multiple.autocomplete("name_5")
    @nlp_character_lookup_multiple.autocomplete("name_6")
    async def slash_rule_auto(self, _, user_input: str):
        characters = await self.get_all_characters(active_only=False)
        choices = [
            i.user.nickname
            for i in characters
            if user_input.lower()
            in f"{i.name} 〰 {i.user.nickname if i.user else ''}".lower()
        ]
        return choices[:25]

    @commands.slash_command(name="nlp_subclasses", guild_ids=GUILD_IDS)
    async def nlp_subclass(self, inter: ApplicationCommandInteraction):
        """Gets subclass breakdown for the all active characters."""
        characters = await self.get_all_characters()

        subclasses = {}
        classes = {}

        for char in characters:
            for clas, sub in char.subclasses.items():
                subclasses[clas] = subclasses.get(clas, []) + [sub]
            for clas, lvl in char.classes.items():
                classes[clas] = classes.get(clas, 0) + 1

        subclasses = dict(
            sorted(subclasses.items(), key=lambda x: len(set(x[1])), reverse=True)
        )

        embed = disnake.Embed(
            title="NLP Subclasses",
            description=f"The number in the header is the number of characters with a subclass in that class, over the "
            "number of characters with that class.",
            timestamp=datetime.now(),
        )

        embed.set_footer(
            text=f"Data for the {len(characters)} Active characters within 90 days of"
        )

        for clas, subs in subclasses.items():
            total = len(subs)
            subs = dict(Counter(subs))
            subs = dict(sorted(subs.items(), key=lambda x: x[1], reverse=True))
            subs = [f"> *{sub}:* {count}" for sub, count in subs.items()]
            embed.add_field(
                name=f"{clas} ({total}/{classes[clas]})",
                value="\n".join(subs),
                inline=True,
            )

        await inter.send(embed=embed, allowed_mentions=disnake.AllowedMentions().none())

    @commands.slash_command(name="nlp_stats", guild_ids=GUILD_IDS)
    async def nlp_stats(self, inter: ApplicationCommandInteraction):
        """Gets stats for active characters, comparing levels, classes, ancestries, and more!"""

        characters = await self.get_all_characters()

        total_stats = {"STR": 0, "DEX": 0, "CON": 0, "INT": 0, "WIS": 0, "CHA": 0}

        max_stats = {
            "STR": [-99, ""],
            "DEX": [-99, ""],
            "CON": [-99, ""],
            "INT": [-99, ""],
            "WIS": [-99, ""],
            "CHA": [-99, ""],
        }

        min_stats = {
            "STR": [99, ""],
            "DEX": [99, ""],
            "CON": [99, ""],
            "INT": [99, ""],
            "WIS": [99, ""],
            "CHA": [99, ""],
        }
        total_level = 0
        levels = []
        races = []
        classes = {}
        classes_each = {}
        mono_classes = 0
        most_multiclass = 0
        for character in characters:
            # Race

            race_standardization = {
                "Half-Elf": "Half-Elf",
                "Elf": "Elf",
                "Dwarf": "Dwarf",
                "Tiefling": "Tiefling",
                "Genasi": "Genasi",
                "Human": "Human",
                "Dragonborn": "Dragonborn",
            }
            race = character.race
            for key, value in race_standardization.items():
                if key in race:
                    race = value
                    break
            races.append(race)

            # Level
            total_level += character.level
            levels.append(character.level)

            # Classes
            for clas, lvl in character.classes.items():
                classes[clas] = classes.get(clas, 0) + 1
                classes_each[clas] = classes_each.get(clas, []) + [lvl]
            if len(character.classes) == 1:
                mono_classes += 1
            if len(character.classes) > most_multiclass:
                most_multiclass = len(character.classes)

            # Stats
            for stat in character.stats:
                total_stats[stat] += character.stats[stat]
                if max_stats[stat][0] < character.stats[stat]:
                    max_stats[stat] = [character.stats[stat], character.name]
                elif max_stats[stat][0] == character.stats[stat]:
                    max_stats[stat][1] += f", {character.name}"

                if min_stats[stat][0] > character.stats[stat]:
                    min_stats[stat] = [character.stats[stat], character.name]
                elif min_stats[stat][0] == character.stats[stat]:
                    min_stats[stat][1] += f", {character.name}"

        races = dict(Counter(races))
        races = dict(sorted(races.items(), key=lambda x: x[1], reverse=True))
        single_race = [race for race, count in races.items() if count == 1]

        classes = dict(Counter(classes))
        classes = dict(sorted(classes.items(), key=lambda x: x[1], reverse=True))
        classes_avg = {
            cls: round(sum(lvls) / len(lvls), 2) for cls, lvls in classes_each.items()
        }
        classes_avg = dict(
            sorted(classes_avg.items(), key=lambda x: x[1], reverse=True)
        )
        classes_max = {cls: max(lvls) for cls, lvls in classes_each.items()}
        classes_max = dict(
            sorted(classes_max.items(), key=lambda x: x[1], reverse=True)
        )

        levels = dict(Counter(levels))
        levels = dict(sorted(levels.items(), key=lambda x: x[0], reverse=True))
        average_levels = round(total_level / len(characters), 2)

        average_stats = {
            name: round(value / len(characters), 2)
            for name, value in total_stats.items()
        }

        tiers = {
            1: [(level, count) for level, count in levels.items() if 5 > level],
            2: [(level, count) for level, count in levels.items() if 5 <= level < 11],
            3: [(level, count) for level, count in levels.items() if 11 <= level < 17],
            4: [(level, count) for level, count in levels.items() if 17 <= level],
        }

        sum_each_tier = {
            tier: sum([count for level, count in levels])
            for tier, levels in tiers.items()
        }
        average_each_tier = {
            tier: round(
                sum([level * count for level, count in levels]) / sum_each_tier[tier], 2
            )
            if sum_each_tier[tier]
            else 0
            for tier, levels in tiers.items()
        }

        embed = disnake.Embed(title="NLP Stats", timestamp=datetime.now())
        embed.set_footer(
            text=f"Data for the {len(characters)} Active characters within 90 days of"
        )

        embed.add_field(
            "Ancestries",
            "\n".join(
                [f"**{race}:** {count}" for race, count in races.items() if count != 1]
            )
            + dedent(f"""
                    **{natural_join(single_race, "and")}:** 1"""),
        )
        embed.add_field(
            "Levels",
            "\n".join([f"**{level}:** {count}" for level, count in levels.items()])
            + "\n\n"
            + dedent(f"""**Characters in each Tier:**
                    {f'''> **Tier 1:** {sum_each_tier[1]} (Average level is {average_each_tier[1]})''' if sum_each_tier[1] else ""}
                    > **Tier 2:** {sum_each_tier[2]} (Average level is {average_each_tier[2]})
                    > **Tier 3:** {sum_each_tier[3]} (Average level is {average_each_tier[3]})
                    > **Tier 4:** {sum_each_tier[4]} (Average level is {average_each_tier[4]})"""),
        )

        average_stats_out = [
            f"**{stat}:** {value}" for stat, value in average_stats.items()
        ]
        min_stats_out = [
            f"**{stat}:** {value[0]} ({len(value[1].split(', '))} {pluralize('char', len(value[1].split(', ')))})"
            for stat, value in min_stats.items()
        ]
        max_stats_out = [
            f"**{stat}:** {value[0]} ({len(value[1].split(', '))} {pluralize('char', len(value[1].split(', ')))})"
            for stat, value in max_stats.items()
        ]

        embed.add_field(
            "Average Level and Stats",
            dedent(f"""**Level:** {average_levels}
                               {" ".join(average_stats_out[:3])}
                               {" ".join(average_stats_out[3:])}"""),
            inline=False,
        )
        embed.add_field(
            "Minimum Stats",
            dedent(f"""{" ".join(min_stats_out[:3])}
                               {" ".join(min_stats_out[3:])}"""),
            inline=False,
        )
        embed.add_field(
            "Maximum Stats",
            dedent(f"""{" ".join(max_stats_out[:3])}
                               {" ".join(max_stats_out[3:])}"""),
            inline=False,
        )

        embed.add_field(
            "Total Classes",
            "\n".join([f"**{clas}:** {count}" for clas, count in classes.items()])
            + dedent(f"""

                    **Single Class Characters:** {mono_classes}
                    **Most Multiclasses:** {most_multiclass}"""),
        )
        embed.add_field(
            "Average Class Level",
            "\n".join([f"**{clas}:** {count}" for clas, count in classes_avg.items()]),
        )
        embed.add_field(
            "Max Class Level",
            "\n".join([f"**{clas}:** {count}" for clas, count in classes_max.items()]),
        )
        await inter.send(embed=embed)

    @commands.slash_command(name="nlp_search")
    async def nlp_search(
        self,
        inter: ApplicationCommandInteraction,
        name: str = commands.param(default=None),
        player: str = commands.param(default=None),
        race: str = commands.param(default=None),
        cls: str = commands.param(name="class", default=None),
        subcls: str = commands.param(name="subclass", default=None),
        level: str = commands.param(default=None),
        stats: str = commands.param(default=None),
    ):
        """
        Searches the NLP characters for the given parameters, returning some details and their sheet URL.

        Parameters
        ----------
        inter: The interaction
        name: Character names to search for. Partial matching, ignores case, comma separated (e.g. "Wyld, Pyrr")
        player: Player names to search for. Partial matching, ignores case, comma separated (e.g. "Croebh, Zhu")
        race: Races to search for. Partial matching, ignores case, comma separated. (e.g. "Elf, Dwarf")
        cls: Class names to search for. Partial matching, ignores case, comma separated (e.g. "Barb, Wizard")
        subcls: Subclass names to search for. Partial matching, ignores case, comma separated (e.g. "Wild, Frenzy")
        level: Levels to search for. Can be a single number, or a comparison (e.g. ">=5, <10")
        stats: Stats to search for. Abbreviated stat name:number or comparison (e.g. "STR:15, DEX:>=12")
        """
        characters = await self.get_all_characters()

        desc = ""

        names = split_arg(name)
        if names:
            desc += f"- **Name Contains:** {natural_join(names, 'or', '*')}\n"
            characters = [
                character
                for character in characters
                if any([True for n in names if n in character.name.lower()])
            ]

        players = split_arg(player)
        if players:
            desc += f"- **Player Contains:** {natural_join(players, 'or', '*')}\n"
            characters = [
                character
                for character in characters
                if any(
                    [
                        True
                        for n in players
                        if n in character.user.nickname.lower()
                        or n in character.user.name.lower()
                    ]
                )
            ]

        races = split_arg(race)
        if races:
            desc += f"- **Race Contains:** {natural_join(races, 'or', '*')}\n"
            characters = [
                character
                for character in characters
                if any([True for n in races if n in character.race.lower()])
            ]

        clss = split_arg(cls)
        if clss:
            desc += f"- **Classes Include:** {natural_join(clss, 'or', '*')}\n"
            characters = [
                character
                for character in characters
                if any(
                    [
                        True
                        for n in clss
                        if any(n in x.lower() for x in character.classes.keys())
                    ]
                )
            ]

        subclss = split_arg(subcls)
        if subclss:
            desc += f"- **Subclasses Includes:** {natural_join(subclss, 'or', '*')}\n"
            characters = [
                character
                for character in characters
                if any(
                    [
                        True
                        for n in subclss
                        if any(n in x.lower() for x in character.subclasses.values())
                    ]
                )
            ]

        levels = split_arg(level)
        if levels:
            desc += f"- **Level Is:** {natural_join(levels, 'or', '*')}\n"
            characters = [
                character
                for character in characters
                if any(
                    [
                        True
                        for n in levels
                        if (n.isdigit() and int(n) == character.level)
                        or (
                            n.startswith(">=")
                            and character.level >= int(n.strip("<=>"))
                        )
                        or (n.startswith(">") and character.level > int(n.strip("<=>")))
                        or (
                            n.startswith("<=")
                            and character.level <= int(n.strip("<=>"))
                        )
                        or (n.startswith("<") and character.level < int(n.strip("<=>")))
                    ]
                )
            ]

        statss = split_arg(stats)
        statss = [
            ((_stat := i.split(":"))[0].upper(), _stat[1]) for i in statss if ":" in i
        ]
        if statss:
            desc += f"- **Stats are:** {natural_join([f'{stat[0]} {stat[1]}' for stat in statss], 'or', '*')}\n"
            characters = [
                character
                for character in characters
                if any(
                    [
                        True
                        for n in statss
                        if n[0] in character.stats
                        and (n[1].isdigit() and int(n[1]) == character.stats[n[0]])
                        or (
                            n[1].startswith(">=")
                            and character.stats[n[0]] >= int(n[1].strip("<=>"))
                        )
                        or (
                            n[1].startswith(">")
                            and character.stats[n[0]] > int(n[1].strip("<=>"))
                        )
                        or (
                            n[1].startswith("<=")
                            and character.stats[n[0]] <= int(n[1].strip("<=>"))
                        )
                        or (
                            n[1].startswith("<")
                            and character.stats[n[0]] < int(n[1].strip("<=>"))
                        )
                    ]
                )
            ]

        embed = disnake.Embed(title="Character Search")
        for char in characters[:20]:
            extended = len(characters) <= 5
            title, value = char_disp(char, extended=extended)
            embed.add_field(name=title, value=value, inline=True)

        embed.description = f"{'20/' if len(characters) > 20 else ''}{len(characters)} {pluralize('result', len(characters))} for the following search:\n{desc}"

        await inter.send(embed=embed, allowed_mentions=disnake.AllowedMentions().none())

    @staticmethod
    async def get_all_characters(active_only: bool = True) -> list[Character]:
        """
        Get all characters available in the database.
        :param active_only: If enabled, will only grab characters active in the last 90 days.
        :return:
        """
        delta = datetime.now() - timedelta(days=90)
        async with db.async_session() as session:
            stmt = select(Character).join(User).where(User.onServer)
            if active_only:
                stmt = stmt.where(User.lastActive >= delta)
            characters = await session.scalars(stmt)
            characters = characters.all()

        return characters

    @staticmethod
    async def nlp_get_active(
        server: disnake.Guild,
        response: disnake.Message,
        days: int,
        channel: disnake.TextChannel = None,
    ) -> None:
        """
        Loops over all the messages in the servers OOC channels for the last `days` days, and collects information about
        when a user was last active.
        """
        delta = timedelta(days=days)
        active_date = datetime.now() - delta
        authors = dict()

        channels = (
            1033410774531571763,  # city-ooc
            1033408354913112094,  # coast-ooc
            1033408355617751210,  # boreal-forest-ooc
            1079217639735447552,  # mountains-ooc
            1079217640284897411,  # east-island-ooc
            1103377002586710077,  # south-island-ooc
            1202008475689820160,  # west-island-ooc
            1303856036792369263,  # north-ooc
            1099802533012193470,  # other-ooc
            1316139007046058015,  # ashen-peninsula-ooc
        )
        if channel:
            channels = (channel.id,)

        for channel_id in channels:  # other-ooc
            channel = server.get_channel(channel_id)
            response = await response.edit(f"{response.content}\n- {channel.mention}")
            messages = await channel.history(limit=None, after=active_date).flatten()
            response = await response.edit(
                f"{response.content} ({len(messages)} messages)"
            )
            for message in messages:
                if (
                    message.author.id in authors
                    and authors[message.author.id] < message.created_at
                ):
                    authors[message.author.id] = message.created_at
                elif message.author.id not in authors:
                    authors[message.author.id] = message.created_at
            response = await response.edit(
                f"{response.content} ({len(authors)} total authors)"
            )

        response = await response.edit(f"{response.content}\nSaving")

        async with db.async_session() as session:
            for author, time in authors.items():
                try:
                    stmt = select(User).where(User.id == author)
                    user_objs = await session.scalars(stmt)
                    user_obj = user_objs.one()
                except NoResultFound:
                    # User has left the server or has no validated character
                    user_obj = User(id=author)
                member = server.get_member(author)
                user_obj.lastActive = time
                user_obj.onServer = bool(member)
                if member:
                    user_obj.name = member.name
                    user_obj.nickname = member.nick
                session.add(user_obj)
            await session.commit()

        await response.edit(f"{response.content}\nFinished!")

    async def nlp_update_character(
        self,
        active_only: bool = True,
        valid_only: bool = True,
        user_ids: list[int] = None,
        inter: ApplicationCommandInteraction | disnake.Message = None,
    ):
        """Grabs the current data from DDB for a character and updates that character in our database."""
        delta = datetime.now() - timedelta(days=90)
        errors = []
        async with db.async_session() as session:
            stmt = select(Character).join(User).where(User.onServer)
            if user_ids:
                stmt = stmt.filter(User.id.in_(user_ids))
            if active_only:
                stmt = stmt.where(User.lastActive >= delta)
            if valid_only:
                stmt = stmt.where(Character.valid)
            result = await session.execute(stmt)
            characters = result.scalars().all()

            response = None
            msg = f"Grabbing {len(characters)} Characters\n0/{len(characters)}"
            if isinstance(inter, disnake.ApplicationCommandInteraction):
                response = await inter.followup.send(msg)
            elif inter:
                response = await inter.edit(f"{inter.content}\n{msg}")

            for i, character in enumerate(characters, start=1):
                if i % 5 == 0 or i == len(characters):
                    if response:
                        response_content = re.sub(
                            r"\d+/\d+", f"{i}/{len(characters)}", response.content
                        )
                        response = await response.edit(response_content)
                data, error = await get_character_data(self.bot, character.url)
                if error:
                    error_out = (
                        f"Error with the following Character:\n"
                        f" - Character: {character.name}\n"
                        f" - URL: {character.url}\n"
                        f" - User: <@{character.user_id}>\n"
                        f" - {error}"
                    )
                    logger.warning(error_out)
                    logger.debug(f" - {data}")
                    character.valid = False
                    errors.append(f"```md\n{error_out}\n```")
                    continue

                time.sleep(1)

                if "classes" not in data:
                    error_out = (
                        f"Error with the following Character:\n"
                        f" - Character: {character.name}\n"
                        f" - URL: {character.url}\n"
                        f" - Classes not found in data"
                    )
                    logger.warning(error_out)
                    logger.debug(f" - {data}")
                    character.valid = False
                    errors.append(f"```md\n{error_out}\n```")
                    continue

                classes, subclasses = get_classes(data)
                stats = get_stats(data)
                invocations = get_invocations(data)
                feats = get_feats(data)

                level = sum(classes.values())
                race = data["race"]["fullName"]
                name = data['name']

                character.name = name
                character.level = level
                character.race = race
                character.classes = classes
                character.subclasses = subclasses
                character.stats = stats
                character.invocations = invocations
                character.feats = feats
                character.valid = True

                session.add(character)

            await session.commit()

        if response:
            response = await response.edit(response_content + "\nSaved")
            reply = response
            for error in errors:
                reply = await reply.reply(error, allowed_mentions=disnake.AllowedMentions().none())

        return response


def setup(bot):
    bot.add_cog(NLPCommands(bot))
