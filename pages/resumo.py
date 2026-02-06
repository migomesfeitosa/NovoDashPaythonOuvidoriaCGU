import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils.preprocessamento import carregar_dados_ouvidoria, carregar_dados_lai, UFS_BRASIL

# --- CONFIGURAÇÕES VISUAIS ---
CORES = {
    "roxo": "#7c3aed", "azul": "#2563eb", "verde": "#16a34a",
    "vermelho": "#dc2626", "laranja": "#f59e0b", "cinza": "#64748b"
}

LAYOUT_CLEAN = {
    "plot_bgcolor": "rgba(0,0,0,0)", "paper_bgcolor": "rgba(0,0,0,0)",
    "font": {"family": "Inter, sans-serif", "color": "#64748b"},
    "margin": {"l": 10, "r": 10, "t": 30, "b": 10},
}

# --- CARGA E TRATAMENTO DE DADOS ---
print(">>> CARREGANDO RESUMO (MODO OTIMIZADO)...")

# 1. OUVIDORIA
df_ouv = carregar_dados_ouvidoria()
if not df_ouv.empty:
    df_ouv.columns = [c.upper().strip() for c in df_ouv.columns]
    mapa_ouv = {
        "DATA REGISTRO": "DATA", "DATA_REGISTRO": "DATA",
        "DIAS PARA RESOLUÇÃO": "PRAZO", "TEMPO_RESOLUCAO": "PRAZO",
        "SITUACAO": "STATUS", "UF_MANIFESTANTE": "UF", "UF_DEMANDANTE": "UF"
    }
    df_ouv.rename(columns=mapa_ouv, inplace=True)
    if "DATA" in df_ouv.columns:
        df_ouv["DATA"] = pd.to_datetime(df_ouv["DATA"], dayfirst=True, errors="coerce")
        df_ouv["ANO"] = df_ouv["DATA"].dt.year
    if "PRAZO" in df_ouv.columns:
        df_ouv["PRAZO"] = pd.to_numeric(df_ouv["PRAZO"], errors="coerce")

# 2. LAI (CARGA COM CORREÇÃO DE MEMÓRIA)
try:
    df_lai = carregar_dados_lai("pedidos")
except:
    df_lai = pd.DataFrame()

# Fallback para leitura local se necessário
# --- 2. LAI (TRATAMENTO ROBUSTO COM FALLBACK) ---
if not df_lai.empty:
    df_lai.columns = [c.upper().strip() for c in df_lai.columns]
    
    mapa_lai = {
        "DATAREGISTRO": "DATA", "DATA_RESPOSTA": "DATA_FIM",
        "DECISAO": "RESULTADO", "SITUACAO": "STATUS",
        "UF_SOLICITANTE": "UF", "ORGAODESTINATARIO": "ORGAO"
    }
    df_lai.rename(columns=mapa_lai, inplace=True)
    
    # Converte datas
    for col in ["DATA", "DATA_FIM"]:
        if col in df_lai.columns:
            df_lai[col] = pd.to_datetime(df_lai[col], errors="coerce")
    
    if "DATA" in df_lai.columns:
        df_lai["ANO"] = df_lai["DATA"].dt.year

    # --- LÓGICA DE PRAZO (O SEGREDO PARA SAIR DO ZERO) ---
    # Passo A: Tenta calcular pelas datas
    if "DATA" in df_lai.columns and "DATA_FIM" in df_lai.columns:
        df_lai["PRAZO_CALC"] = (df_lai["DATA_FIM"] - df_lai["DATA"]).dt.days
    
    # Passo B: Fallback para a coluna PRAZO que o diagnóstico mostrou ser 'category'
    if "PRAZO" in df_lai.columns:
        # Resolve o erro de categoria: converte para texto e depois para número
        prazo_original = pd.to_numeric(
            df_lai["PRAZO"].astype(str).str.replace(',', '.', regex=False), 
            errors='coerce'
        )
        
        if "PRAZO_CALC" not in df_lai.columns:
            df_lai["PRAZO_CALC"] = prazo_original
        else:
            # Preenche onde a data falhou com o valor original
            df_lai["PRAZO_CALC"] = df_lai["PRAZO_CALC"].fillna(prazo_original)

    # Limpeza final
    if "PRAZO_CALC" in df_lai.columns:
        df_lai.loc[df_lai["PRAZO_CALC"] < 0, "PRAZO_CALC"] = 0
        df_lai["PRAZO_CALC"] = df_lai["PRAZO_CALC"].fillna(0)

