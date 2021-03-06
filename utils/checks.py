import disnake.utils
from disnake.ext import commands

from utils import config


# The permission system of the bot is based on a "just works" basis
# You have permissions and the bot has permissions. If you meet the permissions
# required to execute the command (and the bot does as well) then it goes through
# and you can execute the command.
# If these checks fail, then there are two fallbacks.
# A role with the name of Bot Mod and a role with the name of Bot Admin.
# Having these roles provides you access to certain commands without actually having
# the permissions required for them.
# Of course, the owner will always be able to execute commands.

# ===== predicates =====
def author_is_owner(ctx):
    return ctx.author.id == config.OWNER_ID


def _check_permissions(ctx, perms):
    if author_is_owner(ctx):
        return True

    ch = ctx.channel
    author = ctx.author
    try:
        resolved = ch.permissions_for(author)
    except AttributeError:
        resolved = None
    return all(getattr(resolved, name, None) == value for name, value in perms.items())


def _role_or_permissions(ctx, role_filter, **perms):
    if _check_permissions(ctx, perms):
        return True
    ch = ctx.message.channel
    author = ctx.message.author
    if isinstance(ch, disnake.abc.PrivateChannel):
        return False  # can't have roles in PMs

    try:
        role = disnake.utils.find(role_filter, author.roles)
    except:
        return False
    return role is not None


# ===== checks =====
def is_owner():
    def predicate(ctx):
        if author_is_owner(ctx):
            return True
        raise commands.CheckFailure("Only the bot owner may run this command.")

    return commands.check(predicate)


def role_or_permissions(role_name, **perms):
    def predicate(ctx):
        if _role_or_permissions(ctx, lambda r: r.name.lower() == role_name.lower(), **perms):
            return True
        raise commands.CheckFailure(
            f"You require a role named {role_name} or these permissions to run this command: {', '.join(perms)}"
        )

    return commands.check(predicate)


def admin_or_permissions(**perms):
    def predicate(ctx):
        admin_role = "Administrator"
        if _role_or_permissions(ctx, lambda r: r.name.lower() == admin_role.lower(), **perms):
            return True
        raise commands.CheckFailure(
            f"You require a role named Administrator or these permissions to run this command: {', '.join(perms)}"
        )

    return commands.check(predicate)
