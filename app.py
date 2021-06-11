# importa paquetes
'''
import streamlit as st
import pandas as pd
import numpy as np
#! pip install plotly
import plotly.express as px
import matplotlib.pyplot as plt
from pylab import rcParams
import json
#! pip install geopandas
import geopandas as gpd
import base64
import datetime as dt
from shapely.geometry import shape, GeometryCollection, Point
import folium
from folium.map import *
from folium import plugins
from folium.plugins import MeasureControl
from folium.plugins import FloatImage
from folium.plugins import MarkerCluster
from folium.plugins import HeatMap
from folium.features import DivIcon
from collections import defaultdict
from streamlit_folium import folium_static
from dateutil.relativedelta import relativedelta # to add days or years
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.arima.model import ARIMA
import plotly.graph_objects as go
'''

# definir rutas bases de datos
coord_url= 'BD/coordenadas.csv'
vic_url = 'DATA/VICTIMAS_ABR_2021.xlsx'
com_url = 'DATA/COMPARENDOS_ABR_2021.xlsx'
acc_url = 'DATA/ACCIDENTALIDAD_ABR_2021.xls'
barrio_url = 'BD/barrios.json'

# importar bases
@st.cache(persist=True)
def load_data(url):
    df = pd.read_excel(url)
    return df

# importar poligonos
@st.cache(persist=True)
def load_data1(url):
    df = gpd.read_file(url)
    return df

# importar poligonos
@st.cache(persist=True)
def load_data2(url):
    df = pd.read_csv(url)
    return df


# guardar los resultados de barrio
@st.cache(suppress_st_warning=True)
@st.cache(allow_output_mutation=True)
@st.cache(persist=True)
def aplicar_barrio(x):
    
    # encontrar barrio
    def encuentra_barrio(row):
        lat = row['Latitud']
        long = row['Longitud']
        point = Point(long, lat)                                                            
        barrio = "No encontrado"
        for feature in data.index:
            try:
                polygon = shape(data['geometry'][feature])
                if polygon.contains(point):  
                    barrio = data['NOM_BARRIO'][feature]
            except:
                barrio="No encontrado"
        return barrio
    
    coord['Barrio'] = coord.apply(encuentra_barrio, axis = 1)
    
    return coord

'''
def get_table_download_link(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
    href = f'<a href="data:file/csv;base64,{b64}" download="datos.csv">Descargar archivo csv</a>'
    return href
'''

# cargar datos 
vic = load_data(vic_url) # victimas
com = load_data(com_url) # comparendos
acc = load_data(acc_url) # accidentes
data = load_data1(barrio_url) # barrios
coord = load_data2(coord_url).dropna() # coordenadas
coord['count'] = 1



############## PEGAR PARTE 


# poner titulo e imagen
col1, col2 = st.beta_columns((1,7))
col1.write(f'<div class = "image"><img src="https://upload.wikimedia.org/wikipedia/commons/thumb/5/57/Escudo_de_La_Estrella_%28Antioquia%29.svg/50px-Escudo_de_La_Estrella_%28Antioquia%29.svg.png" alt="Simply Easy Learning" width="50"height="70"alig></div>', unsafe_allow_html=True)

st.markdown(
    """
<style>
.image{
    align-content: center;
    font-size: 50;
       }
.css-kywgdc {
    position: absolute;
    top: 0px;
    right: 0px;
    left: 0px;
    height: 0.125rem;
    background-image: linear-gradient(
90deg
, rgb(33 81 99), rgb(56 116 177));
    z-index: 1000020;
}
.fullScreenFrame > div {
    display: flex;
    justify-content: center;
}


</style>
""",
    unsafe_allow_html=True,
)

col2.title(' Informe de Tránsito - La Estrella')
st.sidebar.title('Menú Principal')


##### DESCRIPTIVO ----------------------------------------------------------

# FILTROS
st.sidebar.markdown('### Principales Indicadores')
indicador = st.sidebar.selectbox('Indicador', ['','Accidentes por zona (Top 10)',
                                               'Accidentes por gravedad',
                                               'Accidentes por clase',
                                               'Evolución accidentes por año',
                                               'Evolución accidentes por mes',
                                               'Evolución comparendos por año',
                                               'Evolución comparendos por mes'], key='1',
                            format_func=lambda x: 'Seleccione una opción' if x == '' else x)


###----------------ORGANIZAR BASES DE DATOS----------------------------------

# sacar información de la base de victimas
vic2 = vic.copy(deep = True)
vic2 = vic2.join(pd.get_dummies(vic2['GRAVEDAD']))
vic2 = vic2.join(pd.get_dummies(vic2['SEXO']))
vic2 = vic2.join(pd.get_dummies(vic2['TIPO_VICTIMA']))
vic2 = vic2.join(pd.get_dummies(vic2['CULPABLE']))
vic2['ones'] = 1
vic3 = vic2.groupby(['NRO_RADICADO'])[['h','m','F','M','0','ac','ci','co','mo','pa','pe','E','N','P','S','ones']].sum().reset_index().rename(columns = {'ones':'cant'})

# hacer unión
base = pd.merge(acc, vic3, how = 'left', on ='NRO_RADICADO')
base.iloc[:,14:] = base.iloc[:,14:].fillna(0) # llenar nulos


# diccionarios para columnas
tipo_comparendo = {0:"Anulado", 1:"Infracción", 2:"Accidente", 3:"Decomiso", 4:"Moroso", 5:"Transporte", 6:"Stricker", 7:"Ambiental", 8:"Amonestación",
                  11:"Denuncia O Pérdida", 12:"Electrónico" ,14:"Rtm"}
tipo_infractor = {1:"Conductor", 2:"Peatón", 3:"Pasajero"}
desc_zona = {1:"Parque Principal", 2:"Tablaza", 3:"Autopista", 4:"Variante", 5:"Pueblo Viejo", 6:"Moteles", 7:"Barrio Escobar", 8:"Bavaria", 9:"Chorritos",
            10:"El Dorado", 11:"Escuela De Policia", 12:"La Inmaculada 1", 13:"Cierra Morena", 14:"Ancón", 15:"Ferreria", 16:"Zancibar", 17:"Calle Quinta",
            18:"Suramérica", 19:"Calle Séptima", 20:"Bellavista", 21:"Comfama", 22:"Caquetá", 23:"San Agustín", 24:"El Pedrero", 25:"Primavera",
            26:"Sin Descripción", 27:"Salvatorianos"}
clase_vehiculo = {1:"Automóvil", 2:"Bus", 3:"Buseta", 4:"Camión", 5:"Camioneta", 6:"Campero", 7:"Microbus", 8:"Tractocamión", 11:"Maq.Agrícola",
                 12:"Maq.Industrial", 13:"Bicicleta", 14:"Motocarro", 15:"Tracción Animal", 17:"Motortriciclo", 19:"Cuatrimoto", 24:"Remolque",
                 41:"Semiremolque", 42:"Volqueta", 99:"Sin Clase"}