# --- LISTAS ---
def get_anos(df):
    if "ANO" in df.columns:
        return pd.to_numeric(df["ANO"], errors='coerce').dropna().astype(int).unique().tolist()
    return []

opcoes_ano = sorted(list(set(get_anos(df_ouv) + get_anos(df_lai))), reverse=True)
opcoes_uf = sorted(UFS_BRASIL)

# --- COMPONENTE KPI ---
def card_kpi_novo(titulo, valor, icone, cor_icone, label_extra=""):
    return dbc.Col(
        html.Div(
            className="d-flex align-items-center bg-white shadow-sm p-3 h-100 position-relative",
            style={"borderRadius": "10px", "border": "1px solid #f1f5f9", "overflow": "hidden"},
            children=[
                html.Div(style={"position": "absolute", "left": 0, "top": 0, "bottom": 0, "width": "4px", "backgroundColor": cor_icone}),
                html.Div(
                    html.I(className=f"{icone} fs-4"),
                    className="d-flex align-items-center justify-content-center me-3 ms-2",
                    style={"width": "48px", "height": "48px", "borderRadius": "50%", "backgroundColor": f"{cor_icone}15", "color": cor_icone}
                ),
                html.Div([
                    html.H6(titulo, className="text-muted small fw-bold mb-0 text-uppercase"),
                    html.H3(valor, className="fw-bold m-0 text-dark"),
                    html.Small(label_extra, className="text-muted", style={"fontSize": "0.7rem"})
                ])
            ]
        ), md=3, sm=6, className="mb-3"
    )

# --- LAYOUT ---
layout = html.Div(
    className="d-flex flex-column",
    style={"height": "100vh", "overflow": "hidden"}, 
    children=[
        html.Div(
            className="bg-white p-3 shadow-sm mx-3 mt-3 rounded border",
            style={"flex": "0 0 auto"},
            children=[
                dbc.Row([
                    dbc.Col([
                        html.H4("Visão Integrada", className="fw-bold m-0 text-dark"),
                        html.Small("Resumo Executivo (Ouvidoria + LAI)", className="text-muted"),
                    ], md=4),
                    dbc.Col(dcc.Dropdown(id="resumo-ano", options=[{"label": i, "value": i} for i in opcoes_ano], value=[], multi=True, placeholder="📅 Todos os Anos"), md=4),
                    dbc.Col(dcc.Dropdown(id="resumo-uf", options=[{"label": i, "value": i} for i in opcoes_uf], multi=True, placeholder="📍 Todos os Estados"), md=4),
                ], className="align-items-center")
            ],
        ),
        html.Div(
            className="flex-grow-1 px-3 py-3",
            style={"overflowY": "auto", "overflowX": "hidden"},
            children=[
                html.H6("INDICADORES DE VOLUME & AGILIDADE", className="fw-bold text-secondary mb-3 mt-2 border-bottom pb-2"),
                dbc.Row(id="kpis-linha-1", className="g-3"),
                dbc.Row([
                    dbc.Col(html.Div(className="custom-card p-3 bg-white shadow-sm h-100", children=[
                        html.H6(["Evolução ", html.Span("Ouvidoria (Anual)", style={"color": CORES["roxo"]})], className="fw-bold text-dark mb-3"),
                        dcc.Graph(id="fig-evol-ouv-int", style={"height": "280px"}, config={"displayModeBar": False})
                    ]), md=6),
                    dbc.Col(html.Div(className="custom-card p-3 bg-white shadow-sm h-100", children=[
                        html.H6(["Evolução ", html.Span("LAI (Anual)", style={"color": CORES["azul"]})], className="fw-bold text-dark mb-3"),
                        dcc.Graph(id="fig-evol-lai-int", style={"height": "280px"}, config={"displayModeBar": False})
                    ]), md=6),
                ], className="g-3 mb-4"),
                html.H6("INDICADORES DE QUALIDADE & TEMAS", className="fw-bold text-secondary mb-3 border-bottom pb-2"),
                dbc.Row([
                    dbc.Col([dbc.Row(id="kpis-linha-qualidade", className="g-3")], md=6),
                    dbc.Col(html.Div(className="custom-card p-3 bg-white shadow-sm h-100", children=[
                        html.H6("Top Assuntos (Ouvidoria) vs Órgãos (LAI)", className="fw-bold text-dark mb-3"),
                        dcc.Graph(id="fig-barras-mistas", style={"height": "280px"}, config={"displayModeBar": False})
                    ]), md=6),
                ], className="g-3 mb-5")
            ]
        )
    ]
)

