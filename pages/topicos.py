import dash_bootstrap_components as dbc
from dash import html, dcc, callback, Input, Output
import os
import pandas as pd

# Caminhos
IMG_WORDCLOUD = "assets/wordcloud_assuntos.png"
ARQUIVO_TOPICOS = "data/processed/topicos_nlp.parquet"

# --- LAYOUT FULL SCREEN ---
layout = html.Div(style={
    "height": "100vh",           # Força a altura a ser exatamente a da tela
    "display": "flex", 
    "flexDirection": "column",   # Organiza itens em coluna (Header em cima, conteúdo embaixo)
    "backgroundColor": "#f8f9fa",
    "overflow": "hidden"         # Impede que a página inteira role
}, children=[

    # 1. CABEÇALHO (Altura Fixa)
    html.Div(style={"padding": "15px 25px", "flexShrink": "0"}, children=[
        html.Div(style={
            "backgroundColor": "white", "padding": "15px", "borderRadius": "10px",
            "boxShadow": "0 2px 4px rgba(0,0,0,0.05)", "borderLeft": "5px solid #6c5ce7"
        }, children=[
            html.H3("🧠 Inteligência de Texto & Tópicos (NLP)", className="text-primary m-0"),
            html.Small("Análise semântica automática baseada em IA", className="text-muted")
        ]),
        
        html.Div(className="mt-3", children=[
            dbc.Tabs(id="abas-nlp", active_tab="tab-nuvem", children=[
                dbc.Tab(label="Nuvem de Termos", tab_id="tab-nuvem"),
                dbc.Tab(label="Tópicos Identificados", tab_id="tab-topicos"),
            ]),
        ])
    ]),

    # 2. ÁREA DE CONTEÚDO DINÂMICO (Ocupa o resto da tela)
    html.Div(
        id="conteudo-principal-nlp", 
        style={
            "flexGrow": "1",           # Faz esta Div esticar até o fim da tela
            "overflowY": "auto",       # Ativa o scroll apenas se o conteúdo for maior que o espaço
            "padding": "0 25px 25px 25px"
        }
    )
])

# --- CALLBACK PARA CONTEÚDO RESPONSIVO ---
@callback(
    Output("conteudo-principal-nlp", "children"),
    Input("abas-nlp", "active_tab")
)
def render_content(tab):
    if tab == "tab-nuvem":
        return dbc.Card([
            dbc.CardBody(style={
                "display": "flex", 
                "alignItems": "center", 
                "justifyContent": "center",
                "height": "100%", 
                "minHeight": "60vh"    # Garante que a imagem tenha espaço para crescer
            }, children=[
                html.Img(
                    src=IMG_WORDCLOUD, 
                    style={
                        "maxWidth": "100%", 
                        "maxHeight": "70vh", # Limita a altura da imagem para não criar scroll desnecessário
                        "objectFit": "contain",
                        "borderRadius": "8px"
                    }
                ) if os.path.exists(IMG_WORDCLOUD) else 
                html.Div("⚠️ Imagem não encontrada.", className="alert alert-warning")
            ])
        ], className="shadow-sm border-0 h-100")

    elif tab == "tab-topicos":
        if not os.path.exists(ARQUIVO_TOPICOS):
            return html.Div("⚠️ Arquivo não encontrado.", className="text-danger mt-3")
        
        try:
            df = pd.read_parquet(ARQUIVO_TOPICOS)
            # Criamos uma Row para os cards de tópicos
            return dbc.Row([
                dbc.Col(
                    dbc.Card([
                        dbc.CardBody([
                            html.H5(f"Tópico #{row['Topico_ID']}", className="card-title text-success fw-bold"),
                            html.P(row['Principais_Termos'], className="card-text"),
                            dbc.Progress(value=row['Peso'], max=df['Peso'].max(), color="success", style={"height": "4px"}),
                            html.Small(f"Relevância: {row['Peso']:.1f}", className="text-muted")
                        ])
                    ], className="mb-3 shadow-sm border-0"), 
                    xs=12, md=6, lg=4 # Fica responsivo: 1, 2 ou 3 cards por linha
                ) for _, row in df.iterrows()
            ], className="mt-3")
        except Exception as e:
            return html.Div(f"Erro: {e}", className="text-danger")