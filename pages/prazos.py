import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from utils.preprocessamento import carregar_dados_ouvidoria

# ==============================================================================
# 1. CONFIGURAÇÕES VISUAIS (Importante: Definir no topo)
# ==============================================================================
CORES = {
    "roxo": "#7c3aed",
    "azul": "#2563eb",
    "laranja": "#d97706",
    "vermelho": "#dc2626",
    "cinza": "#cbd5e1",
}

LAYOUT_CLEAN = {
    "plot_bgcolor": "rgba(0,0,0,0)",
    "paper_bgcolor": "rgba(0,0,0,0)",
    "font": {"family": "Inter, sans-serif", "color": "#64748b"},
    "margin": {"l": 10, "r": 10, "t": 20, "b": 20},
}

# ==============================================================================
# 2. CARGA DE DADOS
# ==============================================================================
print(">>> CARREGANDO DADOS DE PRAZOS...")
# --- CARGA E TRATAMENTO DE DADOS ---
df_prazo = carregar_dados_ouvidoria()

if not df_prazo.empty:
    # Padronização de nomes
    df_prazo.columns = [str(c).upper().strip() for c in df_prazo.columns]

    # Mapeamento expandido (Baseado nos padrões da CGU/Ouvidorias)
    mapa_cols = {
        "DIAS PARA RESOLUÇÃO": "TEMPO_RESOLUCAO",
        "DIAS RESOLUCAO": "TEMPO_RESOLUCAO",
        "TEMPO_RESPOSTA": "TEMPO_RESOLUCAO",
        "PRAZO_RESPOSTA": "TEMPO_RESOLUCAO",
        "DIAS_ATRASO": "DIAS_ATRASO",
        "DATA_REGISTRO": "DATA_REGISTRO",
        "DATA REGISTRO": "DATA_REGISTRO",
        "DATA_ABERTURA": "DATA_REGISTRO",  # Adicione o nome que estiver no seu arquivo
        "DT_REGISTRO": "DATA_REGISTRO",    # Outra variação comum
        "NOME ÓRGÃO": "ORGAO",
    }
    df_prazo.rename(columns=mapa_cols, inplace=True)

    # Tenta "adivinhar" a coluna de tempo se o mapeamento falhar
    if "TEMPO_RESOLUCAO" not in df_prazo.columns:
        cols_tempo = [
            c for c in df_prazo.columns if "DIAS" in c or "TEMPO" in c or "PRAZO" in c
        ]
        if cols_tempo:
            df_prazo.rename(columns={cols_tempo[0]: "TEMPO_RESOLUCAO"}, inplace=True)

    # Conversão Numérica (Tratando vírgulas e erros)
    for col in ["TEMPO_RESOLUCAO", "DIAS_ATRASO"]:
        if col in df_prazo.columns:
            df_prazo[col] = pd.to_numeric(
                df_prazo[col].astype(str).str.replace(",", "."), errors="coerce"
            ).fillna(0)

    # Tratamento de Datas e ANO
    if "DATA_REGISTRO" in df_prazo.columns:
        df_prazo["DATA_REGISTRO"] = pd.to_datetime(
            df_prazo["DATA_REGISTRO"], errors="coerce"
        )
        df_prazo["ANO"] = df_prazo["DATA_REGISTRO"].dt.year

# Lista para o filtro (Protegida contra erro se ANO não existir)
if not df_prazo.empty and "ANO" in df_prazo.columns:
    opcoes_ano = sorted(list(df_prazo["ANO"].dropna().unique()), reverse=True)
else:
    opcoes_ano = []


# ==============================================================================
# 3. HELPERS (Funções de Gráfico)
# ==============================================================================
def criar_kpi(valor, titulo, sulfixo="", cor=CORES["roxo"]):
    fig = go.Figure(
        go.Indicator(
            mode="number",
            value=valor,
            number={
                "suffix": sulfixo,
                "font": {"size": 35, "color": cor, "family": "Inter"},
            },
            title={"text": titulo.upper(), "font": {"size": 11, "color": "#64748b"}},
        )
    )
    fig.update_layout(
        paper_bgcolor="white", height=120, margin=dict(l=0, r=0, t=30, b=0)
    )
    return fig


def criar_kpi_texto(texto, subtexto, cor=CORES["laranja"]):
    fig = go.Figure()
    fig.add_annotation(
        text=str(texto),
        x=0.5,
        y=0.6,
        showarrow=False,
        font=dict(size=16, color=cor, family="Inter"),
    )
    fig.add_annotation(
        text=str(subtexto),
        x=0.5,
        y=0.3,
        showarrow=False,
        font=dict(size=12, color="gray", family="Inter"),
    )
    fig.update_layout(
        title=dict(
            text="MAIS LENTO",
            x=0.5,
            y=0.92,
            xanchor="center",
            yanchor="top",
            font=dict(size=11, color="#64748b"),
        ),
        paper_bgcolor="white",
        height=140,
        margin=dict(l=0, r=0, t=45, b=0),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )

    return fig


