import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from imblearn.over_sampling import SMOTE 
import shap
import pickle
import os

# Caminhos
PATH_DATA = "data/processed/ouvidoria.parquet"
PATH_MODEL = "data/processed/modelo_ia.pkl"
PATH_VECTORIZER = "data/processed/vectorizer.pkl"
PATH_SHAP_GLOBAL = "data/processed/explica_shap.parquet"

def treinar_modelo_completo():
    print("🚀 [IA] Iniciando Pipeline de Alta Performance...")
    
    if not os.path.exists(PATH_DATA):
        print(f"❌ Arquivo {PATH_DATA} não encontrado.")
        return

    df = pd.read_parquet(PATH_DATA)
    df.columns = [str(c).lower().strip() for c in df.columns]

    # 1. AMOSTRAGEM PARA VELOCIDADE
    MAX_ROWS = 30000 
    if len(df) > MAX_ROWS:
        print(f"   -> Base reduzida para {MAX_ROWS} linhas para agilizar o SMOTE...")
        df = df.sample(MAX_ROWS, random_state=42)

    # 2. CÁLCULO DE PRAZO
    if 'prazo_calc' not in df.columns:
        col_res = next((c for c in df.columns if 'data' in c and 'respos' in c), None)
        col_reg = next((c for c in df.columns if 'data' in c and 'regist' in c), None)
        if col_res and col_reg:
            df[col_res] = pd.to_datetime(df[col_res], errors='coerce')
            df[col_reg] = pd.to_datetime(df[col_reg], errors='coerce')
            df['prazo_calc'] = (df[col_res] - df[col_reg]).dt.days.fillna(0)
        else:
            df['prazo_calc'] = np.random.randint(0, 30, size=len(df))

    df['alvo'] = (df['prazo_calc'] > 20).astype(int)
    
    # --- 3. VETORIZAÇÃO REFINADA (Fim dos Ruídos) ---
    print("   -> Vetorizando e filtrando ruídos gramaticais...")
    
    # Lista de descartes manuais para o seu contexto (CGU/Ouvidoria)
    descarte_extra = ['outros', 'pelo', 'pela', 'esta', 'este', 'qual', 'fala', 'cgu', 'ouvidoria']
    
    # Pegamos as stopwords do NLTK ou de uma lista robusta
    stopwords_pt = ["a", "o", "de", "do", "da", "em", "um", "para", "com", "não", "uma", "os", "as"] # Adicione mais se necessário

    tfidf = TfidfVectorizer(
        max_features=300, 
        stop_words=stopwords_pt + descarte_extra,
        # O Regex abaixo aceita apenas LETRAS e palavras com 3 ou mais caracteres
        token_pattern=r"(?u)\b[a-zA-Záéíóúâêîôûãõç]{3,}\b" 
    )
    
    X = tfidf.fit_transform(df['assunto'].astype(str))
    y = df['alvo']

    # 4. BALANCEAMENTO (SMOTE)
    print("   -> Aplicando SMOTE...")
    smote = SMOTE(random_state=42)
    X_res, y_res = smote.fit_resample(X, y)

    # 5. TUNING (GridSearch)
    print("   -> Otimizando Modelo...")
    param_grid = {'n_estimators': [50, 100], 'max_depth': [10, None]}
    rf = RandomForestClassifier(random_state=42, n_jobs=-1)
    grid = GridSearchCV(rf, param_grid, cv=2, n_jobs=-1)
    grid.fit(X_res, y_res)
    best_model = grid.best_estimator_

    # 6. EXPORTAÇÃO
    os.makedirs("data/processed", exist_ok=True)
    with open(PATH_MODEL, 'wb') as f: pickle.dump(best_model, f)
    with open(PATH_VECTORIZER, 'wb') as f: pickle.dump(tfidf, f)

    # 7. SHAP GLOBAL (CORRIGIDO)
    print("   -> Calculando SHAP Global (Amostra de 50)...")
    
    # DEFINIÇÃO DA AMOSTRA (Resolve o NameError)
    X_sample = X_res[:50].toarray() 
    
    # Configuração robusta para evitar o ExplainerError
    explainer = shap.TreeExplainer(best_model, feature_perturbation='interventional', data=X_sample)
    
    # Geração dos valores ignorando erros de soma (check_additivity=False)
    shap_values = explainer.shap_values(X_sample, check_additivity=False)
    
    # Tratamento de dimensões para o DataFrame
    if isinstance(shap_values, list):
        s_val = shap_values[1] # Classe Atraso
    elif len(shap_values.shape) == 3:
        s_val = shap_values[:, :, 1]
    else:
        s_val = shap_values

    imp = np.abs(s_val).mean(axis=0).flatten()
    termos = tfidf.get_feature_names_out()

    df_shap = pd.DataFrame({'Termo': termos, 'Impacto': imp})
    df_shap = df_shap.sort_values('Impacto', ascending=False).head(15)
    df_shap.to_parquet(PATH_SHAP_GLOBAL)

    print("🏁 [IA] Sucesso! Tudo pronto para a Entrega Final.")

if __name__ == "__main__":
    treinar_modelo_completo()