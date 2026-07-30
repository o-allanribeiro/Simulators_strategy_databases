import streamlit as st

from nav import NAVIGATION

st.set_page_config(
    page_title="Análise de Arquiteturas para Sistemas Financeiros",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

pg = st.navigation(NAVIGATION)
pg.run()
