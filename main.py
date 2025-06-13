import streamlit as st
from components.pitch import render_pitch
from components.sidebar import show_sidebar
from orchestration.flow import run_agent_flow

st.set_page_config(page_title="Top Bantz AI Commentary", layout="wide")

st.title("\U0001F3C0 Top Bantz AI Commentary")

selected_player = render_pitch()

if selected_player:
    result = run_agent_flow(selected_player["id"], selected_player["name"])
    if result:
        show_sidebar(selected_player["name"], result)
