import json
import logging
from disnake import ApplicationCommandInteraction

from disnake.ext import commands

from utils.functions import (
    get_character_data,
    get_tools,
    get_languages,
    get_feats,
    get_invocations,
    get_bags,
)

logger = logging.getLogger(__name__)


class CharInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # todo: what if this also allowed dicecloud/gsheet? hmm
    @commands.contexts(guild=True, bot_dm=True, private_channel=True)
    @commands.install_types(guild=True, user=True)
    @commands.slash_command()
    async def avrae_character_setup(
        self,
        inter: ApplicationCommandInteraction,
        sheet_url: str,
        tools: bool = True,
        languages: bool = True,
        feats: bool = True,
        invocations: bool = True,
        bags: bool = False,
    ):
        """Generates a multiline command that assist with creating new characters.

        Parameters
        ----------
        inter: ApplicationCommandInteraction
        sheet_url: The DDB character sheet URL to use
        tools: Whether to include tool proficiencies in the output
        languages: Whether to include languages in the output
        feats: Whether to include feats in the output
        invocations: Whether to include eldritch invocations in the output
        bags: Whether to include bags in the output
        """
        await inter.response.defer(ephemeral=True)
        data, error = await get_character_data(self.bot, sheet_url)

        if error:
            await inter.send(f"Issue loading character:\n - {error}")
            return

        out = []

        if tools and any(tools := get_tools(data)):
            prof, exp = tools
            if prof:
                out.append(f"!cvar pTools {','.join(prof)}")
            if exp:
                out.append(f"!cvar eTools {','.join(exp)}")

        if languages and (languages := get_languages(data)):
            out.append(f"!cvar languages {','.join(languages)}")

        if feats and (feats := get_feats(data)):
            out.append(f"!cvar feats {','.join(feats)}")

        if invocations and (invocations := get_invocations(data)):
            out.append(f"!cvar invocations {','.join(invocations)}")

        if bags and (bags := get_bags(data)):
            out.append(f"!cvar bags {json.dumps(bags, separators=(',', ':'))})")
            out.append(
                """!cvar bagSettings {"weightlessBags": ["bag of holding", "handy haversack", "heward's handy haversack"], "customWeights": {}, "weightTracking": "Off", "openMode": "One", "encumbrance": "Off"}"""
            )
            out.append("!csettings compactcoins true")

        # If their data is long enough to make this over the limit, send it separately
        if len("\n".join(out)) >= 1900:
            await inter.send(
                "**__Copy and paste the following commands into this channel:__**\n```py\n"
                + ((out[0][:1900] + "...") if len(out[0]) >= 1900 else out[0])
                + "\n```"
            )
            await inter.send(
                "```py\n!multiline\n" + "\n".join(out[1:]) + "\n```", ephemeral=True
            )
        else:
            await inter.send(
                "**__Copy and paste the following command into this channel:__**\n```py\n!multiline\n"
                + "\n".join(out)
                + "\n```",
                ephemeral=True,
            )


def setup(bot):
    bot.add_cog(CharInfo(bot))
