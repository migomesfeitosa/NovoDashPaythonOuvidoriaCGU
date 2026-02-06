from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc

def criar_filtros_interativos(id_prefixo):
    """Filtros que se atualizam dinamicamente"""
    
    return html.Div([
        dbc.Row([
            # Filtro de Período
            dbc.Col([
                html.Label("📅 Período", className="fw-bold small mb-2"),
                dcc.DatePickerRange(
                    id=f"filtro-periodo-{id_prefixo}",
                    start_date='2023-01-01',
                    end_date='2024-12-31',
                    display_format='DD/MM/YYYY',
                    className="w-100"
                )
            ], md=3),
            
            # Filtro Dinâmico de Órgãos
            dbc.Col([
                html.Label("🏛️ Órgão", className="fw-bold small mb-2"),
                dcc.Dropdown(
                    id=f"filtro-orgao-{id_prefixo}",
                    multi=True,
                    placeholder="Selecione órgãos...",
                    optionHeight=50
                )
            ], md=3),
            
            # Filtro de Situação
            dbc.Col([
                html.Label("📋 Situação", className="fw-bold small mb-2"),
                dcc.Dropdown(
                    id=f"filtro-situacao-{id_prefixo}",
                    options=[
                        {'label': '✅ Respondidas', 'value': 'respondida'},
                        {'label': '⏳ Em andamento', 'value': 'andamento'},
                        {'label': '📦 Arquivadas', 'value': 'arquivada'}
                    ],
                    multi=True,
                    placeholder="Todas situações"
                )
            ], md=3),
            
            # Botões de Ação
            dbc.Col([
                html.Label("⠀", className="mb-2"),  # Espaçador
                dbc.ButtonGroup([
                    dbc.Button("Aplicar Filtros", id=f"btn-aplicar-{id_prefixo}", color="primary"),
                    dbc.Button("Limpar", id=f"btn-limpar-{id_prefixo}", outline=True, color="secondary")
                ], className="w-100")
            ], md=3)
        ], className="g-3"),
        
        # Indicador de filtros ativos
        html.Div(id=f"badges-filtros-{id_prefixo}", className="mt-3")
    ])