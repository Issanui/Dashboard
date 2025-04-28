import streamlit as st
from utils import apply_custom_css

st.set_page_config(page_title="Dashboard Combiné", layout="wide")

apply_custom_css()

st.title("✨ Bienvenue sur le Dashboard Combiné")
st.markdown("""
---
Ce dashboard est composé de deux analyses principales :

- **📊 Load Factor Moyen** (partie 1)
- **📊 Part de vente par Classe** (partie 2)

Utilisez le menu à gauche pour naviguer entre les sections !
---
""")
