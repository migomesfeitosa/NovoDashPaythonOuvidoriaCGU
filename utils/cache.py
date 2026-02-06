"""
Sistema de cache para melhor performance
"""
import pandas as pd
import hashlib
import pickle
import os
from functools import lru_cache
import time

CACHE_DIR = "cache/"
os.makedirs(CACHE_DIR, exist_ok=True)

def cache_dataframe(func):
    """Decorator para cache de dataframes"""
    @lru_cache(maxsize=128)
    def wrapper(*args, **kwargs):
        # Cria hash dos argumentos
        key = hashlib.md5(str((args, kwargs)).encode()).hexdigest()
        cache_file = f"{CACHE_DIR}/{key}.pkl"
        
        # Verifica se cache existe (válido por 1 hora)
        if os.path.exists(cache_file):
            if time.time() - os.path.getmtime(cache_file) < 3600:
                with open(cache_file, 'rb') as f:
                    print(f"📦 Carregando do cache: {func.__name__}")
                    return pickle.load(f)
        
        # Executa função e salva cache
        result = func(*args, **kwargs)
        with open(cache_file, 'wb') as f:
            pickle.dump(result, f)
        
        return result
    
    return wrapper

# Exemplo de uso
@cache_dataframe
def carregar_dados_filtrados(anos=None, ufs=None):
    """Versão com cache da função de carregamento"""
    # Carrega os dados e aplica filtros
    df_filtrado = pd.DataFrame()  # Substitua com sua lógica de carregamento
    if anos is not None:
        df_filtrado = df_filtrado[df_filtrado['ano'].isin(anos)]
    if ufs is not None:
        df_filtrado = df_filtrado[df_filtrado['uf'].isin(ufs)]
    return df_filtrado