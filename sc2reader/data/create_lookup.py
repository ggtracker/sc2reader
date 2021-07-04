abilities = dict()
with open("hots_abilities.csv", "r") as f:
    for line in f:
        num, ability = line.strip("\r\n ").split(",")
        abilities[ability] = [""] * 32

with open("command_lookup.csv", "r") as f:
    for line in f:
        ability, commands = line.strip("\r\n ").split("|", 1)
        abilities[ability] = commands.split("|")

with open("new_lookup.csv", "w") as out:
    for ability, commands in sorted(abilities.items()):
        out.write(",".join([ability] + commands) + "\n")
