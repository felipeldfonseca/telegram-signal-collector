#!/usr/bin/env python3
"""
Teste simples de importação
"""

print("=== TESTE DE IMPORTAÇÃO ===")

try:
    print("1. Testando import básico...")
    import sys
    print(f"   Python version: {sys.version}")
    
    print("2. Testando import collector...")
    import collector
    print("   Collector import: OK")
    
    print("3. Testando import HistoricalParser...")
    from collector.parser import HistoricalParser
    print("   HistoricalParser import: OK")
    
    print("4. Testando criação de instância...")
    from collector import Config
    config = Config()
    parser = HistoricalParser(config)
    print("   HistoricalParser instance: OK")
    
    print("\n✅ TODOS OS TESTES PASSARAM!")
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
