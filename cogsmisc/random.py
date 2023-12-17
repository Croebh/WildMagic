from disnake.ext import commands

from dateparser import parse as parse_date


class Random(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="timestamp")
    async def timestamp(self, inter, time_statement:str, ephemeral: bool = True):
        """Get a Discord timestamp for a relative time statement, like '3 days from now' or '2pm EST'.

        Parameters
        ----------
        time_statement: The relative time statement to parse
        ephemeral: Whether the response should be ephemeral, defaults to True"""
        await inter.response.defer(ephemeral=ephemeral)
        timestamp = parse_date(time_statement)
        if not timestamp:
            await inter.send(f"**Couldn't Parse Time:** `{time_statement}`", ephemeral=ephemeral, delete_after=20)
            return
        unix = int(timestamp.timestamp())
        await inter.send(f"**Generating Timestamp for:** `{time_statement}`\n`<t:{unix}>` <t:{unix}>\n`<t:{unix}:R>` <t:{unix}:R>", ephemeral=ephemeral)


def setup(bot):
    bot.add_cog(Random(bot))
