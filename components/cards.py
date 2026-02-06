import dash_bootstrap_components as dbc
from dash import html, dcc

from utils.design import CONFIG_GRAFICOS

def criar_card(titulo, conteudo, id_grafico=None, md=6, cor_borda=None, altura="400px"):
    """Card padronizado para gráficos"""
    
    estilo = {
        'borderRadius': '12px',
        'boxShadow': '0 4px 12px rgba(0,0,0,0.08)',
        'border': f'1px solid {cor_borda}' if cor_borda else '1px solid #e0e0e0',
        'height': altura,
        'overflow': 'hidden'
    }
    
    return dbc.Col(
        dbc.Card(style=estilo, children=[
            dbc.CardHeader([
                html.H6(titulo, className="mb-0 fw-bold"),
                html.Small("📊 Clique e arraste para zoom", className="text-muted")
            ], className="py-3"),
            dbc.CardBody(
                dcc.Graph(
                    id=id_grafico,
                    config=CONFIG_GRAFICOS,
                    style={'height': 'calc(100% - 60px)'}
                ) if id_grafico else conteudo,
                className="p-3"
            )
        ]),
        md=md,
        className="mb-4"
    )