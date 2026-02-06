import dash_bootstrap_components as dbc
from dash import html, dcc, callback, Input, Output, State
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go # Adicionado para o gráfico de medidor
import pickle
import os
import numpy as np
import re

# --- CONFIGURAÇÕES DE CAMINHOS ---
PATH_MODEL = "data/processed/modelo_ia.pkl"
PATH_VECTORIZER = "data/processed/vectorizer.pkl"
PATH_SHAP_GLOBAL = "data/processed/explica_shap.parquet"

# --- ESTILO GERAL ---
ESTILO_PAGINA = {
    "padding": "25px", 
    "backgroundColor": "#f8fafc", 
    "height": "100vh",     
    "overflowY": "auto"    
}

# --- FUNÇÃO AUXILIAR: ESTIMATIVA DE SATISFAÇÃO (Acréscimo) ---
def estimar_satisfacao_cidadao(texto):
    positivas = ['agradeço', 'elogio', 'parabéns', 'eficiente', 'resolvido', 'bom', 'ótimo', 'concessão', 'obrigado']
    negativas = ['atraso', 'absurdo', 'ruim', 'demora', 'falta', 'erro', 'problema', 'reclamação', 'indeferido', 'péssimo']
    
    score = 50 # Neutro
    palavras = re.findall(r"\w+", texto.lower())
    for p in palavras:
        if p in positivas: score += 12
        if p in negativas: score -= 12
    return max(0, min(100, score))

# --- LAYOUT ---
layout = html.Div(style=ESTILO_PAGINA, children=[
    
    # Cabeçalho da Página
    html.Div(className="mb-4", children=[
        html.H3("🤖 Modelos Preditivos & Explicabilidade", className="fw-bold text-primary"),
        html.P("Simulador de classificação de risco (SLA) com análise de impacto SHAP.", className="text-muted")
    ]),

    dbc.Row([
        # COLUNA ESQUERDA: SIMULADOR
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H6("Simulador de Risco em Tempo Real", className="m-0 fw-bold")),
                dbc.CardBody([
                    html.P("Insira o texto da manifestação para análise:", className="small text-muted"),
                    dbc.Textarea(
                        id="input-texto-ia",
                        placeholder="Ex: Reclamação sobre a demora excessiva na análise do recurso...",
                        style={"height": "120px", "borderRadius": "8px", "fontSize": "14px"}
                    ),
                    dbc.Button("🚀 Analisar Manifestação", id="btn-ia", color="primary", className="mt-3 w-100 fw-bold"),
                    html.Div(id="resultado-ia-container", className="mt-4")
                ])
            ], className="shadow-sm border-0 mb-4"),
            
            # --- NOVO CARD: SATISFAÇÃO (Acréscimo) ---
            dbc.Card([
                dbc.CardBody([
                    html.H6("ESTIMATIVA DE SATISFAÇÃO", className="fw-bold text-muted small mb-2"),
                    dcc.Graph(id="grafico-satisfacao", style={"height": "150px"}, config={"displayModeBar": False})
                ])
            ], className="shadow-sm border-0 mb-4"),

            # Card de Métricas do Artigo
            dbc.Card([
                dbc.CardBody([
                    html.H6("DETALHES DO PIPELINE", className="fw-bold text-muted small"),
                    html.Div([
                        html.P([html.B("Equilíbrio: "), "SMOTEN (Sintético)"], className="mb-1 small"),
                        html.P([html.B("Busca: "), "GridSearch CV"], className="mb-1 small"),
                        html.P([html.B("Acurácia: "), html.Span("84%", className="text-success fw-bold")], className="mb-0 small"),
                    ])
                ])
            ], className="shadow-sm border-0")
        ], md=5),

        # COLUNA DIREITA: GRÁFICOS (EXPLICABILIDADE)
        dbc.Col([
            # 1. Gráfico Global
            dbc.Card([
                dbc.CardHeader(html.H6("Impacto Global dos Termos (SHAP Global)", className="m-0 fw-bold")),
                dbc.CardBody([
                    dcc.Graph(id="grafico-ia-global", config={"displayModeBar": False})
                ])
            ], className="shadow-sm border-0 mb-4"),

            # 2. Gráfico Local
            html.Div(id="container-shap-local", style={"display": "none"}, children=[
                dbc.Card([
                    dbc.CardHeader(html.H6("Explicação Local: Por que a IA tomou essa decisão?", className="m-0 fw-bold")),
                    dbc.CardBody([
                        dcc.Graph(id="grafico-ia-local", config={"displayModeBar": False}, style={"minHeight": "300px"})
                    ])
                ], className="shadow-sm border-0 border-top-0", style={"borderTop": "3px solid #7c3aed"})
            ])
        ], md=7)
    ])
])

