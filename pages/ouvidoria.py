import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils.preprocessamento import carregar_dados_ouvidoria, UFS_BRASIL

# --- PALETA DE CORES ---
COR_SUCESSO = "#16a34a"   # Verde
COR_ALERTA = "#f59e0b"    # Laranja/Amarelo
COR_ERRO = "#dc2626"      # Vermelho
COR_NEUTRA = "#475569"    # Cinza Escuro
COR_DESTAQUE = "#7c3aed"  # Roxo
COR_BARRAS = "#cbd5e1"    # Cinza Claro

# --- CARGA E TRATAMENTO DE DADOS (BLINDADO) ---
print(">>> CARREGANDO OUVIDORIA (DEBUG)...")

df_ouv = carregar_dados_ouvidoria()

if not df_ouv.empty:
    # 1. Padroniza colunas para MAIÚSCULAS e remove espaços extras
    df_ouv.columns = [str(c).upper().strip() for c in df_ouv.columns]
    
    # 2. Mapeamento Universal (Para garantir que funcione com qualquer CSV)
    mapa_colunas = {
        # Datas
        "DATA REGISTRO": "DATA", "DATA_REGISTRO": "DATA", "DT_REGISTRO": "DATA",
        "DATA CONCLUSAO": "DATA_FIM", "DATA_CONCLUSAO": "DATA_FIM", "DT_CONCLUSAO": "DATA_FIM",
        "DATA RESPOSTA": "DATA_FIM",
        
        # Métricas
        "DIAS PARA RESOLUÇÃO": "PRAZO", "TEMPO_RESOLUCAO": "PRAZO", "DIAS_RESOLUCAO": "PRAZO",
        "PRAZO_ATENDIMENTO": "PRAZO",
        
        # Dimensões
        "SITUAÇÃO": "STATUS", "SITUACAO": "STATUS", "STATUS": "STATUS",
        "UF DO MUNICÍPIO MANIFESTAÇÃO": "UF", "UF_MANIFESTACAO": "UF", "UF": "UF", "UF_MANIFESTANTE": "UF",
        "ASSUNTO": "ASSUNTO", "ASSUNTO PEDIDO": "ASSUNTO",
        "NOME ÓRGÃO": "ORGAO", "ORGAO DESTINATARIO": "ORGAO", "ORGAO": "ORGAO",
        "TIPO MANIFESTAÇÃO": "TIPO", "TIPO": "TIPO"
    }
    df_ouv.rename(columns=mapa_colunas, inplace=True)

    # 3. Conversões de Tipos (Essencial para não dar erro de gráfico)
    
    # Datas
    if 'DATA' in df_ouv.columns:
        df_ouv['DATA'] = pd.to_datetime(df_ouv['DATA'], dayfirst=True, errors='coerce')
        df_ouv['ANO'] = df_ouv['DATA'].dt.year
    
    if 'DATA_FIM' in df_ouv.columns:
        df_ouv['DATA_FIM'] = pd.to_datetime(df_ouv['DATA_FIM'], dayfirst=True, errors='coerce')

    # Prazo (Trata vírgula e calcula se necessário)
    if 'PRAZO' in df_ouv.columns:
        # Tenta limpar string (ex: "15,5" -> 15.5)
        df_ouv['PRAZO'] = df_ouv['PRAZO'].astype(str).str.replace(',', '.', regex=False)
        df_ouv['PRAZO'] = pd.to_numeric(df_ouv['PRAZO'], errors='coerce')
    
    # Se PRAZO estiver vazio/zerado mas tivermos as datas, calculamos!
    if 'DATA' in df_ouv.columns and 'DATA_FIM' in df_ouv.columns:
        # Cria coluna auxiliar de cálculo
        df_ouv['PRAZO_CALC'] = (df_ouv['DATA_FIM'] - df_ouv['DATA']).dt.days
        
        # Preenche o PRAZO original onde ele for nulo com o valor calculado
        if 'PRAZO' not in df_ouv.columns:
            df_ouv['PRAZO'] = df_ouv['PRAZO_CALC']
        else:
            df_ouv['PRAZO'] = df_ouv['PRAZO'].fillna(df_ouv['PRAZO_CALC'])
            
    # Garantia final de UF
    if "UF" not in df_ouv.columns:
        df_ouv["UF"] = "NI"

# Filtros (Ordenados e sem NaNs)
opcoes_ano = sorted(list(df_ouv["ANO"].dropna().unique()), reverse=True) if "ANO" in df_ouv.columns else []
opcoes_uf = sorted(UFS_BRASIL)

