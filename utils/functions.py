import re

from models import Character
from utils.constants import SUBCLASS_REPLACEMENTS


def split_arg(arg):
    return arg.lower().replace(", ", ",").split(",") if arg else []


def natural_join(things: list, between: str, wrap_item: tuple[str, str] | str = None):
    if wrap_item:
        wrap_item_l, wrap_item_r = (
            wrap_item if isinstance(wrap_item, tuple) else (wrap_item, wrap_item)
        )
        things = [f"{wrap_item_l}{thing}{wrap_item_r}" for thing in things]
    if len(things) < 3:
        return f" {between} ".join(things)
    first_part = ", ".join(things[:-1])
    return f"{first_part}, {between} {things[-1]}"


def pluralize(word, count):
    return word + "s" if count != 1 else word


async def get_character_data(bot, sheet_url: str):
    """Gets the character data from the DDB API, given a character sheet URL."""
    regex = r"^.*characters\/(\d+)\/?"
    match = re.search(regex, sheet_url)

    if not match:
        return None, "Unable to find a valid DDB character link."

    char_id = match.group(1)
    json_data, error = await bot.ddb_client.get_character(char_id)

    return json_data, error


def chunk_text(
    text, max_chunk_size=1024, chunk_on=("\n\n", "\n", ". ", ", ", " "), chunker_i=0
):
    """
    Recursively chunks *text* into a list of str, with each element no longer than *max_chunk_size*.
    Prefers splitting on the elements of *chunk_on*, in order.

    Stolen from Avrae's code, shamelessly
    """

    if len(text) <= max_chunk_size:  # the chunk is small enough
        return [text]
    if chunker_i >= len(chunk_on):  # we have no more preferred chunk_on characters
        # optimization: instead of merging a thousand characters, just use list slicing
        return [
            text[:max_chunk_size],
            *chunk_text(text[max_chunk_size:], max_chunk_size, chunk_on, chunker_i + 1),
        ]

    # split on the current character
    chunks = []
    split_char = chunk_on[chunker_i]
    for chunk in text.split(split_char):
        chunk = f"{chunk}{split_char}"
        if len(chunk) > max_chunk_size:  # this chunk needs to be split more, recurse
            chunks.extend(chunk_text(chunk, max_chunk_size, chunk_on, chunker_i + 1))
        elif (
            chunks and len(chunk) + len(chunks[-1]) <= max_chunk_size
        ):  # this chunk can be merged
            chunks[-1] += chunk
        else:
            chunks.append(chunk)

    # if the last chunk is just the split_char, yeet it
    if chunks[-1] == split_char:
        chunks.pop()

    # remove extra split_char from last chunk
    chunks[-1] = chunks[-1][: -len(split_char)]
    return chunks


def get_classes(data: dict) -> (dict[str, int], dict[str, str]):
    classes = {}
    subclasses = {}

    for _class in data["classes"]:
        cur_class = _class["definition"]["name"]
        cur_level = _class["level"]
        classes[cur_class] = cur_level
        if _class["subclassDefinition"]:
            sub_name = _class["subclassDefinition"]["name"]
            sub_name = re.sub(rf"""{"|".join(SUBCLASS_REPLACEMENTS)}""", "", sub_name)
            subclasses[cur_class] = sub_name

    return classes, subclasses


def get_tools(data: dict = None) -> (list[str], list[str]):
    """Get the tool proficiencies from the DDB character data"""
    profs = []
    expertise = []
    for _type in data.get("modifiers", {}):
        for modifier in data["modifiers"][_type]:
            # We only care about tool proficiencies
            if modifier["entityTypeId"] == 2103445194:
                if modifier["type"] == "proficiency":
                    profs.append(modifier["friendlySubtypeName"])
                if modifier["type"] == "expertise":
                    expertise.append(modifier["friendlySubtypeName"])

    return profs, expertise


def get_languages(data: dict = None) -> list[str]:
    """Get the languages from the DDB character data"""
    languages = []
    for _type in data.get("modifiers", {}):
        for modifier in data["modifiers"][_type]:
            # We only care about languages
            if modifier["entityTypeId"] == 906033267:
                languages.append(modifier["friendlySubtypeName"])

    return languages


def get_invocations(data: dict = None) -> list[str]:
    """Get the invocations from the DDB character data"""
    invocations = []
    for _type in data["options"]:
        if not data["options"][_type]:
            continue
        for option in data["options"][_type]:
            if (
                option["componentId"] == 10292364
                and option["componentTypeId"] == 12168134
            ):
                invocations.append(option["definition"]["name"])

    return invocations


def get_feats(data: dict = None) -> list[str]:
    """Get the feats from the DDB character data"""
    feats = []
    for _feat in data["feats"]:
        feat_name = _feat["definition"]["name"]
        feat_name = re.sub(r"^\d+:", "", feat_name).strip()

        # Remove some basic things
        if any(
            re.match(x, feat_name)
            for x in [
                "Ability Score Improvement",
                r".+ Ability Score Improvements",
                "Weapon Mastery",
                "Dark Bargain",
            ]
        ):
            continue
        feats.append(feat_name)

    return feats


def get_stats(data: dict = None) -> dict[str, int]:
    stat_names = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]
    stats = {}
    for stat in stat_names:
        stats[stat] = data["avrae"]["stats"][stat.lower()]["score"]

    return stats


def get_bags(data: dict = None) -> list:
    """Get the bags from the DDB character data"""
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
    return list(out.items())


def class_disp(character: Character) -> str:
    """Generate a string for the classes of a character, appending subclass if present, separated by a slash"""
    class_aggr = []
    for _class, level in character.classes.items():
        if _class in character.subclasses:
            _class = f"{_class} ({character.subclasses[_class]})"
        class_aggr.append(f"{_class} {level}")
    return " / ".join(class_aggr)


def stats_disp(character: Character) -> str:
    """Generate a string for the stats of a character, with the stats in a 3x2 grid"""
    stats_aggr = []
    for stat, value_ in character.stats.items():
        stats_aggr.append(f"**{stat}** {value_}")
    value = f"{' '.join(stats_aggr[:3])}\n"
    value += f"{' '.join(stats_aggr[3:])}"
    return value


def char_disp(character: Character, extended: bool = False) -> (str, str):
    """Generate a short display for a character, with some character data and a link to the sheet

    Parameters
    ----------
    character: The character data to display
    extended: Whether to include additional data like invocations and feats
    """
    title = character.name

    value = f"**Player:** <@{character.user.id}>\n"
    value += f"**Ancestry:** {character.race}\n"
    value += f"**Level:** {character.level}\n"
    value += f"**Classes:** {class_disp(character)}\n"
    value += f"{stats_disp(character)}\n"
    if character.invocations and extended:
        value += f"""**Eldritch Invocations:** {", ".join(character.invocations)}\n"""
    if character.feats and extended:
        value += f"""**Feats:** {", ".join(character.feats)}\n"""
    if character.user.lastActive:
        value += f"**Last Active:** <t:{int(character.user.lastActive.timestamp())}>\n"

    value += f"\n[Character Sheet]({character.url})"

    return title, value
