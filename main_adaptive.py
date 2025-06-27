#!/usr/bin/env python3
"""
Sistema de Trading Adaptativo - Telegram Signal Collector
Implementa o workflow completo de análise horária e seleção automática de estratégias

Workflow:
1. Conecta ao Telegram e monitora sinais em tempo real
2. A cada hora (ou quando há sinais suficientes), analisa condições do mercado
3. Seleciona automaticamente a melhor estratégia baseada na análise:
   - Martingale Premium Conservative (ROI: 56.0%)
   - Infinity Conservative (ROI: 45.1%)
   - Pause (quando condições são desfavoráveis)
4. Exibe relatórios em tempo real e salva análises
"""

import asyncio
import argparse
import sys
import os
from datetime import datetime

# Adicionar diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from collector import Config, LiveTrader, AdaptiveStrategy, StrategyType


def print_welcome_banner():
    """Imprime banner de boas-vindas."""
    print("\n" + "🚀" + "=" * 78)
    print("SISTEMA DE TRADING ADAPTATIVO - TELEGRAM SIGNAL COLLECTOR")
    print("=" * 80)
    print("🎯 Análise inteligente de mercado em tempo real")
    print("🔄 Seleção automática da melhor estratégia")
    print("📊 Monitoramento 24/7 com relatórios detalhados")
    print("=" * 80)
    print()


def print_strategy_info():
    """Imprime informações das estratégias disponíveis."""
    print("📋 ESTRATÉGIAS DISPONÍVEIS:")
    print("-" * 40)
    print("🎲 MARTINGALE PREMIUM CONSERVATIVE")
    print("   • ROI: 56.0% mensal")
    print("   • Win Rate: 78.7%")
    print("   • Risco: $36 por sessão")
    print("   • Tentativas: Até G1 (2 tentativas)")
    print()
    print("♾️  INFINITY CONSERVATIVE")
    print("   • ROI: 45.1% mensal")
    print("   • Win Rate: 92.3% (sessões)")
    print("   • Risco: $49 por sessão")
    print("   • Tentativas: 7 níveis progressivos")
    print()
    print("⏸️  PAUSE")
    print("   • Ativado quando G2+STOP > 30%")
    print("   • Preserva capital em condições ruins")
    print("-" * 40)
    print()


def print_decision_criteria():
    """Imprime critérios de decisão."""
    print("🧠 CRITÉRIOS DE DECISÃO AUTOMÁTICA:")
    print("-" * 40)
    print("📊 ANÁLISE NO FINAL DE CADA HORA (XX:59):")
    print("   • Dados completos da hora inteira")
    print("   • Mínimo 5 operações para análise confiável")
    print("   • Taxa de sucesso 1ª tentativa")
    print("   • Taxa de recuperação G1") 
    print("   • Taxa de G2+STOP")
    print()
    print("🎯 SELEÇÃO DE ESTRATÉGIA:")
    print("   • Se G2+STOP > 30% → PAUSE")
    print("   • Se G1 recovery > 65% → MARTINGALE")
    print("   • Se 1ª tentativa > 60% → INFINITY")
    print("   • Confiança mínima: 70%")
    print("-" * 40)
    print()


async def run_live_system():
    """Executa o sistema em tempo real."""
    try:
        # Configurar sistema
        config = Config()
        config.setup_logging()
        
        print_welcome_banner()
        print_strategy_info()
        print_decision_criteria()
        
        # Verificar configurações
        print("🔧 VERIFICANDO CONFIGURAÇÕES:")
        print(f"   📱 Telegram API ID: {'✅ Configurado' if config.api_id else '❌ Não configurado'}")
        print(f"   🔐 Telegram API Hash: {'✅ Configurado' if config.api_hash else '❌ Não configurado'}")
        print(f"   👥 Grupo: {config.group_name if config.group_name else '❌ Não configurado'}")
        print(f"   🕐 Horário: {config.start_hour}:00 - {config.end_hour}:59")
        print(f"   🌍 Timezone: {config.timezone}")
        print()
        
        if not all([config.api_id, config.api_hash, config.group_name]):
            print("❌ ERRO: Configurações do Telegram não encontradas!")
            print("Configure as variáveis de ambiente ou arquivo .env:")
            print("   TG_API_ID=seu_api_id")
            print("   TG_API_HASH=seu_api_hash")
            print("   TG_GROUP=nome_do_grupo")
            return
        
        # Inicializar sistema
        print("🚀 Iniciando sistema adaptativo...")
        trader = LiveTrader(config)
        
        # Executar sistema
        await trader.start_live_trading()
        
    except KeyboardInterrupt:
        print("\n🛑 Sistema interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()


async def test_analysis_system():
    """Testa o sistema de análise com dados históricos."""
    print("🧪 MODO DE TESTE - SISTEMA DE ANÁLISE")
    print("=" * 50)
    
    try:
        config = Config()
        adaptive = AdaptiveStrategy(config)
        
        # Simular diferentes cenários
        test_scenarios = [
            {
                'name': 'Cenário Favorável ao Martingale',
                'first_rate': 45.0,
                'g1_rate': 75.0,
                'g2_stop_rate': 15.0,
                'total_ops': 20
            },
            {
                'name': 'Cenário Favorável ao Infinity',
                'first_rate': 70.0,
                'g1_rate': 50.0,
                'g2_stop_rate': 10.0,
                'total_ops': 25
            },
            {
                'name': 'Cenário para Pausar',
                'first_rate': 40.0,
                'g1_rate': 45.0,
                'g2_stop_rate': 35.0,
                'total_ops': 15
            },
            {
                'name': 'Poucos Dados',
                'first_rate': 60.0,
                'g1_rate': 70.0,
                'g2_stop_rate': 20.0,
                'total_ops': 5
            }
        ]
        
        for scenario in test_scenarios:
            print(f"\n📊 {scenario['name']}:")
            print(f"   1ª tentativa: {scenario['first_rate']:.1f}%")
            print(f"   G1 recovery: {scenario['g1_rate']:.1f}%")
            print(f"   G2+STOP: {scenario['g2_stop_rate']:.1f}%")
            print(f"   Total ops: {scenario['total_ops']}")
            
            strategy, confidence = adaptive._determine_strategy(
                scenario['total_ops'],
                scenario['first_rate'],
                scenario['g1_rate'],
                scenario['g2_stop_rate']
            )
            
            print(f"   🎯 Estratégia: {strategy.value.upper()}")
            print(f"   🎲 Confiança: {confidence:.1f}%")
            print("-" * 40)
        
        print("\n✅ Teste do sistema de análise concluído!")
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(
        description='Sistema de Trading Adaptativo - Telegram Signal Collector',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python main_adaptive.py                    # Executar sistema em tempo real
  python main_adaptive.py --test             # Testar sistema de análise
  python main_adaptive.py --help             # Mostrar esta ajuda

Configuração necessária (.env):
  TG_API_ID=seu_api_id
  TG_API_HASH=seu_api_hash
  TG_GROUP=nome_do_grupo
        """
    )
    
    parser.add_argument(
        '--test', 
        action='store_true',
        help='Executar em modo de teste (análise de cenários)'
    )
    
    args = parser.parse_args()
    
    if args.test:
        asyncio.run(test_analysis_system())
    else:
        asyncio.run(run_live_system())


if __name__ == "__main__":
    main() 