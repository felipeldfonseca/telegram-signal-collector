"""
Parser de mensagens do Telegram para extrair sinais de trading
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import pytz

from .regex import find_signal
from .config import Config

logger = logging.getLogger(__name__)


@dataclass
class Signal:
    """Representa um sinal de trading extraído."""
    timestamp: datetime
    asset: str
    result: str  # 'W' ou 'L'
    attempt: Optional[int]  # 1, 2, 3 ou None para loss
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            'timestamp': self.timestamp,
            'asset': self.asset,
            'result': self.result,
            'attempt': self.attempt
        }
    
    def __str__(self) -> str:
        attempt_str = f"G{self.attempt}" if self.attempt else "STOP"
        return f"{self.timestamp.strftime('%H:%M:%S')} | {self.asset} | {self.result} | {attempt_str}"


class SignalParser:
    """Parser de sinais de trading do Telegram."""
    
    def __init__(self, config: Config):
        self.config = config
        self.timezone = config.timezone
        
    def parse_message(self, message) -> Optional[Signal]:
        """
        Extrai sinal de uma mensagem do Telegram.
        
        Args:
            message: Objeto de mensagem do Telethon
            
        Returns:
            Signal ou None se não for um sinal válido
        """
        try:
            # Verificar se a mensagem tem texto
            if not message.text:
                return None
            
            # Extrair sinal usando regex
            signal_data = find_signal(message.text)
            if not signal_data:
                return None
            
            result, attempt, asset = signal_data
            
            # Converter timestamp para timezone local
            timestamp = message.date
            if timestamp.tzinfo is None:
                timestamp = pytz.UTC.localize(timestamp)
            
            # Converter para timezone do Brasil
            local_timestamp = timestamp.astimezone(self.timezone)
            
            # Validar se está no horário de operação
            if not self._is_valid_time(local_timestamp):
                logger.debug(f"Sinal fora do horário de operação: {local_timestamp}")
                return None
            
            # Criar objeto Signal
            signal = Signal(
                timestamp=local_timestamp,
                asset=asset,
                result=result,
                attempt=attempt
            )
            
            logger.info(f"Sinal encontrado: {signal}")
            return signal
            
        except Exception as e:
            logger.error(f"Erro ao processar mensagem: {e}")
            return None
    
    def _is_valid_time(self, timestamp: datetime) -> bool:
        """
        Verifica se o timestamp está no horário de operação (17:00-23:59:59).
        
        Args:
            timestamp: Timestamp a verificar
            
        Returns:
            True se estiver no horário válido
        """
        hour = timestamp.hour
        return self.config.start_hour <= hour <= self.config.end_hour
    
    def parse_messages(self, messages: List) -> List[Signal]:
        """
        Processa múltiplas mensagens e extrai sinais.
        
        Args:
            messages: Lista de mensagens do Telegram
            
        Returns:
            Lista de sinais extraídos
        """
        signals = []
        processed_count = 0
        
        for message in messages:
            processed_count += 1
            
            if processed_count % 100 == 0:
                logger.info(f"Processadas {processed_count} mensagens...")
            
            signal = self.parse_message(message)
            if signal:
                signals.append(signal)
        
        logger.info(f"Processamento concluído: {processed_count} mensagens, {len(signals)} sinais encontrados")
        return signals
    
    def validate_signal(self, signal: Signal) -> bool:
        """
        Valida se um sinal está correto.
        
        Args:
            signal: Sinal a validar
            
        Returns:
            True se válido
        """
        # Validar resultado
        if signal.result not in ['W', 'L']:
            return False
        
        # Validar tentativa
        if signal.result == 'W' and signal.attempt not in [1, 2, 3]:
            return False
        
        if signal.result == 'L' and signal.attempt is not None:
            return False
        
        # Validar asset
        if not signal.asset or '/' not in signal.asset:
            return False
        
        # Validar timestamp
        if not isinstance(signal.timestamp, datetime):
            return False
        
        return True
    
    def get_statistics(self, signals: List[Signal]) -> Dict[str, Any]:
        """
        Calcula estatísticas dos sinais coletados.
        
        Args:
            signals: Lista de sinais
            
        Returns:
            Dicionário com estatísticas
        """
        if not signals:
            return {}
        
        total = len(signals)
        wins = sum(1 for s in signals if s.result == 'W')
        losses = sum(1 for s in signals if s.result == 'L')
        
        # Contagem por tentativa
        attempts = {1: 0, 2: 0, 3: 0}
        for signal in signals:
            if signal.result == 'W' and signal.attempt:
                attempts[signal.attempt] += 1
        
        # Assets únicos
        unique_assets = len(set(s.asset for s in signals))
        
        # Período
        timestamps = [s.timestamp for s in signals]
        start_time = min(timestamps)
        end_time = max(timestamps)
        
        return {
            'total_signals': total,
            'wins': wins,
            'losses': losses,
            'win_rate': round(wins / total * 100, 2) if total > 0 else 0,
            'attempts': attempts,
            'unique_assets': unique_assets,
            'period': {
                'start': start_time,
                'end': end_time
            }
        }
    
    def print_statistics(self, signals: List[Signal]) -> None:
        """
        Imprime estatísticas dos sinais coletados.
        
        Args:
            signals: Lista de sinais
        """
        stats = self.get_statistics(signals)
        
        if not stats:
            print("📊 Nenhum sinal encontrado")
            return
        
        print("\n📊 Estatísticas dos Sinais Coletados")
        print("=" * 40)
        print(f"Total de sinais: {stats['total_signals']}")
        print(f"Wins: {stats['wins']} ({stats['win_rate']}%)")
        print(f"Losses: {stats['losses']}")
        print(f"Assets únicos: {stats['unique_assets']}")
        
        print("\n🎯 Wins por tentativa:")
        for attempt, count in stats['attempts'].items():
            print(f"  G{attempt}: {count}")
        
        print(f"\n⏰ Período: {stats['period']['start'].strftime('%H:%M:%S')} - {stats['period']['end'].strftime('%H:%M:%S')}")
        print("=" * 40) 