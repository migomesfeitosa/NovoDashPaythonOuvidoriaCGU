import pandas as pd
import glob
import os

print("🔍 DIAGNÓSTICO DE ARQUIVOS CSV")
# Busca arquivos (tenta recursivo e normal)
arquivos = glob.glob("data/raw/*.csv") + glob.glob("data/raw/**/*.csv")
arquivos = sorted(list(set(arquivos))) # Remove duplicados

print(f"📂 Total de arquivos encontrados: {len(arquivos)}")

# Vamos pegar um exemplo de cada tipo principal para analisar
tipos_interesse = ['Pedidos_csv', 'SolicitantesPedidos', 'Recursos_csv']
arquivos_para_checar = []

for t in tipos_interesse:
    matches = [f for f in arquivos if t in os.path.basename(f)]
    if matches:
        # Pega o arquivo mais recente (geralmente o último ano)
        arquivos_para_checar.append(matches[-1])

if not arquivos_para_checar:
    print("❌ Nenhum arquivo relevante (Pedidos, Solicitantes, Recursos) encontrado.")
else:
    for f in arquivos_para_checar:
        nome = os.path.basename(f)
        print(f"\n📄 ANALISANDO: {nome}")
        
        try:
            # Teste 1: Separador Ponto-e-vírgula (Padrão esperado)
            df_semi = pd.read_csv(f, sep=';', nrows=0, encoding='latin1')
            if len(df_semi.columns) > 1:
                print(f"   ✅ [Sep=';'] Parece correto! Colunas ({len(df_semi.columns)}):")
                print(f"      {list(df_semi.columns)[:5]} ...")
            else:
                print(f"   ⚠️ [Sep=';'] Leu apenas 1 coluna. O separador deve ser outro.")

            # Teste 2: Separador Vírgula
            df_comma = pd.read_csv(f, sep=',', nrows=0, encoding='latin1')
            if len(df_comma.columns) > 1:
                print(f"   ✅ [Sep=','] Parece ser vírgula! Colunas ({len(df_comma.columns)}):")
                print(f"      {list(df_comma.columns)[:5]} ...")
            
            # Teste 3: Encoding UTF-8 (às vezes muda)
            try:
                df_utf = pd.read_csv(f, sep=';', nrows=0, encoding='utf-8')
                print("   ℹ️  [UTF-8] Leitura com utf-8 funcionou (teste de encoding).")
            except:
                print("   ℹ️  [UTF-8] Leitura com utf-8 falhou (provavelmente é latin1 mesmo).")

        except Exception as e:
            print(f"   ❌ Erro crítico ao ler arquivo: {e}")

input("\n\nPressione Enter para sair...")