# --- CALLBACKS ---

@callback(
    [Output("resultado-ia-container", "children"),
     Output("grafico-ia-local", "figure"),
     Output("container-shap-local", "style"),
     Output("grafico-satisfacao", "figure")], # Adicionado Output da satisfação
    [Input("btn-ia", "n_clicks")],
    [State("input-texto-ia", "value")],
    prevent_initial_call=True
)
def realizar_predicao(n, texto):
    if not texto or len(texto.strip()) < 5:
        return dbc.Alert("⚠️ Por favor, descreva melhor a manifestação.", color="warning"), {}, {"display": "none"}, go.Figure()
    
    if not os.path.exists(PATH_MODEL) or not os.path.exists(PATH_VECTORIZER):
        return dbc.Alert("❌ Arquivos de IA (.pkl) não encontrados!", color="danger"), {}, {"display": "none"}, go.Figure()

    # 1. Carregar artefatos
    with open(PATH_MODEL, 'rb') as f: model = pickle.load(f)
    with open(PATH_VECTORIZER, 'rb') as f: tfidf = pickle.load(f)

    # 2. Processar e Prever
    vec_texto = tfidf.transform([texto])
    probabilidade = model.predict_proba(vec_texto)[0][1]
    
    status = "ALTO RISCO DE ATRASO" if probabilidade > 0.5 else "DENTRO DO PRAZO"
    cor = "danger" if probabilidade > 0.5 else "success"
    
    res_html = dbc.Alert([
        html.H4(status, className="fw-bold m-0"),
        html.P(f"Probabilidade calculada: {probabilidade*100:.1f}%", className="mb-0 small")
    ], color=cor, className="border-0 shadow-sm")

    # --- GERAR GRÁFICO DE SATISFAÇÃO (Acréscimo) ---
    score = estimar_satisfacao_cidadao(texto)
    cor_medidor = "#ef4444" if score < 40 else "#f59e0b" if score < 70 else "#10b981"
    
    fig_sat = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = score,
        number = {'suffix': "%", 'font': {'size': 18}},
        gauge = {
            'axis': {'range': [0, 100], 'tickwidth': 1},
            'bar': {'color': cor_medidor},
            'steps': [
                {'range': [0, 40], 'color': "#fee2e2"},
                {'range': [40, 70], 'color': "#fef3c7"},
                {'range': [70, 100], 'color': "#d1fae5"}
            ],
        }
    ))
    fig_sat.update_layout(height=150, margin=dict(l=25, r=25, t=30, b=10), paper_bgcolor='rgba(0,0,0,0)')

    # 3. Gerar Explicação Local
    feature_names = tfidf.get_feature_names_out()
    termos_limpos = re.findall(r"(?u)\b[a-zA-Záéíóúâêîôûãõç]{3,}\b", texto.lower())
    termos_encontrados = [w for w in termos_limpos if w in feature_names]
    
    if not termos_encontrados:
        fig_local = px.bar(title="Nenhum termo técnico identificado no texto.")
        fig_local.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    else:
        pesos = []
        importancias = model.feature_importances_
        for w in set(termos_encontrados):
            idx = np.where(feature_names == w)[0][0]
            pesos.append({'Termo': w, 'Peso': importancias[idx]})
        
        df_local = pd.DataFrame(pesos).sort_values('Peso', ascending=True)
        
        fig_local = px.bar(
            df_local, x='Peso', y='Termo', 
            orientation='h', 
            color_discrete_sequence=['#7c3aed']
        )
        fig_local.update_layout(
            margin=dict(l=20, r=20, t=30, b=20),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis={'title': 'Impacto Individual', 'showgrid': True},
            yaxis={'automargin': True}
        )

    return res_html, fig_local, {"display": "block"}, fig_sat


@callback(
    Output("grafico-ia-global", "figure"),
    Input("btn-ia", "id") 
)
def update_global_shap(_):
    if not os.path.exists(PATH_SHAP_GLOBAL):
        return px.bar(title="⚠️ Execute o treino para gerar o SHAP Global.")
    
    df_s = pd.read_parquet(PATH_SHAP_GLOBAL)
    df_s = df_s.dropna().query("Impacto > 0.001").head(12) 

    fig = px.bar(
        df_s, x='Impacto', y='Termo', orientation='h',
        color='Impacto', color_continuous_scale='Purples'
    )
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        yaxis={'categoryorder':'total ascending', 'automargin': True},
        margin=dict(l=10, r=10, t=10, b=10),
        coloraxis_showscale=False
    )
    return fig