import pandas as pd
import os

ARQUIVO = "data/processed/ouvidoria.parquet"

print(f"🔍 Investigando arquivo: {ARQUIVO}")

if not os.path.exists(ARQUIVO):
    print("❌ ERRO CRÍTICO: O arquivo não existe fisicamente!")
else:
    tamanho = os.path.getsize(ARQUIVO) / (1024 * 1024)
    print(f"📦 Tamanho do arquivo: {tamanho:.2f} MB")
    
    try:
        # Tenta ler com engine padrão
        print("📖 Tentando ler com Pandas (padrão)...")
        df = pd.read_parquet(ARQUIVO)
        print("✅ Leitura SUCESSO!")
        print(f"📊 Linhas: {len(df):,}")
        print(f"📋 Colunas encontradas: {list(df.columns)}")
        print("\n🔎 Amostra dos dados:")
        print(df[['DATA', 'ORGAO', 'ASSUNTO']].head())
        
    except Exception as e:
        print(f"❌ Falha na leitura padrão: {e}")
        
        try:
            print("\n📖 Tentando ler com engine='fastparquet'...")
            df = pd.read_parquet(ARQUIVO, engine='fastparquet')
            print("✅ Leitura SUCESSO com fastparquet!")
            print(f"📊 Linhas: {len(df):,}")
        except Exception as e2:
            print(f"❌ Falha crítica também com fastparquet: {e2}")

input("\nPressione Enter para sair...")