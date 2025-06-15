import streamlit as st

def show_sidebar(player_name, result):
    st.sidebar.title(f"\U0001F3C6 {player_name} Commentary")
    st.sidebar.markdown(result["commentary"])
