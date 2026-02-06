"""
Verifica a estrutura do projeto
"""
import os
import sys

print("📁 Verificando estrutura do projeto...")
print("=" * 60)

# Lista de arquivos/diretórios necessários
required_items = [
    "app.py",
    "components/",
    "components/sidebar.py",
    "components/filtros.py",
    "pages/",
    "pages/home.py",
    "pages/lai_ml.py",
    "pages/ouvidoria_ml.py",
    "pages/topicos.py",
    "views/",
    "views/temporal.py",
    "views/geografica.py",
    "views/perfil.py",
    "views/desempenho.py",
    "views/satisfacao.py",
    "utils/",
    "utils/design.py",
    "utils/preprocessamento.py",
    "data/processed/",
    "__pycache__/"  # Será ignorada se não existir
]

missing_items = []
existing_items = []

for item in required_items:
    if item.endswith("/"):
        # É um diretório
        if os.path.exists(item):
            existing_items.append(f"✅ Diretório: {item}")
        else:
            missing_items.append(f"❌ Diretório: {item}")
    else:
        # É um arquivo
        if os.path.exists(item):
            existing_items.append(f"✅ Arquivo: {item}")
        else:
            missing_items.append(f"❌ Arquivo: {item}")

print("📋 Itens encontrados:")
for item in existing_items:
    print(f"  {item}")

print("\n⚠️  Itens faltando:")
for item in missing_items:
    print(f"  {item}")

print("\n" + "=" * 60)

# Verificar se temos dados processados
print("\n📊 Verificando dados processados...")
data_files = [
    ("data/processed/lai.parquet", "LAI"),
    ("data/processed/ouvidoria.parquet", "Ouvidoria")
]

for file_path, name in data_files:
    if os.path.exists(file_path):
        size_mb = os.path.getsize(file_path) / (1024 * 1024)
        print(f"  ✅ {name}: {size_mb:.2f} MB")
    else:
        print(f"  ⚠️  {name}: Arquivo não encontrado")

print("\n" + "=" * 60)
print("🎯 Status: ", end="")
if len(missing_items) == 0:
    print("Estrutura completa! ✅")
else:
    print(f"{len(missing_items)} itens faltando ⚠️")