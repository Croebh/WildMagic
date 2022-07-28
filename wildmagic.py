import asyncio
import logging
import os
import sys
import traceback
from datetime import datetime, timedelta, timezone

from aiohttp import ClientResponseError, ClientOSError
from disnake import Forbidden, HTTPException, NotFound, InvalidArgument

from utils import checks, config

import disnake
from disnake.ext import tasks, commands
from disnake.ext.commands import CommandInvokeError, CommandNotFound, MissingRequiredArgument
from disnake.ext.commands import MissingAnyRole

COGS = ("cogsmisc.repl", "cogsddb.charinfo", "cogshome.tv", "cogsserver.search", "cogsserver.serverlocale")

PREFIX = "??"
NEWLINE = "\n"

intents = disnake.Intents.all()


class CustomHelp(commands.DefaultHelpCommand):
    async def send_pages(self):
        destination = self.get_destination()
        for page in self.paginator.pages:
            embed = disnake.Embed(description=page)
            await destination.send(embed=embed)

    def add_indented_commands(self, command_iter, *, heading, max_size=None):
        if not command_iter:
            return

        self.paginator.add_line(f"**{heading}**")

        for command in command_iter:
            name = command.name
            entry = f"`{PREFIX}{name} {command.signature}`\n> {command.short_doc}"
            self.paginator.add_line(entry)
        self.paginator.add_line()

    def add_command_formatting(self, command):
        """A utility function to format the non-indented block of commands and groups.

        Parameters
        ----------
        command: :class:`Command`
            The command to format.
        """
        if command.description:
            self.paginator.add_line(command.description, empty=True)

        signature = self.get_command_signature(command)
        self.paginator.add_line(f"`{signature}`", empty=True)

        if command.help:
            try:
                for line in command.help.splitlines():
                    self.paginator.add_line(f"> {line}")
            except RuntimeError:
                for line in command.help.splitlines():
                    self.paginator.add_line(line)
                self.paginator.add_line()


bot = commands.Bot(
    command_prefix=commands.when_mentioned_or(PREFIX),
    pm_help=False,
    case_insensitive=True,
    intents=intents,
    owner_id=config.OWNER_ID,
    help_command=CustomHelp(
        sort_commands=False,
        width=1000,
        paginator=commands.Paginator(prefix=None, suffix=None),
        no_category="Uncategorized",
    ),
    test_guilds=[558408317957832726],
)


@bot.event
async def on_command_error(ctx, error):
    error_msg = "You done goofed?"
    if isinstance(error, CommandNotFound):
        error_msg = f"Command not found. View `{PREFIX}help` for valid commands."
    elif isinstance(error, (CommandInvokeError, MissingRequiredArgument)):
        error_msg = f"Incorrect invocation. Please re-examine the command in `{PREFIX}help`."
    elif isinstance(error, MissingAnyRole):
        error_msg = "You don't have any of the roles required to run this command."
    await ctx.message.channel.send(f"Error: {error_msg} ({error})")
    return


@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")


@bot.command(hidden=True)
@checks.is_owner()
async def restart(ctx):
    """Restarts the bot"""
    await ctx.send("Restarting...")
    print("Restarting...")
    os.execv(sys.executable, ["python"] + sys.argv)


log_formatter = logging.Formatter("%(levelname)s:%(name)s: %(message)s")
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(log_formatter)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(handler)
log = logging.getLogger("bot")


@bot.listen("on_message")
async def check_account_age(message):
    if message.channel.id == 914453395472023612 and message.embeds:
        embed = message.embeds[0]
        author = embed.author
        member = message.channel.guild.get_member_named(author.name)
        age = member.created_at

        if age > datetime.now(tz=timezone.utc) - timedelta(days=180):
            await asyncio.sleep(10)
            await message.add_reaction("\N{baby}")


@bot.listen("on_raw_reaction_add")
async def planeshit(event):
    if event.emoji.id == 947259269592530984 and event.user_id == 164249546073964544:
        msg_id = event.message_id
        channel = bot.get_channel(event.channel_id)
        message = await channel.fetch_message(msg_id)

        for reaction in "🇵🇱🇦🇳🇪🇸🇭🇮🇹":
            await message.add_reaction(reaction)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return

    elif isinstance(error, (commands.UserInputError, commands.NoPrivateMessage, ValueError)):
        return await ctx.send(
            f"Error: {str(error)}\nUse `{ctx.prefix}help " + ctx.command.qualified_name + "` for help."
        )

    elif isinstance(error, commands.CheckFailure):
        msg = str(error) or "You are not allowed to run this command."
        return await ctx.send(f"Error: {msg}")

    elif isinstance(error, commands.CommandOnCooldown):
        return await ctx.send("This command is on cooldown for {:.1f} seconds.".format(error.retry_after))

    elif isinstance(error, commands.MaxConcurrencyReached):
        return await ctx.send(str(error))

    elif isinstance(error, CommandInvokeError):
        original = error.original

        if isinstance(original, Forbidden):
            try:
                return await ctx.author.send(
                    "Error: I am missing permissions to run this command. "
                    f"Please make sure I have permission to send messages to <#{ctx.channel.id}>."
                )
            except HTTPException:
                try:
                    return await ctx.send(f"Error: I cannot send messages to this user.")
                except HTTPException:
                    return

        elif isinstance(original, NotFound):
            return await ctx.send("Error: I tried to edit or delete a message that no longer exists.")

        elif isinstance(original, (ClientResponseError, InvalidArgument, asyncio.TimeoutError, ClientOSError)):
            return await ctx.send("Error in Discord API. Please try again.")

        elif isinstance(original, HTTPException):
            if original.response.status == 400:
                return await ctx.send(f"Error: Message is too long, malformed, or empty.\n{original.text}")
            elif 499 < original.response.status < 600:
                return await ctx.send("Error: Internal server error on Discord's end. Please try again.")

    await ctx.send(f"Error: {str(error)}\nUh oh, that wasn't supposed to happen! ")

    log.warning("Error caused by message: `{}`".format(ctx.message.content))
    for line in traceback.format_exception(type(error), error, error.__traceback__):
        log.warning(line)


for cog in COGS:
    bot.load_extension(cog)

if __name__ == "__main__":
    bot.run(config.TOKEN)
