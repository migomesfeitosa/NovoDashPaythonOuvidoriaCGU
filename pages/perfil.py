import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from utils.preprocessamento import carregar_dados_ouvidoria

# ==============================================================================
# 1. CONFIGURAÇÕES VISUAIS
# ==============================================================================
CORES = {
    "roxo": "#7c3aed",
    "azul": "#2563eb",
    "laranja": "#d97706",
    "rosa": "#db2777",
    "verde": "#16a34a",
    "cinza": "#cbd5e1"
}

LAYOUT_CLEAN = {
    "plot_bgcolor": "rgba(0,0,0,0)",
    "paper_bgcolor": "rgba(0,0,0,0)",
    "font": {"family": "Inter, sans-serif", "color": "#64748b"},
    "margin": {"l": 10, "r": 10, "t": 30, "b": 10}
}

# ==============================================================================
# 2. CARGA E TRATAMENTO DE DADOS (ETL)
# ==============================================================================
print(">>> CARREGANDO DADOS DE PERFIL...")
df_perfil = carregar_dados_ouvidoria()

if not df_perfil.empty:
    df_perfil.columns = [str(c).upper().strip() for c in df_perfil.columns]
    
    # Mapeamento para Demografia
    mapa_cols = {
        "FAIXA ETÁRIA": "FAIXA_ETARIA", "FAIXA ETARIA": "FAIXA_ETARIA",
        "GÊNERO": "GENERO", "GENERO": "GENERO", "SEXO": "GENERO",
        "RAÇA/COR": "RACA", "RACA": "RACA", "COR": "RACA",
        "DATA REGISTRO": "DATA_REGISTRO", "DATA": "DATA_REGISTRO",
        "SATISFAÇÃO": "SATISFACAO", "SATISFACAO": "SATISFACAO",
        "ASSUNTO": "ASSUNTO"
    }
    df_perfil.rename(columns=mapa_cols, inplace=True)
    
    # Extração de Nota (se houver)
    if "SATISFACAO" in df_perfil.columns:
        df_perfil['NOTA'] = df_perfil['SATISFACAO'].astype(str).str.extract(r'(\d)').astype(float)
        
    if "DATA_REGISTRO" in df_perfil.columns:
        df_perfil['DATA_REGISTRO'] = pd.to_datetime(df_perfil['DATA_REGISTRO'], errors='coerce')
        if "ANO" not in df_perfil.columns:
            df_perfil["ANO"] = df_perfil["DATA_REGISTRO"].dt.year

# Filtro de Ano
opcoes_ano = sorted(list(df_perfil["ANO"].unique()), reverse=True) if not df_perfil.empty and "ANO" in df_perfil.columns else []

# ==============================================================================
# 3. HELPERS (Componentes)
# ==============================================================================
def card_kpi(titulo, valor, cor=CORES["roxo"]):
    return dbc.Col(
        html.Div(
            className="custom-card p-3 bg-white shadow-sm h-100 border-start border-4",
            style={"borderLeftColor": cor},
            children=[
                html.Small(titulo.upper(), className="text-muted fw-bold"),
                html.H3(valor, className="m-0 fw-bold", style={"color": "#1e293b"})
            ]
        ), md=3
    )

# ==============================================================================
# 4. LAYOUT
# ==============================================================================
layout = html.Div(
    className="d-flex flex-column",
    style={"height": "100vh", "padding": "0px", "backgroundColor": "#f8fafc", "overflow": "hidden"},
    children=[
        
        # --- FILTROS ---
        html.Div(
            className="filter-container",
            style={"margin": "10px 10px 0 10px", "padding": "10px 15px", "backgroundColor": "white", "borderRadius": "8px", "boxShadow": "0 2px 4px rgba(0,0,0,0.05)"},
            children=[
                dbc.Row([
                    dbc.Col([html.H5("Perfil do Cidadão", className="fw-bold m-0 text-dark"), html.Small("Demografia e Equidade", className="text-muted")], md=4),
                    dbc.Col(dcc.Dropdown(id="perfil-ano", options=[{"label": i, "value": i} for i in opcoes_ano], multi=True, placeholder="Filtrar Ano"), md=4),
                    dbc.Col(html.Div(id="kpi-total-cidadaos", className="text-end fw-bold text-primary"), md=4),
                ], className="align-items-center")
            ]
        ),
        
        # --- CONTEÚDO ---
        html.Div(
            className="flex-grow-1 p-3", 
            style={"overflowY": "auto"}, 
            children=[
                
                # LINHA 1: Demografia Básica
                dbc.Row([
                    dbc.Col(html.Div(className="custom-card p-3 bg-white shadow-sm h-100", children=[
                        html.H6("Faixa Etária", className="fw-bold text-secondary mb-3"),
                        dcc.Graph(id="fig-faixa-etaria", style={"height": "300px"})
                    ]), md=6),
                    
                    dbc.Col(html.Div(className="custom-card p-3 bg-white shadow-sm h-100", children=[
                        html.H6("Autodeclaração de Raça/Cor", className="fw-bold text-secondary mb-3"),
                        dcc.Graph(id="fig-raca", style={"height": "300px"})
                    ]), md=6),
                ], className="g-3 mb-3"),
                
                # LINHA 2: Análises Cruzadas
                dbc.Row([
                    dbc.Col(html.Div(className="custom-card p-3 bg-white shadow-sm h-100", children=[
                        html.H6("Satisfação Média por Gênero", className="fw-bold text-secondary mb-3"),
                        html.Small("Existe diferença na percepção de qualidade?", className="text-muted d-block mb-2"),
                        dcc.Graph(id="fig-genero-sat", style={"height": "350px"})
                    ]), md=5),
                    
                    dbc.Col(html.Div(className="custom-card p-3 bg-white shadow-sm h-100", children=[
                        html.H6("Top Assuntos por Raça/Cor (Distribuição %)", className="fw-bold text-secondary mb-3"),
                        html.Small("Quais temas afetam mais cada grupo?", className="text-muted d-block mb-2"),
                        dcc.Graph(id="fig-raca-assunto", style={"height": "350px"})
                    ]), md=7),
                ], className="g-3")
            ]
        )
    ]
)

