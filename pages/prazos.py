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
        return [go.Figure().add_annotation(text="Sem Dados", showarrow=False)] * 7

    dff = df_prazo.copy()

    # Filtro de Ano (Suporta lista ou valor único)
    if anos:
        lista_anos = anos if isinstance(anos, list) else [anos]
        dff = dff[dff["ANO"].isin(lista_anos)]

    # Se a coluna principal não existir, criamos uma zerada para o app não quebrar
    if "TEMPO_RESOLUCAO" not in dff.columns:
        dff["TEMPO_RESOLUCAO"] = 0

    # ... (Restante dos seus cálculos de KPI e Gráficos permanecem iguais)

    # --- CÁLCULO DE KPIs ---
    tempo_medio = dff["TEMPO_RESOLUCAO"].mean()

    # Lógica de Atraso
    if "DIAS_ATRASO" in dff.columns:
        atrasados = len(dff[dff["DIAS_ATRASO"] > 0])
        atraso_medio = dff[dff["DIAS_ATRASO"] > 0]["DIAS_ATRASO"].mean()
    else:
        atrasados = len(dff[dff["TEMPO_RESOLUCAO"] > 30])
        atraso_medio = 0

    sla_pct = ((len(dff) - atrasados) / len(dff) * 100) if len(dff) > 0 else 0

    # Pior Órgão (Calculado apenas sobre quem tem dados de tempo)
    pior_nome, pior_val = "-", 0
    if "ORGAO" in dff.columns:
        df_valid = dff.dropna(subset=["TEMPO_RESOLUCAO"])
        if not df_valid.empty:
            pior_nome = df_valid.groupby("ORGAO")["TEMPO_RESOLUCAO"].mean().idxmax()
            pior_val = df_valid.groupby("ORGAO")["TEMPO_RESOLUCAO"].mean().max()
            # Encurta nome para o KPI
            pior_nome = (
                str(pior_nome)[:18] + "..."
                if len(str(pior_nome)) > 18
                else str(pior_nome)
            )

    # --- GERAÇÃO DOS GRÁFICOS ---

    # 1. Histograma
    fig_hist = px.histogram(
        dff, x="TEMPO_RESOLUCAO", nbins=30, color_discrete_sequence=[CORES["roxo"]]
    )
    fig_hist.update_layout(LAYOUT_CLEAN)
    fig_hist.update_layout(xaxis_title="Dias", yaxis_title=None, bargap=0.1)

    # 2. Evolução
    if "DATA_REGISTRO" in dff.columns:
        df_ev = (
            dff.groupby(dff["DATA_REGISTRO"].dt.to_period("M").astype(str))[
                "TEMPO_RESOLUCAO"
            ]
            .mean()
            .reset_index()
        )
        fig_ev = px.line(df_ev, x="DATA_REGISTRO", y="TEMPO_RESOLUCAO", markers=True)
        fig_ev.update_traces(line_color=CORES["azul"], line_width=3)
        fig_ev.update_layout(LAYOUT_CLEAN)
        fig_ev.update_layout(xaxis_title=None, yaxis_title=None)
    else:
        fig_ev = go.Figure()

    # 3. Ranking
    if "ORGAO" in dff.columns:
        df_rank = dff.dropna(subset=["TEMPO_RESOLUCAO"])
        df_rank = df_rank.groupby("ORGAO")["TEMPO_RESOLUCAO"].mean().reset_index()
        df_rank = df_rank.sort_values("TEMPO_RESOLUCAO", ascending=True).tail(10)

        # Encurtar nomes longos
        df_rank["ORGAO_CURTO"] = df_rank["ORGAO"].apply(
            lambda x: str(x)[:25] + "..." if len(str(x)) > 25 else str(x)
        )

        fig_rank = px.bar(
            df_rank,
            x="TEMPO_RESOLUCAO",
            y="ORGAO_CURTO",
            orientation="h",
            text_auto=".0f",
        )
        fig_rank.update_traces(
            marker_color=CORES["laranja"], textposition="outside", cliponaxis=False
        )
        fig_rank.update_layout(LAYOUT_CLEAN)
        fig_rank.update_layout(
            margin=dict(l=0, r=40, t=10, b=10),
            xaxis=dict(showgrid=True),
            yaxis=dict(automargin=True),
        )
    else:
        fig_rank = go.Figure()

    # Retorno
    return (
        criar_kpi(tempo_medio, "Tempo Médio", "d"),
        criar_kpi(
            sla_pct,
            "No Prazo",
            "%",
            CORES["azul"] if sla_pct > 80 else CORES["laranja"],
        ),
        criar_kpi(
            atraso_medio if not np.isnan(atraso_medio) else 0,
            "Atraso Médio",
            "d",
            CORES["vermelho"],
        ),
        criar_kpi_texto(pior_nome, f"{pior_val:.0f} dias"),
        fig_hist,
        fig_ev,
        fig_rank,
    )
