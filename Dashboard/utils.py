import streamlit as st
import pandas as pd
import os

def apply_custom_css():
    with open("Dashboard/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def load_data_app1():
    if os.path.exists("Dashboard/data/data_app1.csv"):
        return pd.read_csv("Dashboard/data/data_app1.csv", parse_dates=["Sch dep dt with time"])
    else:
        return pd.DataFrame(columns=["Flight No", "Sch dep dt with time", "CAP", "PAX", "COS"])

def save_data_app1(new_data):
    data = load_data_app1()
    combined = pd.concat([data, new_data]).drop_duplicates(subset=["Flight No", "Sch dep dt with time"])
    combined.to_csv("Dashboard/data/data_app1.csv", index=False)

def load_data_app2():
    if os.path.exists("Dashboard/data/data_app2.csv"):
        return pd.read_csv("Dashboard/data/data_app2.csv", parse_dates=["Sch Dep Dt"])
    else:
        return pd.DataFrame(columns=["Sch Dep Dt", "Rez Class", "Total Ss Count", "Annee", "Mois"])

def save_data_app2(new_data):
    data = load_data_app2()
    combined = pd.concat([data, new_data], ignore_index=True)
    combined.to_csv("Dashboard/data/data_app2.csv", index=False)
