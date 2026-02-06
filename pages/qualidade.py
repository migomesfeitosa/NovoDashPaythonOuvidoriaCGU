import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from utils.preprocessamento import carregar_dados_ouvidoria

# --- CORES (Identidade Visual Roxo/Acessível) ---
COR_DESTAQUE = "#7c3aed"  # Roxo
COR_POSITIVO = "#2563eb"  # Azul
COR_NEGATIVO = "#d97706"  # Laranja
COR_NEUTRA = "#cbd5e1"    # Cinza Claro

# --- CARGA E TRATAMENTO ---
df_qual = carregar_dados_ouvidoria()

if not df_qual.empty:
    df_qual.columns = [str(c).upper().strip() for c in df_qual.columns]
    correcao = {
        "SATISFAÇÃO": "SATISFACAO", "SATISFACAO": "SATISFACAO",
        "NOME ÓRGÃO": "ORGAO", "ORGAO": "ORGAO",
        "DATA REGISTRO": "DATA", "DATA": "DATA_REGISTRO",
        "ASSUNTO": "ASSUNTO"
    }
    df_qual.rename(columns=correcao, inplace=True)
    
    # Extrair Nota da Satisfação (Ex: "(5) Muito Satisfeito" -> 5)
    if "SATISFACAO" in df_qual.columns:
        # Pega o primeiro caractere se for numérico (1-5)
        df_qual['NOTA'] = df_qual['SATISFACAO'].astype(str).str.extract(r'(\d)').astype(float)
    
    if "ANO" not in df_qual.columns and "DATA_REGISTRO" in df_qual.columns:
        df_qual['DATA_REGISTRO'] = pd.to_datetime(df_qual['DATA_REGISTRO'], errors='coerce')
        df_qual["ANO"] = df_qual["DATA_REGISTRO"].dt.year

opcoes_ano = sorted(list(df_qual["ANO"].unique()), reverse=True) if not df_qual.empty and "ANO" in df_qual.columns else []

# --- LAYOUT ---
layout = html.Div(
    className="d-flex flex-column",
    style={"height": "100vh", "padding": "0px", "backgroundColor": "#f8fafc", "overflow": "hidden"},
    children=[
        # Filtros
        html.Div(
            className="filter-container",
            style={"margin": "10px 10px 0 10px", "padding": "15px", "backgroundColor": "white", "borderRadius": "8px", "boxShadow": "0 2px 4px rgba(0,0,0,0.05)"},
            children=[
                dbc.Row([
                    dbc.Col([html.H5("Qualidade e Avaliação", className="fw-bold m-0 text-dark"), html.Small("Satisfação do Cidadão", className="text-muted")], md=4),
                    dbc.Col(dcc.Dropdown(id="qual-ano", options=[{"label": i, "value": i} for i in opcoes_ano], multi=True, placeholder="Filtrar Ano"), md=4),
                    dbc.Col(html.Div(id="resumo-notas", className="text-end fw-bold text-primary"), md=4),
                ], className="align-items-center")
            ]
        ),
        
        # Conteúdo
        html.Div(
            className="flex-grow-1 p-3", 
            style={"overflowY": "auto"}, 
            children=[
                # Linha 1: KPIs e Distribuição
                dbc.Row([
                    # KPI Nota Média
                    dbc.Col(html.Div(className="custom-card p-4 bg-white h-100 shadow-sm d-flex flex-column justify-content-center align-items-center", children=[
                        html.H6("Nota Média Geral", className="text-muted mb-2"),
                        html.H1(id="kpi-nota-media", className="display-4 fw-bold", style={"color": COR_DESTAQUE}),
                        html.Small("Escala de 1 a 5", className="text-muted")
                    ]), md=3),
                    
                    # Gráfico de Rosca (Distribuição das Notas)
                    dbc.Col(html.Div(className="custom-card p-3 bg-white h-100 shadow-sm", children=[
                        html.H6("Distribuição das Avaliações", className="fw-bold text-secondary mb-3"),
                        dcc.Graph(id="fig-dist-notas", style={"height": "200px"})
                    ]), md=5),
                    
                    # KPI % Satisfeitos
                    dbc.Col(html.Div(className="custom-card p-4 bg-white h-100 shadow-sm d-flex flex-column justify-content-center align-items-center", children=[
                        html.H6("Índice de Satisfação", className="text-muted mb-2"),
                        html.H1(id="kpi-pct-sat", className="display-4 fw-bold text-success"),
                        html.Small("% Notas 4 e 5", className="text-muted")
                    ]), md=4),
                ], className="g-3 mb-3", style={"minHeight": "250px"}),

                # Linha 2: Ranking e Matriz
                dbc.Row([
                    # Matriz de Dispersão (Volume x Nota) - O Gráfico de Ouro da Qualidade
                    dbc.Col(html.Div(className="custom-card p-3 bg-white h-100 shadow-sm", children=[
                        html.H6("Matriz de Eficiência: Volume x Nota Média", className="fw-bold text-secondary mb-3"),
                        html.Small("Quadrante Superior Direito = Alta Demanda e Boa Nota (Ideal)", className="text-muted d-block mb-2"),
                        dcc.Graph(id="fig-matriz-qual", style={"height": "400px"})
                    ]), md=7),
                    
                    # Ranking Piores/Melhores
                    dbc.Col(html.Div(className="custom-card p-3 bg-white h-100 shadow-sm", children=[
                        html.H6("Ranking por Nota Média (Top 10)", className="fw-bold text-secondary mb-3"),
                        dcc.Graph(id="fig-ranking-nota", style={"height": "400px"})
                    ]), md=5),
                ], className="g-3")
            ]
        )
    ]
)

