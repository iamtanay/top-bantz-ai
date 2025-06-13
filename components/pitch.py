import streamlit as st 
import plotly.graph_objects as go
import json

with open("data/formations.json") as f:
    FORMATIONS = json.load(f)

def render_pitch():
    formation = "4-3-3"
    players = FORMATIONS[formation]

    fig = go.Figure()
    fig.update_layout(
        width=800,
        height=500,
        plot_bgcolor="green",
        xaxis=dict(range=[0, 100], showgrid=False, zeroline=False),
        yaxis=dict(range=[0, 100], showgrid=False, zeroline=False),
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False
    )

    for player in players:
        fig.add_trace(go.Scatter(
            x=[player["x"]],
            y=[player["y"]],
            mode="markers+text",
            marker=dict(size=20, color="white"),
            text=[player["name"]],
            textposition="bottom center",
            hoverinfo="text",
            name=player["name"]
        ))

    st.plotly_chart(fig, use_container_width=True)
    selected_name = st.selectbox("Select Player", [p["name"] for p in players])
    selected_player = next((p for p in players if p["name"] == selected_name), None)
    return selected_player