# ==============================================================================
# 4. LAYOUT
# ==============================================================================
layout = html.Div(
    className="d-flex flex-column",
    style={
        "height": "100vh",
        "padding": "0px",
        "backgroundColor": "#f8fafc",
        "overflow": "hidden",
    },
    children=[
        # Filtros
        html.Div(
            className="filter-container",
            style={
                "margin": "10px 10px 0 10px",
                "padding": "10px 15px",
                "backgroundColor": "white",
                "borderRadius": "8px",
                "boxShadow": "0 2px 4px rgba(0,0,0,0.05)",
            },
            children=[
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H5(
                                    "Gestão de Prazos",
                                    className="fw-bold m-0 text-dark",
                                ),
                                html.Small("SLA e Eficiência", className="text-muted"),
                            ],
                            md=4,
                        ),
                        dbc.Col(
                            dcc.Dropdown(
                                id="prazo-ano",
                                options=[{"label": i, "value": i} for i in opcoes_ano],
                                multi=True,
                                placeholder="Filtrar Ano",
                            ),
                            md=4,
                        ),
                        dbc.Col(
                            html.Div(
                                id="resumo-prazo",
                                className="text-end fw-bold text-primary",
                            ),
                            md=4,
                        ),
                    ],
                    className="align-items-center",
                )
            ],
        ),
        # Conteúdo Principal
        html.Div(
            className="flex-grow-1 p-3",
            style={"overflow": "hidden", "display": "flex", "flexDirection": "column"},
            children=[
                # Linha 1: KPIs
                dbc.Row(
                    [
                        dbc.Col(
                            dcc.Graph(
                                id="kpi-tempo-medio",
                                config={"displayModeBar": False},
                                style={"height": "120px"},
                            ),
                            md=3,
                        ),
                        dbc.Col(
                            dcc.Graph(
                                id="kpi-sla-pct",
                                config={"displayModeBar": False},
                                style={"height": "120px"},
                            ),
                            md=3,
                        ),
                        dbc.Col(
                            dcc.Graph(
                                id="kpi-atraso-medio",
                                config={"displayModeBar": False},
                                style={"height": "120px"},
                            ),
                            md=3,
                        ),
                        dbc.Col(
                            dcc.Graph(
                                id="kpi-orgao-lento",
                                config={"displayModeBar": False},
                                style={"height": "120px"},
                            ),
                            md=3,
                        ),
                    ],
                    className="mb-3 g-2",
                ),
                # Linha 2: Gráficos
                dbc.Row(
                    [
                        dbc.Col(
                            html.Div(
                                className="custom-card p-3 bg-white shadow-sm h-100",
                                children=[
                                    html.H6(
                                        "Distribuição",
                                        className="fw-bold text-secondary mb-2",
                                    ),
                                    dcc.Graph(
                                        id="fig-hist-prazo",
                                        style={"height": "calc(100vh - 280px)"},
                                    ),
                                ],
                            ),
                            md=4,
                            style={"height": "100%"},
                        ),
                        dbc.Col(
                            html.Div(
                                className="custom-card p-3 bg-white shadow-sm h-100",
                                children=[
                                    html.H6(
                                        "Evolução",
                                        className="fw-bold text-secondary mb-2",
                                    ),
                                    dcc.Graph(
                                        id="fig-evolucao-tempo",
                                        style={"height": "calc(100vh - 280px)"},
                                    ),
                                ],
                            ),
                            md=4,
                            style={"height": "100%"},
                        ),
                        dbc.Col(
                            html.Div(
                                className="custom-card p-3 bg-white shadow-sm h-100",
                                children=[
                                    html.H6(
                                        "Lentidão (Top 10)",
                                        className="fw-bold text-secondary mb-2",
                                    ),
                                    dcc.Graph(
                                        id="fig-ranking-tempo",
                                        style={"height": "calc(100vh - 280px)"},
                                    ),
                                ],
                            ),
                            md=4,
                            style={"height": "100%"},
                        ),
                    ],
                    className="g-2 h-100",
                ),
            ],
        ),
    ],
)


