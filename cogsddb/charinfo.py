import json
import re
from typing import Optional

import requests

from disnake.ext import commands

import utils.config


class CharInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(extras={"integration_types": [0, 1], "contexts": [0, 1, 2]})
    async def new_char(self, ctx, sheet_url: str):
        """Generates a multiline command that assist with creating new characters.

        Parameters
        ----------
        sheet_url: The DDB character sheet URL to use"""
        data = await self.get_character_data(ctx, sheet_url)
        # desc, issues = await self._get_desc(ctx, sheet_url, data)
        out = [
            i
            for i in [
                # desc,
                # await self._get_bags(ctx, sheet_url, data),
                await self._get_tools(ctx, sheet_url, data),
                await self._get_languages(ctx, sheet_url, data),
                await self._get_feats(ctx, sheet_url, data),
            ]
            if i
        ]

        # If their description is long enough to make this over the limit, send it separately
        if len("\n".join(out)) >= 1900:
            await ctx.send(
                "**__Copy and paste the following commands into this channel:__**\n```py\n"
                + ((out[0][:1900] + "...") if len(out[0]) >= 1900 else out[0])
                + "\n```"
            )
            await ctx.send("```py\n!multiline\n" + "\n".join(out[1:]) + "\n```", ephemeral=True)
        else:
            await ctx.send(
                "**__Copy and paste the following command into this channel:__**\n```py\n!multiline\n"
                + "\n".join(out)
                + "\n```", ephemeral=True
            )
        # if issues:
        #     await ctx.send(f"**__Issues found:__**\n{', '.join(issues)}", ephemeral=True)

    @commands.command(enabled=False)
    async def get_desc(self, ctx: commands.Context, sheet_url: str):
        """Generates a command to set up your characters description, given a provided DDB character sheet."""
        out, issues = await self._get_desc(ctx, sheet_url)
        out = (out[:1900] + "...") if len(out) >= 1900 else out
        await ctx.send(f"**__Copy and paste the following command into this channel:__**\n```py\n{out}\n```")
        if issues:
            await ctx.send(f"**__Issues found:__**\n{', '.join(issues)}")

    @commands.command(enabled=False)
    async def get_languages(self, ctx: commands.Context, sheet_url: str):
        """Generates a command to set up your characters languages, given a provided DDB character sheet."""
        out = await self._get_languages(ctx, sheet_url)
        await ctx.send(f"**__Copy and paste the following command into this channel:__**\n```py\n{out}\n```")

    @commands.command(enabled=False)
    async def get_feats(self, ctx: commands.Context, sheet_url: str):
        """Generates a command to set up your characters feats, given a provided DDB character sheet."""
        out = await self._get_feats(ctx, sheet_url)
        if not out:
            await ctx.send("No feats found.")
            return
        await ctx.send(f"**__Copy and paste the following command into this channel:__**\n```py\n{out}\n```")

    @commands.command(enabled=False)
    async def get_tools(self, ctx: commands.Context, sheet_url: str):
        """Generates a command to set up your tool proficiencies for `!tool`, given a provided DDB character sheet."""

        out = await self._get_tools(ctx, sheet_url)
        if not out:
            await ctx.send("No tool proficiencies found.")
            return
        await ctx.send(f"**__Copy and paste the following command into this channel:__**\n```py\n{out}\n```")

    @commands.command(enabled=False)
    async def get_bags(self, ctx: commands.Context, sheet_url: str):
        """Generates a command to set up the `!bag` alias, given a provided DDB character sheet."""
        out = await self._get_bags(ctx, sheet_url)
        await ctx.send(
            f"**__Copy and paste the following command into this channel:__**\n```py\n!multiline\n{out}\n```"
        )

    @staticmethod
    async def get_character_data(ctx: commands.Context, sheet_url: str):
        regex = r"^.*characters\/(\d+)\/?"
        match = re.search(regex, sheet_url)

        if not match:
            await ctx.send("Unable to find a valid DDB character link.")
            return

        headers = {
            "accept": "application/json",
            "accept-language": "en-CA,en-VI;q=0.9,en-US;q=0.8,en;q=0.7",
            "authorization": utils.config.BEARER_TOKEN,
            "sec-ch-ua": '" Not A;Brand";v="99", "Chromium";v="102", "Google Chrome";v="102"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
        }

        sheet_url = f"https://character-service.dndbeyond.com/character/v5/character/{match.group(1)}"
        resp = requests.get(sheet_url, headers=headers)
        json_data = json.loads(resp.content)["data"]
        return json_data

    async def _get_desc(self, ctx: commands.Context, sheet_url: str, data: dict = None) -> tuple[str, list[str]]:

        alignments = ["LG", "NG", "CG", "LN", "TN", "CN", "LE", "NE", "CE"]
        if data is None:
            data = await self.get_character_data(ctx, sheet_url)

        classes = []
        for _class in data["classes"]:
            cur_class = _class["definition"]["name"]
            if _class["subclassDefinition"]:
                cur_class += f" ({_class['subclassDefinition']['name']})"
            classes.append(cur_class)
        out = {
            "height": data["height"] or "height",
            "weight": f'{data["weight"]} lb.' if data["weight"] else "weight",
            "race": data["race"]["fullName"] or "race",
            "class": "/".join(classes) or "class",
            "appearance": (
                data["traits"]["appearance"]
                or data.get("notes", {}).get("backstory")
                or "Write a bit about attitude, appearance, and background here."
            ),
            "traits": data["traits"]["personalityTraits"]
            or "Enter your D&D Beyond rolled trait(s) here\nEnter your D&D Beyond rolled trait(s) here",
            "ideals": data["traits"]["ideals"] or "Enter your D&D Beyond rolled ideal(s) here",
            "bonds": data["traits"]["bonds"] or "Enter your D&D Beyond rolled bond(s) here",
            "flaws": data["traits"]["flaws"] or "Enter your D&D Beyond rolled flaw(s) here",
            "alignment": alignments[data["alignmentId"] - 1] if data["alignmentId"] else "Enter your alignment",
        }
        issues = []
        if out["height"] == "height":
            issues.append("Height not set")
        if out["weight"] == "weight":
            issues.append("Weight not set")
        if out["appearance"] == "Write a bit about attitude, appearance, and background here.":
            issues.append("Description (Appearance on DDB) not set")
        for trait in ("traits", "ideals", "bonds", "flaws"):
            if "Enter your D&D Beyond rolled trait(s) here" in out[trait]:
                issues.append(f"{trait.title()} not set")

        appearance = "\n".join([f"> {line}" for line in out["appearance"].strip().splitlines()])
        desc_out = f"""!desc update __**{out['height']} | {out['weight']} | {out['race']} | {out['class']}**__
                       ###APPEARANCEHERE###
                       **Personality Traits**
                       {out["traits"].strip()}
                       **Ideals**
                       {out["ideals"].strip()}
                       **Bonds**
                       {out["bonds"].strip()}
                       **Flaws**
                       {out["flaws"].strip()}
                       **Alignment**
                       {out["alignment"].strip()}"""
        if (len(desc_out) - 20) + len(appearance) >= 2000:
            appearance = appearance[:2000-(len(desc_out)+20)] + "..."
        desc_out = desc_out.replace("###APPEARANCEHERE###", appearance)
        return "\n".join([line.strip() for line in desc_out.splitlines()]), issues

    async def _get_tools(self, ctx: commands.Context, sheet_url: str, data: dict = None) -> Optional[str]:
        if data is None:
            data = await self.get_character_data(ctx, sheet_url)

        profs = []
        expertise = []
        for _type in data["modifiers"]:
            for modifier in data["modifiers"][_type]:
                # We only care about tool proficiencies
                if modifier["entityTypeId"] == 2103445194:
                    if modifier["type"] == "proficiency":
                        profs.append(modifier["friendlySubtypeName"])
                    if modifier["type"] == "expertise":
                        expertise.append(modifier["friendlySubtypeName"])
        out = []
        if profs:
            out.append(f"""!cvar pTools {', '.join(profs)}""")
        if expertise:
            out.append(f"""!cvar eTools {', '.join(expertise)}""")
        return "\n".join(out) or None

    async def _get_languages(self, ctx: commands.Context, sheet_url: str, data: dict = None) -> Optional[str]:
        if data is None:
            data = await self.get_character_data(ctx, sheet_url)

        languages = []
        for _type in data["modifiers"]:
            for modifier in data["modifiers"][_type]:
                # We only care about languages
                if modifier["entityTypeId"] == 906033267:
                    languages.append(modifier["friendlySubtypeName"])

        return f"""!cvar languages {', '.join(languages)}"""

    async def _get_feats(self, ctx: commands.Context, sheet_url: str, data: dict = None) -> Optional[str]:
        if data is None:
            data = await self.get_character_data(ctx, sheet_url)

        feats = []
        for _feat in data["feats"]:
            feats.append(_feat["definition"]["name"])

        if feats:
            return f"""!cvar feats {', '.join(feats)}"""

    async def _get_bags(self, ctx: commands.Context, sheet_url: str, data: dict = None) -> str:

        if data is None:
            data = await self.get_character_data(ctx, sheet_url)

        out = {
            "Backpack": {},
            "Equipment": {},
            "Magical Items": {},
            "Consumables": {},
            "Harvest": {},
        }

        for item in data["inventory"]:
            bag_name = "Backpack"
            if item["definition"]["magic"]:
                bag_name = "Magical Items"
            elif item["definition"]["canEquip"]:
                bag_name = "Equipment"
            elif item["definition"]["isConsumable"]:
                bag_name = "Consumables"
            item_name = item["definition"]["name"]
            quantity = item["quantity"]
            out[bag_name][item_name] = out[bag_name].get(item_name, 0) + quantity
        bag_settings = {
            "weightlessBags": ["bag of holding", "handy haversack", "heward's handy haversack"],
            "customWeights": {},
            "weightTracking": "Off",
            "openMode": "One",
            "encumbrance": "Off",
        }
        return (
            f"!cvar bags {json.dumps(list(out.items()))}\n"
            f"""!cvar bagSettings {json.dumps(bag_settings)}\n"""
            f"!csettings compactcoins true"
        )


def setup(bot):
    bot.add_cog(CharInfo(bot))
