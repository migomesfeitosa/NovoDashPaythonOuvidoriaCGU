import os

def verificar():
    print("--- INICIANDO DIAGNÓSTICO DO PROJETO ---\n")
    
    # 1. Verificar se a pasta pages existe
    if not os.path.exists("pages"):
        print("❌ ERRO CRÍTICO: Pasta 'pages' não encontrada!")
        return

    arquivos = os.listdir("pages")
    print(f"📂 Arquivos encontrados na pasta 'pages': {arquivos}")

    # 2. Verificar nomes físicos dos arquivos
    tem_lai_novo = "lai.py" in arquivos
    tem_ouv_novo = "ouvidoria.py" in arquivos
    tem_lai_velho = "lai_ml.py" in arquivos
    tem_ouv_velho = "ouvidoria_ml.py" in arquivos

    if tem_lai_novo and tem_ouv_novo:
        print("✅ Arquivos físicos renomeados corretamente ('lai.py' e 'ouvidoria.py' existem).")
    else:
        print("\n❌ ERRO DE ARQUIVO FÍSICO:")
        if not tem_lai_novo: print("   - Faltando 'lai.py'")
        if not tem_ouv_novo: print("   - Faltando 'ouvidoria.py'")
        if tem_lai_velho: print("   - AVISO: 'lai_ml.py' antigo ainda existe. APAGUE-O.")
        if tem_ouv_velho: print("   - AVISO: 'ouvidoria_ml.py' antigo ainda existe. APAGUE-O.")

    # 3. Verificar conteúdo do __init__.py
    try:
        with open("pages/__init__.py", "r", encoding="utf-8") as f:
            conteudo = f.read()
            print("\n📄 Conteúdo do pages/__init__.py:")
            print("-" * 20)
            print(conteudo)
            print("-" * 20)
            
            if "from . import lai_ml" in conteudo or "from . import ouvidoria_ml" in conteudo:
                print("❌ ERRO NO __INIT__: Você ainda está importando os nomes antigos (_ml)!")
            elif "from . import lai" in conteudo and "from . import ouvidoria" in conteudo:
                print("✅ Conteúdo do __init__.py parece correto.")
            else:
                print("⚠️ AVISO: O __init__.py está estranho. Verifique os imports.")
    except Exception as e:
        print(f"❌ Erro ao ler __init__.py: {e}")

    # 4. Verificar app.py
    try:
        with open("app.py", "r", encoding="utf-8") as f:
            app_content = f.read()
            if "from pages import home, lai, ouvidoria" in app_content:
                print("✅ app.py está importando os módulos corretos.")
            elif "lai_ml" in app_content or "ouvidoria_ml" in app_content:
                print("❌ ERRO NO APP.PY: Ainda há referências a '_ml' no app.py.")
            else:
                print("⚠️ AVISO: Verifique a linha de importação no app.py.")
    except Exception as e:
        print(f"❌ Erro ao ler app.py: {e}")

if __name__ == "__main__":
    verificar()