tipo_servicio = {0:"Desconocido", 1:"Particuar", 2:"Público", 3:"Oficial", 4:"Diplomático", 5:"Extranjero", 6:"Especial"}
desc_gravedad = {"d":"Daños", "h":"Heridos", "m":"Muertos"}
desc_area_acc = {0:"No Reportado", 1:"Urbana", 2:"Rural"}
desc_sector_acc = {1:"Residencial", 2:"Industrial", 3:"Comercial"}
desc_diseno_acc = {1:"Tramo De Vía", 2:"Intersección", 3:"Vía Peatonal", 4:"Paso Elevado", 5:"Paso Inferior", 6:"Paso A Nivel", 7:"Glorieta", 8:"Puente",
                  9:"Vía Troncal", 10:"Lote O Predio", 11:"Ciclo Ruta", 12:"Pontón", 13:"Tunel"}
desc_tiempo = {0:"No Reportado", 1:"Normal", 2:'Lluvia', 3:"Viento", 4:"Niebla", 8:"Granizo"}

#remplazar diccionarios para la base de accidentes
# crear columnas para guardar descripción
base['ID_ZONA_DESC'] = base['ID_ZONA']
base['GRAVEDAD_DESC'] = base['GRAVEDAD']
base['AREA_DESC'] = base['AREA']
base['SECTOR_DESC'] = base['SECTOR']
base['ZONA_DESC'] = base['ZONA']
base['DISENO_DESC'] = base['DISENO']
base['ESTADO_TIEMPO_DESC'] = base['ESTADO_TIEMPO']


# remplazar nuevas columnas por diccionario
base = base.replace({'ID_ZONA_DESC': desc_zona,'GRAVEDAD_DESC':desc_gravedad,'AREA_DESC':desc_area_acc,'SECTOR_DESC':desc_sector_acc,
            'ZONA_DESC':desc_zona,'DISENO_DESC':desc_diseno_acc, 'ESTADO_TIEMPO_DESC':desc_tiempo})


# cambiar nombre de columnas de victimas
base.rename(columns ={'h':'VIC_HERIDOS','m':'VIC_MUERTOS','F':'VIC_MUJERES','M':'VIC_HOMBRES','cant':'VIC_CANT'}, inplace = True)

# organizar base accidentes
df2 = base.copy(deep = True)
df2["Año"] = df2["FECHA_ACCIDENTE"].dt.year
df2["Mes"] = df2["FECHA_ACCIDENTE"].dt.strftime('%b')
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
df2['Mes'] = pd.Categorical(df2['Mes'], categories=months, ordered=True)
df2["año/mes"] =  df2["FECHA_ACCIDENTE"].dt.strftime('%Y-%m')
df2['Accidentes'] = 1

# organizar base comparendos
com_2 = com.copy(deep = True)
com_2["Año"] = com_2["FECHA"].dt.year
com_2["Accidentes"] = 1
com_2["Zona"] = com_2["ID_ZONA"]
com_2["Mes"] = com_2["FECHA"].dt.strftime('%b')
com_2['Mes'] = pd.Categorical(com_2['Mes'], categories=months, ordered=True)
com_2.replace({"Zona" : desc_zona}, inplace=True) 

###----------------------------GRAFICAS ------------------------------------
lista = sorted(list(acc['FECHA_ACCIDENTE'].dt.year.unique()), reverse = True)
lista2 = months

if indicador == 'Accidentes por zona (Top 10)': 
        
    # condicional para seleccionar todas las opciones

    Todos = st.checkbox("Seleccionar todos los años")
    if Todos:
        periodo2 = lista
    else:
        periodo2 = st.multiselect('Seleccione que años quiere ver:',lista, key='1', help = 'Seleccione una opción')
    #default = [max(lista)]

## grafica 1
    if periodo2 != []:
        df3 = df2[df2['Año'].isin(periodo2)]
        df_barrios = pd.pivot_table(
            df3,
                index = ['ID_ZONA_DESC'],
                values = 'VIC_CANT',
                aggfunc = 'sum'
                ).reset_index()
    
        df_barrios = df_barrios.sort_values(by=['VIC_CANT'],ascending=False)
        grafica = df_barrios[:10].sort_values(by=['VIC_CANT'],ascending=True)
        fig = px.bar(grafica, x="VIC_CANT", y="ID_ZONA_DESC", orientation='h')
        fig.update_layout(title_text='<b>Top 10 zonas con mayor número de víctimas<b>',title_x=0.5, xaxis_title="Cantidad", yaxis_title="Zonas")
        gr1 = fig

## grafica 3
        df_barrios = pd.pivot_table(
            df3,
                index = ['ID_ZONA_DESC'],
                values = 'Accidentes',
                aggfunc = 'sum'
                ).reset_index()
        
        df_barrios = df_barrios.sort_values(by=['Accidentes'],ascending=False)
        grafica = df_barrios[:10].sort_values(by=['Accidentes'],ascending=True)
        fig = px.bar(grafica, x="Accidentes", y="ID_ZONA_DESC", orientation='h')
        fig.update_layout(title_text='<b>Top 10 zonas con mayor número de accidentes<b>',title_x=0.5, xaxis_title="Cantidad", yaxis_title="Zonas")
        gr3 = fig

        st.plotly_chart(gr3)
        st.plotly_chart(gr1)


if indicador == 'Evolución accidentes por año':
    
    # condicional para seleccionar todas las opciones 
    Todos = st.checkbox("Seleccionar todos los meses")
    if Todos:
        periodo3 = lista2
    else:
        periodo3 = st.multiselect('Seleccione que meses quiere ver:',lista2, key='1')


# grafica 5
    if periodo3 != []:
        df3 = df2[df2['Mes'].isin(periodo3)]
        df2_anos = pd.pivot_table(
            df3,index = ['ID_ZONA_DESC', "Año"], values = 'Accidentes', aggfunc = 'sum').reset_index()
        fig = px.line(df2_anos, x="Año", y="Accidentes", color='ID_ZONA_DESC',
                      width=800, height=450)
        fig.update_traces(mode='markers+lines')
        fig.update_layout(title_text='<b>Evolución de accidentes por año en cada Zona<b>', title_x=0.5,
                          xaxis_title="Años", yaxis_title='Cantidad',
                          legend_title_text='<b>Nombre zona:<b>')
        gr5 = fig

# grafica 6
        df2_anos2 = pd.pivot_table(
        df3,
            index = ['ID_ZONA_DESC', "Año"],
            values = 'VIC_CANT',
            aggfunc = 'sum'
            ).reset_index()
        fig = px.line(df2_anos2, x="Año", y="VIC_CANT", color='ID_ZONA_DESC',
                      width=800, height=450)
        fig.update_traces(mode='markers+lines')
        fig.update_layout(title_text='<b>Evolución de víctimas por año en cada Zona<b>',title_x=0.5,
                          xaxis_title='Años', yaxis_title='Cantidad',
                          legend_title_text='<b>Nombre zona:<b>')
        gr6 = fig
        
        st.plotly_chart(gr5)
        st.plotly_chart(gr6)

if indicador == 'Evolución accidentes por mes':
    
    # condicional para seleccionar todas las opciones 
    Todos = st.checkbox("Seleccionar todos los años")
    if Todos:
        periodo2 = lista
    else:
        periodo2 = st.multiselect('Seleccione que años quiere ver:',lista, key='1')

