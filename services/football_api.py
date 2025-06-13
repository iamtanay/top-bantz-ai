import requests
from config import API_FOOTBALL_KEY

BASE_URL = "https://v3.football.api-sports.io"

HEADERS = {
    "x-apisports-key": API_FOOTBALL_KEY  # Correct header
}

def get_player_stat(player_id):
    url = f"{BASE_URL}/players"
    params = {
        "id": player_id,
        "season": 2021  # 2021 confirmed working for Cavani
    }

    res = requests.get(url, headers=HEADERS, params=params)

    if res.status_code != 200:
        return f"No stats available for player ID {player_id}"

    data = res.json()

    if not data.get("response"):
        return f"No data found for player ID {player_id}"

    try:
        player_info = data["response"][0]["player"]
        stats = data["response"][0]["statistics"][0]
        goals = stats["goals"].get("total", 0)
        assists = stats["goals"].get("assists", 0)
        minutes = stats["games"].get("minutes", 0)
        appearances = stats["games"].get("appearences", 0)

        return f"{player_info['name']} scored {goals} goals, provided {assists} assists in {appearances} appearances playing {minutes} minutes."
    except Exception as e:
        return f"Failed to parse stats for player ID {player_id}: {e}"