import streamlit as st
import pandas as pd
import base64
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import requests
import json
import folium
from folium import plugins
from streamlit_folium import folium_static
import ipywidgets
import geocoder
import geopy
import plotly.express as px
# INTRODUCTION
st.beta_set_page_config(page_title='Immobilier Reims', layout = 'wide', initial_sidebar_state = 'auto')
st.set_option('deprecation.showPyplotGlobalUse', False)
st.title("Le marché immobilier à Reims")
st.markdown("""
Voici le bilan du marché immobilier rémois entre 2016 et 2020.
* Base de données: [data-gouv.fr](https://www.data.gouv.fr/fr/datasets/demandes-de-valeurs-foncieres/)
* Librairies Python: pandas, streamlit, numpy, seaborn, folium, geocoder
""")


@st.cache
def load_data(years, locaux):
    df0 = pd.read_csv(
        'https://raw.githubusercontent.com/Aubinrocky/Immobilier/main/datasetimmobilierreimssansimmeubles.csv')
    del df0["Unnamed: 0"]
    nan_rows = df0[df0["Latitude"].isnull()]
    df0 = df0.drop(nan_rows.index)
    df = df0[(df0["Annee"].isin(years)) & (df0["Type local"].isin(locaux))]
    return df, df0


st.sidebar.header('Filtres')
selected_years = st.sidebar.multiselect(
    'Années', [2017, 2018, 2019, 2020], [2017, 2018, 2019, 2020])
type_local = ['Appartement', 'Maison']

df, df0 = load_data(selected_years, type_local)

# SIDEBAR

selected_type_local = st.sidebar.multiselect(
    'Type de local', type_local, type_local)
# Input latitude/longitude
st.sidebar.header("Vous connaissez l'adresse du bien immobilier ?")
selected_connaissance = st.sidebar.selectbox("", ["Non", "Oui"])
if selected_connaissance == "Oui":
    st.sidebar.markdown("""
        Vous pouvez obtenir les coordonnées GPS de votre point ici: https://www.latlong.net/convert-address-to-lat-long.html
        """)
    selected_latitude = st.sidebar.number_input(
        "Entrer la latitude de votre point d'intérêt", step=1e-6, format="%.5f")
    selected_longitude = st.sidebar.number_input(
        "Entrer la longitude de votre point d'intérêt", step=1e-6, format="%.5f")
else:
    selected_latitude = 0
    selected_longitude = 0

# HEATMAP
st.header("Répartition du Prix au m² dans l'agglomération de Reims")
if selected_latitude != 0.00 and selected_longitude != 0.00:
    m = folium.Map(location=[selected_latitude,
                             selected_longitude], zoom_start=19)
    folium.Marker([selected_latitude, selected_longitude],
                  tooltip="<strong>Votre point d'intérêt</strong>", icon=folium.Icon(color='red', prefix='fa', icon='anchor')).add_to(m)
else:
    m = folium.Map(location=[49.258329, 4.031696], zoom_start=13)
# Step 1: Clusters
cluster = plugins.MarkerCluster().add_to(m)
# Step 2: Clusters breaking into Markers
for i in df.index:
    try:
        aux = str(int(df["No voie"][i]))
    except:
        aux = ""
    address = aux+", "+str(df["Type de voie"][i])+" "+str(df["Voie"][i])+", "+str(
        df["Commune"][i])+" "+str(df["Code postal"][i])+" "+str(df["Pays"][i])
    prixMetreCarre = str(round(df["Prix metre carre"][i], 2))
    surface = str(df["Surface reelle bati"][i])
    valeurFonciere = str(round(df["Valeur fonciere"][i], 2))
    Type = str(df["Type local"][i])
    popup = "<br><b>"+"Adresse"+": "+"</b>"+address+"</br>"+"<br><b>"+"Prix/m²: "+"</b>"+prixMetreCarre+" €/m²"+"</br>"+"<br><b>" + \
        "Valeur foncière: "+"</b>"+valeurFonciere+" €"+"</br>"+"<br><b>"+"Surface: " + \
            "</b>"+surface+" m²"+"</br>"+"<br><b>"+"Type: "+"</b>"+Type+"</br>"
    folium.Marker([df["Latitude"][i], df["Longitude"][i]],
                  popup=popup, tooltip=address).add_to(cluster)