# grafica 7
    if periodo2 != []:
        df3 = df2[df2['Año'].isin(periodo2)]
        df2_anos2 = pd.pivot_table(
            df3,
                index = ['ID_ZONA_DESC', "Mes"],
                values = 'Accidentes',
                aggfunc = 'sum'
                ).reset_index()
        fig = px.line(df2_anos2, x="Mes", y="Accidentes", color='ID_ZONA_DESC',
                      width=800, height=450)
        fig.update_traces(mode='markers+lines')
        fig.update_layout(title_text='<b>Evolución de accidentes por mes en cada Zona<b>',title_x=0.5,
                          xaxis_title='Meses', yaxis_title='Cantidad',
                          legend_title_text='<b>Nombre zona:<b>')
        gr7 = fig
    
 # grafica 8
        df3 = df2[df2['Año'].isin(periodo2)]
        df2_anos2 = pd.pivot_table(
            df3,
                index = ['ID_ZONA_DESC', "Mes"],
                values = 'VIC_CANT',
                aggfunc = 'sum'
                ).reset_index()
        fig = px.line(df2_anos2, x="Mes", y="VIC_CANT", color='ID_ZONA_DESC',
                      width=800, height=450)
        fig.update_traces(mode='markers+lines')
        fig.update_layout(title_text='<b>Evolución de víctimas por mes en cada Zona<b>',title_x=0.5,
                          xaxis_title='Meses', yaxis_title='Cantidad',
                          legend_title_text='<b>Nombre zona:<b>')
        gr8 = fig

        st.plotly_chart(gr7)
        st.plotly_chart(gr8)

if indicador == 'Accidentes por gravedad':
    
    # condicional para seleccionar todas las opciones 
    Todos = st.checkbox("Seleccionar todos los meses")
    if Todos:
        periodo3 = lista2
    else:
        periodo3 = st.multiselect('Seleccione que meses quiere ver:',lista2, key='1')
       
    if periodo3 != []: 
        df3 = df2[df2['Mes'].isin(periodo3)]
        df2_gravedad_2 = pd.pivot_table(
            df3,
            index = ['GRAVEDAD', 'Año'],
            values = ["Accidentes"],
            aggfunc = 'sum'
            ).reset_index()
        df2_gravedad_2.replace({'GRAVEDAD' : { 'd' : "Solo daños", 'h' : "Heridos", 'm' : "Muertos" }}, inplace=True)
        fig = px.line(df2_gravedad_2, x="Año", y="Accidentes", color="GRAVEDAD")
        fig.update_traces(mode='markers+lines')
        fig.update_layout(title_text='<b>Accidentes según el tipo de gravedad<b>', title_x=0.5, xaxis_title="Años",
                          yaxis_title="Cantidad", legend_title_text='<b>Gravedad:<b>')

        st.plotly_chart(fig)

if indicador == 'Accidentes por clase': 

    # condicional para seleccionar todas las opciones 
    Todos = st.checkbox("Seleccionar todos los meses")
    if Todos:
        periodo3 = lista2
    else:
        periodo3 = st.multiselect('Seleccione que meses quiere ver:',lista2, key='1')
       
    if periodo3 != []: 
        df3 = df2[df2['Mes'].isin(periodo3)]
        df_tacc2 = pd.pivot_table(
            df3,
                index = ['DESC_CLASE_ACCIDENTE', "Año"],
                values = 'Accidentes',
                aggfunc = 'sum'
                ).reset_index()
    
        fig = px.line(df_tacc2, x="Año", y="Accidentes", color='DESC_CLASE_ACCIDENTE',
                      width=800, height=450)
        fig.update_traces(mode='markers+lines')
        fig.update_layout(title_text='<b>Clase del accidente por año<b>', title_x=0.5, xaxis_title="Años", yaxis_title="Cantidad"
                          , legend_title_text='<b>Clase:<b>')

        st.plotly_chart(fig)

if indicador == 'Evolución comparendos por año': 

    # condicional para seleccionar todas las opciones 
    Todos = st.checkbox("Seleccionar todos los meses")
    if Todos:
        periodo3 = lista2
    else:
        periodo3 = st.multiselect('Seleccione que meses quiere ver:',lista2, key='1')
       
    if periodo3 != []: 
        df3 = com_2[com_2['Mes'].isin(periodo3)]
        df_com = pd.pivot_table(
        df3,
            index = ['Año'],
            values = ["Accidentes"],
            aggfunc = 'sum'
            ).reset_index()
        fig = px.line(df_com, x="Año", y="Accidentes")
        fig.update_traces(mode='markers+lines')
        fig.update_layout(title_text='<b>Comparendos por año<b>', xaxis_title="Años",title_x=0.5, yaxis_title="Cantidad")
        st.plotly_chart(fig)
        
if indicador == 'Evolución comparendos por mes': 

    # condicional para seleccionar todas las opciones 
    Todos = st.checkbox("Seleccionar todos los años")
    if Todos:
        periodo2 = lista
    else:
        periodo2 = st.multiselect('Seleccione que años quiere ver:',lista, key='1')
       
    if periodo2 != []: 
        df3 = com_2[com_2['Año'].isin(periodo2)]
        df_com = pd.pivot_table(
        df3,
            index = ['Mes'],
            values = ["Accidentes"],
            aggfunc = 'sum'
            ).reset_index()
        fig = px.line(df_com, x="Mes", y="Accidentes")
        fig.update_traces(mode='markers+lines')
        fig.update_layout(title_text='<b>Evolución de comparendos por mes<b>', xaxis_title="Meses", title_x=0.5, yaxis_title="Cantidad")
        st.plotly_chart(fig)
        
##### MAPAS ----------------------------------------------------------------
st.sidebar.markdown('### Mapas')

# Seleccionar rango de fechas
date = st.sidebar.date_input("Seleccione fechas", [])


# aplicar función
x = ''
coord = aplicar_barrio(x)
coord.rename(columns={"Nro Radicado": "NRO_RADICADO"},inplace=True) # renombrar columnas
coord2=pd.merge(coord,acc,on='NRO_RADICADO',how='left')
coord2['FECHA'] = coord2['FECHA_ACCIDENTE'].dt.date

# Coordenadas por fecha


try:
   if date[0] is not None and date[1] is not None:
      coord2=coord2[(coord2['FECHA']>=date[0]) & (coord2['FECHA']<=date[1])]
except:
   st.write('')

# agrupar por numero de barrios
porcentajes = coord2.groupby(['Barrio'])[['Direcciones']].count().reset_index() # Groupby por barrio
porcentajes = porcentajes[['Barrio','Direcciones']] # seleccionar barrio y direcciones
porcentajes['%'] = round((porcentajes['Direcciones'] / porcentajes['Direcciones'].sum()*100),2) # % de direcciones encontradas por barrio
porcentajes.rename(columns={"Barrio": "NOM_BARRIO"},inplace=True) # renombrar columnas

# hacer merge entre porcentaje y datos originales
data=pd.merge(data,porcentajes,on='NOM_BARRIO',how='left')



# Seleccionar poligonos
if st.sidebar.checkbox('Mapa de poligonos', False, key='1'):
  
