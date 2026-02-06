import dash_bootstrap_components as dbc
from dash import html
import pandas as pd

def criar_header(df_lai=None, df_ouv=None):
    """Cabeçalho com KPIs destacados"""
    
    kpi1 = "12.548" if df_lai is None else f"{len(df_lai):,}"
    kpi2 = "8.2" if df_ouv is None else "8.2"
    kpi3 = "94%" if df_ouv is None else "94%"
    
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.H1("📊 Painel de Monitoramento CGU", 
                       className="text-primary mb-0"),
                html.P("Controle Central de Transparência e Ouvidoria", 
                      className="text-muted mb-4")
            ], md=8),
            
            dbc.Col([
                dbc.Row([
                    dbc.Col(
                        dbc.Card([
                            dbc.CardBody([
                                html.H6("Total Pedidos LAI", className="text-muted small"),
                                html.H3(kpi1, className="text-primary fw-bold")
                            ])
                        ], className="shadow-sm border-0"),
                        md=4
                    ),
                    dbc.Col(
                        dbc.Card([
                            dbc.CardBody([
                                html.H6("Satisfação Média", className="text-muted small"),
                                html.H3(f"{kpi2}/10", className="text-warning fw-bold")
                            ])
                        ], className="shadow-sm border-0"),
                        md=4
                    ),
                    dbc.Col(
                        dbc.Card([
                            dbc.CardBody([
                                html.H6("No Prazo", className="text-muted small"),
                                html.H3(kpi3, className="text-success fw-bold")
                            ])
                        ], className="shadow-sm border-0"),
                        md=4
                    ),
                ])
            ], md=12)
        ])
    ], className="mb-4")