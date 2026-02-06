from dash import html, dcc

def criar_filtros_padrao(id_prefixo, opcoes_ano, opcoes_uf):
    """
    Cria uma linha com filtros de Ano e UF.
    id_prefixo: string usada para diferenciar os IDs entre páginas (ex: 'home', 'lai')
    """
    return html.Div(
        style={
            "backgroundColor": "white", "padding": "15px", "borderRadius": "8px",
            "boxShadow": "0 2px 4px rgba(0,0,0,0.05)", "marginBottom": "20px"
        },
        children=[
            html.H5("Filtros", className="mb-3"),
            html.Div(
                className="row",
                children=[
                    html.Div(
                        className="col-md-6",
                        children=[
                            html.Label("📅 Ano", className="fw-bold"),
                            dcc.Dropdown(
                                id=f"filtro-ano-{id_prefixo}",
                                options=[{'label': i, 'value': i} for i in opcoes_ano],
                                multi=True,
                                placeholder="Selecione os anos...",
                            )
                        ]
                    ),
                    html.Div(
                        className="col-md-6",
                        children=[
                            html.Label("📍 UF", className="fw-bold"),
                            dcc.Dropdown(
                                id=f"filtro-uf-{id_prefixo}",
                                options=[{'label': i, 'value': i} for i in opcoes_uf],
                                multi=True,
                                placeholder="Selecione as UFs...",
                            )
                        ]
                    )
                ]
            )
        ]
    )