# MAPA DE POLIGONOS
   m = folium.Map(location=[6.140371544959512 , -75.6355338295312], tiles='openstreetmap', control_scale=True, zoom_start=14)

# Crear coropletas
   folium.Choropleth(
           geo_data=data,
           name='Choropleth',
           data=data,
           columns=['NOM_BARRIO','%'],
           key_on="feature.properties.NOM_BARRIO",
           fill_color='YlOrRd',
           legend_name='Info'
          ).add_to(m)
   
   style_function = lambda x: {'fillColor': '#ffffff', 
                            'color':'#000000', 
                            'fillOpacity': 0.1, 
                            'weight': 0.1}

   highlight_function = lambda x: {'fillColor': '#000000', 
                                'color':'#000000', 
                                'fillOpacity': 0.50, 
                                'weight': 0.1}

# Crear etiquetas
   etiquetas = folium.features.GeoJson(
    data,
    style_function=style_function, 
    control=False,
    highlight_function=highlight_function, 
    tooltip=folium.features.GeoJsonTooltip(
        fields=['NOM_BARRIO','%','Direcciones'],
        aliases=['Barrio:','Porcentaje (%):','Nro Accidentes'],
        style=("background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;") 
    )
   ).add_to(m)

# Mantener las etiquetas al frente
   m.keep_in_front(etiquetas)

# Minimizar las capas
   folium.LayerControl('topright', collapsed=True).add_to(m)

# Pantalla completa
   folium.plugins.Fullscreen().add_to(m)

# Agregar herramientas para dibujar
   draw = plugins.Draw(export=True)
   draw.add_to(m)

# Agregar herramienta para medir áreas
   m.add_child(MeasureControl(active_color = 'red', completed_color='red', primary_length_unit = 'kilometers'))

# Agregar el logo de La Estrella
   url = (
    "https://upload.wikimedia.org/wikipedia/commons/thumb/5/57/Escudo_de_La_Estrella_%28Antioquia%29.svg/50px-Escudo_de_La_Estrella_%28Antioquia%29.svg.png"
   )
   FloatImage(url, bottom=5, left=90).add_to(m)
   folium_static(m)

### Selector mapa de calor
if st.sidebar.checkbox('Mapa de calor', False, key='1'):
    
    # MAPA DE CALOR
    m = folium.Map(location=[6.140371544959512 , -75.6355338295312], tiles='openstreetmap', control_scale=True, zoom_start=14)

# Crear etiquetas
    style_function = lambda x: {'fillColor': '#ffffff', 
                            'color':'#000000', 
                            'fillOpacity': 0.1, 
                            'weight': 0.1}

    highlight_function = lambda x: {'fillColor': '#000000', 
                                'color':'#000000', 
                                'fillOpacity': 0.50, 
                                'weight': 0.1}

    etiquetas = folium.features.GeoJson(
    data,
    style_function=style_function, 
    control=False,
    highlight_function=highlight_function, 
    tooltip=folium.features.GeoJsonTooltip(
        fields=['NOM_BARRIO','%'],
        aliases=['Barrio:','Porcentaje (%):'],
        style=("background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;") 
    )
    ).add_to(m)

    # Crear heatmap

    HeatMap(data=coord2[['Latitud', 'Longitud', 'count']].groupby(['Latitud', 'Longitud']).sum().reset_index().values.tolist(), name='Mapa de calor', radius=15, max_zoom=10, min_opacity=0.4, blur=15,gradient = None).add_to(folium.FeatureGroup(name='Heat Map').add_to(m))

    # Mantener las etiquetas al frente
    m.keep_in_front(etiquetas)

    # Minimizar las capas
    folium.LayerControl('topright', collapsed=True).add_to(m)

    # Pantalla completa
    folium.plugins.Fullscreen().add_to(m)

    # Agregar herramientas para dibujar
    draw = plugins.Draw(export=True)
    draw.add_to(m)

    # Agregar herramienta para medir áreas
    m.add_child(MeasureControl(active_color = 'red', completed_color='red', primary_length_unit = 'kilometers'))

    folium_static(m)

### Selector Mapa de puntos
if st.sidebar.checkbox('Mapa de puntos', False, key='1'):

   m = folium.Map(location=[6.140371544959512 , -75.6355338295312], tiles='openstreetmap', control_scale=True, zoom_start=14)

   for i in range(len(coord2)):
       folium.Circle(
           location=[coord2.iloc[i]['Latitud'], coord2.iloc[i]['Longitud']],
           radius=1,
       ).add_to(m)

   # MarkerCluster
   locations = list(zip(coord2.Latitud, coord2.Longitud))
   icons = [folium.Icon(icon="car", prefix="fa") for _ in range(len(locations))]

   cluster = MarkerCluster(locations=locations, icons=icons, name='MarkerCluster', maxClusterRadius = 150, showCoverageOnHover=True)
   m.add_child(cluster)

   # Minimizar las capas
   folium.LayerControl('topright', collapsed=True).add_to(m)

   # Pantalla completa
   folium.plugins.Fullscreen().add_to(m)

   # Agregar herramientas para dibujar
   draw = plugins.Draw(export=True)
   draw.add_to(m)

   # Agregar herramienta para medir áreas
   m.add_child(MeasureControl(active_color = 'red', completed_color='red', primary_length_unit = 'kilometers'))

   folium_static(m)


##### PREDICCIONES ----------------------------------------------------------


### FILTROS
st.sidebar.markdown('### Predicciones')
tema = st.sidebar.selectbox('Tema', ['','Accidentes', 'Comparendos'], key='1',
                            format_func=lambda x: 'Seleccione una opción' if x == '' else x)
periodo = st.sidebar.selectbox('Periodo de tiempo', ['','Día','Semana','Mes'], key='1',
                               format_func=lambda x: 'Seleccione una opción' if x == '' else x)
datos = st.sidebar.checkbox('Ver Datos', False, key='4')


### ACCIDENTES

###----------------ORGANIZAR BASES DE DATOS----------------------------------

# organizar base de datos
acc2 = acc.copy(deep = True)
acc2.columns = map(str.lower, acc2.columns) # volver columnas minuscula
acc2['fecha_accidente'] = pd.to_datetime(acc2['fecha_accidente']) # convertir columna fecha en tipo fecha
acc2['fecha'] = acc2['fecha_accidente'].dt.date
acc2['fecha'] = pd.to_datetime(acc2['fecha']) # convertir columna fecha en tipo fecha
fecha = pd.DataFrame(pd.date_range(start=acc2['fecha'].min(), end= acc2['fecha'].max())) # definir todas las fechas
acc2 = pd.merge(acc2, fecha, how = 'right', left_on = 'fecha', right_on = 0).fillna(0).drop(0, axis = 1) # hacer union y llenar los valores nulos


# construir bodega de datos a nivel de fecha: día, semana, mes
acc_dia = acc2.groupby(['fecha'])[['nro_radicado']].count().reset_index().rename(columns = {'nro_radicado':'acc_total'})
acc_dia['año'] = acc_dia['fecha'].dt.year
acc_sem = acc_dia[['fecha','acc_total']].resample('W', on='fecha').sum().reset_index()
acc_mes = acc_dia[['fecha','acc_total']].resample('M', on='fecha').sum().reset_index()


