import streamlit as st

def remember_fact(player_name, fact):
    if "shown_facts" not in st.session_state:
        st.session_state.shown_facts = {}
    st.session_state.shown_facts[player_name] = fact