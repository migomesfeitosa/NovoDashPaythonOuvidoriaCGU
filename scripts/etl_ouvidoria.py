import pandas as pd
import glob
import os
import unicodedata
import traceback

# CONFIGURAÇÃO
PASTA_RAW = "data/raw/**"
ARQUIVO_SAIDA = "data/processed/ouvidoria.parquet"

def normalizar(texto):
    if not isinstance(texto, str): return str(texto)
    return "".join([c for c in unicodedata.normalize('NFKD', texto) if not unicodedata.combining(c)]).lower().strip()

def rodar_ouvidoria():
    print("🚀 [OUVIDORIA] Iniciando processamento BLINDADO...")
    
    # 1. Tenta apagar o arquivo antigo para não misturar schemas
    if os.path.exists(ARQUIVO_SAIDA):
        try:
            os.remove(ARQUIVO_SAIDA)
            print("   🧹 Arquivo antigo removido com sucesso.")
        except Exception as e:
            print(f"   ⚠️ Não foi possível remover o arquivo antigo (pode estar aberto): {e}")
            print("   ⚠️ Tente apagar manualmente o arquivo 'data/processed/ouvidoria.parquet' se der erro.")

    arquivos = glob.glob(os.path.join(PASTA_RAW, "*.csv"), recursive=True)
    total_processado = 0

    for f in arquivos:
        nome_arq = os.path.basename(f)
        # Pula arquivos da LAI
        if 'pedidos' in nome_arq.lower(): continue

        try:
            # Lê cabeçalho
            df_head = pd.read_csv(f, sep=';', encoding='latin1', nrows=1, on_bad_lines='skip')
            cols_norm = [normalizar(c) for c in df_head.columns]

            if 'data registro' in cols_norm and 'nome orgao' in cols_norm:
                print(f"   -> Processando: {nome_arq}...", end="")
                
                # Lê o arquivo completo
                df = pd.read_csv(f, sep=';', encoding='latin1', on_bad_lines='skip', low_memory=False)
                
                # --- MAPA DE RENOMEAÇÃO ---
                mapa_renomear = {}
                for c_orig in df.columns:
                    c_norm = normalizar(c_orig)
                    
                    if c_norm == 'data registro': mapa_renomear[c_orig] = 'DATA'
                    elif c_norm == 'uf do municipio manifestante': mapa_renomear[c_orig] = 'UF'
                    elif c_norm == 'municipio manifestante': mapa_renomear[c_orig] = 'MUNICIPIO'
                    elif c_norm == 'nome orgao': mapa_renomear[c_orig] = 'ORGAO'
                    elif c_norm == 'assunto': mapa_renomear[c_orig] = 'ASSUNTO'
                    elif c_norm == 'tipo manifestacao': mapa_renomear[c_orig] = 'TIPO'
                    elif c_norm == 'servico': mapa_renomear[c_orig] = 'SERVICO'
                    elif c_norm == 'satisfacao': mapa_renomear[c_orig] = 'SATISFACAO'
                    elif c_norm == 'genero': mapa_renomear[c_orig] = 'GENERO'
                    elif c_norm == 'raca/cor' or c_norm == 'cor': mapa_renomear[c_orig] = 'RACA'
                    elif c_norm == 'faixa etaria': mapa_renomear[c_orig] = 'FAIXA_ETARIA'
                    elif c_norm == 'dias para resolucao': mapa_renomear[c_orig] = 'DIAS_RESOLUCAO'
                    elif c_norm == 'dias de atraso': mapa_renomear[c_orig] = 'DIAS_ATRASO'
                    elif c_norm == 'situacao': mapa_renomear[c_orig] = 'SITUACAO'

                df = df.rename(columns=mapa_renomear)
                
                # Colunas alvo
                cols_desejadas = [
                    'DATA', 'UF', 'MUNICIPIO', 'ORGAO', 'ASSUNTO', 'TIPO', 'SERVICO',
                    'SATISFACAO', 'GENERO', 'RACA', 'FAIXA_ETARIA', 
                    'DIAS_RESOLUCAO', 'DIAS_ATRASO', 'SITUACAO'
                ]
                
                cols_finais = [c for c in cols_desejadas if c in df.columns]
                
                # Garante coluna RESULTADO
                if 'ASSUNTO' in df.columns: df['RESULTADO'] = df['ASSUNTO']
                else: df['RESULTADO'] = 'N/A'
                if 'RESULTADO' not in cols_finais: cols_finais.append('RESULTADO')

                df = df[cols_finais]

                # --- CORREÇÃO DO ERRO DE TIPO (FORÇA TEXTO) ---
                # Força todas as colunas de texto a serem string (mesmo que estejam vazias/NaN)
                cols_texto = ['UF', 'MUNICIPIO', 'ORGAO', 'ASSUNTO', 'TIPO', 'SERVICO', 
                              'SATISFACAO', 'GENERO', 'RACA', 'FAIXA_ETARIA', 'SITUACAO', 'RESULTADO']
                
                for col in cols_texto:
                    if col in df.columns:
                        # Preenche vazios com string vazia e converte para string
                        df[col] = df[col].fillna("").astype(str)
                        # Opcional: Converter para category para economizar memória (se quiser)
                        # df[col] = df[col].astype('category')

                # Tratamento de Data
                df['DATA'] = pd.to_datetime(df['DATA'], dayfirst=True, errors='coerce')
                df['ANO'] = df['DATA'].dt.year.fillna(0).astype(int).astype(str)

                # Salva
                if not os.path.exists(ARQUIVO_SAIDA):
                    df.to_parquet(ARQUIVO_SAIDA, index=False, engine='fastparquet')
                else:
                    df.to_parquet(ARQUIVO_SAIDA, index=False, engine='fastparquet', append=True)
                
                total_processado += len(df)
                print(f" ✅ Salvo (+{len(df):,} linhas)")
                
                # Limpa memória
                del df

        except Exception as e:
            print(f" ❌ Erro: {e}")
            # Se der erro estranho, mostra detalhe para debug
            # print(traceback.format_exc())

    print(f"🏁 [OUVIDORIA] Finalizado! Total acumulado: {total_processado:,} registros.")

if __name__ == "__main__":
    rodar_ouvidoria()