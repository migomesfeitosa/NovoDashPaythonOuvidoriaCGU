import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
from utils.preprocessamento import carregar_dados_lai

# --- DADOS ---
df = carregar_dados_lai("pedidos")
if not df.empty:
    df.columns = [c.upper().strip() for c in df.columns]
    # Normalização de nomes de colunas de Assunto
    mapa = {"ASSUNTO_PEDIDO": "ASSUNTO", "SUB_ASSUNTO_PEDIDO": "SUBASSUNTO", "DATA_REGISTRO": "DATA"}
    df.rename(columns=mapa, inplace=True)
    if "ANO" not in df.columns and "DATA" in df.columns:
        df["ANO"] = pd.to_datetime(df["DATA"], errors='coerce').dt.year

opcoes_ano = sorted(list(df["ANO"].dropna().unique()), reverse=True) if not df.empty and "ANO" in df.columns else []

# --- LAYOUT ---
layout = html.Div(children=[
    html.Div(className="filter-container bg-white p-3 rounded shadow-sm mb-3", children=[
        dbc.Row([
            dbc.Col([html.H5("Temas Solicitados", className="fw-bold m-0"), html.Small("O que o cidadão quer saber?", className="text-muted")], md=6),
            dbc.Col(dcc.Dropdown(id="lait-ano", options=[{"label": i, "value": i} for i in opcoes_ano], multi=True, placeholder="Filtrar Ano"), md=6),
        ], className="align-items-center")
    ]),

    dbc.Row([
        # Gráfico 1: Treemap (Hierarquia Assunto > Subassunto)
        dbc.Col(html.Div(className="custom-card p-3 bg-white shadow-sm h-100", children=[
            html.H6("Mapa de Assuntos (Treemap)", className="fw-bold text-secondary"),
            html.Small("Clique nos blocos para aprofundar", className="text-muted"),
            dcc.Graph(id="lait-fig-treemap", style={"height": "500px"})
        ]), md=8),

        # Gráfico 2: Top 10 Subassuntos (Barras)
        dbc.Col(html.Div(className="custom-card p-3 bg-white shadow-sm h-100", children=[
            html.H6("Top 10 Sub-Assuntos", className="fw-bold text-secondary"),
            dcc.Graph(id="lait-fig-barras", style={"height": "500px"})
        ]), md=4),
    ], className="g-3")
])

@callback(
    [Output("lait-fig-treemap", "figure"), Output("lait-fig-barras", "figure")],
    [Input("lait-ano", "value")]
)
def update_temas(anos):
    dff = df.copy()
    if anos: dff = dff[dff["ANO"].isin(anos if isinstance(anos, list) else [anos])]
    
    if "ASSUNTO" in dff.columns:
        # Treemap
        df_tree = dff.dropna(subset=["ASSUNTO"])
        if "SUBASSUNTO" not in df_tree.columns: df_tree["SUBASSUNTO"] = "Geral"
        df_tree = df_tree.groupby(["ASSUNTO", "SUBASSUNTO"]).size().reset_index(name="Qtd")
        # Filtra os top 30 para não travar o navegador
        df_tree = df_tree.sort_values("Qtd", ascending=False).head(50)
        
        fig_tree = px.treemap(df_tree, path=[px.Constant("Todos"), "ASSUNTO", "SUBASSUNTO"], values="Qtd", color="Qtd", color_continuous_scale="Purples")
        fig_tree.update_layout(margin=dict(t=0, l=0, r=0, b=0))

        # Barras Subassuntos
        df_sub = dff["SUBASSUNTO"].value_counts().head(15).reset_index()
        df_sub.columns = ["Subassunto", "Qtd"]
        df_sub['Subassunto'] = df_sub['Subassunto'].apply(lambda x: str(x)[:25]+"...")
        fig_bar = px.bar(df_sub.sort_values("Qtd"), x="Qtd", y="Subassunto", orientation="h", text="Qtd")
        fig_bar.update_traces(marker_color="#7c3aed", textposition="outside")
        fig_bar.update_layout(plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0), yaxis=dict(title=None))
        
        return fig_tree, fig_bar
    return {}, {}