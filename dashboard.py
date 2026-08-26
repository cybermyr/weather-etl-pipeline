import plotly.express as px
import streamlit as st

from db import get_all_data

st.set_page_config(page_title="Weather Dashboard", layout="wide")

st.title("Weather ETL Dashboard")
st.subheader("Données météo collectées par le pipeline")

df = get_all_data()

# Garde-fou : si la base est vide ou injoignable.
if df.empty:
    st.warning("Aucune donnée disponible. Le pipeline a-t-il déjà été exécuté ?")
    st.stop()

# --- Section 1 : état actuel (dernière mesure de chaque ville) ---
st.header("État actuel par ville")

latest = df.sort_values("created_at").groupby("city", as_index=False).last()

st.dataframe(latest, use_container_width=True)

metric = st.selectbox(
    "Choisir une mesure à comparer",
    options={
        "temperature": "Température (°C)",
        "humidity": "Humidité (%)",
        "wind_speed": "Vitesse du vent (km/h)",
    }.keys(),
    format_func=lambda col: {
        "temperature": "Température (°C)",
        "humidity": "Humidité (%)",
        "wind_speed": "Vitesse du vent (km/h)",
    }[col],
)

fig_compare = px.bar(
    latest.sort_values(metric, ascending=False),
    x="city",
    y=metric,
    color="city",
    title=f"{metric} par ville (dernière mesure)",
)
st.plotly_chart(fig_compare, use_container_width=True)

# --- Section 2 : évolution dans le temps ---
st.header("Évolution dans le temps")

selected_cities = st.multiselect(
    "Choisir les villes à afficher",
    options=sorted(df["city"].unique()),
    default=sorted(df["city"].unique())[:3],
)

if selected_cities:
    history = df[df["city"].isin(selected_cities)]
    fig_history = px.line(
        history.sort_values("created_at"),
        x="created_at",
        y="temperature",
        color="city",
        markers=True,
        title="Évolution de la température dans le temps",
    )
    st.plotly_chart(fig_history, use_container_width=True)
else:
    st.info("Sélectionne au moins une ville pour voir son évolution.")

if st.button("Rafraîchir les données"):
    st.rerun()