from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

def narration_agent(data):
    prompt = f"""
    Generate a lively commentary for the player {data['player']}:
    - Stat: {data['stat']}
    - Fun Fact: {data['fact']}
    Style: Energetic football commentator
    """
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()