import dash_bootstrap_components as dbc
from dash import html, dcc, callback, Input, Output
import os
import pandas as pd

# Caminhos das imagens e dados gerados pelo script NLP
IMG_WORDCLOUD = "assets/wordcloud_assuntos.png"
IMG_WORDCLOUD_TOPICOS = "assets/wordcloud_topicos_lda.png"
IMG_PARETO = "assets/pareto_palavras.png"
ARQUIVO_TOPICOS = "data/processed/topicos_nlp.parquet"

# --- LAYOUT FULL SCREEN ---
layout = html.Div(style={
    "height": "100vh",
    "display": "flex", 
    "flexDirection": "column",
    "backgroundColor": "#f8f9fa",
    "overflow": "hidden"
}, children=[

    # 1. CABEÇALHO
    html.Div(style={"padding": "15px 25px", "flexShrink": "0"}, children=[
        html.Div(style={
            "backgroundColor": "white", "padding": "15px", "borderRadius": "10px",
            "boxShadow": "0 2px 4px rgba(0,0,0,0.05)", "borderLeft": "5px solid #6c5ce7"
        }, children=[
            html.H3("🧠 Inteligência de Texto & Tópicos (NLP)", className="text-primary m-0"),
            html.Small("Análise semântica automática e distribuição de Pareto", className="text-muted")
        ]),
        
        html.Div(className="mt-3", children=[
            dbc.Tabs(id="abas-nlp", active_tab="tab-nuvem", children=[
                dbc.Tab(label="Nuvem de Termos", tab_id="tab-nuvem"),
                dbc.Tab(label="Nuvem de Tópicos (IA)", tab_id="tab-nuvem-topicos"),
                dbc.Tab(label="Distribuição de Pareto", tab_id="tab-pareto"),
                dbc.Tab(label="Cards de Tópicos", tab_id="tab-topicos"),
            ]),
        ])
    ]),

    # 2. ÁREA DE CONTEÚDO DINÂMICO
    html.Div(
        id="conteudo-principal-nlp", 
        style={
            "flexGrow": "1",
            "overflowY": "auto",
            "padding": "0 25px 25px 25px"
        }
    )
])

# --- CALLBACK PARA CONTEÚDO RESPONSIVO (TAMANHO AJUSTADO) ---
@callback(
    Output("conteudo-principal-nlp", "children"),
    Input("abas-nlp", "active_tab")
)
def render_content(tab):
    mapa_imagens = {
        "tab-nuvem": (IMG_WORDCLOUD, "Nuvem de Assuntos Gerais"),
        "tab-nuvem-topicos": (IMG_WORDCLOUD_TOPICOS, "Nuvem de Tópicos Semânticos (LDA)"),
        "tab-pareto": (IMG_PARETO, "Diagrama de Pareto (Visão 100%)")
    }

    if tab in mapa_imagens:
        caminho_img, titulo = mapa_imagens[tab]
        
        return dbc.Card([
            dbc.CardHeader(html.H5(titulo, className="m-0")),
            dbc.CardBody(style={
                "padding": "10px", 
                "display": "flex", 
                "justifyContent": "center"
            }, children=[
                html.Img(
                    src=caminho_img, 
                    style={
                        # O segredo está aqui:
                        "width": "100%",          # Força a largura a caber no card
                        "maxWidth": "850px",      # Impede que fique gigante em telas largas
                        "height": "auto",         # Mantém a proporção
                        "maxHeight": "60vh",      # Limita a altura para não cobrir o menu
                        "objectFit": "contain",   # Garante que a imagem inteira apareça
                        "borderRadius": "5px"
                    }
                ) if os.path.exists(caminho_img) else 
                html.Div("⚠️ Arquivo não encontrado.", className="alert alert-warning")
            ])
        ], className="shadow-sm border-0")

    elif tab == "tab-topicos":
        if not os.path.exists(ARQUIVO_TOPICOS):
            return html.Div("⚠️ Dados de tópicos não encontrados.", className="text-danger mt-3")
        
        try:
            df = pd.read_parquet(ARQUIVO_TOPICOS)
            return dbc.Row([
                dbc.Col(
                    dbc.Card([
                        dbc.CardBody([
                            html.H5(f"Tópico #{row['topico']}", className="card-title text-primary fw-bold"),
                            html.P(row['palavras'], className="card-text", style={"fontSize": "0.9rem"}),
                            dbc.Progress(value=row['peso'], max=df['peso'].max(), color="info", style={"height": "4px"}),
                            html.Small(f"Peso Total: {row['peso']}", className="text-muted")
                        ])
                    ], className="mb-3 shadow-sm border-0"), 
                    xs=12, md=6, lg=4
                ) for _, row in df.iterrows()
            ], className="mt-3")
        except Exception as e:
            return html.Div(f"Erro ao processar tópicos: {e}", className="text-danger")