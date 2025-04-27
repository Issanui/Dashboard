import streamlit as st
import pandas as pd
import os
import csv
import calendar
import random
from io import BytesIO
import streamlit_highcharts as hct
from utils import load_data_app2, save_data_app2, apply_custom_css

# Appliquer le CSS personnalisé
apply_custom_css()

st.header("📊 Partie 2 : Part de vente par Classe")

# Chargement du fichier
with st.container():
    st.subheader("📂 Charger un fichier CSV")
    uploaded_file_app2 = st.file_uploader(
        label="📂 Charger un fichier CSV",
        type=["csv", "txt"],
        key="app2_upload",
        label_visibility="collapsed"
    )

# Traitement du fichier
if uploaded_file_app2 is not None:
    try:
        # Charger le fichier temporairement
        df_temp2 = pd.read_csv(uploaded_file_app2, sep=';')
        df_temp2.columns = df_temp2.columns.str.strip()
        
        # Nettoyer les colonnes clés
        df_temp2['Rez Class'] = df_temp2['Rez Class'].str.strip()
        df_temp2['Seg Dep Port'] = df_temp2['Seg Dep Port'].str.strip()
        df_temp2['Seg Arr Port'] = df_temp2['Seg Arr Port'].str.strip()

        # Vérification des colonnes requises
        colonnes_requises = ['Sch Dep Dt', 'Rez Class', 'Total Ss Count', 'Seg Dep Port', 'Seg Arr Port']
        colonnes_manquantes = [col for col in colonnes_requises if col not in df_temp2.columns]
        
        if colonnes_manquantes:
            st.error(f"❌ Colonnes manquantes dans le fichier : {colonnes_manquantes}")
        else:
            # Nettoyage et transformation des données
            df_temp2 = df_temp2[colonnes_requises].dropna()
            df_temp2 = df_temp2[~df_temp2['Sch Dep Dt'].astype(str).str.contains("Report|Total|<b", na=False)]
            df_temp2['Sch Dep Dt'] = pd.to_datetime(df_temp2['Sch Dep Dt'], dayfirst=True, errors='coerce')
            df_temp2.dropna(subset=['Sch Dep Dt'], inplace=True)
            
            # Décomposer la date en colonnes temporaires
            df_temp2['Annee'] = df_temp2['Sch Dep Dt'].dt.year
            df_temp2['Mois'] = df_temp2['Sch Dep Dt'].dt.month
            df_temp2['Jour'] = df_temp2['Sch Dep Dt'].dt.day  # Si nécessaire
            
            df_temp2['Total Ss Count'] = pd.to_numeric(df_temp2['Total Ss Count'], errors='coerce')
            df_temp2.dropna(subset=['Total Ss Count'], inplace=True)

            # Charger les données existantes
            df_existing = load_data_app2()
            
            # Initialiser une DataFrame vide si aucune donnée n'est chargée
            if df_existing is None or df_existing.empty:
                df_existing = pd.DataFrame(columns=df_temp2.columns)
            
            # Nettoyer les doublons dans les données existantes avant concaténation
            df_existing = df_existing.drop_duplicates(
                subset=['Annee', 'Mois', 'Jour', 'Rez Class', 'Seg Dep Port', 'Seg Arr Port', 'Total Ss Count'],
                keep='first'
            )

            # Nettoyer les doublons dans df_temp2 avant concaténation
            df_temp2 = df_temp2.drop_duplicates(
                subset=['Annee', 'Mois', 'Jour', 'Rez Class', 'Seg Dep Port', 'Seg Arr Port', 'Total Ss Count'],
                keep='first'
            )

            # Combiner les données existantes avec les nouvelles
            df_combined = pd.concat([df_existing, df_temp2], ignore_index=True)
        
            # Supprimer les doublons après la combinaison
            df_combined = df_combined.drop_duplicates(
                subset=['Annee', 'Mois', 'Jour', 'Rez Class', 'Seg Dep Port', 'Seg Arr Port', 'Total Ss Count'],
                keep='first'
            )

            # Conserver uniquement les colonnes nécessaires
            colonnes_a_conserver = ['Sch Dep Dt', 'Rez Class', 'Total Ss Count', 'Seg Dep Port', 'Seg Arr Port','Annee', 'Mois']
            df_combined = df_combined[colonnes_a_conserver]

            # Sauvegarder les données combinées et nettoyées
            save_data_app2(df_combined)
            st.success("✅ Fichier chargé et traité avec succès pour la Partie 2 !")
    except Exception as e:
        st.error(f"❌ Erreur de traitement : {e}")



