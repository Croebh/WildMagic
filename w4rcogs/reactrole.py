# Functions in this cog were initially written by Dusk Argentum#6530 (97153790897045504).
import os  # The os module. Used to call up environmental variables, which help obscure sensitive information. Also
# aids in file management.
import json  # The json module. Used to manage JSONs.
from typing import Union  # Union aids in allowing arguments to be two different things and still work.


import discord  # The Discord module. Used in the bot to do Discord things
from discord import Forbidden, NotFound  # Error handling imports.
from discord.ext import commands  # Imports the commands submodule for use in commands.
from discord.ext.commands import guild_only, has_any_role  # Imports the aforementioned checks.
import asyncio  # Used for sleeping when need be.
from asyncio import TimeoutError  # The TimeoutError exception allows certain checks to function and not exist
# indefinitely.


from wildmagic import PREFIX


class ReactRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

#     @commands.Cog.listener()
#     async def on_command_error(self, ctx, error):  # This listener listens for command errors and returns the context
#         # and the exception encountered.
#         if isinstance(error, CommandInvokeError):  # Functions in this block execute if the command passes an unhandled
#             # exception. In theory, this should never be seen, and is here as a catch-all.
#             error = f"""Incorrect invocation. View `{PREFIX}{f"{ctx.command.root_parent}" if ctx.command.root_parent is
#                                                                                              not None else "help"}` \
#                                                                                              for valid commands."""
#         if isinstance(error, CommandNotFound):  # Functions in this block execute if the command used is not a valid
#             # command.
#             error = f"Command not found. View `{PREFIX}help` for valid commands."
#         elif isinstance(error, MissingAnyRole):  # Functions in this block execute if the command invoker does not have
#             # any of the roles required to run that command.
#             error = "You lack the role required to run this command."
#         try:
#             await ctx.send(f"""Error: {error}
# Context: `{PREFIX}{ctx.command.qualified_name}`""")  # Sends the error message and the context command for
#             # debugging if need be.
#             await ctx.message.add_reaction("👎")  # This is added on to the end of every error in this bot as a way to
#         # inform a member if their command has not worked correctly.
#         except AttributeError:
#             print(str(ctx.message))
#         return  # Yes, I know returns are useless at the bottom of def blocks. I just think they're neat!
    # You probably already have one of these, so I'm not gonna add mine.

    @commands.Cog.listener("on_raw_reaction_add")
    async def react_role_raw_reaction_add(self, payload):  # This listener listens for reactions and returns the payload
        # of the event.
        if self.bot.user.id == payload.user_id:  # Prevents the bot from adding roles to itself.
            return
        with open("react_role.json", "r") as react_role:  # Opens the react_role.json file and loads it as a data
            # object.
            data = json.load(react_role)
        group_check = 0  # Defines a zero-count for an upcoming function.
        group = ""  # Defines an empty string for an upcoming function.
        for group in data["react_role"]["groups"]:  # Functions in this block execute for every item in the groups key
            # within the react_role JSON.
            keys = list(data["react_role"]["groups"].keys())  # Defines the keys within the groups key.
            if str(payload.message_id) in str(data["react_role"]["groups"][str(keys[int(group_check)])]["message"]):
                # Functions in this block execute if the message ID for a group is within that group's message key.
                group = str(keys[int(group_check)])  # Defines the group variable as the keys within the group found.
                break  # Exits the loop.
            else:  # Functions in this block execute if the above condition is not met. In this case, if the message ID
                # is not within the group's message key.
                group_check += 1  # Increments the group_check counter by one.
                if group_check == len(data["react_role"]["groups"]):  # Functions in this block execute if the
                    # group_check counter is equal to the number of keys within the groups key.
                    return  # Stops processing if the above condition is met. This is essentially error handling.
                continue  # Returns to the top of the loop and continues executing.
        if str(payload.emoji) in str(data["react_role"]["groups"][group]["reactions"]):  # Functions in this block
            # execute if the payload's emoji is in the reactions key of the group defined in the above function.
            keys = list(data["react_role"]["groups"][group]["reactions"].keys())  # Defines the list of keys within the
            # reactions key.
            emoji_check = 1  # Defines a one-count for an upcoming function. Used as opposed to a zero-count for ease;
            # the names of the keys within the reactions key are all numbers, and they increment from one, as opposed to
            # zero.
            for emoji in str(data["react_role"]["groups"][group]["reactions"]):  # Functions in this block execute for
                # every item within the reactions key.
                if str(payload.emoji) == str(
                        data["react_role"]["groups"][group]["reactions"][str(emoji_check)]["emoji"]):
                    # Functions in this block execute if the payload's emoji matches the reaction's emoji value.
                    guild = await self.bot.fetch_guild(guild_id=int(payload.guild_id))  # Defines the guild as the one
                    # this event was heard from.
                    role = discord.utils.get(guild.roles, id=int(data["react_role"]["groups"][group]["reactions"]
                                                                 [str(emoji_check)]["role"]))  # Defines the role to
                    # grant as the role in the aforementioned guild with the same ID as the role key's value.
                    member = await guild.fetch_member(member_id=int(payload.user_id))  # Defines the member to grant the
                    # aforementioned role to as the member with the same ID as the user in the payload.
                    error_channel = self.bot.fetch_channel(channel_id=890786093522382908)  # Defines the error channel
                    # to send errors to.
                    # This should be changed for WildMagic to a channel WildMagic can actually access. This is basically
                    # just for debugging purposes, and can likely be removed, if not needed.
                    role_status = 0  # Defines a zero variable for later use.
                    if role in member.roles:  # Functions in this block execute if the role is already within the
                        # member's roles.
                        try:  # Attempts to execute the below code.
                            await member.remove_roles(role)  # Removes the role from the member.
                            role_status = 2  # Redefines the variable as two.
                        except Forbidden:  # Functions in this block execute if the above code throws a Forbidden
                            # exception.
                            await error_channel.send(
                                f"Failed to remove a role from {str(member.name)} ({member.id}): Lacked permissions.")
                            # Sends the a message describing the error to the error channel.
                            return
                    elif role not in member.roles:  # Functions in this block execute if the role is not already within
                        # the member's roles.
                        try:
                            await member.add_roles(role)  # Adds the role to the member.
                            role_status = 1  # Redefines the variable as one.
                        except Forbidden:
                            await error_channel.send(
                                f"Failed to add a role to {str(member.name)} ({member.id}): Lacked permissions.")
                    await member.send(f"""{"Added" if role_status == 1 else "Removed"} the role `{role}` \
{"to" if role_status == 1 else "from"} you in {guild.name}.""")  # Sends the member a DM informing them that their
                    # role has either been added or removed, depending on the value of the role_status variable.
                    channel = await self.bot.fetch_channel(channel_id=payload.channel_id)  # Defines the channel as the
                    # channel within the payload.
                    message = await channel.fetch_message(id=payload.message_id)  # Defines the message as the message
                    # within the payload.
                    await message.remove_reaction(payload.emoji, member)  # Removes the reaction from the message.
                    # This is to keep the count at 1; if it ever exceeds this, it means there was an unhandled exception
                    # and/or a problem with the bot (likely Discord latency or something to that effect).
                    # Just nice to have.
                    return
                else:  # Functions in this block execute if the emoji is not within the group's reactions.
                    if emoji_check == len(data["react_role"]["groups"][group]["reactions"]):  # Functions in this block
                        # execute if the amount of the emoji_check counter exceeds the amount of keys within the
                        # reactions key.
                        return
                    emoji_check += 1  # Increments the emoji_check counter by one.
                    continue
        elif str(payload.emoji) not in str(data["react_role"]["groups"][group]["reactions"]):  # Functions in this block
            # execute if the emoji added to the message is not within the reactions key. Essentially prevents people
            # from adding incorrect emojis.
            guild = await self.bot.fetch_guild(guild_id=int(payload.guild_id))
            member = await guild.fetch_member(member_id=int(payload.user_id))
            channel = await self.bot.fetch_channel(channel_id=payload.channel_id)
            message = await channel.fetch_message(id=payload.message_id)
            await message.remove_reaction(payload.emoji, member)  # Removes the incorrect reaction from the message.
            return
        return

    # @commands.Cog.listener()
    # async def on_ready(self):  # This event listens for when the bot is ready.
    #     print(f"{self.bot.user.name} is online. Awaiting commands.")
    #     await self.bot.change_presence(status=discord.Status.online,
    #                                    activity=discord.Game(f"D&D w/ W&W | {PREFIX}help"))
    #     # Changes the bot's presence.
    #     return
    # Likely not needed for WildMagic.

    @commands.command(name="rr_help", aliases=["rrhelp", "rrh"])  # Defines a command. The name is the name of the
    # command that will cause functions to execute, and the aliases are shortened versions of this name that will also
    # cause the functions to execute.
    @guild_only()  # Checks to ensure that the command is being run in a guild.
    async def help_(self, ctx):  # Defines the help command. Preferred over the built-in help for formatting.
        # This will probably be auto-generated some day.
        # But not today.
        owner = await self.bot.fetch_user(user_id=self.bot.owner_id)
        embed = discord.Embed(title=f"{self.bot.user.name}: Help", description=f"""To view extensive help on a module \
and all its subcommands, invoke the command without any arguments, eg. `{PREFIX}react_role`.""",
                              color=discord.Color(0x3b9da5))
        # Defines an embed as an Embed object and declares its title, description, and color.
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)  # Sets the author of the embed as the guild
        # for cosmetic purposes.
        embed.add_field(name="Modules:", value=f"""**React Role** (Aliases: `rr`)
**`{PREFIX}react_role`**
The module responsible for the management of React Role, including features to manage its groups and reactions, \
as well as managing the posts the module listens to to add roles from.""",
                        inline=False)  # Adds a field with the name
        # of the name argument and a value of the value argument,.
        embed.set_footer(text=f"Made by Dusk Argentum#6530 | {PREFIX}help", icon_url=owner.avatar_url)
        # Sets the footer as some helpful information, ie. the developer's name, the help command, and the version of
        # the bot.
        await ctx.send(embed=embed)  # Sends the embed to the channel.
        await ctx.message.add_reaction("👍")  # All commands, if they successfully execute, have this at the end; it's a
        # neat, personal touch that informs a member that their command has successfully invoked as intended.
        return

    @commands.group(name="react_role", aliases=["rr"], case_insensitive=True)  # Defines a group, which is a command
    # that will have subcommands. The case_insensitive argument must be applied on each individual group, even if
    # declared in the bot, due to Discord being weird.
    @guild_only()
    @has_any_role(353903320051744769, 692769399911874580, 801597333699035156)  # Checks if the command invoker has one
    # of the aforementioned roles in their roles. The first is the developer's role on their testing server, the second
    # is the Administrators role on W&W, and the third is the Hydrohomie role on W&W.
    # The aforementioned Hydrohomie is included for ease of debugging.
    async def react_role(self, ctx):  # Defines the base react_role command.
        if ctx.invoked_subcommand is None:  # Functions in this block execute if no subcommand is invoked.
            owner = await self.bot.fetch_user(user_id=self.bot.owner_id)
            embed = discord.Embed(title="React Role (Aliases: `rr`)", description=f"""React Role is a feature used to
assist in the automatic application and removal of roles upon adding Reactions to specific messages.""",
                                  color=discord.Color(0x3b9da5))
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
            embed.add_field(name="Group Management:",
                            value=f"""**`{PREFIX}react_role add_group [name]`** (Aliases: `ag`)
Adds the specified group to the list of groups.
**`{PREFIX}react_role delete_group [name]`** (Aliases: `dg`)
Deletes the specified group from the list of groups.
**`{PREFIX}react_role list_groups`** (Aliases: `groups`, `gs`, `lg`)
Shows a list of existing groups.
**`{PREFIX}react_role view_group [name]`** (Aliases: `group`, `g`, `vg`)
Shows the information for the specified group, including a link to its post and the reactions within.""",
                            inline=False)  # This help got a little long so I shoved it in here instead of the main
            # help command.
            embed.add_field(name="Post Management:", value=f"""**`{PREFIX}react_role post [group] [channel]`** \
(Aliases: `p`)
Posts the specified group to the specified channel. Defaults to the current channel if no channel is specified.
**`{PREFIX}react_role update [group]`** (Aliases: `u`, `up`)
Updates the post for the specified group, adding and/or removing the new/deleted emoji and the respective roles they \
grant to/from the text field of the post, as well as adding/removing the new/deleted reactions to/from the post.""",
                            inline=False)
            embed.add_field(name="Reaction Management:", value=f"""
**`{PREFIX}react_role add_reaction [group] [emoji] [role]`** (Aliases: `ar`)
Adds the specified reaction to the specified group.
**`{PREFIX}react_role delete_reaction [group] [role]`** (Aliases: `dr`)
Deletes the specified role and its associated reaction from the specified group.""", inline=False)
            embed.add_field(name="ADVANCED:", value=f"""**`{PREFIX}react_role json example`** (Aliases: `j ex`)
Exports an example JSON.
**`{PREFIX}react_role json export`** (Aliases: `j e`)
Exports the react_role JSON for editing purposes.
**`{PREFIX}react_role json import`** (Aliases: `j i`)
Imports the attached JSON and replaces the existing JSON with the attached JSON after passing some rudimentary checks.
Please be advised that commands in the ADVANCED section could result in lost data if used improperly.
**`{PREFIX}react_role json load_backup`** (Aliases: `j back`, `j backup`, `j bu`, `j b`)
Loads a backup JSON created based on the JSON replaced by `json import`.""",
                            inline=False)  # Seriously, don't use the JSON commands if you don't know what you're doing.
            # Even people who DO know what they're doing will sometimes make mistakes.
            embed.set_footer(text=f"Made by Dusk Argentum#6530 | {PREFIX}help", icon_url=owner.avatar_url)
            await ctx.send(embed=embed)
            await ctx.message.add_reaction("👍")
            return

    @react_role.command(name="add_group", aliases=["ag"])  # Defines a sub-command for react_role.
    async def add_group(self, ctx, group: str = None):
        if group is None:  # Functions in this block will execute if the group argument is empty.
            await ctx.send(f"""Please specify the name of the group you would like to create.
Example usage: `{PREFIX}react_role add_group "Example Group"`.""")  # Informs the member of example usage of this
            # command.
            await ctx.message.add_reaction("👎")
            return
        if group.isnumeric():  # Functions in this block will execute if the group is composed solely of numbers.
            # This is here because groups named entirely numbers breaks things. Use the word form of numbers if you
            # must.
            await ctx.send("Please include at least one non-numeric character in this group's name.")
            await ctx.message.add_reaction("👎")
            return
        elif "\\" in group:  # Functions in this block will execute if the group includes a \ anywhere in its name
            # due to Python duplicating escape characters, for some reason. Just don't use them.
            await ctx.send(f"Please do not include any backslashes (`\\`) in this group's name.")
            await ctx.message.add_reaction("👎")
            return
        with open("react_role.json", "r") as react_role:
            data = json.load(react_role)
        if group in str(data["react_role"]["groups"].keys()):  # Functions in this block execute if there is already
            # a group that shares the name as the one attempted to be created.
            await ctx.send(f"""A group with that name already exists. Please try a different one. To view the \
existing group, please use `{PREFIX}react_role view_group {group}`, or list the existing groups with \
`{PREFIX}react_role list_groups`.""")
            await ctx.message.add_reaction("👎")
            return
        new_entry = {
            f"{group}": {
                "channel": "0",
                "message": "0",
                "reactions": {}
            }
        }  # Defines an empty new group, as well as default values for the channel and message keys, and an empty key
        # where reactions will be stored.
        data["react_role"]["groups"].update(new_entry)  # Updates the groups key with the new group.
        with open("react_role.json", "w") as react_role:  # Reopens the react_role json to be written to.
            react_role.seek(0)  # Seeks to the top of the file. Important, otherwise things get misaligned.
            # A lot.
            json.dump(data, react_role, indent=2)  # Writes the new data to the react_role file.
            react_role.truncate()  # Removes extra space, if the new file is longer than the previous. Important,
            # otherwise things get misaligned.
            # A lot more.
        await ctx.send(f"""OK! I've added the group `{group}` to the list of groups. Please feel free to add reactions \
via `{PREFIX}react_role add_reaction "{group}" [emoji] [role]`. Once you're done setting up a group, use \
`{PREFIX}react_role post "{group}"` in the channel you want the group to be posted to.""")
        await ctx.message.add_reaction("👍")
        return

    @react_role.command(name="add_reaction", aliases=["ar"])
    async def add_reaction(self, ctx, group: str = None, emoji: str = None, role: Union[int, str] = None):  # Defines
        # the add_reaction command. The role argument is a Union, so that role names and role IDs are both accepted as
        # valid.
        # The emoji argument can TECHNICALLY be any string, but don't do that. Not only will the react role not have an
        # emoji to look for, but it'll also mess up view_group, and, like, everything else.
        # Naughty people who use non-emoji strings will get sent directly to gay baby jail. Do not pass the Ashflower
        # Guild do not collect 200 gp.
        # I welcome comprehensible solutions that rectify this problem.
        if group is None:
            await ctx.send(f"""Please specify which group to add the reaction to.
Example usage: `{PREFIX}react_role "Example Group" :smirk_cat: "Example Role"`""")
            await ctx.message.add_reaction("👎")
            return
        if group.isnumeric():
            await ctx.send(f"The group `{group}` was not found.")
            await ctx.message.add_reaction("👎")
            return
        elif "\\" in group:
            await ctx.send(f"The group `{group}` was not found.")
            await ctx.message.add_reaction("👎")
            return
        if emoji is None:  # Functions in this block execute if there is no emoji argument.
            # I could never figure out how to look for this specifically, so this also happens if there's only one
            # argument.
            await ctx.send(f"""Please specify which emoji to set the reaction to be.
Example usage: `{PREFIX}react_role "Example Group" :smirk_cat: "Example Role"`""")
            await ctx.message.add_reaction("👎")
            return
        if role is None:  # Functions in this block execute if there is no role argument.
            await ctx.send(f"""Please specify which role the reaction should give.
Example usage: `{PREFIX}react_role "Example Group" :smirk_cat: "Example Role"`""")
            await ctx.message.add_reaction("👎")
            return
        if isinstance(role, int):  # Functions in this block execute if the role argument is an int, which is determined
            # initially by whether or not it is entirely made ouf of numbers. This will be relevant later.
            role = discord.utils.get(ctx.guild.roles, id=role)  # Defines the role as a role in the server with the same
            # ID as the role argument.
            if role is None:  # Functions in this block execute if the newly-defines role is None, which happens if
                # there are no roles in the server with the same ID as the role argument.
                await ctx.send(f"The role `{role}` was not found.")
                await ctx.message.add_reaction("👎")
                return
        elif isinstance(role, str):  # Functions in this block execute if the role argument is a str.
            if role.isnumeric():  # Functions in this block execute if the role argument is a string, but somehow made
                # up entirely of numbers.
                # Which shouldn't happen. But it did one time. So here's the handler for it.
                await ctx.send("""Please assign this reaction to a role with at least one non-numeric character in \
its name.""")
                await ctx.message.add_reaction("👎")
                return
            role_count = 0
            role_name = ""
            for role_name in ctx.guild.roles:  # Functions in this block execute for every item in the list of the
                # server's roles.
                if role_name.name.lower() == role.lower():  # Functions in this block execute if the role's name in
                    # all-lowercase is the same as the role in the JSON's name in all-lowercase.
                    # Confusing variable names aside, this is to ensure that the role argument disregards case.
                    role = discord.utils.get(ctx.guild.roles, name=role_name.name)
                    break
                else:  # Functions in this block execute if the role's name does not meet the condition above.
                    if role_count == len(ctx.guild.roles) - 1:  # Functions in this block execute if the role_count
                        # counter is equal to one less than the amount of roles in the guild.
                        # The reason it checks for one less is due to the fact that the role_count variable starts at
                        # zero, but the list of roles starts at one.
                        await ctx.send(f"The role `{role}` was not found.")
                        await ctx.message.add_reaction("👎")
                        return
                    role_count += 1
                    continue
        with open("react_role.json", "r+") as react_role:
            data = json.load(react_role)
        group_count = 0
        group_name = ""
        for group_name in data["react_role"]["groups"]:
            if group.lower() == group_name.lower():  # Similarly to the role_name situation above, functions in this
                # block execute if the group's name in all-lowercase is the same as the group in the JSON's name is
                # all-lowercase.
                group = group_name  # Defines the group as the group.
                break
            else:
                if group_count == len(data["react_role"]["groups"]) or group.lower() not in str(data["react_role"]
                                                                                                ["groups"]).lower():
                    await ctx.send(f"The group `{group}` was not found.")
                    await ctx.message.add_reaction("👎")
                    return
                group_count += 1
                continue
        if emoji in str(data["react_role"]["groups"][group]["reactions"]):  # Functions in this block execute if the
            # emoji in the emoji argument is already in use.
            await ctx.send(f"The emoji `{emoji}` is in use in this group.")
            await ctx.message.add_reaction("👎")
            return
        if role.name in str(data["react_role"]["groups"][group]["reactions"]):  # Functions in this block execute if the
            # role in the role argument is already in use.
            await ctx.send(f"""The role `{role}` is in use in this group.""")
            await ctx.message.add_reaction("👎")
            return
        new_entry = {
            f"""{str(int(len(data["react_role"]["groups"][group]["reactions"])) + 1)}""": {
                "emoji": f"{str(emoji)}",
                "role": f"{int(role.id)}"
            }
        }  # Defines a new entry with the name of the length of the reactions key plus one, as well as the emoji that
        # the on_raw_reactions_add listener will listen for, and the role for that emoji to grant.
        data["react_role"]["groups"][group]["reactions"].update(new_entry)
        with open("react_role.json", "w") as react_role:
            react_role.seek(0)
            json.dump(data, react_role, indent=2)
            react_role.truncate()
        await ctx.send(f"""OK! The emoji `{emoji}` has been set to grant the role `{role}`.
{f'When this group has finished being set up, please run `{PREFIX}react_role post "{group}" [channel]` for ' +
'reactions to successfully add roles.' if data["react_role"]["groups"][group]["message"] == "0" else
f'Please run {PREFIX}react_role update "{group}" for changes to take effect on the appropriate message.'}""")  # This is
        # the longest inline I have ever written. For some reason. I wasn't even sure it was going to work until I
        # tested it.
        await ctx.message.add_reaction("👍")
        return

    @react_role.command(name="delete_group", aliases=["dg"])
    async def delete_group(self, ctx, group: str = None):
        if group is None:
            await ctx.send(f"""Please specify which group to delete.
Example usage: `{PREFIX}react_role delete_group "Example Group"`""")
            await ctx.message.add_reaction("👎")
            return
        if group.isnumeric():  # Functions in this group will execute if the group argument is composed entirely of
            # numbers.
            await ctx.send(f"The group `{group}` was not found.")  # Since groups composed entirely of numbers cannot be
            # created via add_group, this was added to prevent the further executing if someone attempts to delete a
            # group made entirely of numbers. This could only happen if someone imports a JSON with a group made
            # entirely of numbers, and, at that point, they can just import a new JSON without that group.
            await ctx.message.add_reaction("👎")
            return
        elif "\\" in group:  # Functions in this group will execute if the group argument includes a \.
            await ctx.send(f"The group `{group}` was not found.")  # See above.
            await ctx.message.add_reaction("👎")
            return
        with open("react_role.json", "r") as react_role:
            data = json.load(react_role)
        group_count = 0
        group_name = ""
        for group_name in data["react_role"]["groups"]:
            if group.lower() == group_name.lower():
                group = group_name
                break
            else:
                if group_count == len(data["react_role"]["groups"]) or group.lower() not in str(data["react_role"]
                                                                                                ["groups"]).lower():
                    await ctx.send(f"""The group `{group}` was not found.""")
                    await ctx.message.add_reaction("👎")
                    return
                group_count += 1
                continue
        delete = await ctx.send(f"""Are you sure you want to delete the group `{group}`? Once this action is \
performed, it **cannot** be undone.""")  # Groups are big and important, so there's a deletion prompt.
        await asyncio.sleep(2)  # This gives the member a chance to read the entire deletion prompt message before
        # making their decision. You know, just in case.
        await delete.add_reaction("👍")
        await delete.add_reaction("👎")

        def check(reaction, user):  # Defines a check which listens to the aforementioned message for either a thumbs-up
            # or thumbs-down from the member who sent the message.
            return user == ctx.message.author and str(reaction.emoji) in ["👍", "👎"]

        try:  # Attempts to execute the below code.
            reaction, user = await self.bot.wait_for("reaction_add", timeout=60,
                                                     check=check)  # Throws a TimeoutError exception
            # if the timeout argument is exceeded while waiting for a reaction.
        except TimeoutError:  # Functions in this block execute if the above try statement throws a TimeoutError
            # exception.
            await ctx.send("Deletion confirmation timed out. Deletion automatically aborted.")
            await ctx.message.add_reaction("👎")
            return
        if str(reaction.emoji) == "👍":  # Functions in this block execute if the reaction caught was a thumbs-up.
            await ctx.send(f"Deletion confirmed.")
        elif str(reaction.emoji) == "👎":  # Functions in this block execute if the reaction caught was a thumbs-down.
            await ctx.send("Deletion aborted.")
            await ctx.message.add_reaction("👎")
            return
        channel = 0  # Defines some empty variables for later.
        message = 0
        empty_channel = 0
        empty_message = 0
        try:
            channel = await self.bot.fetch_channel(channel_id=int(data["react_role"]["groups"][group]["channel"]))
            # Attempts to fetch the channel.
        except NotFound:
            empty_channel = 1  # If the channel is not found, it sets the empty_channel variable to one.
        try:
            message = await channel.fetch_message(id=int(data["react_role"]["groups"][group]["message"]))  # Attempts to
            # fetch the message.
        except (AttributeError, NotFound):  # Functions in this block execute if the channel is not found
            # (AttributeError) or if the message is not found.
            empty_message = 1
        if empty_channel == 0 and empty_message == 0:  # Deletes the message if both the message and channel are found.
            await message.delete()
        del data["react_role"]["groups"][group]  # Deletes the group from the groups key.
        with open("react_role.json", "w") as react_role:
            react_role.seek(0)
            json.dump(data, react_role, indent=2)  # Writes the deletion to the file.
            react_role.truncate()
        await ctx.send(f"""The group `{group}` was deleted. {
f"The message for `{group}` was also deleted." if empty_channel == 0 and empty_message == 0 else ""}""")
        await ctx.message.add_reaction("👍")
        return

    @react_role.command(name="delete_reaction", aliases=["dr"])  # This functions similarly to delete_group and so will
    # have minimal comments.
    async def delete_reaction(self, ctx, group: str = None, role: Union[int, str] = None):
        if group is None:
            await ctx.send(f"""Please specify which group to delete a reaction from.
Example usage: `{PREFIX}react_role delete_reaction "Example Group" "Example Role"`""")
            await ctx.message.add_reaction("👎")
            return
        if group.isnumeric():
            await ctx.send(f"The group `{group}` was not found.")
            await ctx.message.add_reaction("👎")
            return
        elif "\\" in group:
            await ctx.send(f"The group `{group}` was not found.")
            await ctx.message.add_reaction("👎")
            return
        if role is None:
            await ctx.send(f"""Please specify which role's reaction to delete.
Example usage: `{PREFIX}react_role delete_reaction "Example Group" "Example Role"`""")
            await ctx.message.add_reaction("👎")
            return
        if role.isnumeric():
            await ctx.send(f"The role `{role}` was not found.")
            await ctx.message.add_reaction("👎")
            return
        with open("react_role.json", "r") as react_role:
            data = json.load(react_role)
        group_count = 0
        group_name = ""
        for group_name in data["react_role"]["groups"]:
            if group.lower() == group_name.lower():
                group = group_name
                break
            else:
                if group_count == len(data["react_role"]["groups"]) or group.lower() not in str(data["react_role"]
                                                                                                ["groups"]).lower():
                    await ctx.send(f"The group `{group}` was not found.")
                    await ctx.message.add_reaction("👎")
                    return
                group_count += 1
                continue
        if len(data["react_role"]["groups"][group]["reactions"]) == 0:  # Functions in this block will execute if
            # the lengths of the group's reactions key is 0, which is to say, if a group has no reactions.
            await ctx.send(f"The group `{group}` has no reactions.")
            await ctx.message.add_reaction("👎")
            return
        if isinstance(role, int):
            role = discord.utils.get(ctx.guild.roles, id=role)
            if role is None:
                await ctx.send(f"The role `{role}` was not found.")
                await ctx.message.add_reaction("👎")
                return
        elif isinstance(role, str):
            role_count = 0
            role_name = ""
            for role_name in ctx.guild.roles:
                if role_name.name.lower() == role.lower():
                    role = discord.utils.get(ctx.guild.roles, name=role_name.name)
                    break
                else:
                    if role_count == len(ctx.guild.roles) - 1:
                        await ctx.send(f"The role `{role}` was not found.")
                        await ctx.message.add_reaction("👎")
                        return
                    role_count += 1
                    continue
        reaction_count = 1
        reaction_name = ""
        for reaction_name in data["react_role"]["groups"][group]["reactions"]:
            if str(role.id) == str(data["react_role"]["groups"][group]["reactions"][str(reaction_count)]["role"]):
                break
            else:
                reaction_count += 1
                continue
        delete = await ctx.send(f"""Are you sure you want to delete the role `{role}` and its associated emoji, \
`{data["react_role"]["groups"][group]["reactions"][str(reaction_count)]["emoji"]}`, from `{group}`? \
Once performed, this action **cannot** be undone.""")
        await asyncio.sleep(2)
        await delete.add_reaction("👍")
        await delete.add_reaction("👎")

        def check(reaction, user):
            return user == ctx.message.author and str(reaction.emoji) in ["👍", "👎"]

        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=60, check=check)
        except TimeoutError:
            await ctx.send("Deletion confirmation timed out. Deletion automatically aborted.")
            await ctx.message.add_reaction("👎")
            return
        if str(reaction.emoji) == "👍":
            await ctx.send(f"Deletion confirmed.")
        elif str(reaction.emoji) == "👎":
            await ctx.send("Deletion aborted.")
            await ctx.message.add_reaction("👎")
            return
        del data["react_role"]["groups"][group]["reactions"][str(reaction_count)]
        if len(data["react_role"]["groups"][group]["reactions"]) == 0:
            with open("react_role.json", "w") as react_role:
                react_role.seek(0)
                json.dump(data, react_role, indent=2)
                react_role.truncate()
            channel = 0
            message = 0
            empty_channel = 0
            empty_message = 0
            try:
                channel = await self.bot.fetch_channel(channel_id=int(data["react_role"]["groups"][group]["channel"]))
                pass
            except NotFound:
                empty_channel = 1
            try:
                message = await channel.fetch_message(id=int(data["react_role"]["groups"][group]["message"]))
            except (AttributeError, NotFound):
                empty_message = 1
            await ctx.send(f"""The reaction for role `{role}` was deleted. \
{f'For this change to be reflected in the message assigned to the role `{role}`, please run `{PREFIX}react_role ' +
f'"{group}" update`.' if empty_channel == 0 or empty_message == 0 else ""}""")
            await ctx.message.add_reaction("👍")
            return
        higher_reactions_count = 1
        print(len(data["react_role"]["groups"][group]["reactions"]))
        for higher_reactions_list in list(data["react_role"]["groups"][group]["reactions"]):
            if int(len(data["react_role"]["groups"][group]["reactions"])) == 0:
                del data["react_role"]["groups"][group]["reactions"][0]
                with open("react_role.json", "w") as react_role:
                    react_role.seek(0)
                    json.dump(data, react_role, indent=2)
                    react_role.truncate()
                break
            elif int(higher_reactions_list) > reaction_count and int(higher_reactions_list) != reaction_count:
                new_entry = {
                    f"{str(higher_reactions_count)}": {
                        "emoji": f"""{data["react_role"]
                        ["groups"][group]["reactions"][str(higher_reactions_list)]["emoji"]}""",
                        "role": f"""{data["react_role"]
                        ["groups"][group]["reactions"][str(higher_reactions_list)]["role"]}"""
                    }
                }
                del data["react_role"]["groups"][group]["reactions"][str(higher_reactions_list)]
                data["react_role"]["groups"][group]["reactions"].update(new_entry)
                with open("react_role.json", "w") as react_role:
                    react_role.seek(0)
                    json.dump(data, react_role, indent=2)
                    react_role.truncate()
                higher_reactions_count += 1
                continue
            else:
                higher_reactions_count += 1
                continue
        channel = 0
        message = 0
        empty_channel = 0
        empty_message = 0
        try:
            channel = await self.bot.fetch_channel(channel_id=int(data["react_role"]["groups"][group]["channel"]))
            pass
        except NotFound:
            empty_channel = 1
        try:
            message = await channel.fetch_message(id=int(data["react_role"]["groups"][group]["message"]))
        except (AttributeError, NotFound):
            empty_message = 1
        await ctx.send(f"""The reaction for role `{role}` was deleted. \
{f"For this change to be reflected in the role `{role}`'s message, please run `{PREFIX}react_role {group} update`."
if empty_channel == 0 or empty_message == 0 else ""}""")
        await ctx.message.add_reaction("👍")
        return

    @react_role.group(name="json", aliases=["j"])  # This defines the JSON subcommand's subcommand group.
    async def json_(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(f"""""")
            owner = await self.bot.fetch_user(user_id=self.bot.owner_id)
            embed = discord.Embed(title="JSON (Aliases: `j`)", description=f"""JSON is used to import and export JSON \
files.
⚠ WARNING ⚠
It is advised that this command and its subcommands be used by advanced users only. Usage of this command and its \
subcommands carries the risk of losing all established groups and reactions if used improperly. Proceed at your \
own risk!""", color=discord.Color(0x3b9da5))
            embed.add_field(name="JSON:", value=f"""**`{PREFIX}react_role json export`** (Aliases: `e`)
Exports the existing JSON.
**`{PREFIX}react_role json example`** (Aliases: `ex`)
Exports an example JSON.
**`{PREFIX}react_role json import`** (Aliases: `i`)
Imports a JSON from an attached file, and performs a very rudimentary check to ensure that it is valid. Please note \
that this checking is fallible.
**`{PREFIX}react_role json load_backup`** (Aliases: `b`, `backup`, `bu`, `back`)
Renames the backup JSON created when importing a JSON so that it replaces the current JSON.""",
                            inline=False)
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return

    @json_.command(name="example", aliases=["ex"])
    async def example(self, ctx):  # This sends the example JSON in its own message using the file argument.
        await ctx.send(file=discord.File("react_role_EXAMPLE.json"))
        await ctx.message.add_reaction("👍")
        return

    @json_.command(name="export", aliases=["e"])
    async def export(self, ctx):  # This sends the current JSON.
        await ctx.send(file=discord.File("react_role.json"))
        await ctx.message.add_reaction("👍")
        return

    @json_.command(name="import", aliases=["i"])
    async def import_(self, ctx):  # This imports an attached JSON.
        if ctx.message.attachments == list(""):  # Functions in this block execute if there are no attachments.
            await ctx.send(f"""Please attach an attachment to your message.""")
            await ctx.message.add_reaction("👎")
            return
        if str(ctx.message.attachments[0].content_type) != "application/json; charset=utf-8":  # Functions in this block
            # execute if the attachment is not a JSON.
            await ctx.send(f"""Please make sure that your attachment is a `.json` with the charset `utf-8`.""")
            await ctx.message.add_reaction("👎")
            return
        await ctx.message.attachments[0].save("react_role_IMPORT.json", seek_begin=True)  # Saves the imported
        # attachment for testing purposes.
        with open("react_role_IMPORT.json", "r") as react_role:
            data = json.load(react_role)
        try:
            data_TEST = data["react_role"]["groups"]
        except KeyError:  # Functions in this block execute if the above test returns a KeyError exception.
            # I welcome better tests.
            await ctx.send(f"""The attached file is not in the correct format and has raised a `KeyError` exception. \
Please ensure that the attached file is valid.
Example JSON:""", file=discord.File("react_role_EXAMPLE.json"))
            os.remove("react_role_IMPORT.json")  # This removes the imported file from the filesystem.
            return
        os.remove("react_role_IMPORT.json")
        channel = await self.bot.fetch_channel(channel_id=890400075958849637)  # Defines the channel variable as a
        # specific backup channel on my development server; no JSONs will ever be lost this way, and no completely
        # irreparable mistakes can be made.
        # This should be changed to a channel WildMagic can access.
        await channel.send(file=discord.File("react_role.json"))  # Sends the file to the backup channel.
        os.replace("react_role.json",
                   "react_role_BACKUP.json")  # This replaces the react_role_BACKUP JSON with the current
        # react_role JSON, backing up the file, regardless of if there is an existing backup.
        await ctx.message.attachments[0].save("react_role.json", seek_begin=True)  # Saves the attachment as the true
        # react_role JSON.
        await ctx.send(f"""JSON import successful. 
To view the updated list of groups, use `{PREFIX}react_role groups`. To view a specific group use `{PREFIX}react_role \
group [group]`. To update the message for an updated group, use `{PREFIX}react_role update [group]`. To post a group,
use `{PREFIX}react_role post [group].`
To view the exported JSON of this JSON, use `{PREFIX}react_role json export`.
To load the backup JSON, a copy of the JSON before it was overwritten with this import, use `{PREFIX}react_role \
json load_backup`.""")
        await ctx.message.add_reaction("👍")
        return

    @json_.command(name="load_backup", aliases=["b", "backup", "bu", "back"])
    async def load_backup(self, ctx):
        try:  # Functions in this block attempt to execute.
            os.replace("react_role_BACKUP.json", "react_role.json")  # Renames the BACKUP JSON to the normal JSON,
            # overwriting the existing one.
        except OSError:  # If the above code raises an OSError exception, functions in this block execute.
            # This should only ever happen if loading two backups in a row without importing anything in-between;
            # hopefully a rare case, but still possible, which is why there is handling.
            await ctx.send(f"""Failed to load backup JSON: The file does not exist.
Backup files are automatically created when importing a JSON.""")
            await ctx.message.add_reaction("👎")
            return
        await ctx.send("Backup JSON loaded. Exporting:", file=discord.File("react_role.json"))  # Automatically exports
        # the JSON.
        await ctx.message.add_reaction("👍")
        return

    @react_role.command(name="list_groups", aliases=["groups", "gs", "lg"])
    async def list_groups(self, ctx):
        with open("react_role.json", "r") as react_role:
            data = json.load(react_role)
        groups = data["react_role"]["groups"].keys()  # Gets every key in the groups key.
        embed = discord.Embed(title="React Role Groups", description="\n".join([str(element) for element in groups]),
                              color=discord.Color(0x3b9da5))  # Defines an embed with a description containing all of
        # the keys defined above separated by a newline.
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
        embed.set_footer(text=f"""To view the reactions within a group, use {PREFIX}react_role view_group "[group]".""")
        await ctx.send(embed=embed)
        await ctx.message.add_reaction("👍")
        return

    @react_role.command(name="post", aliases=["p"])
    async def post(self, ctx, group: str = None, channel: Union[int, str] = None):
        if group is None:
            await ctx.send(f"""Please specify which group to post.
Example usage: `{PREFIX}react_role post "Example Group"`""")
            await ctx.message.add_reaction("👎")
            return
        if group.isnumeric():
            await ctx.send(f"The group `{group}` was not found.")
            await ctx.message.add_reaction("👎")
            return
        elif "\\" in group:
            await ctx.send(f"The group `{group}` was not found.")
            await ctx.message.add_reaction("👎")
            return
        if channel is None:
            channel = int(ctx.channel.id)
        if isinstance(channel, int):
            channel = discord.utils.get(ctx.guild.channels, id=channel)
            if channel is None:
                await ctx.send(f"The channel `{channel}` was not found.")
                await ctx.message.add_reaction("👎")
                return
        elif isinstance(channel, str):
            channel_count = 0
            channel_name = ""
            for channel_name in ctx.guild.channels:
                if channel_name.lower() == channel.lower():
                    channel = discord.utils.get(ctx.guild.channels, name=channel_name.name)
                    break
                else:
                    if channel_count == len(ctx.guild.channels):
                        await ctx.send(f"The channel `{channel}` was not found.")
                        await ctx.message.add_reaction("👎")
                        return
                    channel_count += 1
                    continue
        with open("react_role.json", "r") as react_role:
            data = json.load(react_role)
        group_count = 0
        group_name = ""
        for group_name in data["react_role"]["groups"]:
            if group.lower() == group_name.lower():
                group = group_name
                break
            else:
                if group_count == len(data["react_role"]["groups"]) or group.lower() not in str(data["react_role"]
                                                                                                ["groups"]).lower():
                    await ctx.send(f"The group `{group}` was not found.")
                    await ctx.message.add_reaction("👎")
                    return
                group_count += 1
                continue
        if str(data["react_role"]["groups"][group]["message"]) != "0":  # Functions in this block execute if the channel
            # value is not zero. It would likely only be zero if there is a valid post or if an improper value was
            # entered during a JSON import.
            message = str(data["react_role"]["groups"][group]["message"])
            channel = discord.utils.get(ctx.guild.channels, id=int(data["react_role"]["groups"][group]
                                                                   ["channel"]))
            if channel is None:
                await ctx.send(f"""The channel for this group was not found. The channel ID for the group `{group}` on \
record is `{str(data["react_role"]["groups"][group]["channel"])}`.
To remedy this, please post the group again using `{PREFIX}react_role post {group} [channel]`. If this group has not \
been posted yet, please do so!""")
                await ctx.message.add_reaction("👎")
                return
            try:
                message = await channel.fetch_message(id=int(message))
            except (AttributeError, NotFound):
                await ctx.send(f"""The message for this group was not found. The message ID for the group `{group}` on \
record is `{str(data["react_role"]["groups"][group]["message"])}`.
To remedy this, please post the group again using `{PREFIX}react_role post {group} [channel]`. If this group has not \
been posted yet, please do so!""")
                await ctx.message.add_reaction("👎")
                return
            if ctx.channel.id != int(data["react_role"]["groups"][group]["channel"]):
                channel = ctx.channel
            overwrite = await ctx.send(f"""The group `{group}` already has a post assigned to it \
(<{message.jump_url}>).
Overwrite?""")
            await overwrite.add_reaction("👍")
            await overwrite.add_reaction("👎")

            def check(reaction, user):
                return user == ctx.message.author and str(reaction.emoji) in ["👍", "👎"]

            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=60, check=check)
            except TimeoutError:
                await ctx.send("Overwrite confirmation timed out. Overwrite automatically aborted.")
                await ctx.message.add_reaction("👎")
                return
            if str(reaction.emoji) == "👍":
                await ctx.send(f"""Overwrite confirmed. You can avoid this prompt in the future by using \
`{PREFIX}react_role update {group}` instead.""")
            elif str(reaction.emoji) == "👎":
                await ctx.send("Overwrite aborted.")
                await ctx.message.add_reaction("👎")
                return
        if len(data["react_role"]["groups"][group]["reactions"]) == 0:
            await ctx.send(f"""There were no reactions found for group `{group}`. \
To add some reactions, please use `{PREFIX}react_role add_reaction {group}`.
Example usage: `{PREFIX}react_role add_reaction {group} :smirk_cat: "Example Role"`.""")
            await ctx.message.add_reaction("👎")
            return
        embed = discord.Embed(title="React for a role!", color=discord.Color(0x3b9da5))
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
        reaction_list_emoji = []  # Defines an empty list.
        reaction_list_role = []
        value = []
        current_reaction = 1  # Defines a one-count for reactions.
        for reaction in data["react_role"]["groups"][group]["reactions"]:  # Functions in this block execute for every
            # entry in the reactions key.
            reaction_list_emoji.append(data["react_role"]["groups"][group]["reactions"][str(current_reaction)]["emoji"])
            # Appends the information from the specified key to the end of the reaction_list_emoji list.
            role = discord.utils.get(ctx.guild.roles, id=int(data["react_role"]["groups"][group]["reactions"]
                                                             [str(current_reaction)]["role"]))
            reaction_list_role.append(str(role.name))  # Appends the name of the role to the end of the
            # reaction_list_role list.
            value.append(f"""{reaction_list_emoji[int(current_reaction) - 1]}` | `\
{reaction_list_role[int(current_reaction - 1)]}\n""")  # Appends the above information to the value list and adds
            # some formatting. The values have one subtracted from them due to the count being a one-count when slices
            # start at a zero-count.
            current_reaction += 1
        embed.add_field(name="Emoji` | `Role", value=" ".join([str(element) for element in value]))
        embed.set_footer(text="""If you cannot see any reactions below, go to Settings > Text & Images > Show emoji \
reactions on messages.""")  # This is a rarity, tbh. Everyone's got reactions on these days. But, who knows, maybe
        # someone doesn't...
        try:
            post = await channel.send(embed=embed)
        except Forbidden:
            await ctx.send(f"Post failed. Please ensure the bot has permission to post in <#{channel.id}>.")
            await ctx.message.add_reaction("👎")
            return
        reaction_list = []
        current_reaction = 1
        for reaction in data["react_role"]["groups"][group]["reactions"]:
            reaction_list.append(data["react_role"]["groups"][group]["reactions"][str(current_reaction)]
                                 ["emoji"])
            await post.add_reaction(list(reaction_list)[int(current_reaction - 1)])
            current_reaction += 1
        new_entry = {
            "channel": f"{channel.id}",
            "message": f"{post.id}"
        }
        data["react_role"]["groups"][group].update(new_entry)  # Updates the channel and message values with the channel
        # and message IDs of the post.
        with open("react_role.json", "w") as react_role:
            react_role.seek(0)
            json.dump(data, react_role, indent=2)
            react_role.truncate()
        await ctx.message.add_reaction("👍")
        return

    @react_role.command(name="update", aliases=["u", "up"])
    async def update(self, ctx, group: str = None):
        if group is None:
            await ctx.send(f"""Please specify which group to update.
Example usage: `{PREFIX}react_role update "Example Group"`""")
            return
        if group.isnumeric():
            await ctx.send(f"The group `{group}` was not found.")
            await ctx.message.add_reaction("👎")
            return
        elif "\\" in group:
            await ctx.send(f"The group `{group}` was not found.")
            await ctx.message.add_reaction("👎")
            return
        with open("react_role.json", "r") as react_role:
            data = json.load(react_role)
        group_count = 0
        group_name = ""
        for group_name in data["react_role"]["groups"]:
            if group.lower() == group_name.lower():
                group = group_name
                break
            else:
                if group_count == len(data["react_role"]["groups"]) or group.lower() not in str(data["react_role"]
                                                                                                ["groups"]).lower():
                    await ctx.send(f"The group `{group}` was not found.")
                    await ctx.message.add_reaction("👎")
                    return
                group_count += 1
                continue
        try:
            channel = await self.bot.fetch_channel(channel_id=int(data["react_role"]["groups"][group]["channel"]))
        except NotFound:
            await ctx.send(f"""The channel for this group was not found. The channel ID for the group `{group}` on \
record is `{str(data["react_role"]["groups"][group]["channel"])}`.
To remedy this, please post the group again using `{PREFIX}react_role post {group} [channel]`. If this group has not \
been posted yet, please do so!""")
            await ctx.message.add_reaction("👎")
            return
        try:
            message = await channel.fetch_message(id=int(data["react_role"]["groups"][group]["message"]))
        except (AttributeError, NotFound):
            await ctx.send(f"""The message for this group was not found. The message ID for the group `{group}` on \
record is `{str(data["react_role"]["groups"][group]["message"])}`.
To remedy this, please post the group again using `{PREFIX}react_role post {group} [channel]`. If this group has not \
been posted yet, please do so!""")
            await ctx.message.add_reaction("👎")
            return
        embed = discord.Embed(title="React for a role!", color=discord.Color(0x3b9da5))
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
        reaction_list_emoji = []
        reaction_list_role = []
        value = []
        current_reaction = 1
        for reaction in data["react_role"]["groups"][group]["reactions"]:
            reaction_list_emoji.append(data["react_role"]["groups"][group]["reactions"][str(current_reaction)]["emoji"])
            role = discord.utils.get(ctx.guild.roles, id=int(data["react_role"]["groups"][group]["reactions"]
                                                             [str(current_reaction)]["role"]))
            reaction_list_role.append(str(role.name))
            value.append(f"""{reaction_list_emoji[int(current_reaction) - 1]}` | `\
{reaction_list_role[int(current_reaction - 1)]}\n""")
            current_reaction += 1
        embed.add_field(name="Emoji` | `Role", value=" ".join([str(element) for element in value]))
        embed.set_footer(text="""If you cannot see any reactions below, go to Settings > Text & Images > Show emoji \
reactions on messages.""")
        post = await message.edit(embed=embed)
        await message.clear_reactions()
        reaction_list = []
        current_reaction = 1
        for reaction in data["react_role"]["groups"][group]["reactions"]:
            reaction_list.append(data["react_role"]["groups"][group]["reactions"][str(current_reaction)]
                                 ["emoji"])
            await message.add_reaction(list(reaction_list)[int(current_reaction - 1)])
            current_reaction += 1
        await ctx.message.add_reaction("👍")
        return

    @react_role.command(name="view_group", aliases=["group", "g", "vg"])
    async def view_group(self, ctx, group: str = None):
        if group is None:
            await ctx.send(f"""Please specify which group to view.
You can view a list of groups with `{PREFIX}react_role list_groups`.""")
            return
        if group.isnumeric():
            await ctx.send(f"The group `{group}` was not found.")
            await ctx.message.add_reaction("👎")
            return
        elif "\\" in group:
            await ctx.send(f"The group `{group}` was not found.")
            await ctx.message.add_reaction("👎")
            return
        with open("react_role.json", "r") as react_role:
            data = json.load(react_role)
        group_count = 0
        group_name = ""
        for group_name in data["react_role"]["groups"]:
            if group.lower() == group_name.lower():
                group = group_name
                break
            else:
                if group_count == len(data["react_role"]["groups"]) or group.lower() not in str(data["react_role"]
                                                                                                ["groups"]).lower():
                    await ctx.send(f"The group `{group}` was not found.")
                    await ctx.message.add_reaction("👎")
                    return
                group_count += 1
                continue
        embed = discord.Embed(title=f"{group_name}", color=discord.Color(0x3b9da5))
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
        channel = 0
        message = 0
        empty_channel = 0
        empty_message = 0
        try:
            channel = await self.bot.fetch_channel(channel_id=int(data["react_role"]["groups"][group]["channel"]))
        except NotFound:
            if int(data["react_role"]["groups"][group]["channel"]) == 0:
                empty_channel = 1
                pass
            else:
                await ctx.send(f"""The channel for this group was not found. The channel ID for the group `{group}` on \
record is `{str(data["react_role"]["groups"][group]["channel"])}`.
To remedy this, please post the group again using `{PREFIX}react_role post {group} [channel]`. If this group has not \
been posted this group yet, please do so!""")
                await ctx.message.add_reaction("👎")
                return
        try:
            message = await channel.fetch_message(id=int(data["react_role"]["groups"][group]["message"]))
        except (AttributeError, NotFound):
            if int(data["react_role"]["groups"][group]["message"]) == 0:
                empty_message = 1
                pass
            else:
                await ctx.send(f"""The message for this group was not found. The message ID for the group `{group}` on \
record is `{str(data["react_role"]["groups"][group]["message"])}`.
To remedy this, please post the group again using `{PREFIX}react_role post {group} [channel]`. If this group has not \
been posted yet, please do so!""")
                await ctx.message.add_reaction("👎")
                return
        embed.add_field(name="Post:", value=f"""{f"{message.jump_url}" if empty_channel == 0 or empty_message == 0 else
f"This group doesn't seem to have been posted yet. Post it with `{PREFIX}react_role post {group} [channel]`."}""")
        reaction_list_emoji = []
        reaction_list_role = []
        value = []
        current_reaction = 1
        for reaction in data["react_role"]["groups"][group]["reactions"]:
            reaction_list_emoji.append(data["react_role"]["groups"][group_name]["reactions"][str(current_reaction)]
                                       ["emoji"])
            role = discord.utils.get(ctx.guild.roles, id=int(data["react_role"]["groups"][group]["reactions"]
                                                             [str(current_reaction)]["role"]))
            reaction_list_role.append(str(role.name))
            value.append(f"""{reaction_list_emoji[int(current_reaction) - 1]}` | `\
{reaction_list_role[int(current_reaction - 1)]}\n""")
            current_reaction += 1
        embed.add_field(name="Reactions:", value=f"""{" ".join([str(element) for element in value])
if reaction_list_emoji != [] else "This group has no reactions."}""", inline=False)
        await ctx.send(embed=embed)
        await ctx.message.add_reaction("👍")
        return


def setup(bot):
    bot.add_cog(ReactRole(bot))
