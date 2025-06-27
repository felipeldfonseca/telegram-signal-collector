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
from collector.parser import Signal
from collector.regex import find_signal


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
            
            # Coletar mensagens
            print("🔍 Coletando mensagens...")
            entity = await runner.get_chat_entity()
            
            signals = []
            message_count = 0
            
            async for message in runner.client.iter_messages(entity, limit=500):
                local_time = message.date.astimezone(self.config.timezone)
                
                if local_time < today_start:
                    break
                if local_time > now:
                    continue
                
                message_count += 1
                
                # Parse sem filtro de horário
                if message.text:
                    signal_data = find_signal(message.text)
                    if signal_data:
                        result, attempt, asset = signal_data
                        signal = Signal(
                            timestamp=local_time,
                            asset=asset,
                            result=result,
                            attempt=attempt
                        )
                        signals.append(signal)
            
            print(f"✅ Processadas {message_count} mensagens")
            print(f"🎯 Encontrados {len(signals)} sinais")
            
            # Salvar dados
            if signals:
                print("💾 Salvando dados históricos...")
                self.storage.save_to_csv(signals, now)
                
                # Estatísticas rápidas
                wins = len([s for s in signals if s.result == 'W'])
                losses = len([s for s in signals if s.result == 'L'])
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
        
        # Análise das últimas 2 horas
        now = datetime.now(self.config.timezone)
        two_hours_ago = now - timedelta(hours=2)
        recent_signals = [s for s in signals if s.timestamp >= two_hours_ago]
        
        if len(recent_signals) >= 5:
            print(f"\n🔮 ANÁLISE ÚLTIMAS 2H ({len(recent_signals)} sinais):")
            recent_conditions = self.adaptive.analyze_market_conditions(recent_signals)
            print(f"   {recent_conditions}")
            
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
            
            print(f"   🎲 Confiança: {confidence:.1f}%")
        
        print("\n💡 NOTA: Sistema reavaliará automaticamente às 17:59, 18:59, etc.")
    
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