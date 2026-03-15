# =============================================================================
# 1. IMPORTAR BIBLIOTECAS
# =============================================================================

import os
import re
import time
import pandas as pd
import spacy
from collections import Counter

from wordcloud import WordCloud
import matplotlib.pyplot as plt

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation

from gensim.models.phrases import Phrases, Phraser


# =============================================================================
# 2. CAMINHOS
# =============================================================================

ARQUIVO_DADOS = "data/processed/ouvidoria.parquet"
IMG_WORDCLOUD = "assets/wordcloud_assuntos.png"
IMG_WORDCLOUD_TOPICOS = "assets/wordcloud_topicos_lda.png"
IMG_PARETO = "assets/pareto_palavras.png"
ARQUIVO_TOPICOS = "data/processed/topicos_nlp.parquet"


# =============================================================================
# 3. CARREGAR MODELO NLP
# =============================================================================

print("Carregando modelo NLP...")

nlp = spacy.load("pt_core_news_sm", disable=["parser","ner"])


# =============================================================================
# 4. STOPWORDS DE DOMÍNIO
# =============================================================================

STOPWORDS_DOMINIO = {

# termos administrativos
"informacao","informacoes","servico","servicos","publico","publica",
"programa","programas","administracao","gestao","sistema","sistemas",
"acesso","cadastro","processo","processos",

# termos de ouvidoria
"manifestacao","solicitacao","solicitacoes","pedido","pedidos","demanda",
"encaminhamento","encaminhar","informar","resposta","retorno","atendimento",

# pessoas
"usuario","usuarios","cidadao","cidadaos","senhor","senhora",

# estrutura institucional
"orgao","setor","departamento","unidade",

# burocracia
"registro","protocolo","documento","documentos",

# verbos genéricos
"realizar","fazer","existir","possuir",

# genéricos
"geral","outros","outras",

# geografia
"municipio","nacional","federal","brasil","brasileiro"

"outro", "outra", "outros", "outras", 
"informado", "nformado", "nao_informado", # ruídos de campos vazios
"assunto", "area", "tipo", "sobre",       # meta-palavras
"meir", "metrologia",                     # se forem muito genéricos no seu contexto
"doc", "pdf", "anexo"                     # ruídos de arquivos
}


# =============================================================================
# 5. LIMPEZA DE TEXTO (PROCESSAMENTO EM LOTE)
# =============================================================================

def limpar_textos_batch(textos):
    resultados = []
    for doc in nlp.pipe(textos, batch_size=1000):
        tokens = []
        for token in doc:
            lemma = token.lemma_.lower().strip()
            # REGRA DE OURO: Apenas Substantivos (NOUN), Adjetivos (ADJ) e Nomes Próprios (PROPN)
            if token.pos_ in {"NOUN", "ADJ", "PROPN"}: 
                if (
                    lemma not in STOPWORDS_DOMINIO
                    and lemma not in nlp.Defaults.stop_words
                    and len(lemma) > 3 # Aumentei para 3 para tirar "de", "o", "a"
                    and lemma.isalpha() # Garante que não tem números ou símbolos
                ):
                    tokens.append(lemma)
        resultados.append(" ".join(tokens))
    return resultados


# =============================================================================
# 6. CARREGAR BASE
# =============================================================================

if not os.path.exists(ARQUIVO_DADOS):
    raise FileNotFoundError("Arquivo de dados não encontrado")

print("Carregando base...")

df = pd.read_parquet(ARQUIVO_DADOS)


# detectar coluna de assunto automaticamente

coluna_texto = None

for c in df.columns:
    if c.lower() == "assunto":
        coluna_texto = c
        break

if coluna_texto is None:
    raise ValueError("Coluna 'assunto' não encontrada")


# =============================================================================
# 7. LIMPAR TEXTOS (ORDEM CORRIGIDA)
# =============================================================================

print(f"Base carregada com {len(df)} registros.")

# 1. Amostragem
limite_amostra = 30000
if len(df) > limite_amostra:
    df = df.sample(limite_amostra, random_state=42).copy()

