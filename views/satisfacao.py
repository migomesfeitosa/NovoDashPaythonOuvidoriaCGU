import plotly.express as px
import pandas as pd

def grafico_satisfacao(df):
    if df.empty or 'SATISFACAO' not in df.columns: return {}
    
    # Limpeza básica (converter para string para agrupar)
    dados = df["SATISFACAO"].astype(str).value_counts().sort_index().reset_index()
    dados.columns = ["Nota", "Quantidade"]

    return px.bar(dados, x="Nota", y="Quantidade", title="Distribuição da Satisfação", template="plotly_white", color_discrete_sequence=['gold'])

def grafico_satisfacao_vs_atraso(df):
    if df.empty or 'SATISFACAO' not in df.columns or 'DIAS_ATRASO' not in df.columns: return {}
    
    # Amostra para scatter plot não ficar pesado (1000 pontos aleatórios)
    df_sample = df.sample(n=min(1000, len(df)), random_state=42).copy()
    
    df_sample['DIAS_ATRASO'] = pd.to_numeric(df_sample['DIAS_ATRASO'], errors='coerce').fillna(0)
    
    return px.scatter(
        df_sample, x="DIAS_ATRASO", y="SATISFACAO", 
        title="Relação Atraso x Satisfação (Amostra)", template="plotly_white"
    )