# aplicar formato de fecha
acc_dia['fecha'] = acc_dia['fecha'].apply(lambda t: t.strftime("%Y-%m-%d"))
acc_sem['fecha'] = acc_sem['fecha'].apply(lambda t: t.strftime("%Y-%m-%d"))
acc_mes['fecha'] = acc_mes['fecha'].apply(lambda t: t.strftime("%Y-%m-%d"))


###---------------------PRONÓSTICO DÍA ACCIDENTES----------------------------
@st.cache(allow_output_mutation=True)
@st.cache(persist=True)
def func_acc_dia(x):
# 1. definir base
    df_acc = acc_dia[acc_dia['año'].isin([2020,2021])].reset_index().drop('index', axis = 1) # seleccionar unicamente los años 2020 y 2021
    time= list(df_acc.index) # definir el numero de periodos
    series = list(df_acc['acc_total']) # definir el número de accidentes


# 2. dividir muestra
    split_time = len(time) # quitar los ultimos 3 días
    x_train = series[:split_time] # dividir la serie


###--------------------------- GRAFICAS -------------------------------------


# serie de datos
    df = df_acc[['fecha','acc_total']]
    df.set_index('fecha',inplace=True)
    df.index=pd.to_datetime(df.index)
    fig = px.line(df, x=df.index, y="acc_total", title='<b>Evolución de Accidentes por día<b>',
                  width=750, height=450)
    fig.update_traces(line=dict(width=1.5))
    fig.update_layout(
        xaxis_title="Fecha",
        yaxis_title="Accidentes",
        title_x=0.5,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        template = 'simple_white' )
    a = fig

# componente de tendencia
    result=seasonal_decompose(df['acc_total'], model='additive', period=30)
    df = pd.DataFrame(result.trend)
    fig = px.line(df, x=df.index, y='trend', title='<b>Tendencia de Accidentes por día<b>',
                  width=750, height=450)
    fig.update_traces(line=dict(width=1.5))
    fig.update_layout(
        xaxis_title="Fecha",
        yaxis_title="Accidentes",
        title_x=0.5,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        template = 'simple_white' )
    b = fig
### --------------------------- MODELO --------------------------------------


# ARMA
# modelo
    p = 7
    q = 7
    s = 0
    model = ARIMA(x_train, order=(p,s,q), trend = 'c')
    model_fit = model.fit()


# predecir
    dias = 30
    yhat = model_fit.predict(min(time), max(time)+dias)


# crear tabla con resultados
    df_acc['fecha'] = pd.to_datetime(df_acc['fecha'])
    tb_dia = pd.DataFrame(pd.date_range(start=df_acc['fecha'].min(), end= df_acc['fecha'].max() + dt.timedelta(days=30))).rename(columns = {0:'fecha'})
    tb_dia['Real'] = series + [np.nan]*dias
    tb_dia['Pronóstico'] =  yhat


# graficar
    fig = px.line(tb_dia, x='fecha', y=['Real','Pronóstico'], title='<b>Predicción de Accidentes por día (30 días)<b>',
                  width=800, height=450) #,color_discrete_map={'Real':'rgb(128,177,211)','Pronóstico':'rgb(253,180,98)'})
    fig.update_traces(line=dict(width=1.5))
    fig.add_vline(x=df_acc['fecha'][df_acc['fecha'].shape[0]-1], line_width=3, line_dash="dot", line_color = 'black') #line_color="#620042")
    fig.update_layout(
        xaxis_title="Fecha",
        yaxis_title="Accidentes",
        title_x=0.5,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        template = 'simple_white',
        legend_title_text='')
    c = fig


# redondear accidentes 
    tb_dia['Pronóstico'] = tb_dia['Pronóstico'].apply(lambda x: round(x,0))
    tb_dia['Real'] = tb_dia['Real'].fillna(0).astype('int')
    tb_dia['Pronóstico'] = tb_dia['Pronóstico'].fillna(0).astype('int')
    tb_dia.rename(columns = {'fecha':'Fecha'}, inplace = True)
    d = tb_dia

    return a, b, c, d

a, b, c, d = func_acc_dia(x)

if tema == 'Accidentes' and periodo == 'Día' and datos == True :
    st.plotly_chart(a)
    st.plotly_chart(b)
    st.plotly_chart(c)
    
    
    fig = go.Figure(data=[go.Table(
    header=dict(values=list(d.columns),
                fill_color='lightgrey',
                align='center',
                line_color='darkslategray'),
    cells=dict(values=[d.Fecha.dt.date,
                       d.Real, d.Pronóstico],
               fill_color='white',
               align='center',
               line_color='lightgrey'))
        
])
    fig.update_layout(
    title_text="<b>Tabla con Predicciones <b>")
    st.write(fig)
    
    #st.markdown(get_table_download_link(d), unsafe_allow_html=True)
if tema == 'Accidentes' and periodo == 'Día' and datos == False :
    st.plotly_chart(a)
    st.plotly_chart(b)
    st.plotly_chart(c)


###---------------------PRONÓSTICO SEMANA ACCIDENTES-------------------------


@st.cache(allow_output_mutation=True)
@st.cache(persist=True)
def func_acc_sem(x):
# 1. definir base
    time= list(acc_sem.index) # definir el numero de periodos
    series = list(acc_sem['acc_total']) # definir el número de accidentes

# 2. dividir muestra
    split_time = len(time) - 1 # quitar la ultima sem
    x_train = series[:split_time] # dividir la serie

###--------------------------- GRAFICAS -------------------------------------


# serie de datos
    df = acc_sem[['fecha','acc_total']]
    df.set_index('fecha',inplace=True)
    df.index=pd.to_datetime(df.index)
    fig = px.line(df, x=df.index, y="acc_total", title='<b>Evolución de Accidentes por semana<b>',
                  width=750, height=450)
    fig.update_traces(line=dict(width=1.5))
    fig.update_layout(
        xaxis_title="Fecha",
        yaxis_title="Accidentes",
        title_x=0.5,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        template = 'simple_white' )
    e = fig

# componente de tendencia
    result=seasonal_decompose(df['acc_total'], model='additive', period=32)
    df = pd.DataFrame(result.trend)
    fig = px.line(df, x=df.index, y="trend", title='<b>Tendencia de Accidentes por semana<b>',
                  width=750, height=450)
    fig.update_traces(line=dict(width=1.5))
    fig.update_layout(
        xaxis_title="Fecha",
        yaxis_title="Accidentes",
        title_x=0.5,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        template = 'simple_white' )
    f = fig

### --------------------------- MODELO --------------------------------------

# ARMA
# modelo
    p = 24
    q = 14
    s = 0
    model = ARIMA(x_train, order=(p,s,q), trend = 'ct')
    model_fit = model.fit()

# predecir
    sem = 12
    yhat = model_fit.predict(min(time), max(time)+sem)

# crear tabla con resultados
    acc_sem['fecha'] = pd.to_datetime(acc_sem['fecha'])
    tb_sem = pd.DataFrame(pd.date_range(start=acc_sem['fecha'].min(), end= acc_sem['fecha'].max() + dt.timedelta(days=sem*7), freq='W')).rename(columns = {0:'fecha'})
    tb_sem['Real'] = series + [np.nan]*sem
    tb_sem['Pronóstico'] =  yhat

