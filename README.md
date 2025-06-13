# ⚽ Top Bantz AI Commentary

Top Bantz is an AI-powered football commentary web app that lets you click on players on a pitch and hear dynamic, stat-based commentary. It combines real-time football data with custom agents that generate stats, facts, and spicy banter.

## 🔥 Features

- Interactive football pitch (4-3-3 formation)
- AI-generated player stats, trivia, and fun commentary
- Real-time football data from API-Football
- Modular agent-based orchestration (LangChain-style)

## 🚀 Setup

### 1. Clone the repo

```bash
git clone https://github.com/your-username/top-bantz-ai.git
cd top-bantz-ai
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
# Activate on Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Add your API key

Create a .env file

```bash
API_FOOTBALL_KEY=your_api_sports_key
OPENAI_API_KEY=your_openai_api_key
```

### 5. Run the app

```bash
streamlit run main.py
```

🧠 Tech Stack
-------------

-   **Streamlit** -- frontend

-   **Plotly** -- interactive football pitch

-   **LangChain agents** -- stat, fact, narration

-   **API-Football** -- live player data