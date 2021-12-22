import json

with open("C:/Users/Joseph/Desktop/AVRAE/avrae-data-entry/gamedata/items.json") as f:
  items = json.loads(f.read())

with open("C:/Users/Joseph/Desktop/AVRAE/avrae-data-entry/gamedata/feats.json") as f:
  feats = json.loads(f.read())

with open("C:/Users/Joseph/Desktop/AVRAE/avrae-data-entry/gamedata/spells.json") as f:
  spells = json.loads(f.read())

with open("C:/Users/Joseph/Desktop/AVRAE/avrae-data-entry/gamedata/backgrounds.json") as f:
  backgrounds = json.loads(f.read())

with open("C:/Users/Joseph/Desktop/AVRAE/avrae-data-entry/gamedata/races.json") as f:
  races = json.loads(f.read())

source = "SACoC"

meta_exclusions = ["legendary", "artifact", "potion", "poison"]
out = []

for _item in items:
  if _item['source'] == source and not any([i in _item.get('meta','').lower() for i in meta_exclusions]):
    attunement = _item['attunement']
    if attunement == True:
      attunement = "Requires Attunement"
    desc = f"**Meta:** {_item['meta']}"
    desc += f"\n**Attunement:** {attunement}\n" if attunement else ''
    desc += f"\n{_item['desc']}"
    if len(desc) >= 4096:
      desc = desc[:4000] + "... [Too Long To Display]"
    desc += f"\n\n**Source:** {_item['source']}"
    out.append({"name": "Magic Item: " + _item['name'], "desc": desc, "url": _item['url']})

for _feat in feats:
  if _feat['source'] == source and not any([i in _feat.get('meta','') for i in meta_exclusions]):
    desc = f"{_feat['description']}"
    prerequisite = _feat['prerequisite']
    if prerequisite:
      desc = f"**Prerequisite:** {prerequisite}\n\n{desc}"
    if len(desc) >= 4096:
      desc = desc[:4000] + "... [Too Long To Display]"
    desc += f"\n\n**Source:** {_feat['source']}"
    out.append({"name": "Feat: " + _feat['name'], "desc": desc, "url": _feat['url']})

for _background in backgrounds:
  if _background['source'] == source and not any([i in _background.get('meta','') for i in meta_exclusions]):
    desc = '\n'.join([f"""**{trait['name']}.** {trait['text']}""" for trait in _background['traits']])
    if len(desc) >= 4096:
      desc = desc[:4000] + "... [Too Long To Display]"
    desc += f"\n\n**Source:** {_background['source']}"
    out.append({"name": "Background: " + _background['name'], "desc": desc, "url": _background['url']})

for _race in races:
  if _race['source'] == source and not any([i in _race.get('meta','') for i in meta_exclusions]):
    desc = '\n'.join([f"""**{trait['name']}.** {trait['text']}""" for trait in _race['traits'] if trait['name'] != "Ability Score Increases"])
    if len(desc) >= 4096:
      desc = desc[:4000] + "... [Too Long To Display]"
    desc += f"\n\n**Source:** {_race['source']}"
    out.append({"name": "Race: " + _race['name'], "desc": desc, "url": _race['url']})

for _spell in spells:
#   if _spell['source'] == source:
#     desc = f"""*{_spell['level'] or ''}{['Cantrip','st','nd','rd','th','th','th','th','th','th'][_spell['level']]}{"-level" if _spell['level'] else ''} {_spell['school'].lower()}. ({', '.join(_spell['classes']+_spell['subclasses'])})*\n**Meta**\n"""
#     desc += f"""**Casting Time**: {_spell['casttime']}\n**Range:** {_spell['range']}\n**Components:** {_spell['components']}\n**Duration:** {_spell['duration']}\n\n**Description:** {_spell['description']}"""
#     if _spell['higherlevels']:
#       desc += f"""\n\n**At Higher Levels:** {_spell['higherlevels']}"""
#     if len(desc) >= 4096:
#       desc = desc[:4000] + "... [Too Long To Display]"
#     desc += f"\n\n**Source:** {_spell['source']}"
#     out.append({"name": "Spell: " + _spell['name'], "desc": desc, "url": _spell['url']})


outList = [out[i:i+10] for i in range(0, len(out), 10)]
for i, out in enumerate(outList, 1):
  with open(f"C:/Users/Joseph/Desktop/AVRAE/WildMagic/SACoC-{i}.json", 'w') as f:
    json.dump(out, f, indent=2)