# graficar
    fig = px.line(tb_sem, x='fecha', y=['Real','Pronóstico'], title='<b>Predicción de Accidentes por semana (12 semanas)<b>',
                  width=750, height=450)
    fig.update_traces(line=dict(width=1.5))
    fig.add_vline(x=acc_sem['fecha'][acc_sem['fecha'].shape[0]-1], line_width=3, line_dash="dot", line_color = 'black') #line_color="#620042")
    fig.update_layout(
        xaxis_title="Fecha",
        yaxis_title="Accidentes",
        title_x=0.5,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        template = 'simple_white',
        legend_title_text='')
    g = fig

# redondear accidentes
    tb_sem['Pronóstico'] = tb_sem['Pronóstico'].apply(lambda x: round(x,0))
    tb_sem['Real'] = tb_sem['Real'].fillna(0).astype('int')
    tb_sem['Pronóstico'] = tb_sem['Pronóstico'].fillna(0).astype('int')
    tb_sem.rename(columns = {'fecha':'Fecha'}, inplace = True)
    h = tb_sem
    
    return e, f, g, h

e, f, g, h = func_acc_sem(x)

if tema == 'Accidentes' and periodo == 'Semana' and datos == True :   
    st.plotly_chart(e)
    st.plotly_chart(f)
    st.plotly_chart(g)
    
    
    fig = go.Figure(data=[go.Table(
    header=dict(values=list(h.columns),
                fill_color='lightgrey',
                align='center',
                line_color='darkslategray'),
    cells=dict(values=[h.Fecha.dt.date,
                       h.Real, h.Pronóstico],
               fill_color='white',
               align='center',
               line_color='lightgrey'))
        
])
    fig.update_layout(
    title_text="<b>Tabla con Predicciones <b>")
    st.write(fig)
    
    #st.markdown(get_table_download_link(h), unsafe_allow_html=True)
if tema == 'Accidentes' and periodo == 'Semana' and datos == False :   
    st.plotly_chart(e)
    st.plotly_chart(f)
    st.plotly_chart(g)


###---------------------PRONÓSTICO MES ACCIDENTES----------------------------

@st.cache(allow_output_mutation=True)
@st.cache(persist=True)
def func_acc_mes(x): 
# 1. definir base
    time= list(acc_mes.index) # definir el numero de periodos
    series = list(acc_mes['acc_total']) # definir el número de accidentes

# 2. dividir muestra
    split_time = len(time) - 1 # quitar el ultimo mes
    x_train = series[:split_time] # dividir la serie

###--------------------------- GRAFICAS -------------------------------------

# serie de datos
    df = acc_mes[['fecha','acc_total']]
    df.set_index('fecha',inplace=True)
    df.index=pd.to_datetime(df.index)
    fig = px.line(df, x=df.index, y="acc_total", title='<b>Evolución de Accidentes por mes<b>',
                  width=750, height=450)
    fig.update_traces(line=dict(width=1.5))
    fig.update_layout(
        xaxis_title="Fecha",
        yaxis_title="Accidentes",
        title_x=0.5,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        template = 'simple_white' )
    i = fig

# componente de tendencia
    result=seasonal_decompose(df['acc_total'], model='additive', period=12)
    df = pd.DataFrame(result.trend)
    fig = px.line(df, x=df.index, y="trend", title='<b>Tendencia de Accidentes por mes<b>',
                  width=750, height=450)
    fig.update_traces(line=dict(width=1.5))
    fig.update_layout(
        xaxis_title="Fecha",
        yaxis_title="Accidentes",
        title_x=0.5,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        template = 'simple_white' )
    j = fig
### --------------------------- MODELO --------------------------------------

# ARMA
# modelo
    p = 6
    q = 2
    s = 0
    model = ARIMA(x_train, order=(p,s,q), trend = 'ct')
    model_fit = model.fit()
    
# predecir
    mes = 12
    yhat = model_fit.predict(min(time), max(time)+mes)

# crear tabla con resultados
    acc_mes['fecha'] = pd.to_datetime(acc_mes['fecha'])
    tb_mes = pd.DataFrame(pd.date_range(start=acc_mes['fecha'].min(), end= acc_mes['fecha'].max() + dt.timedelta(days=mes*31), freq='M')).rename(columns = {0:'fecha'})
    tb_mes['Real'] = series[:-1] + [np.nan]*(mes+1)
    tb_mes['Pronóstico'] =  yhat

# graficar
    fig = px.line(tb_mes, x='fecha', y=['Real','Pronóstico'], title='<b>Predicción de Accidentes por mes (12 meses)<b>',
                  width=750, height=450)
    fig.update_traces(line=dict(width=1.5))
    fig.add_vline(x=acc_mes['fecha'][acc_mes['fecha'].shape[0]-2], line_width=3, line_dash="dot", line_color = 'black') #line_color="#620042")
    fig.update_layout(
        xaxis_title="Fecha",
        yaxis_title="Accidentes",
        title_x=0.5,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        template = 'simple_white',
        legend_title_text='')
    k = fig

# redondear accidentes
    tb_mes['Pronóstico'] = tb_mes['Pronóstico'].apply(lambda x: round(x,0))
    tb_mes['Real'] = tb_mes['Real'].fillna(0).astype('int')
    tb_mes['Pronóstico'] = tb_mes['Pronóstico'].fillna(0).astype('int')
    tb_mes.rename(columns = {'fecha':'Fecha'}, inplace = True)
    l = tb_mes
    
    return i, j, k, l

# aplicar función
i, j, k, l = func_acc_mes(x)

if tema == 'Accidentes' and periodo == 'Mes' and datos == True :   
    st.plotly_chart(i)
    st.plotly_chart(j)
    st.plotly_chart(k)
    
    
    fig = go.Figure(data=[go.Table(
    header=dict(values=list(l.columns),
                fill_color='lightgrey',
                align='center',
                line_color='darkslategray'),
    cells=dict(values=[l.Fecha.dt.date,
                       l.Real, l.Pronóstico],
               fill_color='white',
               align='center',
               line_color='lightgrey'))
        
])
    fig.update_layout(
    title_text="<b>Tabla con Predicciones <b>")
    st.write(fig)
    
    #st.markdown(get_table_download_link(l), unsafe_allow_html=True)
if tema == 'Accidentes' and periodo == 'Mes' and datos == False :   
    st.plotly_chart(i)
    st.plotly_chart(j)
    st.plotly_chart(k)


#### COMPARENDOS -------------------------------------------------------------

###----------------ORGANIZAR BASES DE DATOS----------------------------------

# organizar base de datos
com2 = com.copy(deep = True)
com2.columns = map(str.lower, com2.columns) # volver columnas minuscula
com2['fecha'] = pd.to_datetime(com2['fecha']) # convertir columna fecha en tipo fecha
com2['fecha'] = com2['fecha'].dt.date
com2['fecha'] = pd.to_datetime(com2['fecha']) # convertir columna fecha en tipo fecha
fecha = pd.DataFrame(pd.date_range(start=com2['fecha'].min(), end= com2['fecha'].max())) # definir todas las fechas
com2 = pd.merge(com2, fecha, how = 'right', left_on = 'fecha', right_on = 0).fillna(0).drop(0, axis = 1) # hacer union y llenar los valores nulos

