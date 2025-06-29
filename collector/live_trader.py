"""
Sistema de Trading Adaptativo em Tempo Real
Implementa o workflow completo de análise horária e seleção automática de estratégias
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import deque
import json
import os
from telethon import events

from .config import Config
from .runner import Runner
from .parser import Signal
from .storage import Storage
from .adaptive_strategy import AdaptiveStrategy, StrategyType, MarketConditions

logger = logging.getLogger(__name__)


class LiveTrader:
    """Sistema de trading adaptativo em tempo real."""
    
    def __init__(self, config: Config):
        self.config = config
        self.runner = Runner(config)
        self.storage = Storage(config)
        self.adaptive_strategy = AdaptiveStrategy(config)
        
        # Buffer de sinais (última 1 hora para análise)
        self.signal_buffer: deque = deque(maxlen=200)  # ~200 sinais = 2h de dados
        
        # Controle de horários
        self.analysis_interval = 60  # Análise a cada 60 minutos
        self.last_analysis_time: Optional[datetime] = None
        
        # Estado do sistema
        self.is_running = False
        self.trading_active = False
        self.current_session_signals: List[Signal] = []
        
        # Estatísticas da sessão
        self.session_stats = {
            'start_time': None,
            'total_signals': 0,
            'strategy_changes': 0,
            'current_strategy': None,
            'analysis_count': 0
        }
    
    async def start_live_trading(self) -> None:
        """
        Inicia o sistema de trading adaptativo em tempo real.
        """
        logger.info("🚀 Iniciando Sistema de Trading Adaptativo")
        logger.info("=" * 60)
        
        # Configurar cliente Telegram
        await self.runner.setup_client()
        
        # Verificar horário de operação
        now = datetime.now(self.config.timezone)
        if not self._is_trading_hours(now):
            logger.info(f"⏰ Fora do horário de operação ({self.config.start_hour}:00 - {self.config.end_hour}:59)")
            logger.info("Aguardando horário de início...")
            await self._wait_for_trading_hours()
        
        # Inicializar sessão
        self._initialize_session()
        
        # Configurar listeners
        await self._setup_signal_listener()
        
        # Iniciar loop principal
        await self._main_trading_loop()
    
    def _initialize_session(self) -> None:
        """Inicializa uma nova sessão de trading."""
        self.session_stats = {
            'start_time': datetime.now(self.config.timezone),
            'total_signals': 0,
            'strategy_changes': 0,
            'current_strategy': None,
            'analysis_count': 0
        }
        
        self.is_running = True
        self.trading_active = True
        self.current_session_signals = []
        
        logger.info("✅ Sessão de trading inicializada")
        self._print_session_header()
    
    def _print_session_header(self) -> None:
        """Imprime cabeçalho da sessão."""
        now = datetime.now(self.config.timezone)
        
        print("\n" + "=" * 80)
        print("🎯 SISTEMA DE TRADING ADAPTATIVO - SESSÃO INICIADA")
        print("=" * 80)
        print(f"📅 Data: {now.strftime('%d/%m/%Y')}")
        print(f"⏰ Horário: {now.strftime('%H:%M:%S')}")
        print(f"🕐 Período de operação: {self.config.start_hour}:00 - {self.config.end_hour}:59")
        print(f"📊 Análise a cada: {self.analysis_interval} minutos")
        print("=" * 80)
        print()
    
    async def _setup_signal_listener(self) -> None:
        """Configura listener para novos sinais."""
        entity = await self.runner.get_chat_entity()
        
        @self.runner.client.on(events.NewMessage(chats=entity))
        async def handle_new_signal(event):
            try:
                signal = self.runner.parser.parse_message(event.message)
                if signal and self._is_valid_signal_time(signal.timestamp):
                    await self._process_new_signal(signal)
            except Exception as e:
                logger.error(f"Erro ao processar novo sinal: {e}")
        
        logger.info("🎧 Listener de sinais configurado")
    
    async def _process_new_signal(self, signal: Signal) -> None:
        """
        Processa um novo sinal recebido.
        
        Args:
            signal: Novo sinal recebido
        """
        # Adicionar ao buffer
        self.signal_buffer.append(signal)
        self.current_session_signals.append(signal)
        self.session_stats['total_signals'] += 1
        
        # Log do sinal
        self._log_new_signal(signal)
        
        # Salvar sinal
        self.storage.save_signals([signal], 'csv')
        
        # Verificar se precisa fazer análise
        if self._should_analyze_now():
            await self._perform_analysis()
    
    def _log_new_signal(self, signal: Signal) -> None:
        """
        Registra novo sinal no log e console.
        
        Args:
            signal: Sinal recebido
        """
        timestamp = signal.timestamp.strftime('%H:%M:%S')
        attempt_str = f"G{signal.attempt}" if signal.attempt else "STOP"
        
        # Log estruturado
        logger.info(f"📊 Novo sinal: {signal.asset} | {signal.result} | {attempt_str}")
        
        # Console formatado
        print(f"\n🎯 {timestamp} - NOVO SINAL")
        print(f"   💰 Asset: {signal.asset}")
        print(f"   📈 Resultado: {'✅ WIN' if signal.result == 'W' else '❌ LOSS'}")
        print(f"   🎲 Tentativa: {attempt_str}")
        print(f"   📊 Total da sessão: {self.session_stats['total_signals']}")
        
        # Status da estratégia atual
        strategy_info = self.adaptive_strategy.get_current_strategy_info()
        if strategy_info['strategy']:
            print(f"   🎯 Estratégia: {strategy_info['status']}")
        
        print("-" * 50)
    
    def _should_analyze_now(self) -> bool:
        """
        Verifica se deve realizar análise agora.
        Nova lógica: Análise apenas no final de cada hora (XX:59)
        para ter dados completos da hora inteira.
        
        Returns:
            True se deve analisar
        """
        now = datetime.now(self.config.timezone)
        
        # Verificar se está no minuto 59 da hora (final da hora)
        if now.minute != 59:
            return False
        
        # Verificar se já analisou nesta hora
        if self.last_analysis_time is not None:
            # Se já analisou na mesma hora, não analisar novamente
            if (self.last_analysis_time.hour == now.hour and 
                self.last_analysis_time.day == now.day):
                return False
        
        # Verificar se há sinais suficientes na última hora
        one_hour_ago = now - timedelta(hours=1)
        recent_signals = [
            signal for signal in self.signal_buffer 
            if signal.timestamp >= one_hour_ago
        ]
        
        # Só analisar se há pelo menos 5 sinais na última hora
        if len(recent_signals) < 5:
            logger.warning(f"⚠️ Apenas {len(recent_signals)} sinais na última hora. Aguardando mais dados...")
            return False
        
        logger.info(f"🎯 Hora {now.hour}:59 - Iniciando análise com {len(recent_signals)} sinais da última hora")
        return True
    
    async def _perform_analysis(self) -> None:
        """Realiza análise das condições do mercado e atualiza estratégia."""
        logger.info("🔍 Iniciando análise das condições do mercado...")
        
        # Pegar sinais da última hora para análise
        now = datetime.now(self.config.timezone)
        one_hour_ago = now - timedelta(hours=1)
        
        recent_signals = [
            signal for signal in self.signal_buffer 
            if signal.timestamp >= one_hour_ago
        ]
        
        if len(recent_signals) < 5:
            logger.warning("⚠️ Poucos sinais para análise confiável. Aguardando mais dados...")
            return
        
        # Analisar condições
        conditions = self.adaptive_strategy.analyze_market_conditions(recent_signals)
        
        # Atualizar estratégia
        strategy_changed = self.adaptive_strategy.update_strategy(conditions)
        
        if strategy_changed:
            self.session_stats['strategy_changes'] += 1
        
        # Atualizar estado
        self.last_analysis_time = now
        self.session_stats['analysis_count'] += 1
        self.session_stats['current_strategy'] = conditions.recommended_strategy.value
        
        # Log da análise
        self._log_analysis_results(conditions, strategy_changed)
        
        # Salvar análise
        await self._save_analysis_results(conditions)
    
    def _log_analysis_results(self, conditions: MarketConditions, strategy_changed: bool) -> None:
        """
        Registra resultados da análise.
        
        Args:
            conditions: Condições analisadas
            strategy_changed: Se houve mudança de estratégia
        """
        print("\n" + "🔍" + "=" * 78)
        print("📊 ANÁLISE DE MERCADO CONCLUÍDA")
        print("=" * 80)
        print(f"⏰ Horário: {datetime.now(self.config.timezone).strftime('%H:%M:%S')}")
        print(f"📈 {conditions}")
        
        if strategy_changed:
            print("🔄 MUDANÇA DE ESTRATÉGIA DETECTADA!")
            strategy_info = self.adaptive_strategy.get_current_strategy_info()
            print(f"🎯 Nova estratégia: {strategy_info['status']}")
            
            if strategy_info['metrics']:
                print(f"📊 Métricas: {strategy_info['metrics']}")
        else:
            print("✅ Estratégia mantida")
        
        print("=" * 80)
        print()
    
    async def _save_analysis_results(self, conditions: MarketConditions) -> None:
        """
        Salva resultados da análise em arquivo.
        
        Args:
            conditions: Condições analisadas
        """
        analysis_data = {
            'timestamp': datetime.now(self.config.timezone).isoformat(),
            'conditions': {
                'total_operations': conditions.total_operations,
                'first_attempt_success_rate': conditions.first_attempt_success_rate,
                'g1_recovery_rate': conditions.g1_recovery_rate,
                'g2_plus_stop_rate': conditions.g2_plus_stop_rate,
                'recommended_strategy': conditions.recommended_strategy.value,
                'confidence_level': conditions.confidence_level,
                'analysis_period': conditions.analysis_period
            },
            'session_stats': self.session_stats.copy()
        }
        
        # Salvar em arquivo JSON
        analysis_file = f"data/analysis_{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        os.makedirs("data", exist_ok=True)
        
        with open(analysis_file, 'a') as f:
            f.write(json.dumps(analysis_data) + '\n')
    
    async def _main_trading_loop(self) -> None:
        """Loop principal do sistema de trading."""
        logger.info("🔄 Iniciando loop principal de trading")
        
        try:
            while self.is_running:
                now = datetime.now(self.config.timezone)
                
                # Verificar se ainda está no horário de operação
                if not self._is_trading_hours(now):
                    logger.info("⏰ Fim do horário de operação")
                    await self._end_trading_session()
                    break
                
                # Verificar se precisa fazer análise periódica
                if self._should_analyze_now():
                    await self._perform_analysis()
                
                # Status periódico (a cada 10 minutos)
                if now.minute % 10 == 0 and now.second < 30:
                    self._print_status_update()
                
                # Aviso especial quando estiver próximo da análise (XX:58)
                if now.minute == 58 and now.second < 30:
                    self._print_pre_analysis_status()
                
                # Aguardar antes da próxima verificação
                await asyncio.sleep(30)  # Verificar a cada 30 segundos
                
        except KeyboardInterrupt:
            logger.info("🛑 Sistema interrompido pelo usuário")
            await self._end_trading_session()
        
        except Exception as e:
            logger.error(f"❌ Erro no loop principal: {e}")
            await self._end_trading_session()
    
    def _print_status_update(self) -> None:
        """Imprime atualização de status."""
        now = datetime.now(self.config.timezone)
        uptime = now - self.session_stats['start_time']
        
        strategy_info = self.adaptive_strategy.get_current_strategy_info()
        
        print(f"\n⏰ {now.strftime('%H:%M:%S')} - STATUS DO SISTEMA")
        print(f"   🕐 Uptime: {str(uptime).split('.')[0]}")
        print(f"   📊 Sinais recebidos: {self.session_stats['total_signals']}")
        print(f"   🔄 Mudanças de estratégia: {self.session_stats['strategy_changes']}")
        print(f"   📈 Análises realizadas: {self.session_stats['analysis_count']}")
        print(f"   🎯 Estratégia atual: {strategy_info['status']}")
        print("-" * 50)
    
    def _print_pre_analysis_status(self) -> None:
        """Imprime status antes da análise horária."""
        now = datetime.now(self.config.timezone)
        one_hour_ago = now - timedelta(hours=1)
        
        # Contar sinais da última hora
        recent_signals = [
            signal for signal in self.signal_buffer 
            if signal.timestamp >= one_hour_ago
        ]
        
        print(f"\n🔔 {now.strftime('%H:%M:%S')} - PREPARANDO ANÁLISE HORÁRIA")
        print(f"   ⏰ Próxima análise: {now.hour}:59")
        print(f"   📊 Sinais na última hora: {len(recent_signals)}")
        print(f"   🎯 Mínimo necessário: 5 sinais")
        
        if len(recent_signals) >= 5:
            print(f"   ✅ Dados suficientes para análise!")
        else:
            print(f"   ⚠️ Aguardando mais {5 - len(recent_signals)} sinais...")
        
        print("-" * 50)
    
    async def _end_trading_session(self) -> None:
        """Finaliza a sessão de trading."""
        logger.info("🏁 Finalizando sessão de trading")
        
        self.is_running = False
        self.trading_active = False
        
        # Relatório final
        await self._generate_session_report()
        
        # Cleanup
        if self.runner.client:
            await self.runner.cleanup()
    
    async def _generate_session_report(self) -> None:
        """Gera relatório final da sessão."""
        end_time = datetime.now(self.config.timezone)
        duration = end_time - self.session_stats['start_time']
        
        print("\n" + "🏁" + "=" * 78)
        print("📊 RELATÓRIO FINAL DA SESSÃO")
        print("=" * 80)
        print(f"⏰ Início: {self.session_stats['start_time'].strftime('%H:%M:%S')}")
        print(f"🏁 Fim: {end_time.strftime('%H:%M:%S')}")
        print(f"⌛ Duração: {str(duration).split('.')[0]}")
        print(f"📊 Total de sinais: {self.session_stats['total_signals']}")
        print(f"🔄 Mudanças de estratégia: {self.session_stats['strategy_changes']}")
        print(f"📈 Análises realizadas: {self.session_stats['analysis_count']}")
        
        # Resumo das análises
        analysis_summary = self.adaptive_strategy.get_analysis_summary()
        print("\n" + analysis_summary)
        
        print("=" * 80)
        print("✅ Sessão finalizada com sucesso")
        print("=" * 80)
    
    def _is_trading_hours(self, timestamp: datetime) -> bool:
        """
        Verifica se está no horário de operação.
        
        Args:
            timestamp: Timestamp para verificar
            
        Returns:
            True se está no horário de operação
        """
        hour = timestamp.hour
        return self.config.start_hour <= hour <= self.config.end_hour
    
    def _is_valid_signal_time(self, timestamp: datetime) -> bool:
        """
        Verifica se o sinal está no horário válido.
        
        Args:
            timestamp: Timestamp do sinal
            
        Returns:
            True se é válido
        """
        return self._is_trading_hours(timestamp)
    
    async def _wait_for_trading_hours(self) -> None:
        """Aguarda até o horário de início das operações."""
        while True:
            now = datetime.now(self.config.timezone)
            
            if self._is_trading_hours(now):
                logger.info("✅ Horário de operação iniciado!")
                break
            
            # Calcular tempo até o próximo horário de início
            if now.hour < self.config.start_hour:
                # Mesmo dia
                next_start = now.replace(
                    hour=self.config.start_hour, 
                    minute=0, 
                    second=0, 
                    microsecond=0
                )
            else:
                # Próximo dia
                next_day = now + timedelta(days=1)
                next_start = next_day.replace(
                    hour=self.config.start_hour, 
                    minute=0, 
                    second=0, 
                    microsecond=0
                )
            
            wait_time = (next_start - now).total_seconds()
            logger.info(f"⏳ Aguardando {wait_time/3600:.1f}h até {next_start.strftime('%H:%M')}")
            
            # Aguardar 1 minuto antes de verificar novamente
            await asyncio.sleep(60)


# Função de conveniência para iniciar o sistema
async def start_live_trading_system(config: Config) -> None:
    """
    Inicia o sistema de trading adaptativo.
    
    Args:
        config: Configuração do sistema
    """
    trader = LiveTrader(config)
    await trader.start_live_trading()


if __name__ == "__main__":
    # Para teste direto
    from .config import Config
    
    config = Config()
    config.setup_logging()
    
    asyncio.run(start_live_trading_system(config)) 