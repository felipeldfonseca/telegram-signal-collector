#!/usr/bin/env python3
"""
Sistema Integrado de Trading Diário
Combina coleta histórica + análise + trading em tempo real

Workflow:
1. Coleta dados históricos do dia (6:00 até agora)
2. Analisa condições baseado no histórico
3. Inicia sistema de trading em tempo real (17:00-23:59)
4. Salva todos os dados continuamente
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
import pytz

# Adicionar diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from collector import Config, AdaptiveStrategy, Storage, LiveTrader
from collector.runner import Runner
from collector.parser import Signal, HistoricalParser
from collector.regex import find_signal
from collector.adaptive_strategy import StrategyType


class DailyTradingSystem:
    """Sistema integrado de trading diário."""
    
    def __init__(self):
        self.config = Config()
        self.config.setup_logging()
        self.storage = Storage(self.config)
        self.adaptive = AdaptiveStrategy(self.config)
        
    async def run_daily_system(self):
        """Executa sistema completo do dia."""
        print("🚀 SISTEMA INTEGRADO DE TRADING DIÁRIO")
        print("=" * 80)
        print(f"📅 Data: {datetime.now().strftime('%d/%m/%Y')}")
        print(f"⏰ Horário atual: {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 80)
        
        # Etapa 1: Coleta histórica
        historical_signals = await self._collect_historical_data()
        
        # Etapa 2: Análise pré-trading
        await self._analyze_pre_trading_conditions(historical_signals)
        
        # Etapa 3: Sistema em tempo real
        await self._start_live_trading_system()
    
    async def _collect_historical_data(self):
        """Coleta dados históricos do dia."""
        print("\n📊 ETAPA 1: COLETA DE DADOS HISTÓRICOS")
        print("=" * 60)
        
        runner = Runner(self.config)
        
        try:
            # Conectar ao Telegram
            print("📡 Conectando ao Telegram...")
            await runner.setup_client()
            
            # Definir período (06:00 até agora)
            now = datetime.now(self.config.timezone)
            today_start = now.replace(hour=6, minute=0, second=0, microsecond=0)
            
            print(f"🕐 Período: {today_start.strftime('%H:%M')} até {now.strftime('%H:%M')}")
            
            # Coletar mensagens usando HistoricalParser
            print("🔍 Coletando mensagens...")
            entity = await runner.get_chat_entity()
            parser = HistoricalParser(self.config)
            
            signals = []
            message_count = 0
            
            async for message in runner.client.iter_messages(entity, limit=500):
                local_time = message.date.astimezone(self.config.timezone)
                
                if local_time < today_start:
                    break
                if local_time > now:
                    continue
                
                message_count += 1
                
                # Parse sem filtro de horário usando HistoricalParser
                signal = parser.parse_message_no_time_filter(message)
                if signal:
                    signals.append(signal)
            
            print(f"✅ Processadas {message_count} mensagens")
            print(f"🎯 Encontrados {len(signals)} sinais")
            
            # Salvar dados
            if signals:
                print("💾 Salvando dados históricos...")
                # Debug info: show now and signal timestamps
                print(f"[DEBUG] now: {now} (type: {type(now)})")
                print(f"[DEBUG] signal min timestamp: {min([s.timestamp for s in signals]) if signals else 'N/A'}")
                print(f"[DEBUG] signal max timestamp: {max([s.timestamp for s in signals]) if signals else 'N/A'}")
                self.storage.save_to_csv(signals, now)
                
                # Estatísticas rápidas (conforme estratégias: apenas 1ª tentativa + G1 são wins)
                first_attempt_wins = len([s for s in signals if s.result == 'W' and s.attempt == 1])
                g1_wins = len([s for s in signals if s.result == 'W' and s.attempt == 2])
                wins = first_attempt_wins + g1_wins  # Apenas 1ª tentativa + G1
                losses = len([s for s in signals if s.result == 'L']) + len([s for s in signals if s.result == 'W' and s.attempt == 3])  # Losses + G2
                win_rate = wins / len(signals) * 100 if signals else 0
                
                print(f"📈 Resumo: {len(signals)} sinais | {win_rate:.1f}% win rate")
            
            await runner.cleanup()
            return signals
            
        except Exception as e:
            print(f"❌ Erro na coleta: {e}")
            if runner.client:
                await runner.cleanup()
            return []
    
    async def _analyze_pre_trading_conditions(self, signals):
        """Analisa condições pré-trading."""
        print("\n🧠 ETAPA 2: ANÁLISE PRÉ-TRADING")
        print("=" * 60)
        
        if len(signals) < 10:
            print("⚠️ Poucos dados para análise confiável")
            print("🎯 Sistema usará análise em tempo real")
            return
        
        # Análise geral do dia
        print("📊 ANÁLISE GERAL DO DIA:")
        conditions = self.adaptive.analyze_market_conditions(signals)
        print(f"   {conditions}")
        
        # Análise da última hora (mudança de 2h para 1h)
        now = datetime.now(self.config.timezone)
        one_hour_ago = now - timedelta(hours=1)
        recent_signals = [s for s in signals if s.timestamp >= one_hour_ago]
        
        if len(recent_signals) >= 5:
            print(f"\n🔮 ANÁLISE ÚLTIMA HORA ({len(recent_signals)} sinais):")
            recent_conditions = self._analyze_with_detailed_breakdown(recent_signals)
            print(f"   {recent_conditions}")
            
            # Verificar se houve 3 losses consecutivos no final da última hora
            self._check_consecutive_losses_alert(recent_signals)
            
            strategy = recent_conditions.recommended_strategy
            confidence = recent_conditions.confidence_level
            
            print(f"\n🎯 RECOMENDAÇÃO INICIAL PARA 17:00:")
            print("-" * 40)
            
            if strategy.value == 'pause':
                print("   ⏸️  AGUARDAR - Condições desfavoráveis")
            elif strategy.value == 'martingale_conservative':
                print("   🎲 MARTINGALE CONSERVATIVE")
                print("   💰 ROI esperado: 56.0% mensal")
            elif strategy.value == 'infinity_conservative':
                print("   ♾️  INFINITY CONSERVATIVE")
                print("   💰 ROI esperado: 45.1% mensal")
            
            print(f"   🎲 Win rate: {confidence:.1f}%")
            
            # Pergunta sobre condições do mercado
            final_strategy = self._ask_market_condition(strategy)
            
            print(f"\n✅ ESTRATÉGIA FINAL: {final_strategy.value.upper()}")
        
        print("\n💡 NOTA: Sistema reavaliará automaticamente às 17:59, 18:59, etc.")
    
    def _analyze_with_detailed_breakdown(self, signals):
        """Analisa sinais com breakdown detalhado de G2 e STOP separados."""
        if not signals:
            return self.adaptive.analyze_market_conditions(signals)
        
        # Agrupar sinais por operação
        operations = self.adaptive._group_signals_into_operations(signals)
        
        # Calcular métricas detalhadas
        total_ops = len(operations)
        first_attempt_wins = sum(1 for op in operations if op['result'] == 'W' and op['attempts'] == 1)
        g1_recoveries = sum(1 for op in operations if op['result'] == 'W' and op['attempts'] == 2)
        g2_wins = sum(1 for op in operations if op['result'] == 'W' and op['attempts'] == 3)
        stops = sum(1 for op in operations if op['result'] == 'L')
        
        # Calcular taxas
        first_attempt_rate = (first_attempt_wins / total_ops * 100) if total_ops > 0 else 0
        g1_recovery_rate = (g1_recoveries / max(1, total_ops - first_attempt_wins) * 100) if total_ops > first_attempt_wins else 0
        g2_rate = (g2_wins / total_ops * 100) if total_ops > 0 else 0
        stop_rate = (stops / total_ops * 100) if total_ops > 0 else 0
        
        # Calcular win rate geral (apenas 1ª tentativa + G1 são wins, G2 e STOP são losses)
        total_wins = first_attempt_wins + g1_recoveries
        win_rate = (total_wins / total_ops * 100) if total_ops > 0 else 0
        
        # Determinar estratégia usando a mesma lógica do AdaptiveStrategy
        # Calcular G2+STOP rate para consistência
        g2_stop_rate = g2_rate + stop_rate
        
        if total_ops < 10:  # Poucos dados
            recommended_strategy = StrategyType.PAUSE
        elif g2_stop_rate > 30:  # Se G2+STOP > 30%, pausar
            recommended_strategy = StrategyType.PAUSE
        elif g1_recovery_rate > 65:  # Se G1 recovery > 65%, usar Martingale
            recommended_strategy = StrategyType.MARTINGALE_CONSERVATIVE
        elif first_attempt_rate > 60:  # Se 1ª tentativa > 60%, usar Infinity
            recommended_strategy = StrategyType.INFINITY_CONSERVATIVE
        else:
            recommended_strategy = StrategyType.INFINITY_CONSERVATIVE
        
        # Período de análise
        if signals:
            start_time = min(signal.timestamp for signal in signals)
            end_time = max(signal.timestamp for signal in signals)
            period = f"{start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')}"
        else:
            period = "N/A"
        
        # Criar objeto personalizado para retorno com formato modificado
        class DetailedConditions:
            def __init__(self, total_ops, first_rate, g1_rate, g2_rate, stop_rate, strategy, win_rate, period):
                self.total_operations = total_ops
                self.first_attempt_success_rate = first_rate
                self.g1_recovery_rate = g1_rate
                self.g2_rate = g2_rate
                self.stop_rate = stop_rate
                self.recommended_strategy = strategy
                self.confidence_level = win_rate
                self.analysis_period = period
            
            def __str__(self):
                return (f"🔍 Análise {self.analysis_period}: {self.total_operations} ops | "
                       f"1ª: {self.first_attempt_success_rate:.1f}% | "
                       f"G1: {self.g1_recovery_rate:.1f}% | "
                       f"G2: {self.g2_rate:.1f}% | "
                       f"STOP: {self.stop_rate:.1f}% | "
                       f"Estratégia: {self.recommended_strategy.value.upper()} "
                       f"(Win rate: {self.confidence_level:.1f}%)")
        
        return DetailedConditions(
            total_ops, first_attempt_rate, g1_recovery_rate, 
            g2_rate, stop_rate, recommended_strategy, win_rate, period
        )
    
    def _check_consecutive_losses_alert(self, signals):
        """Verifica se houve 3 losses consecutivos no final da última hora."""
        if len(signals) < 3:
            return
        
        # Ordenar sinais por timestamp (mais recentes por último)
        sorted_signals = sorted(signals, key=lambda x: x.timestamp)
        
        # Pegar os últimos 3 sinais finalizados (não intermediários de gales)
        final_signals = []
        for signal in reversed(sorted_signals):
            if signal.result in ['W', 'L']:
                final_signals.append(signal)
                if len(final_signals) == 3:
                    break
        
        # Verificar se os 3 últimos foram losses
        if len(final_signals) == 3 and all(s.result == 'L' for s in final_signals):
            print("\n⚠️ ALERTA: ÚLTIMOS 3 SINAIS FORAM LOSSES CONSECUTIVOS!")
            print("🚨 O mercado pode ter ficado instável no final da última hora")
            print("💡 Considere aguardar estabilização antes de operar")
    
    def _ask_market_condition(self, initial_strategy):
        """Pergunta sobre a condição atual do mercado e ajusta estratégia se necessário."""
        print("\n❓ VERIFICAÇÃO DE CONDIÇÕES DE MERCADO:")
        print("-" * 50)
        
        while True:
            try:
                response = input("🔍 O mercado está visivelmente inoperável? (y/n): ").strip().lower()
                
                if response in ['y', 'yes', 's', 'sim']:
                    print("⏸️ Mercado identificado como INOPERÁVEL")
                    print("🔄 Estratégia alterada para: PAUSE")
                    return StrategyType.PAUSE
                
                elif response in ['n', 'no', 'não', 'nao']:
                    print("✅ Mercado identificado como OPERÁVEL")
                    print(f"🎯 Mantendo estratégia recomendada: {initial_strategy.value.upper()}")
                    return initial_strategy
                
                else:
                    print("❌ Resposta inválida. Digite 'y' para sim ou 'n' para não.")
                    
            except KeyboardInterrupt:
                print("\n🛑 Processo interrompido pelo usuário")
                return StrategyType.PAUSE
            except Exception as e:
                print(f"❌ Erro na entrada: {e}")
                print("🔄 Tentando novamente...")
    
    async def _start_live_trading_system(self):
        """Inicia sistema de trading em tempo real."""
        print("\n🚀 ETAPA 3: SISTEMA EM TEMPO REAL")
        print("=" * 60)
        
        now = datetime.now(self.config.timezone)
        
        # Verificar horário
        if now.hour < 17:
            wait_minutes = (17 - now.hour) * 60 - now.minute
            print(f"⏰ Aguardando {wait_minutes} minutos até 17:00...")
            print("🎯 Sistema iniciará automaticamente no horário")
        elif now.hour > 23:
            print("⏰ Fora do horário de operação (17:00-23:59)")
            print("🎯 Execute novamente amanhã")
            return
        else:
            print("✅ Horário de operação ativo!")
        
        # Iniciar LiveTrader
        print("\n🔄 Iniciando sistema de trading adaptativo...")
        trader = LiveTrader(self.config)
        
        try:
            await trader.start_live_trading()
        except KeyboardInterrupt:
            print("\n🛑 Sistema interrompido pelo usuário")
        except Exception as e:
            print(f"\n❌ Erro no sistema: {e}")


async def main():
    """Função principal."""
    system = DailyTradingSystem()
    await system.run_daily_system()


if __name__ == "__main__":
    asyncio.run(main())