# Chargement de la base sauvegardée
df_app2 = load_data_app2()

if not df_app2.empty:
    df_grouped = df_app2.groupby(['Annee', 'Mois', 'Rez Class', 'Seg Dep Port', 'Seg Arr Port'])['Total Ss Count'].sum().reset_index()
    df_grouped['Month_name'] = df_grouped['Mois'].apply(lambda x: calendar.month_abbr[x] if pd.notnull(x) else "")
    df_grouped['Month_name'] = pd.Categorical(df_grouped['Month_name'], categories=calendar.month_abbr[1:], ordered=True)

    # Sélecteurs
    annees_disponibles = sorted(df_grouped['Annee'].unique())
    annee_selectionnee = st.selectbox("📅 Choisissez une année", options=annees_disponibles)

    df_annee = df_grouped[df_grouped['Annee'] == annee_selectionnee]

    mois_disponibles = sorted(df_annee['Month_name'].unique())
    mois_selectionnes = st.multiselect("📅 Choisissez un ou plusieurs mois", options=mois_disponibles, default=mois_disponibles)

    df_annee = df_annee[df_annee['Month_name'].isin(mois_selectionnes)]

    ports_depart = sorted(df_annee['Seg Dep Port'].unique())
    ports_arrivee = sorted(df_annee['Seg Arr Port'].unique())

    port_depart_selectionne = st.selectbox("🛫 Port de départ", options=ports_depart)
    port_arrivee_selectionne = st.selectbox("🛬 Port d'arrivée", options=ports_arrivee)

    df_filtered = df_annee[
        (df_annee['Seg Dep Port'] == port_depart_selectionne) &
        (df_annee['Seg Arr Port'] == port_arrivee_selectionne)
    ]

    if df_filtered.empty:
        st.warning("⚠️ Pas de données pour cette sélection.")
    else:
        # Recalculer total uniquement sur les données filtrées
        total_counts = df_filtered.groupby(['Annee', 'Mois'])['Total Ss Count'].transform('sum')
        df_filtered['Part class'] = (df_filtered['Total Ss Count'] / total_counts) * 100
        df_filtered['Part class'] = df_filtered['Part class'].round(1)

        # Trier les classes par part décroissante
        df_filtered = df_filtered.sort_values('Part class', ascending=False)

        # Reconstruire les catégories triées
        categories = df_filtered['Rez Class'].unique().tolist()

        # Série pour le graphique
        series = []
        for mois in mois_selectionnes:
            data_mois = df_filtered[df_filtered['Month_name'] == mois]
            # Faire correspondre l’ordre des catégories
            data = [data_mois[data_mois['Rez Class'] == classe]['Part class'].sum() for classe in categories]
            series.append({
                "name": mois,
                "data": data
            })

        # Highcharts definition
        chart_def = {
            "chart": {
                "type": "column",
                "height": 600,
                "backgroundColor": "#f7f9fc",
                "style": {"fontFamily": "Arial, sans-serif"}
            },
            "title": {
                "text": f"🛫 Répartition des Parts de Vente par Classe - {annee_selectionnee}",
                "align": "center",
                "style": {"color": "#333333", "fontSize": "20px", "fontWeight": "bold"}
            },
            "xAxis": {
                "categories": categories,
                "title": {"text": "Classes"},
                "labels": {"style": {"color": "#333333", "fontSize": "14px"}}
            },
            "yAxis": {
                "min": 0,
                "title": {"text": "Part (%)"},
                "gridLineWidth": 1,
                "gridLineColor": "#e6e6e6",
                "labels": {"style": {"color": "#333333", "fontSize": "14px"}}
            },
            "legend": {
                "layout": "horizontal",
                "align": "center",
                "verticalAlign": "bottom",
                "itemStyle": {"color": "#333333", "fontSize": "12px"},
                "itemHoverStyle": {"color": "#000000"}
            },
            "series": series,
            "plotOptions": {
                "column": {
                    "dataLabels": {
                        "enabled": True,
                        "format": "{point.y:.1f}%",
                        "style": {"color": "#333333", "textOutline": "none", "fontWeight": "bold"}
                    }
                }
            },
            "tooltip": {
                "shared": True,
                "backgroundColor": "#ffffff",
                "borderColor": "#cccccc",
                "style": {"color": "#333333", "fontSize": "12px"}
            },
            "credits": {"enabled": False}
        }

        hct.streamlit_highcharts(chart_def, 640)

        with st.expander("📋 Voir et Télécharger le tableau résumé"):
            st.dataframe(
                df_filtered[['Annee', 'Month_name', 'Rez Class', 'Part class', 'Seg Dep Port', 'Seg Arr Port']],
                use_container_width=True
            )

            def convert_df(df):
                output = BytesIO()
                df[['Annee', 'Month_name', 'Rez Class', 'Part class', 'Seg Dep Port', 'Seg Arr Port']].rename(
                    columns={'Month_name': 'Mois', 'Part class': 'Part (%)'}
                ).to_csv(output, index=False)
                return output.getvalue()

            st.download_button(
                label="📥 Télécharger Résumé (CSV)",
                data=convert_df(df_filtered),
                file_name=f"Part_Vente_Classe_{annee_selectionnee}.csv",
                mime="text/csv",
                use_container_width=True
            )
