import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json
from urllib.request import urlopen
from utils.preprocessamento import carregar_dados_ouvidoria, UFS_BRASIL

# --- CORES ---
COR_DESTAQUE = "#7c3aed"  # Roxo
ESCALA_MAPA = "Purples"   # Escala de Roxos

# --- CARGA DE DADOS ---
print(">>> CARREGANDO MAPAS...")
df_geo = carregar_dados_ouvidoria()

if not df_geo.empty:
    df_geo.columns = [str(c).upper().strip() for c in df_geo.columns]
    correcao = {
        "UF DO MUNICÍPIO MANIFESTAÇÃO": "UF", "UF_MANIFESTACAO": "UF",
        "UF DO MUNICÍPIO MANIFESTANTE": "UF", 
        "DATA REGISTRO": "DATA_REGISTRO", "DATA": "DATA_REGISTRO"
    }
    df_geo.rename(columns=correcao, inplace=True)
    if "ANO" not in df_geo.columns and "DATA_REGISTRO" in df_geo.columns:
        df_geo['DATA_REGISTRO'] = pd.to_datetime(df_geo['DATA_REGISTRO'], errors='coerce')
        df_geo["ANO"] = df_geo["DATA_REGISTRO"].dt.year

# --- CARGA GEOJSON ---
geojson_brasil = None
try:
    print(">>> BAIXANDO MAPA...")
    url_mapa = 'https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson'
    with urlopen(url_mapa) as response:
        geojson_brasil = json.load(response)
except Exception as e:
    print(f">>> ERRO MAPA: {e}")
    geojson_brasil = None

opcoes_ano = sorted(list(df_geo["ANO"].unique()), reverse=True) if not df_geo.empty and "ANO" in df_geo.columns else []

# --- LAYOUT ---
layout = html.Div(
    className="d-flex flex-column",
    # height: 100vh e overflow: hidden GARANTEM que não tenha scroll na página inteira
    style={"height": "100vh", "padding": "0px", "backgroundColor": "#f8fafc", "overflow": "hidden"},
    children=[
        # 1. Filtros (Cabeçalho)
        html.Div(
            className="filter-container",
            style={"margin": "10px 10px 0 10px", "padding": "15px", "backgroundColor": "white", "borderRadius": "8px", "boxShadow": "0 2px 4px rgba(0,0,0,0.05)"},
            children=[
                dbc.Row([
                    dbc.Col([html.H5("Análise Territorial", className="fw-bold m-0 text-dark"), html.Small("Distribuição Geográfica", className="text-muted")], md=4),
                    dbc.Col(dcc.Dropdown(id="geo-ano", options=[{"label": i, "value": i} for i in opcoes_ano], multi=True, placeholder="Filtrar Ano"), md=4),
                    dbc.Col(dbc.Button("Atualizar Visualização", id="geo-btn", color="dark", outline=True, className="w-100"), md=4),
                ], className="align-items-center")
            ]
        ),
        
        # 2. Conteúdo (Preenche o resto da tela)
        html.Div(
            className="flex-grow-1 p-3", 
            # overflow: hidden aqui também remove o scroll interno
            style={"overflow": "hidden", "display": "flex", "flexDirection": "column"}, 
            children=[
                dbc.Row([
                    # Coluna Mapa
                    dbc.Col(html.Div(className="custom-card p-3 bg-white shadow-sm", style={"height": "100%"}, children=[
                        html.H6("Mapa de Calor", className="fw-bold text-secondary mb-2"),
                        dcc.Loading(dcc.Graph(
                            id="fig-mapa-real", 
                            # O PULO DO GATO: Altura calculada (100vh - cabeçalho - margens)
                            # 100vh (tela) - 160px (filtros/margens) = Ocupa todo o resto exato
                            style={"height": "calc(100vh - 160px)"} 
                        ))
                    ]), md=7, style={"height": "100%"}), # Coluna com 100% de altura
                    
                    # Coluna Ranking
                    dbc.Col(html.Div(className="custom-card p-3 bg-white shadow-sm", style={"height": "100%"}, children=[
                        html.H6("Ranking de Estados", className="fw-bold text-secondary mb-2"),
                        dcc.Graph(
                            id="fig-ranking-uf", 
                            # Mesma altura calculada para alinhar perfeitamente
                            style={"height": "calc(100vh - 160px)"} 
                        )
                    ]), md=5, style={"height": "100%"}),
                ], className="g-3 h-100") # Row com h-100 (height: 100%)
            ]
        )
    ]
)

@callback(
    [Output("fig-mapa-real", "figure"), Output("fig-ranking-uf", "figure")],
    [Input("geo-ano", "value")]
)
def update_geo(anos):
    dff = df_geo.copy()
    if anos: dff = dff[dff["ANO"].isin(anos if isinstance(anos, list) else [anos])]
    
    if "UF" in dff.columns:
        dff = dff[~dff["UF"].isin(["NI", "NA", "XX", "NÃO INFORMADO"])]
        df_uf = dff["UF"].value_counts().reset_index()
        df_uf.columns = ["UF", "Qtd"]
    else:
        return go.Figure(), go.Figure()

    # --- MAPA ---
    if geojson_brasil:
        fig_mapa = px.choropleth(
            df_uf, geojson=geojson_brasil, locations="UF", featureidkey="properties.sigla",
            color="Qtd", color_continuous_scale=ESCALA_MAPA, hover_name="UF", title=None
        )
        fig_mapa.update_geos(fitbounds="locations", visible=False)
        fig_mapa.update_layout(
            margin={"r":0,"t":0,"l":0,"b":0}, paper_bgcolor='rgba(0,0,0,0)',
            coloraxis_colorbar=dict(title="Qtd", thickness=15, len=0.8)
        )
    else:
        fig_mapa = go.Figure().add_annotation(text="Erro no Mapa", showarrow=False)

    # --- RANKING ---
    df_uf_sorted = df_uf.sort_values("Qtd", ascending=True).tail(15)
    
    fig_ranking = px.bar(df_uf_sorted, x="Qtd", y="UF", orientation="h", text="Qtd")
    fig_ranking.update_traces(marker_color=COR_DESTAQUE, textposition="outside", cliponaxis=False)
    
    fig_ranking.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        # Automargin ajustado para garantir que tudo caiba na tela cheia
        margin=dict(l=0, r=40, t=10, b=10), 
        xaxis=dict(showgrid=True, gridcolor='#f1f5f9'), 
        yaxis=dict(showgrid=False, automargin=True),
        font={'family': "Inter, sans-serif", 'color': '#64748b'}
    )

    return fig_mapa, fig_ranking