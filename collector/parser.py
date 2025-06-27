"""
Parser de mensagens do Telegram para extrair sinais de trading
"""

import logging
import re
from datetime import datetime, date
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
        
    def parse_manual_history(self, file_path: str) -> List[Signal]:
        """
        Parse do histórico manual coletado em formato texto.
        
        Args:
            file_path: Caminho para o arquivo de histórico
            
        Returns:
            Lista de sinais extraídos
        """
        signals = []
        current_date = None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Dividir por linhas
            lines = content.split('\n')
            
            for line in lines:
                line = line.strip()
                
                # Detectar mudança de dia
                if line.startswith('DIA '):
                    date_match = re.search(r'DIA (\d{2})/(\d{2})', line)
                    if date_match:
                        day, month = date_match.groups()
                        # Assumir ano 2025 baseado no contexto
                        current_date = date(2025, int(month), int(day))
                        logger.info(f"Processando data: {current_date}")
                    continue
                
                # Pular linhas vazias ou que não são resultados
                if not line or not line.startswith('> 🌐 IA de Sinais na Ebinex:'):
                    continue
                
                # Extrair horário se presente
                time_match = re.search(r'⏰ Entrada: (\d{2}):(\d{2})', line)
                if time_match:
                    # Esta é uma linha de sinal, não de resultado
                    continue
                
                # Verificar se é um resultado (WIN/STOP)
                if '✅ WIN' in line or '❎ STOP' in line:
                    signal_data = find_signal(line)
                    if signal_data and current_date:
                        result, attempt, asset = signal_data
                        
                        # Para dados manuais, vamos usar um horário estimado
                        # baseado na sequência (será ajustado depois)
                        estimated_time = datetime.combine(
                            current_date, 
                            datetime.min.time().replace(hour=21, minute=0)  # Horário padrão
                        )
                        
                        # Localizar para timezone do Brasil
                        estimated_time = self.timezone.localize(estimated_time)
                        
                        signal = Signal(
                            timestamp=estimated_time,
                            asset=asset,
                            result=result,
                            attempt=attempt
                        )
                        
                        signals.append(signal)
                        logger.debug(f"Sinal extraído: {signal}")
            
            logger.info(f"Parse manual concluído: {len(signals)} sinais encontrados")
            return signals
            
        except Exception as e:
            logger.error(f"Erro ao processar histórico manual: {e}")
            return []
    
    def parse_manual_history_enhanced(self, file_path: str) -> List[Signal]:
        """
        Parse aprimorado do histórico manual com timestamps precisos.
        
        Args:
            file_path: Caminho para o arquivo de histórico
            
        Returns:
            Lista de sinais extraídos com timestamps estimados
        """
        signals = []
        current_date = None
        current_signal_time = None
        current_asset = None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Detectar mudança de dia
                if line.startswith('DIA '):
                    date_match = re.search(r'DIA (\d{2})/(\d{2})', line)
                    if date_match:
                        day, month = date_match.groups()
                        current_date = date(2025, int(month), int(day))
                        logger.info(f"Processando data: {current_date}")
                    continue
                
                # Encontrar sinal de entrada
                if '⚠️ Novo Sinal Encontrado ⚠️' in line:
                    # Procurar asset e horário nas próximas linhas
                    for j in range(i+1, min(i+5, len(lines))):
                        next_line = lines[j].strip()
                        
                        # Extrair asset
                        asset_match = re.search(r'🪙 Par: ([A-Z]+/[A-Z]+)', next_line)
                        if asset_match:
                            current_asset = asset_match.group(1)
                        
                        # Extrair horário
                        time_match = re.search(r'⏰ Entrada: (\d{2}):(\d{2})', next_line)
                        if time_match:
                            hour, minute = map(int, time_match.groups())
                            current_signal_time = (hour, minute)
                            break
                    continue
                
                # Verificar se é um resultado (WIN/STOP)
                if ('✅ WIN' in line or '❎ STOP' in line) and current_date and current_signal_time and current_asset:
                    signal_data = find_signal(line)
                    if signal_data:
                        result, attempt, asset = signal_data
                        
                        # Usar o asset correto (pode ser diferente na linha de resultado)
                        if asset != current_asset:
                            logger.debug(f"Asset mismatch: {current_asset} vs {asset}, usando {current_asset}")
                            asset = current_asset
                        
                        # Criar timestamp preciso
                        hour, minute = current_signal_time
                        timestamp = datetime.combine(
                            current_date,
                            datetime.min.time().replace(hour=hour, minute=minute)
                        )
                        timestamp = self.timezone.localize(timestamp)
                        
                        signal = Signal(
                            timestamp=timestamp,
                            asset=asset,
                            result=result,
                            attempt=attempt
                        )
                        
                        signals.append(signal)
                        logger.debug(f"Sinal extraído: {signal}")
                        
                        # Reset para próximo sinal
                        current_signal_time = None
                        current_asset = None
            
            logger.info(f"Parse manual aprimorado concluído: {len(signals)} sinais encontrados")
            return signals
            
        except Exception as e:
            logger.error(f"Erro ao processar histórico manual aprimorado: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Fallback para método simples
            return self.parse_manual_history_simple(file_path)
    
    def parse_manual_history_simple(self, file_path: str) -> List[Signal]:
        """
        Parse simples do histórico manual - só processa linhas de resultado.
        
        Args:
            file_path: Caminho para o arquivo de histórico
            
        Returns:
            Lista de sinais extraídos
        """
        signals = []
        current_date = None
        signal_counter = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            
            for line in lines:
                line = line.strip()
                
                # Detectar mudança de dia
                if line.startswith('DIA '):
                    date_match = re.search(r'DIA (\d{2})/(\d{2})', line)
                    if date_match:
                        day, month = date_match.groups()
                        current_date = date(2025, int(month), int(day))
                        signal_counter = 0  # Reset contador para o dia
                        logger.info(f"Processando data: {current_date}")
                    continue
                
                # Verificar se é um resultado (WIN/STOP)
                if ('✅ WIN' in line or '❎ STOP' in line) and current_date:
                    signal_data = find_signal(line)
                    if signal_data:
                        result, attempt, asset = signal_data
                        
                        # Criar timestamp estimado baseado na sequência
                        base_hour = 21  # Começar às 21h
                        minutes_offset = signal_counter * 5  # 5 minutos entre sinais
                        
                        total_minutes = (base_hour * 60) + minutes_offset
                        hour = (total_minutes // 60) % 24
                        minute = total_minutes % 60
                        
                        estimated_time = datetime.combine(
                            current_date,
                            datetime.min.time().replace(hour=hour, minute=minute)
                        )
                        estimated_time = self.timezone.localize(estimated_time)
                        
                        signal = Signal(
                            timestamp=estimated_time,
                            asset=asset,
                            result=result,
                            attempt=attempt
                        )
                        
                        signals.append(signal)
                        signal_counter += 1
                        logger.debug(f"Sinal extraído: {signal}")
            
            logger.info(f"Parse manual simples concluído: {len(signals)} sinais encontrados")
            return signals
            
        except Exception as e:
            logger.error(f"Erro ao processar histórico manual simples: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
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