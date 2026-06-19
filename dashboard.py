import streamlit as st
import plotly.express as px
from db import get_all_data

st.title("Weather ETL Dashboard")
st.subheader("Données météo en temps réel")

df = get_all_data()

st.dataframe(df)

fig_temp = px.bar(df, x="city", y="temperature", title="Température par ville (°C)", color="city")
st.plotly_chart(fig_temp)

fig_hum = px.bar(df, x="city", y="humidity", title="Humidité par ville (%)", color="city")
st.plotly_chart(fig_hum)

fig_wind = px.bar(df, x="city", y="wind_speed", title="Vitesse du vent par ville (km/h)", color="city")
st.plotly_chart(fig_wind)

if st.button("Rafraîchir les données"):
    st.rerun()