print("Processando textos...")
inicio = time.time()

# 2. Preparação inicial e remoção de ruídos de "vazio"
textos_raw = df[coluna_texto].fillna("").astype(str).str.lower().tolist()
textos_sem_ruido = [re.sub(r"não informado|nao informado|sem informação|vazio", "", t) for t in textos_raw]

# 3. UNIÃO MANUAL (O pulo do gato: deve ser feito ANTES ou DEPOIS da limpeza)
# Vamos fazer antes para o spaCy entender como uma unidade só
substituicoes = {
    "microempreendedor individual": "microempreendedor_individual",
    "direitos humanos": "direitos_humanos",
    "transporte aereo": "transporte_aereo",
    "etica profissional": "etica_profissional",
    "codigo de conduta": "codigo_conduta",
    "certidao de nascimento": "certidao_nascimento"
}

for original, substituto in substituicoes.items():
    textos_sem_ruido = [t.replace(original, substituto) for t in textos_sem_ruido]

# 4. Limpeza via spaCy (Batch)
df["texto_limpo"] = limpar_textos_batch(textos_sem_ruido)

# 5. REMOVE VAZIOS E GERA CORPUS
df = df[df["texto_limpo"].str.strip() != ""].copy()
corpus = df["texto_limpo"].tolist()

print(f"Tempo NLP: {round(time.time() - inicio, 2)}s para {len(df)} documentos.")

# =============================================================================
# 8. GERAR BIGRAMAS (UNIÃO DE TERMOS COMPOSTOS)
# =============================================================================

tokens = [doc.split() for doc in corpus]

# Ajustamos o threshold: quanto MENOR o valor, MAIS ele une palavras.
# min_count: a expressão deve aparecer pelo menos 3 vezes para ser unida.
phrases = Phrases(tokens, min_count=3, threshold=5) 

bigram = Phraser(phrases)

# Aplica a união (ex: 'microempreendedor', 'individual' vira 'microempreendedor_individual')
tokens_bigram = [bigram[t] for t in tokens]

corpus = [" ".join(t) for t in tokens_bigram]

print("Bigramas gerados (ex: microempreendedor_individual).")


# =============================================================================
# 9. FREQUÊNCIA DE PALAVRAS
# =============================================================================

counter = Counter()

for doc in corpus:
    counter.update(doc.split())

frequencias = {

    k:v
    for k,v in counter.items()
    if v >= 5

}


# =============================================================================
# 10. WORDCLOUD (TEMA CÉU)
# =============================================================================

os.makedirs("assets", exist_ok=True)

wordcloud = WordCloud(

    width=1600,
    height=900,

    background_color="#65347B",

    colormap="Purples",

    max_words=120,

    prefer_horizontal=0.9,

    collocations=False

).generate_from_frequencies(frequencias)


plt.figure(figsize=(16,9))
plt.imshow(wordcloud, interpolation="bilinear")
plt.axis("off")

plt.savefig(IMG_WORDCLOUD, dpi=300, bbox_inches="tight")

plt.close()

print("Nuvem de palavras salva.")


# =============================================================================
# 11. PARETO HORIZONTAL EQUILIBRADO (RIGOR 80% COM LEITURA LIMPA)
# =============================================================================

# 1. Preparar DataFrame e Acumulado
pareto_completo = pd.DataFrame(
    sorted(frequencias.items(), key=lambda x: x[1], reverse=True),
    columns=["palavra", "frequencia"]
)
total_base = pareto_completo["frequencia"].sum()
pareto_completo["acumulado"] = pareto_completo["frequencia"].cumsum() / total_base

# 2. DEFINIR CORTE LIMPO: Pegamos as top 25 palavras
# Isso garante que os labels no eixo Y não fiquem minúsculos
n_limite = 25
df_top = pareto_completo.head(n_limite).copy()

# 3. CALCULAR O "RESTO DOS 80%":
# Pegamos as palavras da posição 26 até onde atinge 80%
df_meio = pareto_completo.iloc[n_limite:]
df_meio_80 = df_meio[df_meio["acumulado"] <= 0.81]