else:
    st.info("📭 Aucune donnée disponible pour la Partie 2.")


# Tarifs fixes
tarifs_data = [
    {'Seg Arr Port': 'BKO', 'Seg Dep Port': 'GAQ', 'Rez Class': 'Y', 'Tarif': 194000},
    {'Seg Arr Port': 'BKO', 'Seg Dep Port': 'GAQ', 'Rez Class': 'B', 'Tarif': 175800},
    {'Seg Arr Port': 'BKO', 'Seg Dep Port': 'GAQ', 'Rez Class': 'M', 'Tarif': 154800},
    {'Seg Arr Port': 'BKO', 'Seg Dep Port': 'GAQ', 'Rez Class': 'L', 'Tarif': 135200},
    {'Seg Arr Port': 'BKO', 'Seg Dep Port': 'GAQ', 'Rez Class': 'V', 'Tarif': 124000},
    {'Seg Arr Port': 'BKO', 'Seg Dep Port': 'GAQ', 'Rez Class': 'E', 'Tarif': 103800},
    {'Seg Arr Port': 'GAQ', 'Seg Dep Port': 'BKO', 'Rez Class': 'Y', 'Tarif': 194000},
    {'Seg Arr Port': 'GAQ', 'Seg Dep Port': 'BKO', 'Rez Class': 'B', 'Tarif': 175800},
    {'Seg Arr Port': 'GAQ', 'Seg Dep Port': 'BKO', 'Rez Class': 'M', 'Tarif': 154800},
    {'Seg Arr Port': 'GAQ', 'Seg Dep Port': 'BKO', 'Rez Class': 'L', 'Tarif': 135200},
    {'Seg Arr Port': 'GAQ', 'Seg Dep Port': 'BKO', 'Rez Class': 'V', 'Tarif': 124000},
    {'Seg Arr Port': 'GAQ', 'Seg Dep Port': 'BKO', 'Rez Class': 'E', 'Tarif': 103800},
    {'Seg Arr Port': 'BKO', 'Seg Dep Port': 'TOM', 'Rez Class': 'Y', 'Tarif': 194000},
    {'Seg Arr Port': 'BKO', 'Seg Dep Port': 'TOM', 'Rez Class': 'B', 'Tarif': 175800},
    {'Seg Arr Port': 'BKO', 'Seg Dep Port': 'TOM', 'Rez Class': 'M', 'Tarif': 154800},
    {'Seg Arr Port': 'BKO', 'Seg Dep Port': 'TOM', 'Rez Class': 'L', 'Tarif': 135200},
    {'Seg Arr Port': 'BKO', 'Seg Dep Port': 'TOM', 'Rez Class': 'V', 'Tarif': 124000},
    {'Seg Arr Port': 'BKO', 'Seg Dep Port': 'TOM', 'Rez Class': 'E', 'Tarif': 83800},
    {'Seg Arr Port': 'TOM', 'Seg Dep Port': 'BKO', 'Rez Class': 'Y', 'Tarif': 194000},
    {'Seg Arr Port': 'TOM', 'Seg Dep Port': 'BKO', 'Rez Class': 'B', 'Tarif': 175800},
    {'Seg Arr Port': 'TOM', 'Seg Dep Port': 'BKO', 'Rez Class': 'M', 'Tarif': 154800},
    {'Seg Arr Port': 'TOM', 'Seg Dep Port': 'BKO', 'Rez Class': 'L', 'Tarif': 135200},
    {'Seg Arr Port': 'TOM', 'Seg Dep Port': 'BKO', 'Rez Class': 'V', 'Tarif': 124000},
    {'Seg Arr Port': 'TOM', 'Seg Dep Port': 'BKO', 'Rez Class': 'E', 'Tarif': 83800},
    {'Seg Arr Port': 'BKO', 'Seg Dep Port': 'KYS', 'Rez Class': 'Y', 'Tarif': 119000},
    {'Seg Arr Port': 'BKO', 'Seg Dep Port': 'KYS', 'Rez Class': 'B', 'Tarif': 105000},
    {'Seg Arr Port': 'BKO', 'Seg Dep Port': 'KYS', 'Rez Class': 'M', 'Tarif': 92000},
    {'Seg Arr Port': 'BKO', 'Seg Dep Port': 'KYS', 'Rez Class': 'L', 'Tarif': 81200},
    {'Seg Arr Port': 'BKO', 'Seg Dep Port': 'KYS', 'Rez Class': 'V', 'Tarif': 74000},
    {'Seg Arr Port': 'BKO', 'Seg Dep Port': 'KYS', 'Rez Class': 'E', 'Tarif': 63800},
    {'Seg Arr Port': 'KYS', 'Seg Dep Port': 'BKO', 'Rez Class': 'Y', 'Tarif': 119000},
    {'Seg Arr Port': 'KYS', 'Seg Dep Port': 'BKO', 'Rez Class': 'B', 'Tarif': 105000},
    {'Seg Arr Port': 'KYS', 'Seg Dep Port': 'BKO', 'Rez Class': 'M', 'Tarif': 92000},
    {'Seg Arr Port': 'KYS', 'Seg Dep Port': 'BKO', 'Rez Class': 'L', 'Tarif': 81200},
    {'Seg Arr Port': 'KYS', 'Seg Dep Port': 'BKO', 'Rez Class': 'V', 'Tarif': 74000},
    {'Seg Arr Port': 'KYS', 'Seg Dep Port': 'BKO', 'Rez Class': 'E', 'Tarif': 63800},
]

