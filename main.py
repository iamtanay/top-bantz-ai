import streamlit as st
from components.pitch import render_pitch
from components.sidebar import show_sidebar
from orchestration.flow import run_agent_flow
import asyncio

st.set_page_config(page_title="Top Bantz AI Commentary", layout="wide")

st.title("\U000026BD Top Bantz AI Commentary")

selected_player = render_pitch()

if selected_player:
    # Await the async function properly using asyncio.run
    result = asyncio.run(run_agent_flow(selected_player["id"], selected_player["name"]))
    if result:
        show_sidebar(selected_player["name"], result)