# construir bodega de datos a nivel de fecha: día, semana, mes
com_dia = com2.groupby(['fecha'])[['nro_comparendo']].count().reset_index().rename(columns = {'nro_comparendo':'com_total'})
com_dia['año'] = com_dia['fecha'].dt.year
com_sem = com_dia[['fecha','com_total']].resample('W', on='fecha').sum().reset_index()
com_mes = com_dia[['fecha','com_total']].resample('M', on='fecha').sum().reset_index()

# aplicar formato de fecha
com_dia['fecha'] = com_dia['fecha'].apply(lambda t: t.strftime("%Y-%m-%d"))
com_sem['fecha'] = com_sem['fecha'].apply(lambda t: t.strftime("%Y-%m-%d"))
com_mes['fecha'] = com_mes['fecha'].apply(lambda t: t.strftime("%Y-%m-%d"))


###---------------------PRONÓSTICO DÍA COMPARENDOS----------------------------

@st.cache(allow_output_mutation=True)
@st.cache(persist=True)
def func_com_dia(x):
# 1. definir base
    df_com = com_dia[com_dia['año'].isin([2020,2021])].reset_index().drop('index', axis = 1) # seleccionar unicamente los años 2020 y 2021
    time= list(df_com.index) # definir el numero de periodos
    series = list(df_com['com_total']) # definir el número de accidentes

# 2. dividir muestra
    split_time = len(time) - 3 # quitar los ultimos 3 días
    x_train = series[:split_time] # dividir la serie

###--------------------------- GRAFICAS -------------------------------------

# serie de datos
    df = df_com[['fecha','com_total']]
    df.set_index('fecha',inplace=True)
    df.index=pd.to_datetime(df.index)
    fig = px.line(df, x=df.index, y="com_total", title='<b>Evolución de Comparendos por día<b>',
                  width=750, height=450)
    fig.update_traces(line=dict(width=1.5))
    fig.update_layout(
        xaxis_title="Fecha",
        yaxis_title="Comparendos",
        title_x=0.5,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        template = 'simple_white' )
    m = fig

# componente de tendencia
    result=seasonal_decompose(df['com_total'], model='additive', period=30)
    df = pd.DataFrame(result.trend)
    fig = px.line(df, x=df.index, y="trend", title='<b>Tendencia de Comparendos por día<b>',
                  width=750, height=450)
    fig.update_traces(line=dict(width=1.5))
    fig.update_layout(
        xaxis_title="Fecha",
        yaxis_title="Comparendos",
        title_x=0.5,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        template = 'simple_white' )
    n = fig

### --------------------------- MODELO --------------------------------------

# ARMA
# modelo
    p = 1
    q = 2
    s = 0
    model = ARIMA(x_train, order=(p,s,q), trend = 'c')
    model_fit = model.fit()
    

# predecir
    dias = 30
    yhat = model_fit.predict(min(time), max(time)+dias)

# crear tabla con resultados
    df_com['fecha'] = pd.to_datetime(df_com['fecha'])
    tb_dia = pd.DataFrame(pd.date_range(start=df_com['fecha'].min(), end= df_com['fecha'].max() + dt.timedelta(days=30))).rename(columns = {0:'fecha'})
    tb_dia['Real'] = series + [np.nan]*dias
    tb_dia['Pronóstico'] =  yhat
    
    # graficar
    fig = px.line(tb_dia, x='fecha', y=['Real','Pronóstico'], title='<b>Predicción de Comparendos por día (30 días)<b>',
                  width=750, height=450)
    fig.update_traces(line=dict(width=1.5))
    fig.add_vline(x=df_com['fecha'][df_com['fecha'].shape[0]-1], line_width=3, line_dash="dot", line_color = 'black') #line_color="#620042")
    fig.update_layout(
        xaxis_title="Fecha",
        yaxis_title="Comparendos",
        title_x=0.5,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        template = 'simple_white',
        legend_title_text='')
    o = fig
        
    # redondear accidentes
    tb_dia['Pronóstico'] = tb_dia['Pronóstico'].apply(lambda x: round(x,0))
    tb_dia['Real'] = tb_dia['Real'].fillna(0).astype('int')
    tb_dia['Pronóstico'] = tb_dia['Pronóstico'].fillna(0).astype('int')
    tb_dia.rename(columns = {'fecha':'Fecha'}, inplace = True)
    p = tb_dia
        
    return m, n, o, p

# aplicar función
m, n, o, p = func_com_dia(x)

if tema == 'Comparendos' and periodo == 'Día' and datos == True :   
    st.plotly_chart(m)
    st.plotly_chart(n)
    st.plotly_chart(o)
    
    fig = go.Figure(data=[go.Table(
    header=dict(values=list(p.columns),
                fill_color='lightgrey',
                align='center',
                line_color='darkslategray'),
    cells=dict(values=[p.Fecha.dt.date,
                       p.Real, p.Pronóstico],
               fill_color='white',
               align='center',
               line_color='lightgrey'))
        
])
    fig.update_layout(
    title_text="<b>Tabla con Predicciones <b>")
    st.write(fig)
    
    #st.markdown(get_table_download_link(p), unsafe_allow_html=True)
if tema == 'Comparendos' and periodo == 'Día' and datos == False :   
    st.plotly_chart(m)
    st.plotly_chart(n)
    st.plotly_chart(o)
###---------------------PRONÓSTICO SEMANA COMPARENDOS-------------------------


@st.cache(allow_output_mutation=True)
@st.cache(persist=True)
def func_com_sem(x):
# 1. definir base
    time= list(com_sem.index) # definir el numero de periodos
    series = list(com_sem['com_total']) # definir el número de accidentes

# 2. dividir muestra
    split_time = len(time) - 1 # quitar la ultima sem
    x_train = series[:split_time] # dividir la serie

###--------------------------- GRAFICAS -------------------------------------


# serie de datos
    df = com_sem[['fecha','com_total']]
    df.set_index('fecha',inplace=True)
    df.index=pd.to_datetime(df.index)
    fig = px.line(df, x=df.index, y="com_total", title='<b>Evolución de Comparendos por semana<b>',
                  width=750, height=450)
    fig.update_traces(line=dict(width=1.5))
    fig.update_layout(
        xaxis_title="Fecha",
        yaxis_title="Comparendos",
        title_x=0.5,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        template = 'simple_white' )
    u = fig
    

# componente de tendencia
    result=seasonal_decompose(df['com_total'], model='additive', period=32)
    df = pd.DataFrame(result.trend)
    fig = px.line(df, x=df.index, y="trend", title='<b>Tendencia de Comparendos por semana<b>',
                  width=750, height=450)
    fig.update_traces(line=dict(width=1.5))
    fig.update_layout(
        xaxis_title="Fecha",
        yaxis_title="Comparendos",
        title_x=0.5,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        template = 'simple_white' )
    r = fig
    
    