# Step 3: Heat
max_value = df['Prix metre carre'].max()
heat = plugins.HeatMap(df[["Latitude", "Longitude", "Prix metre carre"]].values,
                       min_opacity=0.2,
                       max_val=max_value,
                       radius=30, blur=20,
                       max_zoom=11)
heat.add_to(m)
folium_static(m)

# Selection Année
df_selected_data = df[(df["Annee"].isin(selected_years)) & (
    df["Type local"].isin(selected_type_local))]
st.header('Affichage de la base de données sélectionnée')
st.write('Dimension du jeu de données: ' + str(df_selected_data.shape[0]) + ' lignes et ' + str(
    df_selected_data.shape[1]) + ' colonnes.')
st.dataframe(df_selected_data.head(100))


# Nb biens vendus par an
st.header("Nombre de biens immobiliers vendus par an")
sns.set(rc={'figure.figsize': (9, 4)})
sns.set(style="dark")
sns.countplot(x="Annee", hue="Type local", data=df0)
st.pyplot()

# Création tableau de données mathématiques
st.header("Statistiques globales du prix au m² à Reims")
st.markdown("""Voici l'évolution des statistiques globales du prix/m² à Reims entre 2017 et 2020 : 
""")
dff_2017 = df0[df0["Annee"] == 2017]["Prix metre carre"].sort_values()
dff_2018 = df0[df0["Annee"] == 2018]["Prix metre carre"].sort_values()
dff_2019 = df0[df0["Annee"] == 2019]["Prix metre carre"].sort_values()
dff_2020 = df0[df0["Annee"] == 2020]["Prix metre carre"].sort_values()
stats = [[2017, dff_2017.quantile(.25), dff_2017.quantile(.5), dff_2017.quantile(.75), dff_2017.mean()],
         [2018, dff_2018.quantile(.25), dff_2018.quantile(.5),
          dff_2018.quantile(.75), dff_2018.mean()],
         [2019, dff_2019.quantile(.25), dff_2019.quantile(.5),
          dff_2019.quantile(.75), dff_2019.mean()],
         [2020, dff_2020.quantile(.25), dff_2020.quantile(.5), dff_2020.quantile(.75), dff_2020.mean()]]
df_stat = pd.DataFrame(
    stats, columns=["Annee", "Quartile 1 (€/m²)", "Mediane (€/m²)", "Quartile 3 (€/m²)", "Moyenne (€/m²)"])
df_stat = np.round(df_stat, 2)
st.dataframe(df_stat)
plt.plot(df_stat["Annee"], df_stat["Quartile 1 (€/m²)"],
         label="Quartile 1 (€/m²)")
plt.plot(df_stat["Annee"], df_stat["Mediane (€/m²)"],
         label="Mediane (€/m²)")
plt.plot(df_stat["Annee"], df_stat["Quartile 3 (€/m²)"],
         label="Quartile 3 (€/m²)")
plt.plot(df_stat["Annee"], df_stat["Moyenne (€/m²)"],
         label="Moyenne (€/m²)")
st.markdown("""Traçons maintenant ces données sur un graphe :""")
# plt.plot(x,z, marker = '+', color = 'g',label = 'exponential growth')
plt.legend()
st.pyplot()
st.markdown("""On remarque que la moyenne des valeurs de notre jeu de données est très impactée par les ventes immobilières les plus élevées, c'est pour cette raison que la médiane est dans ce cas plus pertinente. 
""")

# Répartition de la valeur foncière par année
st.header("Répartition des valeurs foncières par an")
fig = px.box(df, x="Annee", y="Valeur fonciere", hover_data=[
             'No voie', "Voie", "Code postal"], color="Type local")
# fig.show()
st.plotly_chart(fig)
# Répartition de la surface reelle bati par année
st.header("Répartition des surfaces habitables par an")
fig = px.box(df, x="Annee", y="Surface reelle bati", hover_data=[
             'No voie', "Voie", "Code postal"], color="Type local")
# fig.show()
st.plotly_chart(fig)
# Répartition de la surface reelle bati par année
st.header("Répartition du Prix du mètre carré par an")
fig = px.box(df, x="Annee", y="Prix metre carre", hover_data=[
             'No voie', "Voie", "Code postal"], color="Type local")
# fig.show()
st.plotly_chart(fig)
