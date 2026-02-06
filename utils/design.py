"""
Arquivo central de design e cores.
Baseado em paletas acessíveis (Colorblind Safe) e Design System de Gov.
"""

# Paleta de cores original (mantendo compatibilidade)
CORES = {
    'LAI': '#0072B2',       # Azul Forte (Confiança)
    'OUVIDORIA': '#D55E00', # Laranja Queimado (Atenção/Humano)
    
    # Semântica de Resultado
    'SUCESSO': '#009E73',   # Verde Azulado (Distingue bem do vermelho)
    'ERRO': '#D55E00',      # Laranja/Vermelho forte
    'NEUTRO': '#999999',    # Cinza para dados irrelevantes
    'ALERTA': '#F0E442',    # Amarelo (Usar com texto preto)
    
    # Interface
    'BACKGROUND': '#F4F6F8',
    'CARD_BG': '#FFFFFF',
    'TEXTO': '#2c3e50'
}

# Paleta de cores aprimorada (nova)
PALETA = {
    'primaria': '#0052CC',        # Azul institucional
    'secundaria': '#FF6B35',      # Laranja ação
    'sucesso': '#00A878',         # Verde confirmação
    'alerta': '#FFD166',          # Amarelo atenção
    'erro': '#E63946',            # Vermelho problema
    'neutro': '#6C757D',          # Cinza neutro
    'fundo': '#F8F9FA',           # Fundo claro
    'card': '#FFFFFF',            # Card branco
}

# Mapas de Cores para Gráficos (Plotly)
MAPA_FONTE = {
    'LAI': CORES['LAI'], 
    'Ouvidoria': CORES['OUVIDORIA']
}

MAPA_RESULTADO = {
    'Acesso Concedido': CORES['SUCESSO'],
    'Acesso Negado': CORES['ERRO'],
    'Respondida': CORES['SUCESSO'],
    'Arquivada': CORES['NEUTRO'],
}

MAPA_PRAZO = {
    False: CORES['SUCESSO'], # Não atrasado
    True: CORES['ERRO']      # Atrasado
}

# Mapas de cores aprimorados
MAPAS_CORES = {
    'fontes': {
        'LAI': PALETA['primaria'],
        'Ouvidoria': PALETA['secundaria']
    },
    'resultados': {
        'Concedido': PALETA['sucesso'],
        'Negado': PALETA['erro'],
        'Parcial': PALETA['alerta']
    },
    'satisfacao': {
        '1': '#E63946', '2': '#FF6B35', '3': '#FFD166',
        '4': '#A7C957', '5': '#00A878'
    }
}

# Configurações de gráficos
CONFIG_GRAFICOS = {
    'displayModeBar': True,
    'displaylogo': False,
    'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
    'responsive': True,
    'toImageButtonOptions': {
        'format': 'png',
        'filename': 'grafico_cgu',
        'height': 500,
        'width': 800,
        'scale': 2
    }
}

# Exporta todas as variáveis importantes
__all__ = [
    'CORES', 'PALETA', 'MAPA_FONTE', 'MAPA_RESULTADO', 
    'MAPA_PRAZO', 'MAPAS_CORES', 'CONFIG_GRAFICOS'
]