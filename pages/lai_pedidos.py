import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from utils.preprocessamento import carregar_dados_lai

# --- CONFIGURAÇÕES VISUAIS ---
CORES = {
    "roxo": "#7c3aed", "azul": "#2563eb", "verde": "#16a34a",
    "vermelho": "#dc2626", "laranja": "#d97706", "cinza": "#64748b"
}

# --- DADOS (ETL Otimizado) ---
# --- DADOS (ETL Otimizado com Correção de Category) ---
df = carregar_dados_lai("pedidos")

if not df.empty:
    df.columns = [c.upper().strip() for c in df.columns]
    
    # Mapeamento
    mapa = {
        "DECISAO": "RESULTADO", "SITUACAO": "STATUS", 
        "ORGAO_DESTINATARIO": "ORGAO", "ANO": "ANO"
    }
    df.rename(columns=mapa, inplace=True)
    
    # --- CORREÇÃO DO PRAZO (De Category para Numeric) ---
    if 'PRAZO' in df.columns:
        # Primeiro convertemos para string, depois removemos lixo e passamos para número
        df['PRAZO'] = (
            df['PRAZO']
            .astype(str)
            .str.replace(',', '.', regex=False)
            .str.extract('(\d+\.?\d*)')[0] # Extrai apenas os números (caso tenha "10 dias")
        )
        df['PRAZO'] = pd.to_numeric(df['PRAZO'], errors='coerce')

    # --- CORREÇÃO DA DATA (Caso as primeiras linhas sejam nulas) ---
    if 'DATA' in df.columns:
        df['DATA'] = pd.to_datetime(df['DATA'], errors='coerce')
        # Se o ANO estiver vazio, tenta extrair da DATA
        if df['ANO'].isnull().all():
            df['ANO'] = df['DATA'].dt.year
            
opcoes_ano = sorted(list(df["ANO"].dropna().unique()), reverse=True) if not df.empty else []

# --- COMPONENTES VISUAIS ---
def card_kpi(titulo, valor, cor=CORES["roxo"]):
    return dbc.Col(
        html.Div(
            className="p-3 bg-white shadow-sm h-100 border-start border-4",
            style={"borderLeftColor": cor, "borderRadius": "8px"},
            children=[
                html.Small(titulo.upper(), className="text-muted fw-bold", style={"fontSize": "0.7rem"}),
                html.H4(valor, className="m-0 fw-bold mt-1", style={"color": "#1e293b"})
            ]
        ), md=3, xs=6
    )

# --- LAYOUT ---
layout = dbc.Container(fluid=True, children=[
    # 1. Filtros
    html.Div(className="bg-white p-3 rounded shadow-sm my-3 border", children=[
        dbc.Row([
            dbc.Col([
                html.H5("Pedidos & Eficiência", className="fw-bold m-0"), 
                html.Small("Gestão de Demandas da LAI", className="text-muted")
            ], md=5),
            dbc.Col(dcc.Dropdown(
                id="laip-ano", 
                options=[{"label": int(i), "value": i} for i in opcoes_ano], 
                multi=True, placeholder="Todos os Anos"
            ), md=4),
            dbc.Col(dbc.Button("Exportar CSV", id="laip-btn", color="success", outline=True, className="w-100"), md=3),
        ], className="align-items-center")
    ]),

    # 2. KPIs e Gráficos
    dbc.Row(id="laip-kpis", className="mb-3 g-3"),
    
    dbc.Row([
        # Gráfico Pizza (Resultado)
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H6("Resultado dos Pedidos", className="fw-bold text-secondary mb-3"),
                dcc.Graph(id="laip-fig-resultado", style={"height": "380px"})
            ])
        ], className="shadow-sm border-0"), md=4),
        
        # Gráfico Ranking (Barras)
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H6("Top 10 Órgãos Mais Demandados", className="fw-bold text-secondary mb-3"),
                dcc.Graph(id="laip-fig-ranking", style={"height": "380px"})
            ])
        ], className="shadow-sm border-0"), md=8),
    ], className="g-3"),
    
    dcc.Download(id="laip-download")
], style={"paddingBottom": "30px"})

# --- CALLBACK ---
@callback(
    [Output("laip-kpis", "children"), Output("laip-fig-resultado", "figure"), 
     Output("laip-fig-ranking", "figure"), Output("laip-download", "data")],
    [Input("laip-ano", "value"), Input("laip-btn", "n_clicks")]
)
def update_pedidos(anos, n_clicks):
    dff = df.copy()
    if anos: dff = dff[dff["ANO"].isin(anos)]
    
    # 1. KPIs
    total = len(dff)
    conc = neg = 0
    if 'RESULTADO' in dff.columns:
        conc = len(dff[dff['RESULTADO'].astype(str).str.contains('Concedido|Deferido', case=False, na=False)])
        neg = len(dff[dff['RESULTADO'].astype(str).str.contains('Negado|Indeferido', case=False, na=False)])
    
    # Prazo Médio (Garante que só pega números reais)
    prazo_texto = "—"
    if 'PRAZO' in dff.columns:
        # Remove nulos e foca apenas em valores positivos
        col_prazo_limpa = dff['PRAZO'].dropna()
        if not col_prazo_limpa.empty:
            media = col_prazo_limpa[col_prazo_limpa >= 0].mean()
            if pd.notna(media):
                prazo_texto = f"{media:.1f} dias"
    
    kpis = [
        card_kpi("Total Pedidos", f"{total:,}".replace(",", "."), CORES["roxo"]),
        card_kpi("Concessão", f"{(conc/total*100):.1f}%" if total > 0 else "0%", CORES["verde"]),
        card_kpi("Negação", f"{(neg/total*100):.1f}%" if total > 0 else "0%", CORES["vermelho"]),
        card_kpi("Prazo Médio Resposta", prazo_texto, CORES["laranja"])
    ]

    # 2. Pizza - Legenda Ajustada (Abaixo do gráfico para não sobrepor)
    if "RESULTADO" in dff.columns:
        df_res = dff["RESULTADO"].value_counts().head(5).reset_index()
        df_res.columns = ["Resultado", "Qtd"]
        fig_res = px.pie(df_res, names="Resultado", values="Qtd", hole=0.5, 
                         color_discrete_sequence=px.colors.qualitative.Pastel)
        
        fig_res.update_layout(
            showlegend=True,
            legend=dict(
                orientation="h",       # Horizontal
                yanchor="top", y=-0.05, # Joga para baixo do gráfico
                xanchor="center", x=0.5 # Centraliza
            ),
            margin=dict(l=20, r=20, t=30, b=80), # Aumentamos 'b' para a legenda aparecer
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
    else:
        fig_res = go.Figure().add_annotation(text="Sem dados", showarrow=False)

    # 3. Barras Ranking
    if "ORGAO" in dff.columns:
        df_rank = dff["ORGAO"].value_counts().head(10).reset_index()
        df_rank.columns = ["Orgao", "Qtd"]
        df_rank['Label'] = df_rank['Orgao'].str[:35] + "..."
        
        fig_rank = px.bar(df_rank.sort_values("Qtd"), x="Qtd", y="Label", orientation="h", text="Qtd")
        fig_rank.update_traces(marker_color=CORES["azul"], textposition="outside")
        fig_rank.update_layout(
            xaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
            yaxis=dict(title=None),
            margin=dict(l=10, r=40, t=10, b=10),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
    else:
        fig_rank = go.Figure().add_annotation(text="Sem dados", showarrow=False)

    dl = dcc.send_data_frame(dff.to_csv, "lai_pedidos.csv", index=False) if n_clicks else None
    return kpis, fig_res, fig_rank, dl