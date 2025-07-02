"""
Configurações do Telegram Signal Collector
"""

import os
import logging
from typing import Optional
from datetime import datetime
import pytz
from dotenv import load_dotenv

# Carrega variáveis de ambiente
# Força o caminho do .env para garantir que seja encontrado
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)


class Config:
    """Classe de configuração centralizada."""
    
    def __init__(self):
        # Telegram API
        self.api_id = os.getenv('TG_API_ID')
        self.api_hash = os.getenv('TG_API_HASH')
        self.session_name = os.getenv('TG_SESSION', 'telegram_session')
        self.group_name = os.getenv('TG_GROUP', 'https://t.me/+Nsw0tHsIhbNhNDkx')
        
        # PostgreSQL
        self.pg_dsn = os.getenv('PG_DSN', '')
        
        # Timezone
        self.timezone = pytz.timezone('America/Sao_Paulo')
        
        # Horário de operação (17:00 - 23:59:59)
        self.start_hour = 17
        self.end_hour = 23
        self.end_minute = 59
        self.end_second = 59
        
        # Logging
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        self.log_level = getattr(logging, log_level, logging.INFO)
        
        # Validações
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Valida configurações obrigatórias."""
        if not self.api_id:
            raise ValueError("TG_API_ID é obrigatório e não está no .env")
        
        if not self.api_hash:
            raise ValueError("TG_API_HASH é obrigatório e não está no .env")
        
        if not self.group_name:
            raise ValueError("TG_GROUP é obrigatório")
    
    def get_day_boundaries(self, date: datetime) -> tuple[datetime, datetime]:
        """
        Retorna os limites de um dia específico no timezone configurado.
        
        Args:
            date: Data no timezone local
            
        Returns:
            Tupla com (start_datetime, end_datetime)
        """
        # Garantir que a data está no timezone correto
        if date.tzinfo is None:
            date = self.timezone.localize(date)
        elif date.tzinfo != self.timezone:
            date = date.astimezone(self.timezone)
        
        # Início: 17:00:00 do dia especificado
        start_dt = date.replace(
            hour=self.start_hour,
            minute=0,
            second=0,
            microsecond=0
        )
        
        # Fim: 23:59:59 do mesmo dia
        end_dt = date.replace(
            hour=self.end_hour,
            minute=self.end_minute,
            second=self.end_second,
            microsecond=999999
        )
        
        return start_dt, end_dt
    
    def setup_logging(self) -> None:
        """Configura o sistema de logging."""
        logging.basicConfig(
            level=self.log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Reduzir verbosidade do Telethon
        logging.getLogger('telethon').setLevel(logging.WARNING)
    
    @property
    def has_postgres(self) -> bool:
        """Verifica se PostgreSQL está configurado."""
        return bool(self.pg_dsn)
    
    def __repr__(self) -> str:
        return (
            f"Config(api_id={self.api_id}, "
            f"group='{self.group_name}', "
            f"has_postgres={self.has_postgres})"
        ) 