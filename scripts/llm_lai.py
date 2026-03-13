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
# 7. LIMPAR TEXTOS (COM TRAVA DE MEMÓRIA E AMOSTRAGEM)
# =============================================================================

print(f"Base carregada com {len(df)} registros.")

# AJUSTE DE PERFORMANCE: Amostragem para evitar travamento
limite_amostra = 30000
if len(df) > limite_amostra:
    print(f"Base muito grande. Reduzindo para {limite_amostra} registros para viabilizar o NLP...")
    df = df.sample(limite_amostra, random_state=42).copy()

print("Processando textos (spaCy Batch)...")

inicio = time.time()

# Garante que não existam valores nulos que quebrem o spaCy
textos = df[coluna_texto].fillna("").astype(str).tolist()

# Antes de chamar o limpar_textos_batch:
textos = df[coluna_texto].astype(str).str.lower().tolist()
# Remove padrões comuns de "campo vazio"
textos = [re.sub(r"não informado|nao informado|sem informação|vazio", "", t) for t in textos]

# Processamento em lote (Batch)
df["texto_limpo"] = limpar_textos_batch(textos)

# Remove registros que ficaram vazios após a limpeza de stopwords
df = df[df["texto_limpo"].str.strip() != ""].copy()

corpus = df["texto_limpo"].tolist()

print(f"Tempo NLP: {round(time.time() - inicio, 2)} segundos para {len(df)} documentos.")


# =============================================================================
# 8. GERAR BIGRAMAS
# =============================================================================

tokens = [doc.split() for doc in corpus]

phrases = Phrases(tokens, min_count=5, threshold=10)

bigram = Phraser(phrases)

tokens_bigram = [bigram[t] for t in tokens]

corpus = [" ".join(t) for t in tokens_bigram]


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
# 11. GRÁFICO DE PARETO (COM CATEGORIA 'OUTROS' PARA 100%)
# =============================================================================

# 1. Preparar o DataFrame completo
pareto_completo = pd.DataFrame(
    sorted(frequencias.items(), key=lambda x: x[1], reverse=True),
    columns=["palavra","frequencia"]
)

# 2. Separar o Top 19 e agrupar o restante em 'Outros'
top_n = 19
df_top = pareto_completo.head(top_n).copy()
df_others_raw = pareto_completo.iloc[top_n:].copy()

# Soma a frequência de todas as palavras restantes
soma_outros = df_others_raw["frequencia"].sum()
df_others = pd.DataFrame([{"palavra": "Outros", "frequencia": soma_outros}])

# 3. Consolidar o DataFrame final (20 barras no total)
top_pareto = pd.concat([df_top, df_others], ignore_index=True)

# 4. Calcular percentuais sobre o total absoluto
total_geral = top_pareto["frequencia"].sum()
top_pareto["percentual"] = top_pareto["frequencia"] / total_geral
top_pareto["acumulado"] = top_pareto["percentual"].cumsum()

# 5. Gerar o Gráfico
fig, ax = plt.subplots(figsize=(12,6))

# Barras em Lilás
ax.bar(top_pareto["palavra"], top_pareto["frequencia"], color="#9370DB") 

ax.set_xticklabels(top_pareto["palavra"], rotation=45, ha='right')
ax.set_ylabel("Frequência")

ax2 = ax.twinx()

# Linha em Roxo Escuro (Agora chegando em 1.0 / 100%)
ax2.plot(top_pareto["palavra"], top_pareto["acumulado"], marker="o", color="#6A0DAD", linewidth=2)

ax2.set_ylabel("Percentual acumulado")
ax2.set_ylim(0, 1.1) # Garante que o topo dos 100% apareça bem

plt.title("Pareto dos Termos Mais Frequentes (Visão 100%)")
plt.tight_layout()

plt.savefig(IMG_PARETO, dpi=300, bbox_inches="tight")
plt.close()

print("Gráfico de Pareto consolidado (100%) salvo.")

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