# --- LAYOUT ---
layout = html.Div(
    className="d-flex flex-column",
    style={"height": "100vh", "padding": "0px", "backgroundColor": "#f8fafc", "overflow": "hidden"},
    children=[
        # 1. Filtros (Fixos)
        html.Div(
            className="filter-container",
            style={"margin": "10px 10px 0 10px", "padding": "15px 20px", "backgroundColor": "white", "borderRadius": "8px", "boxShadow": "0 2px 4px rgba(0,0,0,0.05)"},
            children=[
                dbc.Row([
                    dbc.Col([html.H4("Painel Ouvidoria", className="fw-bold text-dark m-0"), html.Small("Monitoramento e Gestão", className="text-muted small")], md=3),
                    dbc.Col(dcc.Dropdown(id="ouv-ano", options=[{"label": i, "value": i} for i in opcoes_ano], multi=True, placeholder="Filtrar Anos"), md=3),
                    dbc.Col(dcc.Dropdown(id="ouv-uf", options=[{"label": i, "value": i} for i in opcoes_uf], multi=True, placeholder="Filtrar UF"), md=3),
                    dbc.Col(dbc.Button([html.I(className="bi bi-download me-2"), "Exportar CSV"], id="ouv-btn-download", color="dark", outline=True, className="w-100"), md=3),
                    dcc.Download(id="ouv-download")
                ], className="align-items-center g-3")
            ]
        ),

        # 2. Conteúdo (Scrollável)
        html.Div(
            className="flex-grow-1",
            style={"padding": "15px", "overflowY": "auto", "overflowX": "hidden"},
            children=[
                # LINHA 1: KPIs (Gráficos Indicadores)
                dbc.Row([
                    dbc.Col(dcc.Graph(id="kpi-qlik-vol", config={'displayModeBar': False}, style={"height": "120px"}), md=3),
                    dbc.Col(dcc.Graph(id="kpi-qlik-tempo", config={'displayModeBar': False}, style={"height": "120px"}), md=3),
                    dbc.Col(dcc.Graph(id="kpi-qlik-sla", config={'displayModeBar': False}, style={"height": "120px"}), md=3),
                    dbc.Col(dcc.Graph(id="kpi-qlik-pendencia", config={'displayModeBar': False}, style={"height": "120px"}), md=3),
                ], className="mb-4 g-3"),

                # LINHA 2: GRÁFICOS PRINCIPAIS
                dbc.Row([
                    # COMBO CHART (Volume x Tempo)
                    dbc.Col(html.Div(className="custom-card p-3 bg-white rounded shadow-sm h-100", children=[
                        html.H6("Volume x Tempo de Resposta (Mensal)", className="fw-bold text-secondary mb-3"),
                        dcc.Graph(id="fig-combo-temporal", style={"height": "350px"}, config={'displayModeBar': False})
                    ]), md=8),
                    
                    # TOP ASSUNTOS
                    dbc.Col(html.Div(className="custom-card p-3 bg-white rounded shadow-sm h-100", children=[
                        html.H6("Top 5 Assuntos", className="fw-bold text-secondary mb-3"),
                        dcc.Graph(id="fig-top-assuntos", style={"height": "350px"}, config={'displayModeBar': False})
                    ]), md=4),
                ], className="mb-4 g-3"),

                # LINHA 3: PARETO ORGÃOS
                dbc.Row([
                    dbc.Col(html.Div(className="custom-card p-3 bg-white rounded shadow-sm", children=[
                        html.H6("Ranking de Órgãos (Volume)", className="fw-bold text-secondary mb-3"),
                        dcc.Graph(id="fig-pareto-orgao", style={"height": "500px"}, config={'displayModeBar': False})
                    ]), md=12),
                ], className="g-3 mb-5") # Padding extra no final
            ]
        )
    ]
)

