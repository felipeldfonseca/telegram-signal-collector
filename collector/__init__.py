"""
Telegram Signal Collector Package

Um sistema automatizado para coletar sinais de trading do Telegram.
"""

__version__ = "1.0.0"
__author__ = "Telegram Signal Collector"

from .config import Config
from .parser import SignalParser, HistoricalParser
from .storage import Storage
from .runner import Runner
from .adaptive_strategy import AdaptiveStrategy, StrategyType
from .live_trader import LiveTrader

__all__ = ["Config", "SignalParser", "HistoricalParser", "Storage", "Runner", "AdaptiveStrategy", "StrategyType", "LiveTrader"]
