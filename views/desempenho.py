import plotly.express as px
import pandas as pd
from utils.design import CORES


def kpi_tempo_medio(df):
    if df.empty or "DIAS_RESOLUCAO" not in df.columns:
        return 0
    # Converte para numérico forçado
    dias = pd.to_numeric(df["DIAS_RESOLUCAO"], errors="coerce")
    return round(dias.mean(), 1)


def grafico_atraso(df):
    if df.empty or "DIAS_ATRASO" not in df.columns:
        return {}

    atraso = pd.to_numeric(df["DIAS_ATRASO"], errors="coerce").dropna()
    # Filtra apenas quem tem atraso > 0
    atraso = atraso[atraso > 0]

    return px.histogram(
        atraso,
        x="DIAS_ATRASO",
        nbins=30,
        title="Distribuição dos Dias de Atraso",
        template="plotly_white",
        color_discrete_sequence=[CORES['ERRO']]
    )


def grafico_prazo_por_orgao(df):
    if df.empty or "ORGAO" not in df.columns or "DIAS_RESOLUCAO" not in df.columns:
        return {}

    # Prepara dados (numérico)
    df_temp = df.copy()
    df_temp["DIAS_RESOLUCAO"] = pd.to_numeric(
        df_temp["DIAS_RESOLUCAO"], errors="coerce"
    )

    dados = (
        df_temp.groupby("ORGAO")["DIAS_RESOLUCAO"]
        .mean()
        .reset_index()
        .sort_values("DIAS_RESOLUCAO", ascending=False)
        .head(15)
    )

    return px.bar(
        dados,
        y="ORGAO",
        x="DIAS_RESOLUCAO",
        orientation="h",
        title="Top 15 Órgãos Mais Lentos (Dias Médios)",
        template="plotly_white",
    )
