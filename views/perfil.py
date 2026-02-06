import plotly.express as px

def grafico_genero(df):
    if df.empty or 'GENERO' not in df.columns: return {}
    
    dados = df["GENERO"].value_counts().reset_index()
    dados.columns = ["Gênero", "Quantidade"]
    
    return px.pie(dados, names="Gênero", values="Quantidade", title="Distribuição por Gênero", hole=0.5)

def grafico_raca(df):
    if df.empty or 'RACA' not in df.columns: return {}
    
    dados = df["RACA"].value_counts().reset_index()
    dados.columns = ["Raça/Cor", "Quantidade"]
    
    return px.bar(dados, x="Raça/Cor", y="Quantidade", title="Autodeclaração Raça/Cor", template="plotly_white")

def grafico_faixa_etaria(df):
    if df.empty or 'FAIXA_ETARIA' not in df.columns: return {}
    
    dados = df["FAIXA_ETARIA"].value_counts().reset_index()
    dados.columns = ["Faixa Etária", "Quantidade"]
    dados = dados.sort_values("Faixa Etária") # Tenta ordenar logicamente
    
    return px.bar(dados, y="Faixa Etária", x="Quantidade", orientation="h", title="Faixa Etária", template="plotly_white")