# ==============================================================================
# 5. CALLBACK
# ==============================================================================
@callback(
    [
        Output("kpi-tempo-medio", "figure"),
        Output("kpi-sla-pct", "figure"),
        Output("kpi-atraso-medio", "figure"),
        Output("kpi-orgao-lento", "figure"),
        Output("fig-hist-prazo", "figure"),
        Output("fig-evolucao-tempo", "figure"),
        Output("fig-ranking-tempo", "figure"),
    ],
    [Input("prazo-ano", "value")],
)
def update_prazos(anos):
    if df_prazo.empty:
        empty_fig = go.Figure().add_annotation(text="Sem Dados", showarrow=False)
        return [empty_fig] * 7

    dff = df_prazo.copy()

    # --- PROTEÇÃO CONTRA KEYERROR ---
    # Se por algum motivo o mapeamento falhou, garantimos que a coluna exista, mesmo que zerada
    if "TEMPO_RESOLUCAO" not in dff.columns:
        # Tenta procurar qualquer coluna que tenha 'DIAS' ou 'TEMPO' no nome
        cols_possiveis = [c for c in dff.columns if 'DIAS' in str(c).upper() or 'TEMPO' in str(c).upper()]
        if cols_possiveis:
            dff["TEMPO_RESOLUCAO"] = dff[cols_possiveis[0]]
        else:
            dff["TEMPO_RESOLUCAO"] = 0 # Cria a coluna com zero para evitar o erro de KeyError
    
    # Garante que seja numérico (se houver strings, o mean() quebra)
    dff["TEMPO_RESOLUCAO"] = pd.to_numeric(dff["TEMPO_RESOLUCAO"], errors='coerce').fillna(0)
    # --------------------------------

    # Filtro de Ano
    if anos:
        lista_anos = anos if isinstance(anos, list) else [anos]
        dff = dff[dff["ANO"].isin(lista_anos)]
    
    if dff.empty:
        empty_fig = go.Figure().add_annotation(text="Nenhum dado", showarrow=False)
        return [empty_fig] * 7

    # Agora o cálculo não vai mais dar KeyError
    tempo_medio = float(dff["TEMPO_RESOLUCAO"].mean())
    
    # ... resto do código
    
    # Cálculo de Atrasos
    col_atraso = "DIAS_ATRASO" if "DIAS_ATRASO" in dff.columns else "TEMPO_RESOLUCAO"
    mask_atraso = dff[col_atraso] > (30 if col_atraso == "TEMPO_RESOLUCAO" else 0)
    
    total_atrasados = len(dff[mask_atraso])
    atraso_medio = dff.loc[mask_atraso, col_atraso].mean()
    atraso_medio = float(atraso_medio) if pd.notnull(atraso_medio) else 0
    
    sla_pct = ((len(dff) - total_atrasados) / len(dff) * 100) if len(dff) > 0 else 0

    # 4. KPI de Órgão Lento
    pior_nome, pior_val = "N/A", 0
    if "ORGAO" in dff.columns:
        resumo_orgao = dff.groupby("ORGAO")["TEMPO_RESOLUCAO"].mean()
        if not resumo_orgao.empty:
            pior_nome = resumo_orgao.idxmax()
            pior_val = resumo_orgao.max()
            pior_nome = str(pior_nome)[:15] + "..." if len(str(pior_nome)) > 15 else str(pior_nome)

    # 5. Gráfico de Evolução (Correção do Erro de Period)
    if "DATA_REGISTRO" in dff.columns and not dff["DATA_REGISTRO"].isnull().all():
        df_ev = dff.copy()
        # Converte para String para evitar erro de serialização JSON
        df_ev["MES_REF"] = df_ev["DATA_REGISTRO"].dt.strftime("%Y-%m")
        df_ev = df_ev.groupby("MES_REF")["TEMPO_RESOLUCAO"].mean().reset_index()
        
        fig_ev = px.line(df_ev, x="MES_REF", y="TEMPO_RESOLUCAO", markers=True)
        fig_ev.update_traces(line_color=CORES["azul"], line_width=3)
    else:
        fig_ev = go.Figure().add_annotation(text="Datas ausentes", showarrow=False)

    # 6. Gráfico de Ranking (Pareto-like)
    if "ORGAO" in dff.columns:
        df_rank = dff.groupby("ORGAO")["TEMPO_RESOLUCAO"].mean().reset_index()
        df_rank = df_rank.sort_values("TEMPO_RESOLUCAO", ascending=True).tail(10)
        
        fig_rank = px.bar(
            df_rank, x="TEMPO_RESOLUCAO", y="ORGAO", 
            orientation="h", text_auto=".0f"
        )
        fig_rank.update_traces(marker_color=CORES["laranja"])
    else:
        fig_rank = go.Figure()

    # 7. Histograma
    fig_hist = px.histogram(dff, x="TEMPO_RESOLUCAO", color_discrete_sequence=[CORES["roxo"]])

    # Aplicar Layout Clean em todos
    for f in [fig_ev, fig_rank, fig_hist]:
        f.update_layout(LAYOUT_CLEAN)

    return (
        criar_kpi(tempo_medio, "Tempo Médio", " d"),
        criar_kpi(sla_pct, "No Prazo", "%", CORES["azul"] if sla_pct > 80 else CORES["laranja"]),
        criar_kpi(atraso_medio, "Atraso Médio", " d", CORES["vermelho"]),
        criar_kpi_texto(pior_nome, f"{pior_val:.0f} dias"),
        fig_hist,
        fig_ev,
        fig_rank,
    )