@callback(
    [Output("kpi-qlik-vol", "figure"), Output("kpi-qlik-tempo", "figure"), 
     Output("kpi-qlik-sla", "figure"), Output("kpi-qlik-pendencia", "figure"),
     Output("fig-combo-temporal", "figure"), Output("fig-top-assuntos", "figure"), 
     Output("fig-pareto-orgao", "figure"),
     Output("ouv-download", "data")],
    [Input("ouv-ano", "value"), Input("ouv-uf", "value"), Input("ouv-btn-download", "n_clicks")]
)
def update_ouvidoria(anos, ufs, n_clicks):
    dff = df_ouv.copy()
    
    # Filtros
    if not dff.empty:
        if anos: dff = dff[dff["ANO"].isin(anos if isinstance(anos, list) else [anos])]
        if ufs: dff = dff[dff["UF"].isin(ufs if isinstance(ufs, list) else [ufs])] if "UF" in dff.columns else dff

    # --- KPI Helper (Visual estilo Qlik/PowerBI) ---
    def criar_kpi_qlik(valor_atual, titulo, sulfixo="", cor=COR_NEUTRA):
        fig = go.Figure()
        fig.add_trace(go.Indicator(
            mode = "number",
            value = valor_atual,
            number = {'suffix': sulfixo, 'font': {'size': 40, 'color': cor, 'family': "Inter, sans-serif"}},
            title = {'text': titulo.upper(), 'font': {'size': 12, 'color': "#64748b"}},
            domain = {'x': [0, 1], 'y': [0, 1]}
        ))
        fig.update_layout(paper_bgcolor="white", height=120, margin=dict(l=10, r=10, t=30, b=10))
        return fig

    # --- CÁLCULOS ---
    total = len(dff)
    
    # Tempo Médio (Usa a coluna PRAZO padronizada)
    tempo_medio = 0
    if 'PRAZO' in dff.columns:
        # Pega média apenas dos valores positivos
        tempo_medio = dff[dff['PRAZO'] > 0]['PRAZO'].mean()
        if pd.isna(tempo_medio): tempo_medio = 0

    # SLA (< 30 dias)
    no_prazo = len(dff[dff['PRAZO'] <= 30]) if 'PRAZO' in dff.columns else 0
    sla_pct = (no_prazo / total * 100) if total > 0 else 0
    
    # Pendentes
    pendentes = 0
    if 'STATUS' in dff.columns:
        pendentes = len(dff[~dff['STATUS'].astype(str).str.contains('Concluída|Respondida|Encerrada', case=False, na=False)])

    # Geração dos KPIs
    kpi1 = criar_kpi_qlik(total, "Total Manifestações", "", COR_NEUTRA)
    kpi2 = criar_kpi_qlik(tempo_medio, "Tempo Médio", " dias", COR_ALERTA if tempo_medio > 20 else COR_SUCESSO)
    kpi3 = criar_kpi_qlik(sla_pct, "SLA (< 30 dias)", "%", COR_SUCESSO if sla_pct >= 80 else COR_ALERTA)
    kpi4 = criar_kpi_qlik(pendentes, "Em Aberto", "", COR_ERRO if pendentes > 0 else COR_SUCESSO)

    # 2. COMBO CHART (VOLUME x TEMPO)
    fig_combo = go.Figure()
    if "DATA" in dff.columns:
        # Agrupa por Mês (usando DATA padronizada)
        df_g = dff.groupby(dff['DATA'].dt.to_period('M').astype(str)).agg(
            Volume=('DATA', 'count'), 
            Tempo=('PRAZO', 'mean') if 'PRAZO' in dff.columns else ('DATA', lambda x: 0)
        ).reset_index()
        df_g.rename(columns={'DATA': 'Mes'}, inplace=True)
        
        # Barras (Volume)
        fig_combo.add_trace(go.Bar(x=df_g['Mes'], y=df_g['Volume'], name='Volume', marker_color=COR_BARRAS))
        
        # Linha (Tempo)
        fig_combo.add_trace(go.Scatter(
            x=df_g['Mes'], y=df_g['Tempo'], name='Dias (Médio)', 
            mode='lines+markers', line=dict(color=COR_DESTAQUE, width=3), yaxis='y2'
        ))
        
        fig_combo.update_layout(
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center"),
            yaxis=dict(showgrid=False, title="Volume"), 
            yaxis2=dict(overlaying='y', side='right', showgrid=False, title="Dias"),
            margin=dict(l=20, r=20, t=30, b=20)
        )
    else:
        fig_combo = go.Figure().add_annotation(text="Sem dados Temporais", showarrow=False)

    # 3. TOP ASSUNTOS
    if 'ASSUNTO' in dff.columns:
        df_ass = dff['ASSUNTO'].value_counts().head(5).reset_index()
        df_ass.columns = ['Assunto', 'Qtd']
        df_ass['Assunto'] = df_ass['Assunto'].apply(lambda x: str(x)[:25]+"..." if len(str(x))>25 else str(x))
        df_ass = df_ass.sort_values('Qtd', ascending=True)
        
        fig_top = px.bar(df_ass, x='Qtd', y='Assunto', orientation='h', text='Qtd')
        fig_top.update_traces(marker_color=COR_DESTAQUE, textposition='inside')
        fig_top.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=20, t=10, b=0), yaxis_title=None)
    else: fig_top = go.Figure()

    # 4. PARETO ORGÃOS
    if 'ORGAO' in dff.columns:
        df_org = dff['ORGAO'].value_counts().head(15).reset_index()
        df_org.columns = ['Orgao', 'Qtd']
        df_org['Orgao'] = df_org['Orgao'].apply(lambda x: str(x)[:40]+"..." if len(str(x))>40 else str(x))
        df_org = df_org.sort_values('Qtd', ascending=True)
        
        fig_pareto = px.bar(df_org, x='Qtd', y='Orgao', orientation='h', text='Qtd')
        fig_pareto.update_traces(marker_color=COR_DESTAQUE, textposition='outside')
        fig_pareto.update_layout(
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=40, t=10, b=20), xaxis_title="Quantidade", yaxis_title=None
        )
    else: fig_pareto = go.Figure()

    dl = dcc.send_data_frame(dff.to_csv, "monitoramento_ouvidoria.csv", index=False) if n_clicks else None

    return kpi1, kpi2, kpi3, kpi4, fig_combo, fig_top, fig_pareto, dl