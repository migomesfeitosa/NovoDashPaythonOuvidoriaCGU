import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils.preprocessamento import carregar_dados_lai, carregar_dados_ouvidoria, UFS_BRASIL

try:
    from utils.design import MAPA_FONTE
except:
    MAPA_FONTE = {}

# --- ESTILO LIMPO PARA GRÁFICOS ---
def layout_premium(fig):
    fig.update_layout(
        margin=dict(l=10, r=10, t=25, b=5),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font={'family': "Inter, sans-serif", 'color': '#64748b'},
        xaxis={'showgrid': False, 'showline': True, 'linecolor': '#e2e8f0'},
        yaxis={'showgrid': True, 'gridcolor': '#f1f5f9', 'zeroline': False},
        hoverlabel={'bgcolor': "white", 'font_size': 12, 'font_family': "Inter"},
        title_font={'size': 13, 'color': '#334155', 'family': 'Inter, sans-serif'},
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

# --- CARGA ---
def get_dados_integrados():
    df_lai = carregar_dados_lai("pedidos")
    df_ouv = carregar_dados_ouvidoria()
    cols = ["ANO", "UF", "Fonte", "ORGAO", "RESULTADO"]
    dfs = []
    if not df_lai.empty: dfs.append(df_lai[[c for c in cols if c in df_lai.columns]])
    if not df_ouv.empty:
        if "RESULTADO" not in df_ouv.columns and "ASSUNTO" in df_ouv.columns:
            df_ouv["RESULTADO"] = df_ouv["ASSUNTO"]
        dfs.append(df_ouv[[c for c in cols if c in df_ouv.columns]])
    if dfs: return pd.concat(dfs, ignore_index=True)
    return pd.DataFrame()

df_full = get_dados_integrados()
opcoes_ano = sorted(list(df_full["ANO"].unique()), reverse=True) if not df_full.empty and "ANO" in df_full.columns else []
opcoes_uf = sorted(UFS_BRASIL) + ["NI"]

# --- LAYOUT ---
layout = html.Div(
    className="d-flex flex-column",
    style={"height": "100vh", "padding": "0px", "backgroundColor": "#f4f6f8", "overflow": "hidden"}, 
    children=[
        
        # 1. FILTROS
        html.Div(
            className="filter-container",
            style={"margin": "10px 10px 0 10px", "padding": "10px 15px"}, # Margin bottom removida, o gap cuida do resto
            children=[
                dbc.Row([
                    dbc.Col([
                        html.H5("Visão Geral", className="m-0 fw-bold text-dark"),
                        html.Span("Monitoramento Federal", className="text-muted small", style={"fontSize": "0.75rem"}),
                    ], md=2),
                    
                    dbc.Col([html.Label("Ano", className="small fw-bold mb-0"), dcc.Dropdown(id="filtro-ano", options=[{"label": i, "value": i} for i in opcoes_ano], multi=True, placeholder="Todos", style={"fontSize": "0.85rem"})], md=3),
                    dbc.Col([html.Label("UF (Origem)", className="small fw-bold mb-0"), dcc.Dropdown(id="filtro-uf", options=[{"label": i, "value": i} for i in opcoes_uf], multi=True, placeholder="Todas", style={"fontSize": "0.85rem"})], md=2),
                    dbc.Col([html.Label("Fonte", className="small fw-bold mb-0"), dcc.Dropdown(id="filtro-tipo", options=[{"label": "Ouvidoria", "value": "Ouvidoria"}, {"label": "LAI", "value": "LAI"}], placeholder="Ambos", style={"fontSize": "0.85rem"})], md=2),
                    
                    dbc.Col([
                        html.Label("Ação", className="small fw-bold mb-0"),
                        dbc.Button(
                            [html.I(className="bi bi-download me-2"), "Excel"], 
                            id="btn-download", 
                            color="success", 
                            outline=True, 
                            size="sm",
                            className="w-100 d-flex align-items-center justify-content-center", 
                            style={"height": "36px"}
                        ),
                        dcc.Download(id="download-dataframe-csv"),
                    ], md=3),
                ], className="g-2 align-items-end")
            ]
        ),

        # 2. CONTEÚDO (Flexbox com GAP)
        html.Div(
            className="flex-grow-1 d-flex flex-column",
            # AQUI ESTÁ A MÁGICA: "gap": "15px" cria o espaço entre os filhos automaticamente
            style={"overflowY": "hidden", "padding": "15px 10px 10px 10px", "gap": "15px"},
            children=[
                
                # KPIs
                dbc.Row([
                    dbc.Col(html.Div(className="custom-card kpi-card", style={"borderLeftColor": "#5a67d8"}, title="Total de manifestações", children=[
                        html.Div(className="p-2 ps-3", children=[html.Div("Volume Total", className="kpi-title"), html.Div(id="kpi-total", className="kpi-value")])
                    ]), md=4),
                    dbc.Col(html.Div(className="custom-card kpi-card", style={"borderLeftColor": "#ecc94b"}, title="Canal principal", children=[
                        html.Div(className="p-2 ps-3", children=[html.Div("Fonte Principal", className="kpi-title"), html.Div(id="kpi-fonte", className="kpi-value")])
                    ]), md=4),
                    dbc.Col(html.Div(className="custom-card kpi-card", style={"borderLeftColor": "#48bb78"}, title="Abrangência geográfica", children=[
                        html.Div(className="p-2 ps-3", children=[html.Div("Abrangência (UFs)", className="kpi-title"), html.Div(id="kpi-ufs", className="kpi-value")])
                    ]), md=4),
                ], className="g-2 flex-shrink-0", style={"minHeight": "80px"}), # Removi mb-2

                # LINHA 1 (Flex Grow)
                dbc.Row([
                    dbc.Col(html.Div(className="custom-card", children=[
                        html.Div("Evolução Temporal", className="card-header-custom py-1"),
                        dcc.Graph(id="grafico-evolucao", style={"flex": "1"}, config={'displayModeBar': False}, className="h-100")
                    ]), md=8, className="h-100"), 
                    
                    dbc.Col(html.Div(className="custom-card", children=[
                        html.Div("Fonte", className="card-header-custom py-1"),
                        dcc.Graph(id="grafico-tipo", style={"flex": "1"}, config={'displayModeBar': False}, className="h-100")
                    ]), md=4, className="h-100"),
                ], className="g-2", style={"flex": "1", "minHeight": "0"}), # Removi mb-2

                # LINHA 2 (Flex Grow)
                dbc.Row([
                    dbc.Col(html.Div(className="custom-card", children=[
                        html.Div("Top Órgãos", className="card-header-custom py-1"),
                        dcc.Graph(id="grafico-orgaos", style={"flex": "1"}, config={'displayModeBar': False}, className="h-100")
                    ]), md=6, className="h-100"),
                    
                    dbc.Col(html.Div(className="custom-card", children=[
                        html.Div("Principais Assuntos", className="card-header-custom py-1"),
                        dcc.Graph(id="grafico-assuntos", style={"flex": "1"}, config={'displayModeBar': False}, className="h-100")
                    ]), md=6, className="h-100"),
                ], className="g-2", style={"flex": "1", "minHeight": "0"}),
            ]
        )
    ]
)

# --- CALLBACK ---
@callback(
    [Output("kpi-total", "children"), Output("kpi-fonte", "children"), Output("kpi-ufs", "children"),
     Output("grafico-evolucao", "figure"), Output("grafico-tipo", "figure"),
     Output("grafico-orgaos", "figure"), Output("grafico-assuntos", "figure"),
     Output("download-dataframe-csv", "data")],
    [Input("filtro-ano", "value"), Input("filtro-uf", "value"),
     Input("filtro-tipo", "value"), Input("btn-download", "n_clicks")],
    prevent_initial_call=False
)
def update_home(anos, ufs, tipo, n_clicks):
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else "No Trigger"
    dff = df_full.copy()
    fig_vazia = go.Figure().update_layout(title="Sem dados", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis={'visible': False}, yaxis={'visible': False})

    if not dff.empty:
        if anos: dff = dff[dff["ANO"].isin(anos if isinstance(anos, list) else [anos])]
        if ufs: dff = dff[dff["UF"].isin(ufs if isinstance(ufs, list) else [ufs])] if "UF" in dff.columns else dff
        if tipo: dff = dff[dff["Fonte"] == tipo]

    download_data = dcc.send_data_frame(dff.to_csv, "dados.csv", index=False) if trigger_id == "btn-download" and not dff.empty else None
    if dff.empty: return "0", "-", "0", fig_vazia, fig_vazia, fig_vazia, fig_vazia, None

    total = f"{len(dff):,}".replace(",", ".")
    kpi2 = dff["Fonte"].value_counts().idxmax()
    if "UF" in dff.columns:
        ufs_validas = [u for u in dff["UF"].unique() if u in UFS_BRASIL]
        kpi3 = "Federal" if len(ufs_validas) == 0 else str(len(ufs_validas))
    else: kpi3 = "-"

    if "ANO" in dff.columns:
        evol = dff.groupby(["ANO", "Fonte"], observed=True).size().reset_index(name="Qtd")
        fig_ev = layout_premium(px.area(evol, x="ANO", y="Qtd", color="Fonte", color_discrete_map=MAPA_FONTE))
    else: fig_ev = fig_vazia

    df_p = dff["Fonte"].value_counts().reset_index()
    df_p.columns = ["Fonte", "Qtd"]
    fig_tp = layout_premium(px.pie(df_p, values="Qtd", names="Fonte", hole=0.6, color_discrete_map=MAPA_FONTE))
    fig_tp.update_layout(showlegend=False, annotations=[dict(text=total, x=0.5, y=0.5, font_size=16, showarrow=False)])

    def barras(col, cor, eixo):
        if col not in dff.columns: return fig_vazia
        top = dff[col].value_counts().head(7).reset_index()
        top.columns = [eixo, "Qtd"]
        top = top.sort_values("Qtd")
        fig = px.bar(top, x="Qtd", y=eixo, orientation="h")
        fig.update_traces(marker_color=cor)
        return layout_premium(fig)

    return total, kpi2, kpi3, fig_ev, fig_tp, barras("ORGAO", "#48bb78", "Órgão"), barras("RESULTADO", "#f6ad55", "Assunto"), download_data