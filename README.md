# 🏛️ Painel de Inteligência - Transparência e Ouvidoria (CGU)

## 🎯 Objetivo

Este projeto visa monitorar a saúde da relação entre Estado e Cidadão, integrando dados de **Transparência Passiva (LAI)** e **Manifestações de Ouvidoria**. O painel utiliza Ciência de Dados e Machine Learning para identificar gargalos, prever negativas de acesso e analisar a satisfação do cidadão.

## 📊 Visões do Painel

### 1. Visão Estratégica (Home)

- Monitoramento de volume de demandas (LAI vs Ouvidoria).
- Série temporal comparativa.
- Mapa de calor da participação cidadã.

### 2. Monitoramento LAI

- Análise de pedidos negados vs concedidos.
- Ranking de órgãos mais demandados.
- Eficiência no tempo de resposta.

### 3. Inteligência da Ouvidoria

- Perfil demográfico do cidadão (Gênero, Raça, Faixa Etária).
- Análise de satisfação e resolutividade.
- Principais assuntos reclamados.

### 4. Laboratório de IA (Em desenvolvimento)

- **Predição:** Modelo para estimar probabilidade de negativa de um pedido.
- **Clusterização:** Agrupamento de órgãos por perfil de atendimento.
- **NLP:** Análise de tópicos em textos de manifestações.

## 🛠️ Tecnologias

- **Linguagem:** Python 3.10+
- **Interface:** Dash & Plotly
- **Processamento:** Pandas & PyArrow (Parquet)
- **Machine Learning:** Scikit-learn, SHAP, Imbalanced-learn

## 🚀 Como Rodar o Projeto

1. **Instale as dependências:**

   ```bash
   pip install -r requirements.txt
