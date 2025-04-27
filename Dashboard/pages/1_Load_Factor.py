import streamlit as st
import pandas as pd
import io
import calendar
import streamlit_highcharts as hct
from utils import load_data_app1, save_data_app1, apply_custom_css

# Apply custom CSS
apply_custom_css()

# Styled background
page_bg_css = """
<style>
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(120deg, #f0f2f6, #d9e4f5);
    }
    [data-testid="stHeader"] {
        background: rgba(0, 0, 0, 0);
    }
    [data-testid="stSidebar"] {
        background-color: #e0e8f0;
    }
    section[data-testid="stFileUploader"] > label div {
        background-color: #4CAF50;
        color: white;
        padding: 10px 20px;
        border-radius: 8px;
        text-align: center;
        font-weight: bold;
        cursor: pointer;
    }
</style>
"""
st.markdown(page_bg_css, unsafe_allow_html=True)

st.header("📊 Partie 1 : Load Factor Moyen")

# File upload
with st.container():
    uploaded_file_app1 = st.file_uploader(
        label="Charger un fichier CSV", 
        type=["csv", "txt"], 
        key="app1_upload",
        label_visibility="collapsed"
    )

# Processing
if uploaded_file_app1 is not None:
    try:
        df_temp = pd.read_csv(uploaded_file_app1, sep=";")
        df_temp.columns = df_temp.columns.str.strip()

        if "Sch dep dt with time" in df_temp.columns:
            df_temp["Sch dep dt with time"] = pd.to_datetime(df_temp["Sch dep dt with time"], dayfirst=True, errors="coerce")
            df_temp["COS"] = pd.to_numeric(df_temp["COS"], errors="coerce")

            before_count = load_data_app1().shape[0]
            save_data_app1(df_temp)
            after_count = load_data_app1().shape[0]

            added_rows = after_count - before_count
            st.success(f"✅ {added_rows} ligne(s) ajoutée(s) avec succès pour la Partie 1 !")
        else:
            st.error("❌ Colonne 'Sch dep dt with time' introuvable.")
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement du fichier : {e}")

# Load saved data
df_app1 = load_data_app1()

if not df_app1.empty:
    # --- Filter by Year ---
    if "Year" not in df_app1.columns:
        df_app1["Year"] = df_app1["Sch dep dt with time"].dt.year

    years = sorted(df_app1["Year"].dropna().unique())
    year_selected = st.selectbox("📅 Sélectionner une Année", years)
    df_app1 = df_app1[df_app1["Year"] == year_selected]

    # --- Filter by Flight No ---
    if "Flight No" in df_app1.columns:
        flight_numbers = df_app1["Flight No"].dropna().unique()
        flight_selected = st.selectbox("✈️ Sélectionner un numéro de vol (Flight No)", sorted(flight_numbers))

        df_app1 = df_app1[df_app1["Flight No"] == flight_selected]
    else:
        st.warning("⚠️ La colonne 'Flight No' est manquante.")

    # --- Prepare data
    df_app1["Month"] = df_app1["Sch dep dt with time"].dt.month.astype("Int64")
    df_app1["Month_name"] = df_app1["Month"].apply(lambda x: calendar.month_abbr[int(x)] if pd.notnull(x) else "")
    df_app1["Month_name"] = pd.Categorical(df_app1["Month_name"], categories=calendar.month_abbr[1:], ordered=True)

    agg = df_app1.groupby(["Month_name"], as_index=False)["COS"].mean()
    agg["LF moyen"] = agg["COS"].round(2)

    # --- Handle NaN values by replacing them with null for JSON compatibility
    agg = agg.replace({pd.NA: None, float('nan'): None})

    # --- Define the vertical bar chart with red bars
    categories = list(agg["Month_name"].unique())
    series = [{
        "type": "column",  # Vertical bar chart
        "name": f"Année {year_selected}",
        "data": agg["LF moyen"].tolist(),
        "color": "#FF0000"  # Set bars to red
    }]

    chart_def = {
        "chart": {
            "type": "column",
            "height": 600,  # Increased height for better readability
            "backgroundColor": "#f7f9fc",
            "style": {
                "fontFamily": "Arial, sans-serif"
            },
            "borderRadius": 8,
        },
        "title": {
            "text": f"📊 Load Factor Moyen par Mois - Année {year_selected}",
            "align": "center",
            "style": {
                "color": "#333333",
                "fontSize": "20px",
                "fontWeight": "bold"
            }
        },
        "xAxis": {
            "categories": categories,
            "title": {"text": "Mois"},
            "labels": {
                "style": {
                    "color": "#333333",
                    "fontSize": "14px"  # Increased font size for better readability
                }
            }
        },
        "yAxis": {
            "min": 0,
            "title": {"text": "Load Factor (%)"},
            "gridLineWidth": 1,
            "gridLineColor": "#e6e6e6",
            "labels": {
                "style": {
                    "color": "#333333",
                    "fontSize": "14px"  # Increased font size for labels
                }
            },
        },
        "legend": {
            "layout": "horizontal",
            "align": "center",
            "verticalAlign": "bottom",
            "itemStyle": {
                "color": "#333333",
                "fontSize": "12px"
            },
            "itemHoverStyle": {
                "color": "#000000"
            }
        },
        "series": series,
        "plotOptions": {
            "column": {
                "borderRadius": 10,  # Rounded corners for bars
                "dataLabels": {
                    "enabled": True,
                    "format": "{point.y:.1f}%",  # Show percentages with one decimal
                    "style": {
                        "color": "#333333",
                        "textOutline": "none",
                        "fontWeight": "bold"
                    }
                },
                "groupPadding": 0.1
            }
        },
        "tooltip": {
            "shared": True,
            "backgroundColor": "#ffffff",
            "borderColor": "#cccccc",
            "style": {
                "color": "#333333",
                "fontSize": "12px"
            }
        },
        "credits": {"enabled": False}
    }

    # Display the chart
    hct.streamlit_highcharts(chart_def, 640)

    # --- Summary
    with st.expander("📋 Voir et Télécharger le tableau résumé"):
        st.dataframe(agg[["Month_name", "LF moyen"]], use_container_width=True)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            agg[["Month_name", "LF moyen"]].to_excel(writer, index=False, sheet_name="Résumé")

        st.download_button(
            label="📥 Télécharger Résumé (Excel)",
            data=output.getvalue(),
            file_name=f"Resume_Load_Factor_{year_selected}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
else:
    st.info("📭 Aucune donnée disponible pour la Partie 1.")