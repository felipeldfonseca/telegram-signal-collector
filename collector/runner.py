"""
Executor principal para coleta de sinais do Telegram
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from tqdm import tqdm
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError
from telethon.tl.types import User

from .config import Config
from .parser import SignalParser, Signal
from .storage import Storage

logger = logging.getLogger(__name__)


class Runner:
    """Executor principal para coleta de sinais."""
    
    def __init__(self, config: Config):
        self.config = config
        self.parser = SignalParser(config)
        self.storage = Storage(config)
        self.client = None
        
    async def setup_client(self) -> None:
        """Inicializa cliente do Telegram."""
        self.client = TelegramClient(
            self.config.session_name,
            self.config.api_id,
            self.config.api_hash
        )
        
        await self.client.start()
        logger.info("Cliente do Telegram conectado")
        
        # Verificar se está logado
        me = await self.client.get_me()
        logger.info(f"Logado como: {me.first_name} (@{me.username})")
    
    async def get_chat_entity(self):
        """Obtém entidade do chat/grupo."""
        try:
            entity = await self.client.get_entity(self.config.group_name)
            logger.info(f"Grupo encontrado: {entity.title}")
            return entity
        except Exception as e:
            logger.error(f"Erro ao encontrar grupo '{self.config.group_name}': {e}")
            raise
    
    async def collect_history(self, start_date: datetime, end_date: datetime) -> List[Signal]:
        """
        Coleta histórico de mensagens para um período.
        
        Args:
            start_date: Data/hora inicial
            end_date: Data/hora final
            
        Returns:
            Lista de sinais extraídos
        """
        if not self.client:
            await self.setup_client()
        
        entity = await self.get_chat_entity()
        
        logger.info(f"Coletando histórico de {start_date} até {end_date}")
        
        messages = []
        async for message in self.client.iter_messages(
            entity,
            offset_date=end_date,
            reverse=True,
            limit=None
        ):
            # Verificar se a mensagem está no período desejado
            if message.date < start_date:
                continue
            if message.date > end_date:
                break
                
            messages.append(message)
        
        logger.info(f"Coletadas {len(messages)} mensagens do período")
        
        # Processar mensagens com barra de progresso
        signals = []
        with tqdm(total=len(messages), desc="Processando mensagens") as pbar:
            for message in messages:
                signal = self.parser.parse_message(message)
                if signal:
                    signals.append(signal)
                pbar.update(1)
        
        logger.info(f"Encontrados {len(signals)} sinais")
        return signals
    
    async def collect_day(self, date: datetime) -> List[Signal]:
        """
        Coleta sinais de um dia específico.
        
        Args:
            date: Data para coletar
            
        Returns:
            Lista de sinais
        """
        start_dt, end_dt = self.config.get_day_boundaries(date)
        
        logger.info(f"Coletando sinais do dia {date.strftime('%Y-%m-%d')}")
        logger.info(f"Período: {start_dt} até {end_dt}")
        
        return await self.collect_history(start_dt, end_dt)
    
    async def collect_range(self, start_date: datetime, end_date: datetime) -> List[Signal]:
        """
        Coleta sinais de um intervalo de datas.
        
        Args:
            start_date: Data inicial
            end_date: Data final
            
        Returns:
            Lista de sinais
        """
        all_signals = []
        current_date = start_date
        
        while current_date <= end_date:
            logger.info(f"Processando dia {current_date.strftime('%Y-%m-%d')}")
            
            try:
                day_signals = await self.collect_day(current_date)
                all_signals.extend(day_signals)
                
                # Salvar sinais do dia
                if day_signals:
                    self.storage.save_to_csv(day_signals, current_date)
                    logger.info(f"Salvos {len(day_signals)} sinais do dia {current_date.strftime('%Y-%m-%d')}")
                
            except FloodWaitError as e:
                logger.warning(f"Rate limit atingido. Aguardando {e.seconds} segundos...")
                await asyncio.sleep(e.seconds)
                continue
            
            except Exception as e:
                logger.error(f"Erro ao processar dia {current_date}: {e}")
                continue
            
            current_date += timedelta(days=1)
        
        return all_signals
    
    async def start_live_listener(self, export_format: str = 'csv') -> None:
        """
        Inicia listener em tempo real para novos sinais.
        
        Args:
            export_format: Formato de exportação ('csv', 'pg', 'both')
        """
        if not self.client:
            await self.setup_client()
        
        entity = await self.get_chat_entity()
        
        logger.info("🎯 Iniciando listener em tempo real...")
        logger.info(f"Grupo: {entity.title}")
        logger.info(f"Horário de operação: {self.config.start_hour}:00 - {self.config.end_hour}:59")
        logger.info("Pressione Ctrl+C para parar")
        
        # Handler para novas mensagens
        @self.client.on(events.NewMessage(chats=entity))
        async def handle_new_message(event):
            try:
                signal = self.parser.parse_message(event.message)
                if signal:
                    logger.info(f"🎯 Novo sinal: {signal}")
                    
                    # Salvar sinal
                    self.storage.save_signals([signal], export_format)
                    
                    # Imprimir na tela
                    print(f"\n🎯 {datetime.now().strftime('%H:%M:%S')} - Novo sinal:")
                    print(f"   Asset: {signal.asset}")
                    print(f"   Resultado: {signal.result}")
                    print(f"   Tentativa: {signal.attempt if signal.attempt else 'STOP'}")
                    print("-" * 50)
                    
            except Exception as e:
                logger.error(f"Erro ao processar nova mensagem: {e}")
        
        # Manter cliente rodando
        try:
            await self.client.run_until_disconnected()
        except KeyboardInterrupt:
            logger.info("Listener interrompido pelo usuário")
        finally:
            await self.cleanup()
    
    async def cleanup(self) -> None:
        """Limpa recursos."""
        if self.client:
            await self.client.disconnect()
            logger.info("Cliente desconectado")
    
    def run_backfill(self, start_date: datetime, end_date: Optional[datetime] = None, export_format: str = 'csv') -> None:
        """
        Executa coleta de histórico (modo backfill).
        
        Args:
            start_date: Data inicial
            end_date: Data final (opcional, padrão é start_date)
            export_format: Formato de exportação
        """
        async def _run():
            try:
                if end_date is None:
                    # Coletar apenas um dia
                    signals = await self.collect_day(start_date)
                    date_for_csv = start_date
                else:
                    # Coletar intervalo
                    signals = await self.collect_range(start_date, end_date)
                    date_for_csv = start_date
                
                if signals:
                    # Imprimir estatísticas
                    self.parser.print_statistics(signals)
                    
                    # Salvar dados
                    self.storage.save_signals(signals, export_format, date_for_csv)
                    
                    print(f"\n✅ Coleta concluída! {len(signals)} sinais processados.")
                else:
                    print("ℹ️ Nenhum sinal encontrado no período especificado.")
                
            except Exception as e:
                logger.error(f"Erro durante backfill: {e}")
                raise
            finally:
                await self.cleanup()
        
        # Executar de forma assíncrona
        asyncio.run(_run())
    
    def run_live(self, export_format: str = 'csv') -> None:
        """
        Executa listener em tempo real.
        
        Args:
            export_format: Formato de exportação
        """
        async def _run():
            try:
                await self.start_live_listener(export_format)
            except Exception as e:
                logger.error(f"Erro durante listener: {e}")
                raise
            finally:
                await self.cleanup()
        
        # Executar de forma assíncrona
        asyncio.run(_run())
    
    def test_connection(self) -> bool:
        """
        Testa conexão com Telegram e grupo.
        
        Returns:
            True se conexão foi bem-sucedida
        """
        async def _test():
            try:
                await self.setup_client()
                entity = await self.get_chat_entity()
                
                # Testar acesso às mensagens
                count = 0
                async for message in self.client.iter_messages(entity, limit=1):
                    count += 1
                    break
                
                print(f"✅ Conexão bem-sucedida!")
                print(f"   Grupo: {entity.title}")
                print(f"   Tipo: {type(entity).__name__}")
                print(f"   Acesso a mensagens: {'Sim' if count > 0 else 'Limitado'}")
                
                return True
                
            except Exception as e:
                print(f"❌ Erro de conexão: {e}")
                return False
            finally:
                await self.cleanup()
        
        return asyncio.run(_test()) 