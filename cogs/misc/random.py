from datetime import timedelta, datetime, timezone

from disnake import InteractionContextTypes
from disnake.ext import commands
import disnake

from dateparser import parse as parse_date


class Random(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    contexts = InteractionContextTypes.all()

    @commands.contexts(guild=True, bot_dm=True, private_channel=True)
    @commands.install_types(guild=True, user=True)
    @commands.slash_command(name="timestamp")
    async def timestamp(self, inter, time_statement: str, ephemeral: bool = True):
        """Get a Discord timestamp for a relative time statement, like '3 days from now' or '2pm EST'.

        Parameters
        ----------
        inter: The interaction itself
        time_statement: The relative time statement to parse
        ephemeral: Whether the response should be ephemeral, defaults to True"""
        await inter.response.defer(ephemeral=ephemeral)
        timestamp = parse_date(time_statement)
        if not timestamp:
            await inter.send(
                f"**Couldn't Parse Time:** `{time_statement}`",
                ephemeral=ephemeral,
                delete_after=20,
            )
            return
        unix = int(timestamp.timestamp())
        await inter.send(
            f"**Generating Timestamp for:** `{time_statement}`\n`<t:{unix}>` <t:{unix}>\n`<t:{unix}:R>` <t:{unix}:R>",
            ephemeral=ephemeral,
        )

    @commands.slash_command(
        name="owlbear_latest", description="Gets the latest Owlbear Rodeo map link"
    )
    async def owlbear_latest(self, inter, days: int = 7):
        """Gets the latest Owlbear Rodeo map link"""
        await inter.response.defer(ephemeral=True)
        await inter.followup.send(
            f"Beginning search for the latest Owlbear Rodeo map link for the last {days} days",
            ephemeral=True,
        )
        delta = timedelta(days=days)
        active_date = datetime.now(tz=timezone.utc) - delta

        async for message in inter.channel.history(
            limit=None, after=active_date, oldest_first=False
        ):
            if message.author.id == self.bot.user.id:
                continue
            if "owlbear.rodeo/room" in message.content.lower():
                timestamp = int(message.created_at.timestamp())
                await message.reply(
                    f"Last Owlbear Rodeo link in this channel was <t:{timestamp}> <t:{timestamp}:R>!\n> {message.content}",
                    mention_author=False,
                    allowed_mentions=disnake.AllowedMentions(users=False),
                )
                break
        else:
            await inter.followup.send(
                f"No Owlbear Rodeo links found in the last {days} days", ephemeral=True
            )


def setup(bot):
    bot.add_cog(Random(bot))