# ==============================================================================
# 5. CALLBACK
# ==============================================================================
@callback(
    [Output("kpi-total-cidadaos", "children"),
     Output("fig-faixa-etaria", "figure"), Output("fig-raca", "figure"),
     Output("fig-genero-sat", "figure"), Output("fig-raca-assunto", "figure")],
    [Input("perfil-ano", "value")]
)
def update_perfil(anos):
    dff = df_perfil.copy()
    if anos: dff = dff[dff["ANO"].isin(anos if isinstance(anos, list) else [anos])]
    
    total = len(dff)
    vazio = go.Figure().add_annotation(text="Sem dados demográficos", showarrow=False)
    if dff.empty: return "-", vazio, vazio, vazio, vazio

    # --- 1. FAIXA ETÁRIA ---
    if "FAIXA_ETARIA" in dff.columns:
        df_faixa = dff[~dff["FAIXA_ETARIA"].isin(["Não Informado", "NI", "NaN"])]
        df_faixa = df_faixa["FAIXA_ETARIA"].value_counts().reset_index()
        df_faixa.columns = ["Faixa", "Qtd"]
        df_faixa = df_faixa.sort_values("Faixa")
        
        fig_etaria = px.bar(df_faixa, x="Faixa", y="Qtd", text="Qtd")
        fig_etaria.update_traces(marker_color=CORES["roxo"], textposition="outside")
        fig_etaria.update_layout(LAYOUT_CLEAN)
        fig_etaria.update_layout(yaxis_title=None, xaxis_title=None)
    else: fig_etaria = vazio

    # --- 2. RAÇA/COR ---
    if "RACA" in dff.columns:
        df_raca = dff["RACA"].value_counts().reset_index()
        df_raca.columns = ["Raca", "Qtd"]
        fig_raca = px.pie(df_raca, names="Raca", values="Qtd", hole=0.6, color_discrete_sequence=px.colors.qualitative.Pastel1)
        fig_raca.update_layout(LAYOUT_CLEAN)
        fig_raca.update_layout(showlegend=True, legend=dict(orientation="v"))
    else: fig_raca = vazio

    # --- 3. GÊNERO x SATISFAÇÃO ---
    if "GENERO" in dff.columns and "NOTA" in dff.columns:
        df_gen = dff.dropna(subset=["GENERO", "NOTA"])
        df_gen = df_gen[~df_gen["GENERO"].isin(["Não Informado", "NI"])]
        df_gen_agrup = df_gen.groupby("GENERO")["NOTA"].mean().reset_index()
        
        fig_gen = px.bar(df_gen_agrup, x="GENERO", y="NOTA", text_auto=".2f")
        fig_gen.update_traces(marker_color=CORES["azul"], width=0.5)
        fig_gen.update_layout(LAYOUT_CLEAN)
        fig_gen.update_layout(yaxis=dict(range=[0, 5.5], title="Nota Média"), xaxis_title=None)
    else: fig_gen = vazio

    # --- 4. RAÇA x ASSUNTO (CORREÇÃO AQUI) ---
    if "RACA" in dff.columns and "ASSUNTO" in dff.columns:
        df_cross = dff.dropna(subset=["RACA", "ASSUNTO"])
        top_racas = df_cross["RACA"].value_counts().head(4).index
        top_assuntos = df_cross["ASSUNTO"].value_counts().head(5).index
        
        df_cross = df_cross[df_cross["RACA"].isin(top_racas) & df_cross["ASSUNTO"].isin(top_assuntos)]
        df_cross = df_cross.groupby(["RACA", "ASSUNTO"]).size().reset_index(name="Qtd")
        
        # --- A CORREÇÃO FOI FEITA AQUI ---
        # Removido barmode="fill" de dentro do px.bar
        fig_cross = px.bar(df_cross, x="RACA", y="Qtd", color="ASSUNTO", color_discrete_sequence=px.colors.qualitative.Safe)
        
        # O modo de preenchimento (100%) é definido no layout com barnorm='percent'
        fig_cross.update_layout(LAYOUT_CLEAN)
        fig_cross.update_layout(
            barmode='stack',       # Empilha normal
            barnorm='percent',     # Normaliza para 100%
            yaxis_title="% do Total", 
            xaxis_title=None, 
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
    else: fig_cross = vazio

    return f"Total: {total}", fig_etaria, fig_raca, fig_gen, fig_cross