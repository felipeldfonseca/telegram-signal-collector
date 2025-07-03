"""
Sistema de armazenamento para CSV e PostgreSQL
"""

import os
import logging
from datetime import datetime
from typing import List, Optional
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import sql

from .config import Config
from .parser import Signal

logger = logging.getLogger(__name__)


class Storage:
    """Classe para gerenciar armazenamento de sinais."""
    
    def __init__(self, config: Config):
        self.config = config
        self.timezone = config.timezone
    
    def save_to_csv(self, signals: List[Signal], date: Optional[datetime] = None) -> str:
        """
        Salva sinais em arquivo CSV.
        
        Args:
            signals: Lista de sinais
            date: Data para nomear o arquivo (opcional)
            
        Returns:
            Caminho do arquivo criado
        """
        if not signals:
            logger.warning("Nenhum sinal para salvar em CSV")
            return ""
        
        # Determinar data para o nome do arquivo
        if date is None:
            date = signals[0].timestamp.date()
        elif hasattr(date, 'date'):
            date = date.date()
        
        # Nome do arquivo
        filename = f"signals_{date.strftime('%Y-%m-%d')}.csv"
        filepath = os.path.join("data", filename)
        
        # Criar diretório se não existir
        os.makedirs("data", exist_ok=True)
        
        # Converter sinais para DataFrame
        data = []
        for signal in signals:
            data.append({
                'timestamp': signal.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'asset': signal.asset,
                'result': signal.result,
                'attempt': signal.attempt
            })
        
        df = pd.DataFrame(data)
        
        # Verificar se arquivo já existe
        file_exists = os.path.exists(filepath)
        
        try:
            if file_exists:
                # Carregar dados existentes
                existing_df = pd.read_csv(filepath)
                
                # Combinar com novos dados
                combined_df = pd.concat([existing_df, df], ignore_index=True)
                
                # Remover duplicatas baseado em timestamp, asset, result
                combined_df = combined_df.drop_duplicates(
                    subset=['timestamp', 'asset', 'result'], 
                    keep='first'
                )
                
                # Ordenar por timestamp
                combined_df = combined_df.sort_values('timestamp')
                
                # Salvar
                combined_df.to_csv(filepath, index=False)
                logger.info(f"Atualizado CSV: {filepath} ({len(combined_df)} registros)")
                
            else:
                # Salvar novo arquivo
                df.to_csv(filepath, index=False)
                logger.info(f"Criado CSV: {filepath} ({len(df)} registros)")
            
            return filepath
            
        except Exception as e:
            logger.error(f"Erro ao salvar CSV: {e}")
            raise
    
    def save_to_postgres(self, signals: List[Signal]) -> int:
        """
        Salva sinais no PostgreSQL.
        
        Args:
            signals: Lista de sinais
            
        Returns:
            Número de registros inseridos
        """
        if not signals:
            logger.warning("Nenhum sinal para salvar no PostgreSQL")
            return 0
        
        if not self.config.has_postgres:
            logger.error("PostgreSQL não configurado")
            raise ValueError("PostgreSQL não configurado")
        
        try:
            with psycopg2.connect(self.config.pg_dsn) as conn:
                with conn.cursor() as cur:
                    # Criar tabela se não existir
                    self._create_table_if_not_exists(cur)
                    
                    # Preparar dados para inserção
                    insert_data = []
                    for signal in signals:
                        insert_data.append((
                            signal.timestamp,
                            signal.asset,
                            signal.result,
                            signal.attempt
                        ))
                    
                    # Inserção em lote com ON CONFLICT
                    insert_query = """
                        INSERT INTO signals (timestamp, asset, result, attempt)
                        VALUES %s
                        ON CONFLICT (timestamp, asset, result, attempt) 
                        DO NOTHING
                        RETURNING id
                    """
                    
                    # Usar execute_values para inserção em lote
                    from psycopg2.extras import execute_values
                    cur.execute("BEGIN")
                    
                    result = execute_values(
                        cur,
                        insert_query,
                        insert_data,
                        template=None,
                        page_size=100,
                        fetch=True
                    )
                    
                    inserted_count = len(result) if result else 0
                    
                    cur.execute("COMMIT")
                    
                    logger.info(f"Inseridos {inserted_count} novos registros no PostgreSQL")
                    return inserted_count
                    
        except Exception as e:
            logger.error(f"Erro ao salvar no PostgreSQL: {e}")
            raise
    
    def _create_table_if_not_exists(self, cursor) -> None:
        """Cria tabela de sinais se não existir."""
        create_table_query = """
            CREATE TABLE IF NOT EXISTS signals (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                asset VARCHAR(20) NOT NULL,
                result CHAR(1) NOT NULL CHECK (result IN ('W', 'L')),
                attempt INTEGER CHECK (attempt IN (1, 2, 3)),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(timestamp, asset, result, attempt)
            )
        """
        
        cursor.execute(create_table_query)
        
        # Criar índices se não existirem
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_signals_timestamp ON signals(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_signals_asset ON signals(asset)",
            "CREATE INDEX IF NOT EXISTS idx_signals_result ON signals(result)"
        ]
        
        for index_query in indexes:
            cursor.execute(index_query)
    
    def load_from_postgres(self, start_date: datetime, end_date: datetime) -> List[Signal]:
        """
        Carrega sinais do PostgreSQL para um período.
        
        Args:
            start_date: Data inicial
            end_date: Data final
            
        Returns:
            Lista de sinais
        """
        if not self.config.has_postgres:
            logger.error("PostgreSQL não configurado")
            return []
        
        try:
            with psycopg2.connect(self.config.pg_dsn) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    query = """
                        SELECT timestamp, asset, result, attempt
                        FROM signals
                        WHERE timestamp >= %s AND timestamp <= %s
                        ORDER BY timestamp
                    """
                    
                    cur.execute(query, (start_date, end_date))
                    rows = cur.fetchall()
                    
                    signals = []
                    for row in rows:
                        signal = Signal(
                            timestamp=row['timestamp'],
                            asset=row['asset'],
                            result=row['result'],
                            attempt=row['attempt']
                        )
                        signals.append(signal)
                    
                    logger.info(f"Carregados {len(signals)} sinais do PostgreSQL")
                    return signals
                    
        except Exception as e:
            logger.error(f"Erro ao carregar do PostgreSQL: {e}")
            return []
    
    def load_from_csv(self, filepath: str) -> List[Signal]:
        """
        Carrega sinais de arquivo CSV.
        
        Args:
            filepath: Caminho do arquivo CSV
            
        Returns:
            Lista de sinais
        """
        if not os.path.exists(filepath):
            logger.warning(f"Arquivo CSV não encontrado: {filepath}")
            return []
        
        try:
            df = pd.read_csv(filepath)
            
            signals = []
            for _, row in df.iterrows():
                # Converter timestamp string para datetime
                timestamp_str = row['timestamp']
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                timestamp = self.timezone.localize(timestamp)
                
                # Converter attempt (pode ser NaN)
                attempt = row['attempt']
                if pd.isna(attempt):
                    attempt = None
                else:
                    attempt = int(attempt)
                
                signal = Signal(
                    timestamp=timestamp,
                    asset=row['asset'],
                    result=row['result'],
                    attempt=attempt
                )
                signals.append(signal)
            
            logger.info(f"Carregados {len(signals)} sinais do CSV: {filepath}")
            return signals
            
        except Exception as e:
            logger.error(f"Erro ao carregar CSV: {e}")
            return []
    
    def get_postgres_stats(self) -> dict:
        """
        Obtém estatísticas da tabela PostgreSQL.
        
        Returns:
            Dicionário com estatísticas
        """
        if not self.config.has_postgres:
            return {}
        
        try:
            with psycopg2.connect(self.config.pg_dsn) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Estatísticas gerais
                    cur.execute("""
                        SELECT 
                            COUNT(*) as total_records,
                            COUNT(DISTINCT asset) as unique_assets,
                            MIN(timestamp) as first_signal,
                            MAX(timestamp) as last_signal,
                            SUM(CASE WHEN result = 'W' THEN 1 ELSE 0 END) as total_wins,
                            SUM(CASE WHEN result = 'L' THEN 1 ELSE 0 END) as total_losses
                        FROM signals
                    """)
                    
                    stats = dict(cur.fetchone())
                    
                    # Wins por tentativa
                    cur.execute("""
                        SELECT attempt, COUNT(*) as count
                        FROM signals
                        WHERE result = 'W'
                        GROUP BY attempt
                        ORDER BY attempt
                    """)
                    
                    attempts = {row['attempt']: row['count'] for row in cur.fetchall()}
                    stats['wins_by_attempt'] = attempts
                    
                    return stats
                    
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas PostgreSQL: {e}")
            return {}
    
    def save_signals(self, signals: List[Signal], export_format: str = 'csv', date: Optional[datetime] = None) -> None:
        """
        Salva sinais no formato especificado.
        
        Args:
            signals: Lista de sinais
            export_format: Formato ('csv', 'pg', ou 'both')
            date: Data para CSV (opcional)
        """
        if not signals:
            logger.warning("Nenhum sinal para salvar")
            return
        
        if export_format in ['csv', 'both']:
            try:
                filepath = self.save_to_csv(signals, date)
                print(f"✅ Dados salvos em CSV: {filepath}")
            except Exception as e:
                logger.error(f"Erro ao salvar CSV: {e}")
                if export_format == 'csv':
                    raise
        
        if export_format in ['pg', 'both']:
            try:
                count = self.save_to_postgres(signals)
                print(f"✅ {count} registros salvos no PostgreSQL")
            except Exception as e:
                logger.error(f"Erro ao salvar PostgreSQL: {e}")
                if export_format == 'pg':
                    raise 