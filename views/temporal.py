import plotly.express as px
import pandas as pd

from utils.design import MAPA_FONTE

def grafico_evolucao_mensal(df):
    if df.empty or 'MES_ANO' not in df.columns: return {}

    # Agrupa por Mês
    serie = df.groupby("MES_ANO").size().reset_index(name="quantidade")
    serie = serie.sort_values("MES_ANO") # Garante ordem cronológica

    fig = px.line(
        serie,
        x="MES_ANO",
        y="quantidade",
        title="Evolução Mensal das Manifestações",
        markers=True,
        template="plotly_white",
        color_discrete_map=MAPA_FONTE
    )
    fig.update_xaxes(type='category') # Melhor para eixos de texto YYYY-MM
    return fig