"""
Arquivo para testar todas as importações
"""
import sys

print("🔍 Testando importações...")

try:
    from utils.design import MAPA_FONTE
    print("✅ utils.design importado com sucesso")
except Exception as e:
    print(f"❌ Erro em utils.design: {e}")

try:
    from views.temporal import grafico_evolucao_mensal
    print("✅ views.temporal importado com sucesso")
except Exception as e:
    print(f"❌ Erro em views.temporal: {e}")

try:
    from pages.lai_pedidos import layout
    print("✅ pages.lai importado com sucesso")
except Exception as e:
    print(f"❌ Erro em pages.lai: {e}")

print("\n📋 Verificação concluída!")