# --- CALLBACK ---
@callback(
    [Output("kpis-linha-1", "children"), Output("kpis-linha-qualidade", "children"),
     Output("fig-evol-ouv-int", "figure"), Output("fig-evol-lai-int", "figure"), Output("fig-barras-mistas", "figure")],
    [Input("resumo-ano", "value"), Input("resumo-uf", "value")]
)
def update_integrado(anos, ufs):
    dff_ouv = df_ouv.copy()
    dff_lai = df_lai.copy()
    
    # Filtros
    if anos:
        lista_anos = anos if isinstance(anos, list) else [anos]
        if "ANO" in dff_ouv.columns: dff_ouv = dff_ouv[dff_ouv["ANO"].isin(lista_anos)]
        if "ANO" in dff_lai.columns: dff_lai = dff_lai[dff_lai["ANO"].isin(lista_anos)]
    if ufs:
        lista_ufs = ufs if isinstance(ufs, list) else [ufs]
        if "UF" in dff_ouv.columns: dff_ouv = dff_ouv[dff_ouv["UF"].isin(lista_ufs)]
        if "UF" in dff_lai.columns: dff_lai = dff_lai[dff_lai["UF"].isin(lista_ufs)]

    # --- CÁLCULOS OUVIDORIA ---
    vol_ouv = len(dff_ouv)
    prazo_ouv = dff_ouv[dff_ouv["PRAZO"] > 0]["PRAZO"].mean() if "PRAZO" in dff_ouv.columns else 0
    # Correção: Adicionamos "" dentro do fillna para não dar erro de Valor
   # Primeiro astype(str), depois fazemos a busca. Isso mata o erro de Categoria.
    resolvidos = len(dff_ouv[dff_ouv["STATUS"].astype(str).str.contains("Concluída|Encerrada|Respondida", case=False, na=False)]) if "STATUS" in dff_ouv.columns else 0
    pct_resolv = (resolvidos / vol_ouv * 100) if vol_ouv > 0 else 0
    pendentes_ouv = vol_ouv - resolvidos

    # --- CÁLCULOS LAI (CORREÇÃO DO ERRO DE MEMÓRIA) ---
    vol_lai = len(dff_lai)
    prazo_lai = 0
    if "PRAZO_CALC" in dff_lai.columns:
        prazo_lai = dff_lai[dff_lai["PRAZO_CALC"] >= 0]["PRAZO_CALC"].mean()
    if pd.isna(prazo_lai): prazo_lai = 0

    # CORREÇÃO CRÍTICA:
    # 1. Removemos .astype(str) para não explodir a memória
    # 2. Usamos na=False para tratar nulos sem converter
    concedidos = 0
    if "RESULTADO" in dff_lai.columns:
        concedidos = len(dff_lai[dff_lai["RESULTADO"].str.contains("Concedido|Deferido|Acesso Concedido", case=False, na=False)])
        
    pct_transp = (concedidos / vol_lai * 100) if vol_lai > 0 else 0
    negados_lai = vol_lai - concedidos

    # KPIs Linha 1
    kpis_1 = [
        card_kpi_novo("Total Ouvidoria", f"{vol_ouv:,}".replace(",", "."), "bi bi-megaphone-fill", CORES["roxo"], "Manifestações"),
        card_kpi_novo("Total LAI", f"{vol_lai:,}".replace(",", "."), "bi bi-file-earmark-lock2-fill", CORES["azul"], "Pedidos de Acesso"),
        card_kpi_novo("Tempo Ouvidoria", f"{prazo_ouv:.0f} dias", "bi bi-clock-history", CORES["laranja"], "Média Resolução"),
        card_kpi_novo("Tempo LAI", f"{prazo_lai:.0f} dias", "bi bi-hourglass-split", CORES["laranja"], "Média Resposta"),
    ]

    # KPIs Qualidade
    def card_mini(titulo, valor, cor):
        return dbc.Col(html.Div(className="p-3 bg-white shadow-sm border rounded", children=[
            html.Small(titulo, className="text-muted fw-bold d-block mb-1"),
            html.H4(valor, className="fw-bold m-0", style={"color": cor})
        ]), md=6, className="mb-3")

    kpis_qualidade = [
        card_mini("Resolutividade (Ouv)", f"{pct_resolv:.1f}%", CORES["verde"]),
        card_mini("Transparência (LAI)", f"{pct_transp:.1f}%", CORES["verde"]),
        card_mini("Pendentes (Ouv)", f"{pendentes_ouv}", CORES["vermelho"]),
        card_mini("Negados (LAI)", f"{negados_lai}", CORES["vermelho"]),
    ]

    # Gráficos Evolução (Anual)
    def plot_evol_anual(df, cor, nome):
        fig = go.Figure()
        if "DATA" in df.columns and not df.empty:
            ts = df.groupby(df["DATA"].dt.year).size().reset_index(name="Qtd")
            ts.columns = ["Ano", "Qtd"]
            fig.add_trace(go.Scatter(x=ts["Ano"], y=ts["Qtd"], fill='tozeroy', mode='lines+markers', line=dict(color=cor, width=3), marker=dict(size=8)))
            fig.update_layout(LAYOUT_CLEAN, xaxis_title=None, yaxis_title=None, margin=dict(l=0,r=0,t=10,b=20), xaxis=dict(tickmode='linear', dtick=1))
        else: fig.add_annotation(text="Sem dados", showarrow=False)
        return fig

    fig_evol_ouv = plot_evol_anual(dff_ouv, CORES["roxo"], "Ouvidoria")
    fig_evol_lai = plot_evol_anual(dff_lai, CORES["azul"], "LAI")

    # Gráfico Barras Misto
    fig_misto = go.Figure()
    if "ASSUNTO" in dff_ouv.columns:
        top_o = dff_ouv["ASSUNTO"].value_counts().head(3).reset_index()
        top_o.columns = ["Item", "Qtd"]
        top_o["Item"] = "OUV: " + top_o["Item"].apply(lambda x: str(x)[:15])
        fig_misto.add_trace(go.Bar(y=top_o["Item"], x=top_o["Qtd"], orientation='h', name="Ouvidoria", marker_color=CORES["roxo"]))

    if "ORGAO" in dff_lai.columns:
        top_l = dff_lai["ORGAO"].value_counts().head(3).reset_index()
        top_l.columns = ["Item", "Qtd"]
        top_l["Item"] = "LAI: " + top_l["Item"].apply(lambda x: str(x)[:15])
        fig_misto.add_trace(go.Bar(y=top_l["Item"], x=top_l["Qtd"], orientation='h', name="LAI", marker_color=CORES["azul"]))
    
    fig_misto.update_layout(LAYOUT_CLEAN, barmode="group", legend=dict(orientation="h", y=-0.2))

    return kpis_1, kpis_qualidade, fig_evol_ouv, fig_evol_lai, fig_misto


