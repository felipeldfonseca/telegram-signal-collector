#!/usr/bin/env python3
"""
Coleta TODOS os sinais de hoje (sem filtro de horário) e faz análise completa
Prepara o sistema para trading adaptativo das 17:00-23:59
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
import pytz

# Adicionar diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from collector import Config, AdaptiveStrategy, Storage
from collector.runner import Runner
from collector.parser import Signal
from collector.regex import find_signal


class FullDayParser:
    """Parser que coleta sinais de qualquer horário."""
    
    def __init__(self, config: Config):
        self.config = config
        self.timezone = config.timezone
    
    def parse_message_no_time_filter(self, message) -> Signal:
        """
        Parse mensagem SEM filtro de horário.
        
        Args:
            message: Mensagem do Telegram
            
        Returns:
            Signal ou None
        """
        try:
            if not message.text:
                return None
            
            # Extrair sinal usando regex
            signal_data = find_signal(message.text)
            if not signal_data:
                return None
            
            result, attempt, asset = signal_data
            
            # Converter timestamp
            timestamp = message.date
            if timestamp.tzinfo is None:
                timestamp = pytz.UTC.localize(timestamp)
            
            local_timestamp = timestamp.astimezone(self.timezone)
            
            # Criar signal SEM validação de horário
            signal = Signal(
                timestamp=local_timestamp,
                asset=asset,
                result=result,
                attempt=attempt
            )
            
            return signal
            
        except Exception as e:
            print(f"Erro ao processar mensagem: {e}")
            return None


async def collect_full_day_data():
    """Coleta TODOS os sinais de hoje."""
    print("📊 COLETANDO TODOS OS SINAIS DE HOJE")
    print("=" * 60)
    
    config = Config()
    config.setup_logging()
    runner = Runner(config)
    storage = Storage(config)
    parser = FullDayParser(config)
    
    try:
        # Conectar ao Telegram
        print("📡 Conectando ao Telegram...")
        await runner.setup_client()
        
        # Definir período (06:00 até agora)
        now = datetime.now(config.timezone)
        today_start = now.replace(hour=6, minute=0, second=0, microsecond=0)
        
        print(f"🕐 Período: {today_start.strftime('%H:%M')} até {now.strftime('%H:%M')}")
        print(f"📅 Data: {now.strftime('%d/%m/%Y')}")
        
        # Coletar mensagens manualmente
        print("\n🔍 Coletando mensagens...")
        entity = await runner.get_chat_entity()
        
        signals = []
        message_count = 0
        
        async for message in runner.client.iter_messages(entity, limit=500):
            # Verificar se está no período
            local_time = message.date.astimezone(config.timezone)
            
            if local_time < today_start:
                break  # Mensagens muito antigas
            
            if local_time > now:
                continue  # Mensagens futuras (não deveria acontecer)
            
            message_count += 1
            
            # Tentar extrair sinal
            signal = parser.parse_message_no_time_filter(message)
            if signal:
                signals.append(signal)
        
        print(f"✅ Processadas {message_count} mensagens")
        print(f"🎯 Encontrados {len(signals)} sinais")
        
        if signals:
            # Salvar dados
            print("\n💾 Salvando dados...")
            storage.save_to_csv(signals, now)
            
            # Estatísticas detalhadas
            print("\n📈 ESTATÍSTICAS COMPLETAS DO DIA:")
            print("-" * 50)
            
            # Agrupar por resultado (conforme estratégias: apenas 1ª tentativa + G1 são wins)
            first_attempt_wins = [s for s in signals if s.result == 'W' and s.attempt == 1]
            g1_wins = [s for s in signals if s.result == 'W' and s.attempt == 2]
            wins = first_attempt_wins + g1_wins  # Apenas 1ª tentativa + G1
            losses = [s for s in signals if s.result == 'L'] + [s for s in signals if s.result == 'W' and s.attempt == 3]  # Losses + G2
            
            print(f"📊 Total de sinais: {len(signals)}")
            print(f"✅ Wins: {len(wins)} ({len(wins)/len(signals)*100:.1f}%)")
            print(f"❌ Losses: {len(losses)} ({len(losses)/len(signals)*100:.1f}%)")
            
            # Agrupar por tentativa
            first_attempt = [s for s in signals if s.result == 'W' and s.attempt == 1]
            g1_wins = [s for s in signals if s.result == 'W' and s.attempt == 2]
            g2_wins = [s for s in signals if s.result == 'W' and s.attempt == 3]
            
            print(f"🎯 1ª tentativa: {len(first_attempt)} ({len(first_attempt)/len(signals)*100:.1f}%)")
            print(f"🔄 G1 wins: {len(g1_wins)} ({len(g1_wins)/len(signals)*100:.1f}%)")
            print(f"🔄 G2 wins: {len(g2_wins)} ({len(g2_wins)/len(signals)*100:.1f}%)")
            
            # Agrupar por ativo
            print(f"\n💰 SINAIS POR ATIVO:")
            assets = {}
            for signal in signals:
                if signal.asset not in assets:
                    assets[signal.asset] = {'first_wins': 0, 'g1_wins': 0, 'losses': 0}
                
                # Conforme estratégias: apenas 1ª tentativa e G1 são wins
                if signal.result == 'W' and signal.attempt == 1:
                    assets[signal.asset]['first_wins'] += 1
                elif signal.result == 'W' and signal.attempt == 2:
                    assets[signal.asset]['g1_wins'] += 1
                else:
                    # Losses reais + G2 (consideramos como losses)
                    assets[signal.asset]['losses'] += 1
            
            for asset, stats in sorted(assets.items()):
                wins = stats['first_wins'] + stats['g1_wins']  # Apenas 1ª tentativa + G1
                total = wins + stats['losses']
                win_rate = wins / total * 100 if total > 0 else 0
                print(f"   {asset}: {wins}W/{stats['losses']}L ({win_rate:.1f}%)")
            
            # Análise temporal por hora
            print(f"\n⏰ DISTRIBUIÇÃO TEMPORAL:")
            hourly = {}
            for signal in signals:
                hour = signal.timestamp.hour
                if hour not in hourly:
                    hourly[hour] = {'first_wins': 0, 'g1_wins': 0, 'losses': 0}
                
                # Conforme estratégias: apenas 1ª tentativa e G1 são wins
                if signal.result == 'W' and signal.attempt == 1:
                    hourly[hour]['first_wins'] += 1
                elif signal.result == 'W' and signal.attempt == 2:
                    hourly[hour]['g1_wins'] += 1
                else:
                    # Losses reais + G2 (consideramos como losses)
                    hourly[hour]['losses'] += 1
            
            for hour in sorted(hourly.keys()):
                stats = hourly[hour]
                wins = stats['first_wins'] + stats['g1_wins']  # Apenas 1ª tentativa + G1
                total = wins + stats['losses']
                win_rate = wins / total * 100 if total > 0 else 0
                print(f"   {hour:02d}:00-{hour:02d}:59: {total} sinais ({win_rate:.1f}% win rate)")
            
            # Últimos sinais
            print(f"\n📋 ÚLTIMOS 15 SINAIS:")
            print("-" * 50)
            for signal in signals[-15:]:
                attempt_str = f"G{signal.attempt}" if signal.attempt else "1ª"
                result_str = "✅ WIN" if signal.result == 'W' else "❌ LOSS"
                print(f"   {signal.timestamp.strftime('%H:%M')} | {signal.asset} | {result_str} | {attempt_str}")
            
        else:
            print("⚠️ Nenhum sinal encontrado hoje")
        
        await runner.cleanup()
        return signals
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        if runner.client:
            await runner.cleanup()
        return []


async def analyze_full_day_conditions(signals):
    """Analisa condições do mercado com dados completos do dia."""
    print("\n🧠 ANÁLISE COMPLETA DE CONDIÇÕES DE MERCADO")
    print("=" * 70)
    
    if len(signals) < 5:
        print("⚠️ Poucos dados para análise confiável")
        return
    
    config = Config()
    adaptive = AdaptiveStrategy(config)
    
    # Análise geral do dia
    print("📊 ANÁLISE GERAL DO DIA COMPLETO:")
    conditions = adaptive.analyze_market_conditions(signals)
    print(f"   {conditions}")
    
    # Análise por períodos de 1 hora
    if len(signals) >= 20:
        print("\n📈 ANÁLISE POR PERÍODOS (2h cada):")
        print("-" * 50)
        
        periods = {}
        for signal in signals:
            period = signal.timestamp.hour // 2 * 2  # 6-8, 8-10, 10-12, etc.
            if period not in periods:
                periods[period] = []
            periods[period].append(signal)
        
        for period_start in sorted(periods.keys()):
            period_signals = periods[period_start]
            if len(period_signals) >= 3:
                period_end = period_start + 2
                print(f"\n   🕐 {period_start:02d}:00-{period_end:02d}:00 ({len(period_signals)} sinais):")
                period_conditions = adaptive.analyze_market_conditions(period_signals)
                print(f"      {period_conditions}")
    
    # Análise da última 1 hora (mais relevante para previsão)
    print("\n🔮 ANÁLISE DA ÚLTIMA 1 HORA (MAIS RELEVANTE):")
    print("-" * 50)
    
    now = datetime.now(config.timezone)
    two_hours_ago = now - timedelta(hours=2)
    
    recent_signals = [s for s in signals if s.timestamp >= two_hours_ago]
    
    if len(recent_signals) >= 5:
        recent_conditions = adaptive.analyze_market_conditions(recent_signals)
        print(f"📊 Baseado nos últimos {len(recent_signals)} sinais (últimas 2h):")
        print(f"   {recent_conditions}")
        
        # Recomendação para 17:00-18:00
        strategy = recent_conditions.recommended_strategy
        confidence = recent_conditions.confidence_level
        
        print(f"\n🎯 RECOMENDAÇÃO PARA 17:00-18:00:")
        print("-" * 40)
        
        if strategy.value == 'pause':
            print("   ⏸️  AGUARDAR - Condições desfavoráveis detectadas")
            print("   💡 Sugestão: Monitorar primeiros sinais das 17:00")
            print("   🔍 Reavaliação: A cada 10 sinais ou às 18:00")
        elif strategy.value == 'martingale_conservative':
            print("   🎲 MARTINGALE CONSERVATIVE - Alta recuperação G1 detectada")
            print("   💰 ROI esperado: 56.0% mensal")
            print("   🎯 Estrutura: $4 → $8 (máximo 2 tentativas)")
        elif strategy.value == 'infinity_conservative':
            print("   ♾️  INFINITY CONSERVATIVE - Alta taxa 1ª tentativa detectada")
            print("   💰 ROI esperado: 45.1% mensal")
            print("   🎯 Estrutura: 7 níveis progressivos")
        
        print(f"   🎲 Confiança: {confidence:.1f}%")
        
        # Análise de tendência
        if len(recent_signals) >= 10:
            first_half = recent_signals[:len(recent_signals)//2]
            second_half = recent_signals[len(recent_signals)//2:]
            
            # Conforme estratégias: apenas 1ª tentativa e G1 são wins
            first_wins = len([s for s in first_half if (s.result == 'W' and s.attempt in [1, 2])])
            second_wins = len([s for s in second_half if (s.result == 'W' and s.attempt in [1, 2])])
            first_win_rate = first_wins / len(first_half) * 100
            second_win_rate = second_wins / len(second_half) * 100
            
            trend = second_win_rate - first_win_rate
            
            print(f"\n📈 TENDÊNCIA RECENTE:")
            print(f"   1ª metade: {first_win_rate:.1f}% win rate")
            print(f"   2ª metade: {second_win_rate:.1f}% win rate")
            
            if trend > 5:
                print(f"   📈 Tendência POSITIVA (+{trend:.1f}%)")
            elif trend < -5:
                print(f"   📉 Tendência NEGATIVA ({trend:.1f}%)")
            else:
                print(f"   ➡️ Tendência ESTÁVEL ({trend:+.1f}%)")
    
    else:
        print(f"   ⚠️ Apenas {len(recent_signals)} sinais nas últimas 2h")
        print("   📊 Usando análise do dia completo para previsão")
        
        if len(signals) >= 10:
            day_conditions = adaptive.analyze_market_conditions(signals)
            print(f"   {day_conditions}")


async def prepare_for_trading():
    """Prepara sistema para trading das 17:00-23:59."""
    print("\n🚀 PREPARANDO SISTEMA PARA TRADING 17:00-23:59")
    print("=" * 70)
    
    now = datetime.now()
    target_time = now.replace(hour=17, minute=0, second=0, microsecond=0)
    
    if now >= target_time:
        print("✅ Já passou das 17:00 - Sistema pode iniciar imediatamente")
        print("🎯 Execute: python main_adaptive.py")
    else:
        wait_time = (target_time - now).total_seconds()
        wait_minutes = int(wait_time / 60)
        print(f"⏰ Aguardando {wait_minutes} minutos até 17:00")
        print(f"🎯 Sistema iniciará automaticamente às {target_time.strftime('%H:%M')}")
    
    print("\n📋 SISTEMA PRONTO PARA:")
    print("   ✅ Monitoramento em tempo real (17:00-23:59)")
    print("   ✅ Análise automática a cada hora")
    print("   ✅ Seleção adaptativa de estratégia")
    print("   ✅ Relatórios detalhados")
    
    print("\n🎯 WORKFLOW DAS 17:00-18:00:")
    print("   1. Sistema inicia coleta em tempo real")
    print("   2. Primeiros 10 sinais → Análise inicial")
    print("   3. 18:00 → Análise completa da 1ª hora")
    print("   4. Seleção/ajuste de estratégia")
    print("   5. Continua até 23:59")


async def main():
    """Função principal."""
    print("🎯 ANÁLISE COMPLETA DO DIA + PREPARAÇÃO PARA TRADING")
    print("=" * 80)
    print(f"📅 Data: {datetime.now().strftime('%d/%m/%Y')}")
    print(f"⏰ Horário atual: {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 80)
    
    # Etapa 1: Coletar TODOS os sinais do dia
    signals = await collect_full_day_data()
    
    # Etapa 2: Análise completa das condições
    await analyze_full_day_conditions(signals)
    
    # Etapa 3: Preparar para trading
    await prepare_for_trading()
    
    print("\n" + "=" * 80)
    print("✅ ANÁLISE COMPLETA CONCLUÍDA - SISTEMA PRONTO PARA TRADING!")
    print("🚀 Execute: python main_adaptive.py")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main()) 