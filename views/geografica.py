import plotly.express as px
import json
import os

# Carrega o GeoJSON uma única vez na memória para ser rápido
caminho_geo = "assets/brazil_geo.json"
GEOJSON_BRASIL = {}

if os.path.exists(caminho_geo):
    with open(caminho_geo, "r", encoding="utf-8") as f:
        GEOJSON_BRASIL = json.load(f)
else:
    print("⚠️ AVISO: Arquivo 'assets/brazil_geo.json' não encontrado. O mapa pode não carregar.")

def grafico_por_uf(df):
    if df.empty or 'UF' not in df.columns: return {}
    
    dados = df["UF"].value_counts().reset_index()
    dados.columns = ["UF", "Quantidade"]
    dados = dados[dados["UF"].str.len() == 2]

    return px.bar(dados, x="UF", y="Quantidade", title="Manifestações por UF", template="plotly_white")

def mapa_brasil(df):
    if df.empty or 'UF' not in df.columns: return {}
    
    dados = df["UF"].value_counts().reset_index()
    dados.columns = ["UF", "Quantidade"]
    dados = dados[dados["UF"].str.len() == 2]

    # Se o GeoJSON não carregou, retorna vazio ou tenta baixar (opcional)
    if not GEOJSON_BRASIL:
        return {}

    fig = px.choropleth(
        dados,
        locations="UF",
        geojson=GEOJSON_BRASIL,
        featureidkey="properties.sigla",
        color="Quantidade",
        scope="south america",
        title="Mapa de Calor (Brasil)",
        color_continuous_scale="Blues"
    )
    fig.update_geos(fitbounds="locations", visible=False)
    return fig