### --------------------------- MODELO --------------------------------------

# ARMA
# modelo
    p = 25
    q = 2
    s = 0
    model = ARIMA(x_train, order=(p,s,q), trend = 'ct')
    model_fit = model.fit()

# predecir
    sem = 12
    yhat = model_fit.predict(min(time), max(time)+sem)

# crear tabla con resultados
    com_sem['fecha'] = pd.to_datetime(com_sem['fecha'])
    tb_sem = pd.DataFrame(pd.date_range(start=com_sem['fecha'].min(), end= com_sem['fecha'].max() + dt.timedelta(days=sem*7), freq='W')).rename(columns = {0:'fecha'})
    tb_sem['Real'] = series + [np.nan]*sem
    tb_sem['Pronóstico'] =  yhat

# graficar
    fig = px.line(tb_sem, x='fecha', y=['Real','Pronóstico'], title='<b>Predicción de Comparendos por semana (12 semanas)<b>',
                  width=750, height=450)
    fig.update_traces(line=dict(width=1.5))
    fig.add_vline(x=com_sem['fecha'][com_sem['fecha'].shape[0]-1], line_width=3, line_dash="dot", line_color = 'black') #line_color="#620042")
    fig.update_layout(
        xaxis_title="Fecha",
        yaxis_title="Comparendos",
        title_x=0.5,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        template = 'simple_white',
        legend_title_text='')
    s = fig

# redondear accidentes
    tb_sem['Pronóstico'] = tb_sem['Pronóstico'].apply(lambda x: round(x,0))
    tb_sem['Real'] = tb_sem['Real'].fillna(0).astype('int')
    tb_sem['Pronóstico'] = tb_sem['Pronóstico'].fillna(0).astype('int')
    tb_sem.rename(columns = {'fecha':'Fecha'}, inplace = True)
    t = tb_sem
        
    return u, r, s, t

# aplicar función
u, r, s, t = func_com_sem(x)

if tema == 'Comparendos' and periodo == 'Semana' and datos == True :   
    st.plotly_chart(u)
    st.plotly_chart(r)
    st.plotly_chart(s)
    
    fig = go.Figure(data=[go.Table(
    header=dict(values=list(t.columns),
                fill_color='lightgrey',
                align='center',
                line_color='darkslategray'),
    cells=dict(values=[t.Fecha.dt.date,
                       t.Real, t.Pronóstico],
               fill_color='white',
               align='center',
               line_color='lightgrey'))
        
])
    fig.update_layout(
    title_text="<b>Tabla con Predicciones <b>")
    st.write(fig)
    
    #st.markdown(get_table_download_link(t), unsafe_allow_html=True)
if tema == 'Comparendos' and periodo == 'Semana' and datos == False :   
    st.plotly_chart(u)
    st.plotly_chart(r)
    st.plotly_chart(s)

###---------------------PRONÓSTICO MES COMPARENDOS----------------------------

@st.cache(allow_output_mutation=True)
@st.cache(persist=True)
def func_com_mes(x):
    
# 1. definir base
    time= list(com_mes.index) # definir el numero de periodos
    series = list(com_mes['com_total']) # definir el número de accidentes
    
# 2. dividir muestra
    split_time = len(time) - 1 # quitar el ultimo mes
    x_train = series[:split_time] # dividir la serie

###--------------------------- GRAFICAS -------------------------------------

# definir los datos
    df = com_mes[['fecha','com_total']]

# grafica de serie
    df.set_index('fecha',inplace=True)
    df.index=pd.to_datetime(df.index)
    fig = px.line(df, x=df.index, y="com_total", title='<b>Evolución de Comparendos por mes<b>',
                  width=750, height=450)
    fig.update_traces(line=dict(width=1.5))
    fig.update_layout(
        xaxis_title="Fecha",
        yaxis_title="Comparendos",
        title_x=0.5,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        template = 'simple_white' )
    v = fig

# componente de tendencia
    result=seasonal_decompose(df['com_total'], model='additive', period=12)
    df = pd.DataFrame(result.trend)
    fig = px.line(df, x=df.index, y="trend", title='<b>Tendencia de Comparendos por mes<b>',
                  width=750, height=450)
    fig.update_traces(line=dict(width=1.5))
    fig.update_layout(
        xaxis_title="Fecha",
        yaxis_title="Comparendos",
        title_x=0.5,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        template = 'simple_white',
        legend_title_text='')
    w = fig

### --------------------------- MODELO --------------------------------------

# ARMA
# modelo
    p = 2
    q = 2
    s = 0
    model = ARIMA(x_train, order=(p,s,q), trend = 'ct')
    model_fit = model.fit()

# predecir
    mes = 12
    yhat = model_fit.predict(min(time), max(time)+mes)

# crear tabla con resultados
    com_mes['fecha'] = pd.to_datetime(com_mes['fecha'])
    tb_mes = pd.DataFrame(pd.date_range(start=com_mes['fecha'].min(), end= com_mes['fecha'].max() + dt.timedelta(days=mes*31), freq='M')).rename(columns = {0:'fecha'})
    tb_mes['Real'] = series[:-1] + [np.nan]*(mes+1)
    tb_mes['Pronóstico'] =  yhat

# graficar
    fig = px.line(tb_mes, x='fecha', y=['Real','Pronóstico'], title='<b>Predicción de Comparendos por mes (12 meses)<b>',
                  width=750, height=450)
    fig.update_traces(line=dict(width=1.5))
    fig.add_vline(x=com_mes['fecha'][com_mes['fecha'].shape[0]-2], line_width=3, line_dash="dot", line_color = 'black') #line_color="#620042")
    fig.update_layout(
        xaxis_title="Fecha",
        yaxis_title="Comparendos",
        title_x=0.5,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        template = 'simple_white',
        legend_title_text='')
    y = fig

# redondear accidentes
    tb_mes['Pronóstico'] = tb_mes['Pronóstico'].apply(lambda x: round(x,0))
    tb_mes['Real'] = tb_mes['Real'].fillna(0).astype('int')
    tb_mes['Pronóstico'] = tb_mes['Pronóstico'].fillna(0).astype('int')
    tb_mes.rename(columns = {'fecha':'Fecha'}, inplace = True)
    z = tb_mes

    return v, w, y, z

# aplicar función
v, w, y, z = func_com_mes(x)
    
if tema == 'Comparendos' and periodo == 'Mes' and datos == True :   
    st.plotly_chart(v)
    st.plotly_chart(w)
    st.plotly_chart(y)

    fig = go.Figure(data=[go.Table(
    header=dict(values=list(z.columns),
                fill_color='lightgrey',
                align='center',
                line_color='darkslategray'),
    cells=dict(values=[z.Fecha.dt.date,
                       z.Real, z.Pronóstico],
               fill_color='white',
               align='center',
               line_color='lightgrey'))
        
])
    fig.update_layout(
    title_text="<b>Tabla con Predicciones <b>")
    st.write(fig)
    
    #st.markdown(get_table_download_link(z), unsafe_allow_html=True)
if tema == 'Comparendos' and periodo == 'Mes' and datos == False :   
    st.plotly_chart(v)
    st.plotly_chart(w)
    st.plotly_chart(y)





