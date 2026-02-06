import pandas as pd
from utils.preprocessamento import carregar_dados_lai

def diagnostico_dados():
    print("🔍 INICIANDO DIAGNÓSTICO DE DADOS (LAI PEDIDOS)...")
    
    # 1. Tenta carregar os dados
    try:
        df = carregar_dados_lai("pedidos")
        if df is None or df.empty:
            print("❌ Erro: O DataFrame está vazio ou não foi carregado.")
            return
    except Exception as e:
        print(f"❌ Erro ao carregar arquivo: {e}")
        return

    # 2. Lista TODAS as colunas para conferir o nome exato
    print("\n--- 📋 COLUNAS ENCONTRADAS ---")
    print(df.columns.tolist())

    # 3. Procura por termos relacionados a Prazo/Tempo/Datas
    termos_busca = ['PRAZO', 'DIAS', 'RESPOSTA', 'ATENDIMENTO', 'DATA']
    colunas_suspeitas = [c for c in df.columns if any(t in c.upper() for t in termos_busca)]
    
    print("\n--- 🕵️ COLUNAS SUSPEITAS PARA O CÁLCULO DE PRAZO ---")
    if colunas_suspeitas:
        # Mostra as colunas suspeitas e os 5 primeiros valores de cada uma
        print(df[colunas_suspeitas].head(5))
        
        print("\n--- 🧬 TIPOS DE DADOS (Dtypes) ---")
        print(df[colunas_suspeitas].dtypes)
    else:
        print("⚠️ Nenhuma coluna óbvia de prazo ou data foi encontrada.")

    print("\n--- 🏁 FIM DO DIAGNÓSTICO ---")

if __name__ == "__main__":
    diagnostico_dados()