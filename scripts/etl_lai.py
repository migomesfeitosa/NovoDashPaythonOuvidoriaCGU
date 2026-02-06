import pandas as pd
import glob
import os
import gc

# CONFIGURAÇÃO
PASTA_RAW = "data/raw/**"
ARQUIVO_PEDIDOS = "data/processed/lai_pedidos.parquet"
ARQUIVO_RECURSOS = "data/processed/lai_recursos.parquet"

def carregar_csv_seguro(filepath, colunas_interesse=None):
    """
    Lê CSV tratando erros de encoding (UTF-16 vs Latin1) e separadores.
    """
    tentativas = [
        ('utf-16', ';'),   # Formato detectado nos arquivos mais recentes
        ('latin1', ';'),   # Formato antigo
        ('utf-8', ';')     
    ]

    for enc, sep in tentativas:
        try:
            # Lê apenas o cabeçalho para validar
            df_head = pd.read_csv(filepath, sep=sep, encoding=enc, nrows=1, on_bad_lines='skip')
            cols_arquivo = [c.strip() for c in df_head.columns]
            
            # Verifica integridade básica (evita arquivos corrompidos ou com BOM errado)
            if len(cols_arquivo) > 1 and "Unnamed: 0" not in cols_arquivo[0]:
                
                # Filtra colunas se solicitado
                use_cols = None
                if colunas_interesse:
                    use_cols = [c for c in cols_arquivo if c in colunas_interesse]
                    if not use_cols:
                        continue 

                # Leitura Real
                return pd.read_csv(filepath, sep=sep, encoding=enc, on_bad_lines='skip', 
                                   usecols=use_cols, low_memory=False, dtype=str)
        except Exception:
            continue 
            
    return pd.DataFrame() 

def rodar_lai():
    print("🚀 [LAI] Iniciando processamento (Modo Seguro)...")
    
    # Busca recursiva de arquivos CSV
    arquivos = glob.glob(os.path.join("data/raw", "*.csv")) + glob.glob(os.path.join("data/raw", "**", "*.csv"))
    arquivos = sorted(list(set(arquivos)))
    
    if not arquivos: return print("❌ Nenhum arquivo encontrado em data/raw.")

    dfs_pedidos = []
    dfs_solicitantes = []
    dfs_recursos = []

    for f in arquivos:
        nome_low = os.path.basename(f).lower()
        
        # --- FILTROS DE ARQUIVO (A Lógica Crucial) ---
        # 1. Pedidos (mas não solicitantes)
        is_pedido = 'pedidos' in nome_low and 'solicitante' not in nome_low
        # 2. Solicitantes (APENAS de Pedidos, para evitar o erro de Protocolo)
        is_solicitante = 'solicitantespedidos' in nome_low 
        # 3. Recursos (mas não solicitantes)
        is_recurso = 'recurso' in nome_low and 'solicitante' not in nome_low

        if not (is_pedido or is_solicitante or is_recurso): continue

        print(f"   -> Lendo: {os.path.basename(f)}...", end="")

        try:
            # --- PEDIDOS ---
            if is_pedido:
                mapa = {
                    'ProtocoloPedido': 'PROTOCOLO', 'IdPedido': 'ID_PEDIDO',
                    'DataRegistro': 'DATA', 'Uf': 'UF_ORGAO', 'OrgaoDestinatario': 'ORGAO',
                    'Decisao': 'RESULTADO', 'Situacao': 'SITUACAO', 'PrazoAtendimento': 'PRAZO',
                    'FoiProrrogado': 'PRORROGADO', 'AssuntoPedido': 'ASSUNTO', 'SubAssuntoPedido': 'SUBASSUNTO'
                }
                df = carregar_csv_seguro(f, mapa.keys())
                if not df.empty:
                    df = df.rename(columns=mapa)
                    dfs_pedidos.append(df)
                    print(" ✅ Pedido")

            # --- SOLICITANTES (Perfil Demográfico) ---
            elif is_solicitante:
                mapa = {
                    'ProtocoloPedido': 'PROTOCOLO',
                    'TipoDemandante': 'TIPO_DEMANDANTE', 'DataNascimento': 'DATA_NASC',
                    'Genero': 'GENERO', 'Escolaridade': 'ESCOLARIDADE',
                    'Profissao': 'PROFISSAO', 'UF': 'UF_CIDADAO', 'Municipio': 'MUNICIPIO_CIDADAO'
                }
                df = carregar_csv_seguro(f, mapa.keys())
                if not df.empty:
                    df = df.rename(columns=mapa)
                    dfs_solicitantes.append(df)
                    print(" ✅ Perfil")

            # --- RECURSOS (Judicialização) ---
            elif is_recurso:
                mapa = {
                    'ProtocoloPedido': 'PROTOCOLO', 
                    'Instancia': 'INSTANCIA', 'TipoRecurso': 'TIPO_RECURSO',
                    'DataRecurso': 'DATA_RECURSO', 'Situacao': 'SITUACAO_RECURSO',
                    'TipoDecisao': 'DECISAO_RECURSO'
                }
                df = carregar_csv_seguro(f, mapa.keys())
                if not df.empty:
                    df = df.rename(columns=mapa)
                    dfs_recursos.append(df)
                    print(" ✅ Recurso")

        except Exception as e: 
            print(f" ❌ Erro: {e}")

    # --- CONSOLIDAÇÃO ---
    print("\n📦 Consolidando dados...")

    # 1. Processa Pedidos + Solicitantes
    if dfs_pedidos:
        full_pedidos = pd.concat(dfs_pedidos, ignore_index=True)
        # Datas
        full_pedidos['DATA'] = pd.to_datetime(full_pedidos['DATA'], dayfirst=True, errors='coerce')
        full_pedidos['ANO'] = full_pedidos['DATA'].dt.year.fillna(0).astype(int).astype(str)
        
        # Cruzamento (Left Join) com verificação de segurança
        if dfs_solicitantes:
            full_solic = pd.concat(dfs_solicitantes, ignore_index=True)
            if 'PROTOCOLO' in full_solic.columns:
                # Remove duplicatas de protocolo para não explodir a base
                full_solic = full_solic.drop_duplicates(subset=['PROTOCOLO'])
                print(f"   🔗 Cruzando {len(full_pedidos)} pedidos com perfis...")
                full_pedidos = pd.merge(full_pedidos, full_solic, on='PROTOCOLO', how='left')
            else:
                print("   ⚠️ Aviso: Coluna PROTOCOLO ausente nos solicitantes.")
        
        # Tratamento UF
        if 'UF_CIDADAO' in full_pedidos.columns:
            full_pedidos['UF'] = full_pedidos['UF_CIDADAO'].fillna('NI')
        else:
            full_pedidos['UF'] = 'NI'

        # Salva
        os.makedirs("data/processed", exist_ok=True)
        full_pedidos.to_parquet(ARQUIVO_PEDIDOS, index=False)
        print(f"🏁 [LAI] Pedidos salvos: {len(full_pedidos):,} registros.")
    
    # 2. Processa Recursos
    if dfs_recursos:
        full_recursos = pd.concat(dfs_recursos, ignore_index=True)
        full_recursos.to_parquet(ARQUIVO_RECURSOS, index=False)
        print(f"🏁 [LAI] Recursos salvos: {len(full_recursos):,} registros.")

    gc.collect()

if __name__ == "__main__":
    rodar_lai()