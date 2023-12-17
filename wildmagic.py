import os
import sys

from utils import checks, config

import disnake
from disnake.ext import commands
from disnake.ext.commands import CommandInvokeError, CommandNotFound, MissingRequiredArgument
from disnake.ext.commands import MissingAnyRole

COGS = ("cogsmisc.repl", "cogsddb.charinfo", "cogsmisc.random")

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
    case_insensitive=True,
    intents=intents,
    owner_id=config.OWNER_ID,
    help_command=CustomHelp(
        sort_commands=False,
        width=1000,
        paginator=commands.Paginator(prefix=None, suffix=None),
        no_category="Uncategorized",
    ),
    # test_guilds=[558408317957832726],
    command_sync_flags=commands.CommandSyncFlags.all()
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

for cog in COGS:
    bot.load_extension(cog)

if __name__ == "__main__":
    bot.run(config.TOKEN)
