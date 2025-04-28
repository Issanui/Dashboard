import streamlit as st
import pandas as pd
import io
import calendar
import streamlit_highcharts as hct
from utils import load_data_app1, save_data_app1, apply_custom_css

# Appliquer le CSS personnalisé
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

st.header("📊 Partie 1 : Load Factor Moyen (Courbes Lisses)")

# Mapping of flight numbers to route names
flight_to_route = {
    103.0: "BkoGaq",
    104.0: "GaqBko",
    105.0: "BkoKys",
    106.0: "KysBko",
    109.0: "BkoTom",
    110.0: "TomBko",
    1005.0: "BkoKys",
    1006.0: "KysBko",
    1009.0: "BKoGaq - GaqTom",
    1010.0: "TomBko"
}

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
    # --- Filter by Flight No ---
    if "Flight No" in df_app1.columns:
        df_app1["Route"] = df_app1["Flight No"].map(flight_to_route)
        routes = df_app1["Route"].dropna().unique()
        routes_selected = st.multiselect("🛫 Sélectionner une ou plusieurs routes", sorted(routes))

        if routes_selected:
            df_app1 = df_app1[df_app1["Route"].isin(routes_selected)]
        else:
            st.warning("⚠️ Aucune route sélectionnée.")
    else:
        st.warning("⚠️ La colonne 'Flight No' est manquante.")

    # --- Prepare data
    df_app1["Year"] = df_app1["Sch dep dt with time"].dt.year
    df_app1["Month"] = pd.to_numeric(df_app1["Sch dep dt with time"].dt.month, errors="coerce").fillna(0).astype(int)
    df_app1["Year-Month"] = df_app1["Year"].astype(str) + "-" + df_app1["Month"].apply(lambda x: f"{x:02d}" if x > 0 else "00")
    df_app1["Year-Month"] = pd.Categorical(df_app1["Year-Month"], sorted(df_app1["Year-Month"].unique()))

    agg = df_app1.groupby(["Route", "Year-Month"], as_index=False)["COS"].mean()
    agg["LF moyen"] = agg["COS"].round(2)

    # --- Handle NaN values by replacing them with null for JSON compatibility
    agg = agg.replace({pd.NA: None, float('nan'): None})

    # --- Define the smooth line chart
    categories = list(agg["Year-Month"].unique())
    series = []

    for route in routes_selected:
        route_data = agg[agg["Route"] == route]
        series.append({
            "type": "spline",  # Smooth line chart
            "name": route,
            "data": route_data["LF moyen"].tolist(),
            "marker": {
                "enabled": True,  # Show markers on the curve
                "radius": 4  # Marker size
            }
        })

    chart_def = {
        "chart": {
            "type": "spline",  # Smooth curves with spline
            "height": 600,  # Increased height for better readability
            "backgroundColor": "#f7f9fc",
            "style": {
                "fontFamily": "Arial, sans-serif"
            },
            "borderRadius": 8,
        },
        "title": {
            "text": f"📊 Load Factor Moyen par Année et Mois (Courbes Lisses)",
            "align": "center",
            "style": {
                "color": "#333333",
                "fontSize": "20px",
                "fontWeight": "bold"
            }
        },
        "xAxis": {
            "categories": categories,
            "title": {"text": "Année-Mois"},
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
        st.dataframe(agg[["Route", "Year-Month", "LF moyen"]], use_container_width=True)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            agg[["Route", "Year-Month", "LF moyen"]].to_excel(writer, index=False, sheet_name="Résumé")

        st.download_button(
            label="📥 Télécharger Résumé (Excel)",
            data=output.getvalue(),
            file_name=f"Resume_Load_Factor.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
else:
    st.info("📭 Aucune donnée disponible pour la Partie 1.")
