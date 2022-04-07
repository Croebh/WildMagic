import json
import re
from typing import Optional

import requests

from utils import utils

from disnake.ext import commands


class CharInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def get_desc(self, ctx: commands.Context, url: str):
        """Generates a command to set up your characters description, given a provided DDB character sheet."""
        # await utils.try_delete(ctx.message)
        out = await self._get_desc(ctx, url)
        await ctx.send(f"```py\n{out}\n```")

    @commands.command()
    async def get_tools(self, ctx: commands.Context, url: str):
        """Generates a command to set up your tool proficiencies for `!tool`, given a provided DDB character sheet."""
        # await utils.try_delete(ctx.message)
        out = await self._get_tools(ctx, url)
        if not out:
            await ctx.send("No tool proficiencies found.")
            return
        await ctx.send(f"```py\n{out}\n```")

    @commands.command()
    async def get_bags(self, ctx: commands.Context, url: str):
        """Generates a command to set up the `!bag` alias, given a provided DDB character sheet."""
        # await utils.try_delete(ctx.message)
        out = await self._get_bags(ctx, url)
        await ctx.send(f"```py\n{out}\n```")

    @commands.command()
    async def new_char(self, ctx: commands.Context, url: str):
        """Generates a multiline command that assist with creating new characters,
        given a provided DDB character sheet."""
        # await utils.try_delete(ctx.message)
        out = [i for i in [await self._get_desc(ctx, url),
                           await self._get_bags(ctx, url),
                           await self._get_tools(ctx, url)]
               if i]
        await ctx.send("```py\n!multiline\n" + '\n'.join(out) + "\n```")

    @staticmethod
    async def get_character_data(ctx: commands.Context, url: str):
        regex = r"^.*characters\/(\d+)\/?"
        match = re.search(regex, url)

        if not match:
            await ctx.send("Unable to find a valid DDB character link.")
            return

        url = f"https://character-service.dndbeyond.com/character/v3/character/{match.group(1)}"
        resp = requests.get(url)
        json_data = json.loads(resp.content)['data']
        return json_data

    async def _get_desc(self, ctx: commands.Context, url: str) -> str:

        alignments = ["LG", "NG", "CG",
                      "LN", "TN", "CN",
                      "LE", "NE", "CE"]

        data = await self.get_character_data(ctx, url)

        classes = []
        for _class in data['classes']:
            cur_class = _class['definition']['name']
            if _class['subclassDefinition']:
                cur_class += f" ({_class['subclassDefinition']['name']})"
            classes.append(cur_class)
        out = {
            "height": data["height"] or "height",
            "weight": f'{data["weight"]} lb.' or "weight",
            "race": data['race']['fullName'] or "race",
            "class": '/'.join(classes) or "class",
            "appearance": data['traits'][
                              "appearance"] or "Write a bit about attitude, appearance, and background here.",
            "traits": data['traits'][
                          "personalityTraits"] or "Enter your D&D Beyond rolled trait(s) here\n"
                                                  "Enter your D&D Beyond rolled trait(s) here",
            "ideals": data['traits']["ideals"] or "Enter your D&D Beyond rolled ideal(s) here",
            "bonds": data['traits']["bonds"] or "Enter your D&D Beyond rolled bond(s) here",
            "flaws": data['traits']["flaws"] or "Enter your D&D Beyond rolled flaw(s) here",
            "alignment": alignments[data['alignmentId'] - 1] if data[
                'alignmentId'] else "Enter your alignment"
        }
        desc_out = f"""!desc update __**{out['height']} | {out['weight']} | {out['race']} | {out['class']}**__
                       > {out["appearance"]}
                       **Personality Traits**
                       {out["traits"]}
                       **Ideals**
                       {out["ideals"]}
                       **Bonds**
                       {out["bonds"]}
                       **Flaws**
                       {out["flaws"]}
                       **Alignment**
                       {out["alignment"]}"""
        return '\n'.join([line.strip() for line in desc_out.splitlines()])

    async def _get_tools(self, ctx: commands.Context, url: str) -> Optional[str]:

        data = await self.get_character_data(ctx, url)

        profs = []
        expertise = []
        for _type in data['modifiers']:
            for modifier in data['modifiers'][_type]:
                # We only care about tool proficiencies
                if modifier['entityTypeId'] == 2103445194:
                    if modifier['type'] == 'proficiency':
                        profs.append(modifier['friendlySubtypeName'])
                    if modifier['type'] == 'expertise':
                        expertise.append(modifier['friendlySubtypeName'])
        out = []
        if profs:
            out.append(f"""!cvar pTools {', '.join(profs)}""")
        if expertise:
            out.append(f"""!cvar eTools {', '.join(expertise)}""")
        return '\n'.join(out) or None

    async def _get_bags(self, ctx: commands.Context, url: str) -> str:

        data = await self.get_character_data(ctx, url)

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
        return f"!cvar bags {json.dumps(list(out.items()))}"


def setup(bot):
    bot.add_cog(CharInfo(bot))
