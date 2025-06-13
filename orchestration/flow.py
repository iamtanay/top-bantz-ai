from agents.stat_agent import stat_agent
from agents.fact_agent import fact_agent
from agents.narration_agent import narration_agent
from agents.memory_agent import remember_fact

def run_agent_flow(player_id, player_name):
    stat = stat_agent(player_id)
    
    if stat.startswith("No data"):
        return None

    fact = fact_agent(player_name)
    commentary = narration_agent({
        "stat": stat,
        "fact": fact,
        "player": player_name
    })
    remember_fact(player_name, fact)

    return {
        "stat": stat,
        "fact": fact,
        "commentary": commentary
    }
