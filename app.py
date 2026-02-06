import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output

# Importar o Sidebar
from components.sidebar import criar_sidebar

# Importar as Páginas
from pages import (
    resumo,
    lai_pedidos, 
    lai_temas, 
    lai_recursos, 
    ouvidoria, 
    prazos, 
    geo, 
    qualidade, 
    perfil, 
    ia_modelos,
    topicos
)

# Inicializar App
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP], suppress_callback_exceptions=True)

# --- LAYOUT PRINCIPAL ---
# Importante: Precisamos de um ID para o Sidebar também ('sidebar-container')
app.layout = html.Div([
    dcc.Location(id="url"),
    
    # Container do Sidebar (Será atualizado via Callback para mudar a cor do botão ativo)
    html.Div(id="sidebar-container"), 
    
    # Conteúdo da Página (Com margem para não ficar embaixo do sidebar)
    html.Div(id="page-content", style={"marginLeft": "260px", "transition": "margin-left .3s"})
])

# --- CALLBACK DE ROTEAMENTO (ONDE ESTAVA O ERRO) ---
@app.callback(
    [Output("page-content", "children"), 
     Output("sidebar-container", "children")], # <--- O ERRO ESTAVA AQUI: TEM 2 OUTPUTS
    [Input("url", "pathname")]
)
def render_page_content(pathname):
    # 1. Gera o Sidebar com o botão ativo correto
    sidebar = criar_sidebar(pathname)
    
    # 2. Define qual layout carregar
    if pathname == "/" or pathname == "/resumo":
        content = resumo.layout
    
    elif pathname == "/ouvidoria":
        content = ouvidoria.layout
    
    elif pathname == "/prazos":
        content = prazos.layout

    elif pathname == "/qualidade":
        content = qualidade.layout
        
    elif pathname == "/geo":
        content = geo.layout
        
    elif pathname == "/perfil":
        content = perfil.layout
        
    elif pathname == "/topicos":
        content = topicos.layout

    # --- ROTAS DA LAI ---
    elif pathname == "/lai":
        content = lai_pedidos.layout
        
    elif pathname == "/lai/temas":
        content = lai_temas.layout
        
    elif pathname == "/lai/recursos":
        content = lai_recursos.layout
        
    elif pathname == "/ia-modelos":
        content = ia_modelos.layout
        
    else:
        # Página 404
        content = html.Div([
            html.H1("404: Página não encontrada", className="text-danger"),
            html.Hr(),
            html.P(f"O caminho {pathname} não foi reconhecido...")
        ], className="p-5")

    # --- RETORNA A TUPLA (CONTEÚDO, SIDEBAR) ---
    return content, sidebar  # <--- CORREÇÃO FINAL: Retorna os 2 itens
    

if __name__ == "__main__":
    app.run(debug=True)  # <--- FORMA CORRETA