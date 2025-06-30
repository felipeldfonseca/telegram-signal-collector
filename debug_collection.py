#!/usr/bin/env python3
"""
Debug da coleta de sinais
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
import pytz

# Adicionar diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from collector import Config, Storage
from collector.runner import Runner
from collector.parser import HistoricalParser

async def debug_collection():
    """Debug da coleta de sinais."""
    print("🔍 DEBUG DA COLETA DE SINAIS")
    print("=" * 60)
    
    config = Config()
    config.setup_logging()
    runner = Runner(config)
    parser = HistoricalParser(config)
    
    try:
        # Conectar ao Telegram
        print("📡 Conectando ao Telegram...")
        await runner.setup_client()
        
        # Definir período (06:00 até agora)
        now = datetime.now(config.timezone)
        today_start = now.replace(hour=6, minute=0, second=0, microsecond=0)
        
        print(f"🕐 Período: {today_start.strftime('%H:%M')} até {now.strftime('%H:%M')}")
        
        # Coletar mensagens
        print("🔍 Coletando mensagens...")
        entity = await runner.get_chat_entity()
        
        signals = []
        message_count = 0
        recent_signals = []  # Para debug dos sinais mais recentes
        
        async for message in runner.client.iter_messages(entity, limit=500):
            local_time = message.date.astimezone(config.timezone)
            
            if local_time < today_start:
                break
            if local_time > now:
                continue
            
            message_count += 1
            
            # Debug: mostrar algumas mensagens recentes
            if message_count <= 10:
                print(f"   Mensagem {message_count}: {local_time.strftime('%H:%M:%S')} - {message.text[:50] if message.text else 'Sem texto'}...")
            
            # Tentar extrair sinal
            signal = parser.parse_message_no_time_filter(message)
            if signal:
                signals.append(signal)
                
                # Guardar os 10 sinais mais recentes para debug
                if len(recent_signals) < 10:
                    recent_signals.append(signal)
        
        print(f"✅ Processadas {message_count} mensagens")
        print(f"🎯 Encontrados {len(signals)} sinais")
        
        # Mostrar os sinais mais recentes (por timestamp)
        if signals:
            print(f"\n📋 SINAIS MAIS RECENTES (por timestamp):")
            print("-" * 50)
            # Ordenar por timestamp (mais recente primeiro)
            sorted_signals = sorted(signals, key=lambda x: x.timestamp, reverse=True)
            for i, signal in enumerate(sorted_signals[:15]):
                print(f"   {i+1:2d}. {signal.timestamp.strftime('%H:%M:%S')} | {signal.asset} | {signal.result} | G{signal.attempt if signal.attempt else 'STOP'}")
            
            print(f"\n📋 SINAIS MAIS ANTIGOS (por timestamp):")
            print("-" * 50)
            # Mostrar os mais antigos também
            for i, signal in enumerate(sorted_signals[-10:]):
                print(f"   {i+1:2d}. {signal.timestamp.strftime('%H:%M:%S')} | {signal.asset} | {signal.result} | G{signal.attempt if signal.attempt else 'STOP'}")
        
        await runner.cleanup()
        return signals
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        if runner.client:
            await runner.cleanup()
        return []

if __name__ == "__main__":
    asyncio.run(debug_collection())
