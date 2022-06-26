from async_lru import alru_cache
import time

import disnake
from disnake.ext import commands


def get_ttl_hash(seconds=3600):
    """Return the same value within `seconds` time period"""
    return round(time.time() / seconds)


class Search(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["transcript"])
    async def transcripts(self, ctx, search_type, user: disnake.Member):
        """
        Allows you to search through transcript logs by type.
        This caches the results for 1 hour, to reduce server/bot load.

        **Valid Search Types:** `character`, `help`, `support`, `quest`
        **Valid User Type:** Can either be an @ tag, or their user ID.
        """

        match search_type:
            case "character":
                search_type = ["Character Submissions"]
            case "help" | "support":
                search_type = ["Help and Support"]
            case "quest":
                search_type = ["Quest Request"]
            case "all":
                search_type = ["Character Submissions", "Help and Support", "Quest Request"]
            case _:
                await ctx.send("What kinda search, silly?")
                return

        if user is None:
            await ctx.send("Who are you searching for, silly?")
            return

        async with ctx.typing():
            transcripts = await self.get_transcripts(ttl_hash=get_ttl_hash())

        for search in search_type:
            out = []
            for transcript in transcripts[search]:
                if transcript["member"] and user.id == transcript["member"].id:
                    out.append(transcript)
                    if len(out) >= 25:
                        break
            if not out:
                await ctx.send(f"No results found in {search}.")
                return

            embed = disnake.Embed(title=search, description=f"Results for <@{user.id}>")
            for transcript in out:
                embed.add_field(
                    name=transcript["ticket"],
                    value=f"{transcript['transcript']}\n[Transcript Message]({transcript['message']})",
                )
            embed.set_footer(text="??transcript [user]")
            await ctx.send(embed=embed)

    @commands.command(aliases=["application"])
    async def applications(self, ctx, user: disnake.Member):
        """
        Allows you to search through applications by user.
        This caches the results for 1 hour, to reduce server/bot load.

        **Valid User Type:** Can either be an @ tag, or their user ID.
        """

        if user is None:
            await ctx.send("Who are you searching for, silly?")
            return

        out = []

        async with ctx.typing():
            applications = await self.get_applications(ttl_hash=get_ttl_hash())

        for application in applications:
            if application["member"] and user.id == application["member"].id:
                out.append(application)
                if len(out) >= 25:
                    break
        if not out:
            await ctx.send("No results found.")
            return

        embed = disnake.Embed(title="Application Lookup", description=f"Results for <@{user.id}>")
        for application in out:
            embed.description += f"\n[{application['type']}]({application['message']})"
        embed.set_footer(text="??application [user]")
        await ctx.send(embed=embed)

    @alru_cache()
    async def get_applications(self, ttl_hash=None):
        guild = self.bot.get_guild(895259516411711528)
        channel = guild.get_channel(914453395472023612)

        applications = []

        messages = await channel.history(limit=None).flatten()

        for message in messages:
            if message.embeds:
                embed = message.embeds[0]
                author = embed.author
                member = guild.get_member_named(author.name)
                applications.append({"member": member, "message": message.jump_url, "type": embed.title})

        return applications

    @alru_cache()
    async def get_transcripts(self, ttl_hash=None):
        del ttl_hash
        guild = self.bot.get_guild(895259516411711528)
        channel = guild.get_channel(903480482384216064)

        transcripts = {"Character Submissions": [], "Help and Support": [], "Quest Request": []}

        messages = await channel.history(limit=None).flatten()

        for message in messages:
            if message.embeds and message.embeds[0].fields:
                embed = message.embeds[0]

                member = guild.get_member(int(embed.fields[0].value.strip("<>@")))

                transcripts[embed.fields[2].value].append(
                    {
                        "member": member,
                        "message": message.jump_url,
                        "transcript": embed.fields[3].value,
                        "ticket": embed.fields[1].value,
                    }
                )

        return transcripts


def setup(bot):
    bot.add_cog(Search(bot))
