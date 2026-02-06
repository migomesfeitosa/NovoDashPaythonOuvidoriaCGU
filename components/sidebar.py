import dash
from dash import html
import dash_bootstrap_components as dbc

# --- ESTILOS DO SIDEBAR ---
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "260px",
    "padding": "2rem 1rem",
    "backgroundColor": "#ffffff",
    "boxShadow": "4px 0 15px rgba(0,0,0,0.02)",
    "zIndex": 1050,
    # "overflowY": "hidden",
    "overflowY": "auto",
    "borderRight": "1px solid #f0f0f0",
}


def get_nav_link_style(active=False):
    base_style = {
        "color": "#64748b",
        "fontWeight": "500",
        "fontSize": "0.85rem",
        "padding": "8px 15px",
        "borderRadius": "8px",
        "marginBottom": "4px",
        "transition": "all 0.2s ease",
        "display": "flex",
        "alignItems": "center",
        "textDecoration": "none",
    }
    if active:
        # Estilo Ativo: Roxo claro no fundo, Roxo forte no texto
        base_style.update(
            {"backgroundColor": "#f3e8ff", "color": "#7c3aed", "fontWeight": "600"}
        )
    return base_style


def criar_sidebar(pathname):
    return html.Div(
        style=SIDEBAR_STYLE,
        children=[
            # CABEÇALHO
            html.Div(
                className="mb-4 text-center",
                children=[
                    html.H3(
                        "Gov.Data",
                        className="fw-bold mb-0",
                        style={"color": "#7c3aed", "letterSpacing": "-1px"},
                    ),
                    html.Small(
                        "Inteligência & Transparência",
                        className="text-muted",
                        style={"fontSize": "0.75rem"},
                    ),
                ],
            ),
            html.Hr(style={"borderColor": "#f0f0f0"}),
            dbc.Nav(
                [
                    # 1. ESTRATÉGICO
                    html.Div(
                        "ESTRATÉGICO",
                        className="small text-muted fw-bold mt-3 mb-2 px-3",
                        style={"fontSize": "0.7rem", "letterSpacing": "0.5px"},
                    ),
                    dbc.NavLink(
                        [html.I(className="bi bi-grid-fill me-3"), "Resumo Executivo"],
                        href="/resumo",
                        active="exact",
                        style=get_nav_link_style(pathname == "/resumo"),
                    ),
                    # 2. OUVIDORIA (Foco em Gestão)
                    html.Div(
                        "GESTÃO DE OUVIDORIA",
                        className="small text-muted fw-bold mt-4 mb-2 px-3",
                        style={"fontSize": "0.7rem", "letterSpacing": "0.5px"},
                    ),
                    dbc.NavLink(
                        [
                            html.I(className="bi bi-list-check me-3"),
                            "Monitoramento Diário",
                        ],
                        href="/ouvidoria",
                        active="exact",
                        style=get_nav_link_style(pathname == "/ouvidoria"),
                    ),
                    dbc.NavLink(
                        [html.I(className="bi bi-stopwatch-fill me-3"), "Prazos e SLA"],
                        href="/prazos",
                        active="exact",
                        style=get_nav_link_style(pathname == "/prazos"),
                    ),
                    # 3. GESTÃO DA LAI (Destrinchada)
                    html.Div(
                        "GESTÃO DA LAI",
                        className="small text-muted fw-bold mt-4 mb-2 px-3",
                        style={
                            "fontSize": "0.7rem",
                            "letterSpacing": "0.5px",
                            "color": "#7c3aed",
                        },
                    ),
                    dbc.NavLink(
                        [
                            html.I(className="bi bi-bar-chart-fill me-3"),
                            "Pedidos & Eficiência",
                        ],
                        href="/lai",
                        active="exact",
                        style=get_nav_link_style(pathname == "/lai"),
                    ),
                    dbc.NavLink(
                        [
                            html.I(className="bi bi-chat-quote-fill me-3"),
                            "Temas Solicitados",
                        ],
                        href="/lai/temas",
                        active="exact",
                        style=get_nav_link_style(pathname == "/lai/temas"),
                    ),
                    dbc.NavLink(
                        [html.I(className="bi bi-hammer me-3"), "Recursos (Judicial)"],
                        href="/lai/recursos",
                        active="exact",
                        style=get_nav_link_style(pathname == "/lai/recursos"),
                    ),
                    # 4. ANÁLISE TEMÁTICA (O que faltava)
                    html.Div(
                        "ANÁLISE TEMÁTICA",
                        className="small text-muted fw-bold mt-4 mb-2 px-3",
                        style={"fontSize": "0.7rem", "letterSpacing": "0.5px"},
                    ),
                    dbc.NavLink(
                        [html.I(className="bi bi-map-fill me-3"), "Território (Mapas)"],
                        href="/geo",
                        active="exact",
                        style=get_nav_link_style(pathname == "/geo"),
                    ),
                    dbc.NavLink(
                        [
                            html.I(className="bi bi-star-fill me-3"),
                            "Qualidade dos Órgãos",
                        ],
                        href="/qualidade",
                        active="exact",
                        style=get_nav_link_style(pathname == "/qualidade"),
                    ),
                    dbc.NavLink(
                        [
                            html.I(className="bi bi-people-fill me-3"),
                            "Perfil do Cidadão",
                        ],
                        href="/perfil",
                        active="exact",
                        style=get_nav_link_style(pathname == "/perfil"),
                    ),
                    # 5. INTELIGÊNCIA ARTIFICIAL (O que faltava)
                    html.Div(
                        "INTELIGÊNCIA ARTIFICIAL",
                        className="small text-muted fw-bold mt-4 mb-2 px-3",
                        style={"fontSize": "0.7rem", "letterSpacing": "0.5px"},
                    ),
                    dbc.NavLink(
                        [html.I(className="bi bi-cpu me-3"), "Mineração de Texto"],
                        href="/topicos",
                        active="exact",
                        style=get_nav_link_style(pathname == "/topicos"),
                    ),
                    dbc.NavLink(
                        [
                            html.I(className="bi bi-robot me-2"),
                            "Modelos Preditivos (IA)",
                        ],
                        href="/ia-modelos",
                        active="exact",
                    ),
                ],
                vertical=True,
                pills=True,
                className="pb-5",
            ),  # Padding bottom extra para não cortar o último item
        ],
    )
