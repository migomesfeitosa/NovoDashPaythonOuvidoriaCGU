import pandas as pd
import os
from wordcloud import WordCloud
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import re

# Caminhos
ARQUIVO_DADOS = "data/processed/ouvidoria.parquet"
IMG_WORDCLOUD = "assets/wordcloud_assuntos.png"
ARQUIVO_TOPICOS = "data/processed/topicos_nlp.parquet"


# --- 1. EXPANSÃO DA LISTA DE RUÍDOS (STOPWORDS) ---
# Adicionamos palavras que dominam a nuvem mas não informam nada útil
STOPWORDS_PERSONALIZADAS = [
    "nao",
    "informado",
    "servico",
    "servicos",
    "assunto",
    "outros",
    "geral",
    "sobre",
    "portal",
    "outras",
    "informada",
    "brasil",
    "sistema",
    "federal",
    "unidade",
    "brasileira",
    "beneficios",
    "sociais",
    "programa",
    "programas",
    "governo",
    "nacional",
    "partir",
    "referente",
    "area",
    "municipio",
    "informacao",
]


def limpar_texto(texto):
    if not texto:
        return ""
    texto = str(texto).lower()
    # Remove "não informado" e variações antes de remover pontuação
    texto = re.sub(r"não informado|nao informado|n/a|vazio", "", texto)
    # Remove caracteres especiais
    texto = re.sub(r"[^\w\s]", "", texto)
    return texto.strip()


def rodar_nlp():
    print("🧠 [NLP] Iniciando processamento de texto...")

    if not os.path.exists(ARQUIVO_DADOS):
        print(f"❌ Arquivo {ARQUIVO_DADOS} não encontrado.")
        return

    # 1. Carregar Dados
    df = pd.read_parquet(ARQUIVO_DADOS)

    # IMPORTANTE: No seu ETL anterior, as colunas ficaram em snake_case (minúsculo)
    coluna_assunto = "assunto" if "assunto" in df.columns else "ASSUNTO"

    if coluna_assunto not in df.columns:
        print(f"❌ Coluna {coluna_assunto} não encontrada. Colunas: {df.columns}")
        return

    # --- FILTRAGEM DE RUÍDO NA FONTE ---
    # Removemos linhas que são apenas "não informado" antes mesmo de limpar
    df = df[df[coluna_assunto].str.lower() != "não informado"].copy()

    df = df.tail(50000).copy()

    print("   -> Limpando textos e removendo ruídos...")
    textos = df[coluna_assunto].dropna().apply(limpar_texto)
    # Remove strings vazias que sobraram após a limpeza
    textos = textos[textos != ""]

    # 2. Gerar WordCloud
    print("   -> Gerando Nuvem de Palavras...")

    # Unificamos as stopwords básicas com as nossas personalizadas
    from nltk.corpus import stopwords
    import nltk

    nltk.download("stopwords", quiet=True)
    stopwords_pt = stopwords.words("portuguese")
    # Removemos acentos das stopwords para bater com o regex do limpar_texto
    stopwords_pt = [re.sub(r"[^\w\s]", "", s) for s in stopwords_pt]
    stopwords_pt.extend(STOPWORDS_PERSONALIZADAS)

    texto_completo = " ".join(textos)

    # A WordCloud precisa receber as stopwords para não mostrar "e", "do", "da"
    wc = WordCloud(
        width=1200,
        height=600,
        background_color="white",
        colormap="viridis",
        stopwords=set(stopwords_pt),
        # --- ADICIONE/AJUSTE ESTES DOIS ---
        collocations=True,  # Permite que o WordCloud agrupe pares como "Assédio Moral"
        min_word_length=4,  # Ignora palavras muito curtas que sobraram
        max_words=150,  # Limita para focar no que realmente importa
    ).generate(texto_completo)

    wc.to_file(IMG_WORDCLOUD)
    print(f"      ✅ Salva em {IMG_WORDCLOUD}")

    # 3. Modelagem de Tópicos (LDA)
    print("   -> Identificando Tópicos (LDA)...")

    # O CountVectorizer também precisa das stopwords para o LDA ficar limpo
    vectorizer = CountVectorizer(
        stop_words=stopwords_pt,
        max_features=1000,
        ngram_range=(1, 2),  # <--- Isso faz o LDA entender "Assédio Moral" como um termo único
        max_df=0.8,  # Ignora palavras que aparecem em mais de 80% dos textos (muito comuns)
        min_df=105,
    )
    dtm = vectorizer.fit_transform(textos)

    lda = LatentDirichletAllocation(n_components=5, random_state=42)
    lda.fit(dtm)

    topicos_data = []
    feature_names = vectorizer.get_feature_names_out()

    for index, topic in enumerate(lda.components_):
        palavras = [feature_names[i] for i in topic.argsort()[-10:]]
        topicos_data.append(
            {
                "Topico_ID": index + 1,
                "Principais_Termos": ", ".join(palavras),
                "Peso": topic.sum(),
            }
        )

    df_topicos = pd.DataFrame(topicos_data)
    os.makedirs(os.path.dirname(ARQUIVO_TOPICOS), exist_ok=True)
    df_topicos.to_parquet(ARQUIVO_TOPICOS, index=False)
    print(f"      ✅ Tópicos salvos em {ARQUIVO_TOPICOS}")
    print("🏁 [NLP] Processamento concluído!")


if __name__ == "__main__":
    rodar_nlp()
