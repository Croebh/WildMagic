import json

with open("C:/Users/Joseph/Desktop/AVRAE/avrae-data-entry/gamedata/items.json") as f:
  items = json.loads(f.read())


adv_items = """Hell Hound Cloak
Eagle Whistle
Bracelet of Rock Magic
Balance of Harmony
Amulet of Protection from Turning
Scorpion Armor
Mask of the Beast
Amulet of the Black Skull
Ring of Truth Telling
Feather of Diatryma Summoning
Badge of the Watch
Shield of the Uven Rune
Propeller Helm
Orb of Gonging
Horned Ring
Horn of the Endless Maze
Dodecahedron of Doom
Chest of Preserving
Blast Scepter""".splitlines()

out = []

for item in adv_items:
  for _item in items:
    if item.replace("'", "") == _item['name'].replace("'", ""):
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
      break

outList = [out[i:i+5] for i in range(0, len(out), 5)]
for i, out in enumerate(outList, 1):
  with open(f"C:/Users/Joseph/Desktop/AVRAE/WildMagic/Adventure-{i}.json", 'w') as f:
    json.dump(out, f, indent=2)