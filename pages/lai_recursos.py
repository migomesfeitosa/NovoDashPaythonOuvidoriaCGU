import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
from utils.preprocessamento import carregar_dados_lai

# --- CARREGAMENTO DE DADOS ---
df_ped = carregar_dados_lai("pedidos")
df_rec = carregar_dados_lai("recursos")

if not df_rec.empty:
    df_rec.columns = [c.upper().strip() for c in df_rec.columns]
    # Mapeamento exaustivo para garantir que a Pizza encontre os dados
    mapa = {
        "DECISAO": "RESULTADO", 
        "DESC_DECISAO": "RESULTADO", 
        "SITUACAO": "RESULTADO",
        "SITUACAO_RECURSO": "RESULTADO",
        "INSTANCIA": "INSTANCIA"
    }
    df_rec.rename(columns=mapa, inplace=True)

# --- LAYOUT ---
layout = html.Div(style={
    "height": "100vh", 
    "display": "flex", 
    "flexDirection": "column", 
    "backgroundColor": "#f4f7f9",
    "overflowX": "hidden"
}, children=[

    # 1. HEADER (Largura Máxima de 1600px para não esticar)
    html.Div(className="p-3", style={"flexShrink": "0"}, children=[
        dbc.Container(fluid=True, children=[
            html.Div(className="bg-white p-3 rounded shadow-sm", style={"borderLeft": "5px solid #6c5ce7"}, children=[
                html.H4("Recursos & Judicialização", className="fw-bold m-0 text-dark"),
                html.Small("Análise de contestação de respostas e instâncias de revisão", className="text-muted")
            ]),
        ], style={"maxWidth": "1600px"}) 
    ]),

    # 2. ÁREA DE GRÁFICOS
    html.Div(style={
        "flexGrow": "1", 
        "overflowY": "auto", 
        "padding": "0 15px 15px 15px"
    }, children=[
        dbc.Container(fluid=True, style={"maxWidth": "1600px"}, children=[
            
            dbc.Row([
                # Funil
                dbc.Col(dbc.Card([
                    dbc.CardBody([
                        html.H6("Funil de Recorrência", className="fw-bold text-muted mb-3"),
                        dcc.Graph(id="lair-fig-funil", style={"height": "320px"})
                    ])
                ], className="border-0 shadow-sm h-100"), xs=12, lg=6),

                # Pizza com Legenda no Canto Direito
                dbc.Col(dbc.Card([
                    dbc.CardBody([
                        html.H6("Resultado dos Recursos", className="fw-bold text-muted mb-3"),
                        dcc.Graph(id="lair-fig-pizza", style={"height": "320px"})
                    ])
                ], className="border-0 shadow-sm h-100"), xs=12, lg=6),
            ], className="g-3 mb-3 mx-0"),

            # Instâncias
            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardBody([
                        html.H6("Volume por Instância", className="fw-bold text-muted mb-3"),
                        dcc.Graph(id="lair-fig-instancia", style={"height": "280px"})
                    ])
                ], className="border-0 shadow-sm"), width=12)
            ], className="g-3 mx-0")
        ])
    ])
])

# --- CALLBACK ---
@callback(
    [Output("lair-fig-funil", "figure"), 
     Output("lair-fig-pizza", "figure"), 
     Output("lair-fig-instancia", "figure")],
    [Input("url", "pathname")] 
)
def update_recursos(_):
    # 1. Funil
    fig_funil = px.funnel(
        pd.DataFrame({'Etapa': ['Pedidos', 'Recursos'], 'Qtd': [len(df_ped), len(df_rec)]}),
        x='Qtd', y='Etapa', color_discrete_sequence=["#2563eb"]
    )
    fig_funil.update_layout(margin=dict(l=50, r=50, t=10, b=10), paper_bgcolor='rgba(0,0,0,0)')

    # 2. Pizza com Legenda à Direita
    if "RESULTADO" in df_rec.columns and not df_rec.empty:
        df_decisao = df_rec["RESULTADO"].value_counts().reset_index()
        df_decisao.columns = ["Decisao", "Qtd"]
        
        fig_pizza = px.pie(
            df_decisao, names="Decisao", values="Qtd",
            hole=0.5, color_discrete_sequence=px.colors.qualitative.Safe
        )
        # --- AJUSTE DA LEGENDA AQUI ---
        fig_pizza.update_layout(
            margin=dict(l=10, r=10, t=10, b=10),
            showlegend=True,
            legend=dict(
                orientation="v",      # Vertical
                yanchor="middle",     # Centralizado verticalmente
                y=0.5,                # Posição 50% da altura
                xanchor="left",       # Ancorado à esquerda da posição X
                x=1.02                # Posicionado logo após o fim do gráfico (canto direito)
            )
        )
    else:
        fig_pizza = px.pie(title="Coluna de Decisão não encontrada")

    # 3. Instância
    if "INSTANCIA" in df_rec.columns:
        df_inst = df_rec["INSTANCIA"].value_counts().reset_index()
        df_inst.columns = ["Instancia", "Qtd"]
        fig_inst = px.bar(df_inst, x="Instancia", y="Qtd", text="Qtd", color="Instancia")
        fig_inst.update_layout(showlegend=False, plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=20, r=20, t=20, b=20))
    else: fig_inst = {}

    return fig_funil, fig_pizza, fig_inst