# Conversion des tarifs en DataFrame
tarifs_df = pd.DataFrame(tarifs_data)

if not df_filtered.empty:
    # Fusionner les tarifs avec les données filtrées
    df_filtered = df_filtered.merge(
        tarifs_df,
        on=['Seg Dep Port', 'Seg Arr Port', 'Rez Class'],
        how='left'
    )

    # Grouper par année, mois, origine-destination, et classe
    df_grouped_revenu = df_filtered.groupby(
        ['Annee', 'Mois', 'Seg Dep Port', 'Seg Arr Port', 'Rez Class']
    ).agg({
        'Total Ss Count': 'sum',  # Somme des compteurs
        'Tarif': 'first'          # Prendre le tarif (identique pour chaque groupe)
    }).reset_index()

    # Calcul du revenu par classe
    df_grouped_revenu['Revenu'] = df_grouped_revenu['Total Ss Count'] * df_grouped_revenu['Tarif']

    # Calcul du revenu total
    total_revenu = df_grouped_revenu['Revenu'].sum()

    # Calcul de la part du revenu par classe
    df_grouped_revenu['Part revenu'] = (df_grouped_revenu['Revenu'] / total_revenu) * 100
    df_grouped_revenu['Part revenu'] = df_grouped_revenu['Part revenu'].round(1)

    # Trier les classes par part de revenu décroissante
    df_grouped_revenu = df_grouped_revenu.sort_values('Part revenu', ascending=False)

    # Reconstruire les catégories triées pour le graphique
    categories_revenu = df_grouped_revenu['Rez Class'].unique().tolist()

    # Construire la série pour le graphique
    series_revenu = []
    for mois in mois_selectionnes:
        data_mois = df_grouped_revenu[df_grouped_revenu['Mois'] == list(calendar.month_abbr).index(mois)]
        data = [data_mois[data_mois['Rez Class'] == classe]['Part revenu'].sum() for classe in categories_revenu]
        series_revenu.append({
            "name": mois,
            "data": data
        })

    # Définition du graphique pour la part des revenus
    chart_def_revenu = {
        "chart": {
            "type": "column",
            "height": 600,
            "backgroundColor": "#f7f9fc",
            "style": {"fontFamily": "Arial, sans-serif"}
        },
        "title": {
            "text": f"🛫 Répartition des Revenus par Classe - {annee_selectionnee}",
            "align": "center",
            "style": {"color": "#333333", "fontSize": "20px", "fontWeight": "bold"}
        },
        "xAxis": {
            "categories": categories_revenu,
            "title": {"text": "Classes"},
            "labels": {"style": {"color": "#333333", "fontSize": "14px"}}
        },
        "yAxis": {
            "min": 0,
            "title": {"text": "Part du revenu (%)"},
            "gridLineWidth": 1,
            "gridLineColor": "#e6e6e6",
            "labels": {"style": {"color": "#333333", "fontSize": "14px"}}
        },
        "legend": {
            "layout": "horizontal",
            "align": "center",
            "verticalAlign": "bottom",
            "itemStyle": {"color": "#333333", "fontSize": "12px"},
            "itemHoverStyle": {"color": "#000000"}
        },
        "series": series_revenu,
        "plotOptions": {
            "column": {
                "dataLabels": {
                    "enabled": True,
                    "format": "{point.y:.1f}%",
                    "style": {"color": "#333333", "textOutline": "none", "fontWeight": "bold"}
                }
            }
        },
        "tooltip": {
            "shared": True,
            "backgroundColor": "#ffffff",
            "borderColor": "#cccccc",
            "style": {"color": "#333333", "fontSize": "12px"}
        },
        "credits": {"enabled": False}
    }

    # Afficher le second graphique
    hct.streamlit_highcharts(chart_def_revenu, 640)

    with st.expander("📋 Voir et Télécharger le tableau résumé des revenus"):
        st.dataframe(
            df_grouped_revenu[['Annee', 'Mois', 'Rez Class', 'Seg Dep Port', 'Seg Arr Port', 'Total Ss Count', 'Revenu', 'Part revenu']],
            use_container_width=True
        )

        def convert_df_revenu(df):
            output = BytesIO()
            df[['Annee', 'Mois', 'Rez Class', 'Seg Dep Port', 'Seg Arr Port', 'Total Ss Count', 'Revenu', 'Part revenu']].rename(
                columns={'Part revenu': 'Part Revenu (%)'}
            ).to_csv(output, index=False)
            return output.getvalue()

        st.download_button(
            label="📥 Télécharger Résumé des Revenus (CSV)",
            data=convert_df_revenu(df_grouped_revenu),
            file_name=f"Revenu_Part_Classe_{annee_selectionnee}.csv",
            mime="text/csv",
            use_container_width=True
        )