from services.data_loader import get_player_fact

def fact_agent(player_name: str) -> str:
    return get_player_fact(player_name)