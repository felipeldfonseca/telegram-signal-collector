#!/usr/bin/env python3
"""
Consolidador de Dados Diários - Telegram Signal Collector

Script para executar no final do dia (perto da meia-noite) que:
1. Coleta operações que ainda não foram capturadas (após parar o sistema principal)
2. Consolida todos os CSVs do dia em um arquivo final
3. Organiza na pasta /daily ops/ para histórico completo

Estrutura esperada:
data/trading ops/June/27/
├── pre-op time/signals_2025-06-27.csv    # Dados antes de operar
├── op time/signals_2025-06-27.csv        # Dados durante operação
└── daily ops/signals_2025-06-27.csv      # ← ARQUIVO FINAL CONSOLIDADO

Uso: python consolidate_daily_data.py
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
import pandas as pd
from pathlib import Path
import pytz

# Adicionar diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from collector import Config, Storage
from collector.runner import Runner
from collector.parser import Signal
from collector.regex import find_signal


class DailyConsolidator:
    """Consolidador de dados diários."""
    
    def __init__(self):
        self.config = Config()
        self.config.setup_logging()
        self.storage = Storage(self.config)
        self.today = datetime.now(self.config.timezone).date()
        
        # Definir caminhos
        self.base_path = Path("data/trading ops") / self.today.strftime("%B") / str(self.today.day)
        self.pre_op_path = self.base_path / "pre-op time"
        self.op_time_path = self.base_path / "op time"
        self.daily_ops_path = self.base_path / "daily ops"
        
        # Criar pasta daily ops se não existir
        self.daily_ops_path.mkdir(parents=True, exist_ok=True)
    
    def print_banner(self):
        """Imprime banner do consolidador."""
        print("🔄 CONSOLIDADOR DE DADOS DIÁRIOS")
        print("=" * 60)
        print(f"📅 Data: {self.today.strftime('%d/%m/%Y')}")
        print(f"⏰ Horário: {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 60)
    
    def load_existing_csvs(self):
        """Carrega CSVs existentes do dia."""
        print("\n📂 CARREGANDO DADOS EXISTENTES:")
        print("-" * 40)
        
        all_signals = []
        files_found = []
        
        # Arquivo pre-op time
        pre_op_file = self.pre_op_path / f"signals_{self.today.strftime('%Y-%m-%d')}.csv"
        if pre_op_file.exists():
            try:
                df_pre = pd.read_csv(pre_op_file)
                df_pre['timestamp'] = pd.to_datetime(df_pre['timestamp'])
                print(f"✅ Pre-op time: {len(df_pre)} sinais")
                all_signals.extend(df_pre.to_dict('records'))
                files_found.append('pre-op')
            except Exception as e:
                print(f"⚠️ Erro ao carregar pre-op: {e}")
        else:
            print("❌ Pre-op time: Arquivo não encontrado")
        
        # Arquivo op time
        op_time_file = self.op_time_path / f"signals_{self.today.strftime('%Y-%m-%d')}.csv"
        if op_time_file.exists():
            try:
                df_op = pd.read_csv(op_time_file)
                df_op['timestamp'] = pd.to_datetime(df_op['timestamp'])
                print(f"✅ Op time: {len(df_op)} sinais")
                all_signals.extend(df_op.to_dict('records'))
                files_found.append('op-time')
            except Exception as e:
                print(f"⚠️ Erro ao carregar op time: {e}")
        else:
            print("❌ Op time: Arquivo não encontrado")
        
        if not files_found:
            print("⚠️ Nenhum arquivo encontrado - será feita coleta completa do dia")
            return [], None, None
        
        # Converter para DataFrame e ordenar por timestamp
        if all_signals:
            df_combined = pd.DataFrame(all_signals)
            df_combined = df_combined.sort_values('timestamp').drop_duplicates()
            
            # Encontrar último timestamp
            last_timestamp = df_combined['timestamp'].max()
            first_timestamp = df_combined['timestamp'].min()
            
            print(f"📊 Total existente: {len(df_combined)} sinais")
            print(f"🕐 Período: {first_timestamp.strftime('%H:%M')} até {last_timestamp.strftime('%H:%M')}")
            
            return df_combined, first_timestamp, last_timestamp
        
        return [], None, None
    
    async def collect_missing_signals(self, last_timestamp):
        """Coleta sinais que ainda não foram capturados."""
        print(f"\n🔍 COLETANDO SINAIS FALTANTES:")
        print("-" * 40)
        
        runner = Runner(self.config)
        
        try:
            # Conectar ao Telegram
            print("📡 Conectando ao Telegram...")
            await runner.setup_client()
            
            # Definir período de busca
            now = datetime.now(self.config.timezone)
            
            if last_timestamp:
                # Buscar desde último sinal + 1 minuto
                search_from = last_timestamp + timedelta(minutes=1)
                print(f"🕐 Buscando desde: {search_from.strftime('%H:%M')} até {now.strftime('%H:%M')}")
            else:
                # Buscar dia completo (6:00 até agora)
                search_from = now.replace(hour=6, minute=0, second=0, microsecond=0)
                print(f"🕐 Buscando dia completo: {search_from.strftime('%H:%M')} até {now.strftime('%H:%M')}")
            
            # Coletar mensagens
            entity = await runner.get_chat_entity()
            
            new_signals = []
            message_count = 0
            
            async for message in runner.client.iter_messages(entity, limit=1000):
                # Converter timezone corretamente
                if message.date.tzinfo is None:
                    local_time = pytz.UTC.localize(message.date).astimezone(self.config.timezone)
                else:
                    local_time = message.date.astimezone(self.config.timezone)
                
                # Parar se chegou em mensagens muito antigas
                if local_time.date() < self.today:
                    break
                
                # Pular se não está no período de interesse
                if local_time < search_from or local_time > now:
                    continue
                
                message_count += 1
                
                # Tentar extrair sinal
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
                        new_signals.append(signal)
            
            print(f"✅ Processadas {message_count} mensagens")
            print(f"🎯 Novos sinais encontrados: {len(new_signals)}")
            
            await runner.cleanup()
            return new_signals
            
        except Exception as e:
            print(f"❌ Erro na coleta: {e}")
            if runner.client:
                await runner.cleanup()
            return []
    
    def consolidate_all_data(self, existing_df, new_signals):
        """Consolida todos os dados em um DataFrame final."""
        print(f"\n🔄 CONSOLIDANDO DADOS:")
        print("-" * 40)
        
        all_data = []
        
        # Adicionar dados existentes
        if existing_df is not None and len(existing_df) > 0:
            for _, row in existing_df.iterrows():
                all_data.append({
                    'timestamp': row['timestamp'],
                    'asset': row['asset'],
                    'result': row['result'],
                    'attempt': row['attempt']
                })
            print(f"📊 Dados existentes: {len(existing_df)} sinais")
        
        # Adicionar novos sinais
        for signal in new_signals:
            all_data.append({
                'timestamp': signal.timestamp,
                'asset': signal.asset,
                'result': signal.result,
                'attempt': signal.attempt
            })
        print(f"🆕 Novos sinais: {len(new_signals)} sinais")
        
        if not all_data:
            print("⚠️ Nenhum dado para consolidar")
            return None
        
        # Criar DataFrame final
        df_final = pd.DataFrame(all_data)
        
        # Remover duplicatas e ordenar
        df_final = df_final.drop_duplicates(subset=['timestamp', 'asset'], keep='first')
        df_final = df_final.sort_values('timestamp')
        
        print(f"✅ Total consolidado: {len(df_final)} sinais únicos")
        
        return df_final
    
    def save_consolidated_data(self, df_final):
        """Salva dados consolidados no arquivo final."""
        print(f"\n💾 SALVANDO DADOS CONSOLIDADOS:")
        print("-" * 40)
        
        if df_final is None or len(df_final) == 0:
            print("⚠️ Nenhum dado para salvar")
            return None
        
        # Arquivo final
        final_file = self.daily_ops_path / f"signals_{self.today.strftime('%Y-%m-%d')}.csv"
        
        try:
            # Salvar CSV
            df_final.to_csv(final_file, index=False)
            print(f"✅ Arquivo salvo: {final_file}")
            print(f"📊 Total de registros: {len(df_final)}")
            
            return final_file
            
        except Exception as e:
            print(f"❌ Erro ao salvar: {e}")
            return None
    
    def generate_daily_report(self, df_final):
        """Gera relatório completo do dia."""
        print(f"\n📈 RELATÓRIO COMPLETO DO DIA:")
        print("=" * 60)
        
        if df_final is None or len(df_final) == 0:
            print("⚠️ Nenhum dado para analisar")
            return
        
        # Estatísticas gerais
        total_signals = len(df_final)
        wins = len(df_final[df_final['result'] == 'W'])
        losses = len(df_final[df_final['result'] == 'L'])
        win_rate = wins / total_signals * 100
        
        print(f"📊 RESUMO GERAL:")
        print(f"   Total de sinais: {total_signals}")
        print(f"   ✅ Wins: {wins} ({win_rate:.1f}%)")
        print(f"   ❌ Losses: {losses} ({(100-win_rate):.1f}%)")
        
        # Por tentativa (apenas wins)
        wins_df = df_final[df_final['result'] == 'W']
        if len(wins_df) > 0:
            first_attempt = len(wins_df[wins_df['attempt'] == 1])
            g1_wins = len(wins_df[wins_df['attempt'] == 2])
            g2_wins = len(wins_df[wins_df['attempt'] == 3])
            
            print(f"\n🎯 ANÁLISE DE TENTATIVAS:")
            print(f"   1ª tentativa: {first_attempt} ({first_attempt/total_signals*100:.1f}%)")
            print(f"   G1 recovery: {g1_wins} ({g1_wins/total_signals*100:.1f}%)")
            print(f"   G2 recovery: {g2_wins} ({g2_wins/total_signals*100:.1f}%)")
        
        # Por ativo
        print(f"\n💰 PERFORMANCE POR ATIVO:")
        for asset in sorted(df_final['asset'].unique()):
            asset_data = df_final[df_final['asset'] == asset]
            asset_wins = len(asset_data[asset_data['result'] == 'W'])
            asset_losses = len(asset_data[asset_data['result'] == 'L'])
            asset_total = len(asset_data)
            asset_wr = asset_wins / asset_total * 100 if asset_total > 0 else 0
            
            print(f"   {asset}: {asset_wins}W/{asset_losses}L ({asset_wr:.1f}%) - {asset_total} total")
        
        # Distribuição temporal
        print(f"\n⏰ DISTRIBUIÇÃO POR HORA:")
        df_final['hour'] = pd.to_datetime(df_final['timestamp']).dt.hour
        hourly = df_final.groupby('hour').agg({
            'result': ['count', lambda x: (x == 'W').sum()]
        }).round(1)
        
        for hour in sorted(df_final['hour'].unique()):
            hour_data = df_final[df_final['hour'] == hour]
            hour_total = len(hour_data)
            hour_wins = len(hour_data[hour_data['result'] == 'W'])
            hour_wr = hour_wins / hour_total * 100 if hour_total > 0 else 0
            
            print(f"   {hour:02d}:00-{hour:02d}:59: {hour_total} sinais ({hour_wr:.1f}% WR)")
        
        # Período de dados
        first_signal = df_final['timestamp'].min()
        last_signal = df_final['timestamp'].max()
        duration = pd.to_datetime(last_signal) - pd.to_datetime(first_signal)
        
        print(f"\n📅 PERÍODO DOS DADOS:")
        print(f"   Primeiro sinal: {pd.to_datetime(first_signal).strftime('%H:%M:%S')}")
        print(f"   Último sinal: {pd.to_datetime(last_signal).strftime('%H:%M:%S')}")
        print(f"   Duração: {duration}")
        
        print("=" * 60)
    
    async def run_consolidation(self):
        """Executa processo completo de consolidação."""
        self.print_banner()
        
        # Etapa 1: Carregar dados existentes
        existing_df, first_timestamp, last_timestamp = self.load_existing_csvs()
        
        # Etapa 2: Coletar dados faltantes
        new_signals = await self.collect_missing_signals(last_timestamp)
        
        # Etapa 3: Consolidar todos os dados
        df_final = self.consolidate_all_data(existing_df, new_signals)
        
        # Etapa 4: Salvar arquivo final
        final_file = self.save_consolidated_data(df_final)
        
        # Etapa 5: Gerar relatório
        self.generate_daily_report(df_final)
        
        if final_file:
            print(f"\n🎉 CONSOLIDAÇÃO CONCLUÍDA COM SUCESSO!")
            print(f"📁 Arquivo final: {final_file}")
            print(f"🎯 Execute este script novamente amanhã no final do dia")
        else:
            print(f"\n⚠️ Consolidação concluída com problemas")
        
        print("=" * 60)


async def main():
    """Função principal."""
    consolidator = DailyConsolidator()
    await consolidator.run_consolidation()


if __name__ == "__main__":
    asyncio.run(main()) 