@callback(
    [Output("kpi-nota-media", "children"), Output("kpi-pct-sat", "children"),
     Output("fig-dist-notas", "figure"), Output("fig-matriz-qual", "figure"), Output("fig-ranking-nota", "figure")],
    [Input("qual-ano", "value")]
)
def update_qualidade(anos):
    dff = df_qual.copy()
    if anos: dff = dff[dff["ANO"].isin(anos if isinstance(anos, list) else [anos])]
    
    # Se não tiver dados de nota, retorna vazio
    if "NOTA" not in dff.columns or dff["NOTA"].dropna().empty:
        vazio = go.Figure().add_annotation(text="Sem dados de avaliação", showarrow=False)
        return "-", "-", vazio, vazio, vazio

    # --- KPIs ---
    nota_media = dff["NOTA"].mean()
    satisfeitos = len(dff[dff["NOTA"] >= 4])
    total_avaliados = len(dff[dff["NOTA"].notna()])
    pct_sat = (satisfeitos / total_avaliados * 100) if total_avaliados > 0 else 0
    
    kpi_nota = f"{nota_media:.2f}"
    kpi_pct = f"{pct_sat:.1f}%"

    # --- 1. DONUT: Distribuição ---
    df_dist = dff["NOTA"].value_counts().reset_index().sort_values("NOTA")
    df_dist.columns = ["Nota", "Qtd"]
    # Cores fixas para notas 1 a 5 (Vermelho -> Verde)
    cores_map = {1: "#ef4444", 2: "#f97316", 3: "#eab308", 4: "#84cc16", 5: "#22c55e"}
    
    fig_dist = go.Figure(data=[go.Pie(
        labels=df_dist["Nota"], values=df_dist["Qtd"], hole=.6,
        marker_colors=[cores_map.get(x, "#cbd5e1") for x in df_dist["Nota"]]
    )])
    fig_dist.update_layout(margin=dict(t=0, b=0, l=0, r=0), showlegend=True, legend=dict(orientation="v", y=0.5))

    # --- 2. MATRIZ: Volume x Nota (Scatter) ---
    if "ORGAO" in dff.columns:
        df_orgao = dff.groupby("ORGAO").agg(
            Volume=("NOTA", "count"),
            Nota_Media=("NOTA", "mean")
        ).reset_index()
        # Filtra órgãos com poucas avaliações para não sujar o gráfico (Min 5 avaliações)
        df_orgao = df_orgao[df_orgao["Volume"] > 5]
        
        fig_matriz = px.scatter(
            df_orgao, x="Volume", y="Nota_Media", 
            hover_name="ORGAO", size="Volume", 
            color="Nota_Media", color_continuous_scale="RdYlGn", # Escala Vermelho-Amarelo-Verde
            title=None
        )
        # Linha média
        fig_matriz.add_hline(y=nota_media, line_dash="dot", line_color="grey", annotation_text="Média Geral")
        fig_matriz.update_layout(
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=20, b=20, l=20, r=20),
            xaxis=dict(title="Quantidade de Avaliações", showgrid=True, gridcolor="#f1f5f9"),
            yaxis=dict(title="Nota Média", showgrid=True, gridcolor="#f1f5f9", range=[0.5, 5.5])
        )
    else:
        fig_matriz = go.Figure()

    # --- 3. RANKING (Barras) ---
    if "ORGAO" in dff.columns:
        df_rank = dff.groupby("ORGAO")["NOTA"].mean().reset_index()
        df_rank = df_rank.sort_values("NOTA", ascending=True).tail(10) # Melhores notas
        
        fig_rank = px.bar(df_rank, x="NOTA", y="ORGAO", orientation="h", text_auto=".2f")
        fig_rank.update_traces(marker_color=COR_DESTAQUE)
        fig_rank.update_layout(
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=20, b=20, l=10, r=20),
            xaxis=dict(showgrid=True, range=[0, 5.5], title="Nota Média"),
            yaxis=dict(title=None)
        )
    else:
        fig_rank = go.Figure()

    return kpi_nota, kpi_pct, fig_dist, fig_matriz, fig_rank