soma_relevantes_80 = df_meio_80["frequencia"].sum()
soma_cauda_longa = pareto_completo.iloc[len(df_top) + len(df_meio_80):]["frequencia"].sum()

# 4. Criar as linhas de agrupamento
row_relevantes = pd.DataFrame([{"palavra": f"Outros {len(df_meio_80)} termos (até 80%)", "frequencia": soma_relevantes_80}])
row_cauda = pd.DataFrame([{"palavra": "Demais termos (100%)", "frequencia": soma_cauda_longa}])

# 5. Consolidar e Inverter
top_pareto = pd.concat([df_top[["palavra", "frequencia"]], row_relevantes, row_cauda], ignore_index=True)
top_pareto = top_pareto.iloc[::-1].reset_index(drop=True)

# Recalcular acumulado para a linha
top_pareto["acumulado_grafico"] = (top_pareto["frequencia"][::-1].cumsum()[::-1]) / total_base

# 6. Gerar Gráfico
fig, ax1 = plt.subplots(figsize=(12, 10)) # Altura fixa confortável para 27 linhas

bars = ax1.barh(top_pareto["palavra"], top_pareto["frequencia"], color="#9370DB", alpha=0.7)
ax2 = ax1.twiny()
ax2.plot(top_pareto["acumulado_grafico"], top_pareto["palavra"], marker="o", color="#6A0DAD")
ax2.axvline(x=0.8, color='red', linestyle='--', label="Corte 80%")

ax1.set_xlabel("Frequência Absoluta")
ax2.set_xlabel("Percentual Acumulado (%)")
plt.title("Análise de Pareto: Top 25 + Agrupamento de Relevância (Rigor 80%)")

plt.tight_layout()
plt.savefig(IMG_PARETO, dpi=300)
plt.close()

# =============================================================================
# 12. MODELAGEM DE TÓPICOS (LDA)
# =============================================================================

vectorizer = CountVectorizer(

    max_features=600,

    ngram_range=(1,2),

    min_df=5,

    max_df=0.75

)

dtm = vectorizer.fit_transform(corpus)

feature_names = vectorizer.get_feature_names_out()


lda = LatentDirichletAllocation(

    n_components=6,

    random_state=42,

    max_iter=30

)

lda.fit(dtm)


# =============================================================================
# 13. EXTRAIR PALAVRAS DOS TÓPICOS
# =============================================================================

topicos = []

for i, componente in enumerate(lda.components_):

    indices = componente.argsort()[-10:][::-1]

    palavras = [feature_names[j] for j in indices]

    topicos.append({

        "topico": i+1,
        "palavras": ", ".join(palavras),
        "peso": round(componente.sum(),2)

    })


df_topicos = pd.DataFrame(topicos)


# =============================================================================
# 14. SALVAR TÓPICOS
# =============================================================================

os.makedirs("data/processed", exist_ok=True)

df_topicos.to_parquet(ARQUIVO_TOPICOS, index=False)

print("Tópicos salvos.")


# =============================================================================
# 15. WORDCLOUD DOS TÓPICOS
# =============================================================================

pesos = {}

for _,row in df_topicos.iterrows():

    palavras = row["palavras"].split(",")

    peso = row["peso"] / len(palavras)

    for p in palavras:

        p = p.strip()

        pesos[p] = pesos.get(p,0) + peso


wc_topicos = WordCloud(

    width=1600,
    height=900,

    background_color="#65347B",

    colormap="Purples"

).generate_from_frequencies(pesos)


plt.figure(figsize=(16,9))

plt.imshow(wc_topicos, interpolation="bilinear")

plt.axis("off")

plt.savefig(IMG_WORDCLOUD_TOPICOS, dpi=300, bbox_inches="tight")

plt.close()

print("Nuvem de tópicos salva.")


# =============================================================================
# FIM
# =============================================================================

print("Pipeline NLP finalizado.")
