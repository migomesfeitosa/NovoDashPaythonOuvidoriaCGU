import pandas as pd
import os
import gc

# Lista Oficial de UFs
UFS_BRASIL = [
    'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 
    'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 
    'SP', 'SE', 'TO'
]

# Caches globais para performance
_cache_ouv = None
_cache_lai_pedidos = None
_cache_lai_recursos = None

def otimizar_memoria(df):
    """Reduz o tamanho do DataFrame na RAM convertendo objects para category."""
    for col in df.columns:
        if df[col].dtype == 'object':
            num_unique = len(df[col].unique())
            num_total = len(df)
            if num_total > 0 and num_unique / num_total < 0.5:
                df[col] = df[col].astype('category')
        elif df[col].dtype == 'int64':
            df[col] = pd.to_numeric(df[col], downcast='unsigned')
    return df

def tratar_ufs(df):
    """Padroniza a coluna UF."""
    if 'UF' not in df.columns: return df
    df['UF'] = df['UF'].astype(str).str.upper().str.strip()
    mask_invalido = ~df['UF'].isin(UFS_BRASIL)
    if mask_invalido.any():
        df.loc[mask_invalido, 'UF'] = 'NI'
    return df

def carregar_dados_ouvidoria():
    global _cache_ouv
    if _cache_ouv is not None: return _cache_ouv

    path = "data/processed/ouvidoria.parquet"
    if not os.path.exists(path): return pd.DataFrame()

    try:
        try: df = pd.read_parquet(path)
        except: df = pd.read_parquet(path, engine='fastparquet')
        
        df = tratar_ufs(df)
        if 'DATA' in df.columns:
            df['DATA'] = pd.to_datetime(df['DATA'], errors='coerce')
            df['ANO'] = df['DATA'].dt.year.fillna(0).astype(int).astype(str)
            
        df['Fonte'] = 'Ouvidoria'
        df = otimizar_memoria(df)
        _cache_ouv = df
        return df
    except Exception as e:
        print(f"❌ Erro Ouvidoria: {e}")
        return pd.DataFrame()

def carregar_dados_lai(tipo="pedidos"):
    """
    Carrega dados da LAI.
    tipo="pedidos": Retorna Pedidos + Perfil
    tipo="recursos": Retorna Recursos
    """
    global _cache_lai_pedidos, _cache_lai_recursos
    
    if tipo == "pedidos":
        if _cache_lai_pedidos is not None: return _cache_lai_pedidos
        path = "data/processed/lai_pedidos.parquet"
    else:
        if _cache_lai_recursos is not None: return _cache_lai_recursos
        path = "data/processed/lai_recursos.parquet"

    if not os.path.exists(path): return pd.DataFrame()

    try:
        try: df = pd.read_parquet(path)
        except: df = pd.read_parquet(path, engine='fastparquet')
        
        if tipo == "pedidos":
            if 'UF' not in df.columns: df['UF'] = 'NI'
            df = tratar_ufs(df)
            # Garante colunas vitais para os gráficos
            for c in ['GENERO', 'ESCOLARIDADE', 'RACA', 'PROFISSAO']:
                if c not in df.columns: df[c] = 'Não Informado'
            df['Fonte'] = 'LAI'

        df = otimizar_memoria(df)
        
        if tipo == "pedidos": _cache_lai_pedidos = df
        else: _cache_lai_recursos = df
        
        return df

    except Exception as e:
        print(f"❌ Erro LAI ({tipo}): {e}")
        return pd.DataFrame()