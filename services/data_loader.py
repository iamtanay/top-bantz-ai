import json

def get_player_fact(player_name):
    with open("data/players.json") as f:
        facts = json.load(f)
    return facts.get(player_name, "A promising talent with a lot to prove.")