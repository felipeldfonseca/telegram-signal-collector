"""
Sistema Adaptativo de Estratégias para Trading
Analisa condições de mercado em tempo real e seleciona automaticamente
a melhor estratégia (Martingale Premium Conservative vs Infinity Conservative)
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import pandas as pd

from .parser import Signal
from .config import Config

logger = logging.getLogger(__name__)


class StrategyType(Enum):
    """Tipos de estratégia disponíveis."""
    MARTINGALE_CONSERVATIVE = "martingale_conservative"
    INFINITY_CONSERVATIVE = "infinity_conservative"
    PAUSE = "pause"


@dataclass
class StrategyMetrics:
    """Métricas de uma estratégia."""
    win_rate: float
    roi_monthly: float
    risk_per_session: float
    max_attempts: int
    profit_per_win: float
    
    def __str__(self) -> str:
        return (f"Win Rate: {self.win_rate:.1f}% | "
                f"ROI: {self.roi_monthly:.1f}% | "
                f"Risk: ${self.risk_per_session}")


@dataclass
class MarketConditions:
    """Condições atuais do mercado baseadas na análise de sinais."""
    total_operations: int
    first_attempt_success_rate: float
    g1_recovery_rate: float
    g2_plus_stop_rate: float
    recommended_strategy: StrategyType
    confidence_level: float
    analysis_period: str
    
    def __str__(self) -> str:
        return (f"🔍 Análise {self.analysis_period}: {self.total_operations} ops | "
                f"1ª: {self.first_attempt_success_rate:.1f}% | "
                f"G1: {self.g1_recovery_rate:.1f}% | "
                f"G2+STOP: {self.g2_plus_stop_rate:.1f}% | "
                f"Estratégia: {self.recommended_strategy.value.upper()} "
                f"(Confiança: {self.confidence_level:.1f}%)")


class AdaptiveStrategy:
    """Sistema adaptativo de seleção de estratégias."""
    
    def __init__(self, config: Config):
        self.config = config
        self.timezone = config.timezone
        
        # Configurações das estratégias
        self.strategies = {
            StrategyType.MARTINGALE_CONSERVATIVE: StrategyMetrics(
                win_rate=78.7,
                roi_monthly=56.0,
                risk_per_session=36.0,
                max_attempts=2,
                profit_per_win=4.0
            ),
            StrategyType.INFINITY_CONSERVATIVE: StrategyMetrics(
                win_rate=92.3,
                roi_monthly=45.1,
                risk_per_session=49.0,
                max_attempts=7,
                profit_per_win=6.0
            )
        }
        
        # Critérios de decisão
        self.decision_thresholds = {
            'pause_threshold': 30.0,  # Se G2+STOP > 30%, pausar
            'martingale_threshold': 65.0,  # Se G1 recovery > 65%, usar Martingale
            'infinity_threshold': 60.0,  # Se 1ª tentativa > 60%, usar Infinity
            'min_operations': 10,  # Mínimo de operações para análise confiável
            'confidence_threshold': 70.0  # Confiança mínima para mudança
        }
        
        # Estado atual
        self.current_strategy: Optional[StrategyType] = None
        self.last_analysis_time: Optional[datetime] = None
        self.analysis_history: List[MarketConditions] = []
        
    def analyze_market_conditions(self, signals: List[Signal]) -> MarketConditions:
        """
        Analisa condições do mercado baseado nos sinais coletados.
        
        Args:
            signals: Lista de sinais para análise
            
        Returns:
            Condições do mercado e estratégia recomendada
        """
        if not signals:
            return MarketConditions(
                total_operations=0,
                first_attempt_success_rate=0.0,
                g1_recovery_rate=0.0,
                g2_plus_stop_rate=0.0,
                recommended_strategy=StrategyType.PAUSE,
                confidence_level=0.0,
                analysis_period="Sem dados"
            )
        
        # Agrupar sinais por operação (mesmo asset + tempo próximo)
        operations = self._group_signals_into_operations(signals)
        
        # Calcular métricas
        total_ops = len(operations)
        first_attempt_wins = sum(1 for op in operations if op['result'] == 'W' and op['attempts'] == 1)
        g1_recoveries = sum(1 for op in operations if op['result'] == 'W' and op['attempts'] == 2)
        g2_plus_stops = sum(1 for op in operations if op['attempts'] >= 3)
        
        # Calcular taxas
        first_attempt_rate = (first_attempt_wins / total_ops * 100) if total_ops > 0 else 0
        g1_recovery_rate = (g1_recoveries / max(1, total_ops - first_attempt_wins) * 100) if total_ops > first_attempt_wins else 0
        g2_plus_stop_rate = (g2_plus_stops / total_ops * 100) if total_ops > 0 else 0
        
        # Determinar estratégia recomendada
        recommended_strategy, confidence = self._determine_strategy(
            total_ops, first_attempt_rate, g1_recovery_rate, g2_plus_stop_rate
        )
        
        # Período de análise
        if signals:
            start_time = min(signal.timestamp for signal in signals)
            end_time = max(signal.timestamp for signal in signals)
            period = f"{start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')}"
        else:
            period = "N/A"
        
        return MarketConditions(
            total_operations=total_ops,
            first_attempt_success_rate=first_attempt_rate,
            g1_recovery_rate=g1_recovery_rate,
            g2_plus_stop_rate=g2_plus_stop_rate,
            recommended_strategy=recommended_strategy,
            confidence_level=confidence,
            analysis_period=period
        )
    
    def _group_signals_into_operations(self, signals: List[Signal]) -> List[Dict[str, Any]]:
        """
        Agrupa sinais em operações completas.
        
        Args:
            signals: Lista de sinais
            
        Returns:
            Lista de operações com resultado final
        """
        operations = []
        signals_by_asset = {}
        
        # Agrupar por ativo
        for signal in sorted(signals, key=lambda x: x.timestamp):
            if signal.asset not in signals_by_asset:
                signals_by_asset[signal.asset] = []
            signals_by_asset[signal.asset].append(signal)
        
        # Processar cada ativo
        for asset, asset_signals in signals_by_asset.items():
            i = 0
            while i < len(asset_signals):
                current_signal = asset_signals[i]
                
                # Se é um WIN, determinar em qual tentativa
                if current_signal.result == 'W':
                    attempts = current_signal.attempt if current_signal.attempt else 1
                    operations.append({
                        'asset': asset,
                        'timestamp': current_signal.timestamp,
                        'result': 'W',
                        'attempts': attempts
                    })
                    i += 1
                
                # Se é um LOSS, contar quantas tentativas foram feitas
                elif current_signal.result == 'L':
                    # Procurar tentativas anteriores próximas
                    attempts = 1
                    j = i - 1
                    
                    # Verificar sinais anteriores no mesmo ativo
                    while j >= 0 and (current_signal.timestamp - asset_signals[j].timestamp).total_seconds() <= 600:  # 10 minutos
                        if asset_signals[j].asset == asset:
                            attempts += 1
                        j -= 1
                    
                    # Máximo de 3 tentativas
                    attempts = min(attempts, 3)
                    
                    operations.append({
                        'asset': asset,
                        'timestamp': current_signal.timestamp,
                        'result': 'L',
                        'attempts': attempts
                    })
                    i += 1
                else:
                    i += 1
        
        return operations
    
    def _determine_strategy(self, total_ops: int, first_rate: float, g1_rate: float, g2_stop_rate: float) -> Tuple[StrategyType, float]:
        """
        Determina a melhor estratégia baseada nas métricas.
        
        Args:
            total_ops: Total de operações
            first_rate: Taxa de sucesso na 1ª tentativa
            g1_rate: Taxa de recuperação no G1
            g2_stop_rate: Taxa de G2+STOP
            
        Returns:
            Tupla com (estratégia recomendada, confiança)
        """
        # Verificar se há dados suficientes
        if total_ops < self.decision_thresholds['min_operations']:
            return StrategyType.PAUSE, 30.0
        
        # Critério 1: Se G2+STOP muito alto, pausar
        if g2_stop_rate > self.decision_thresholds['pause_threshold']:
            confidence = min(95.0, g2_stop_rate * 2)
            return StrategyType.PAUSE, confidence
        
        # Critério 2: Se alta taxa de recuperação G1, usar Martingale
        if g1_rate > self.decision_thresholds['martingale_threshold']:
            confidence = min(90.0, g1_rate + 20)
            return StrategyType.MARTINGALE_CONSERVATIVE, confidence
        
        # Critério 3: Se alta taxa de 1ª tentativa, usar Infinity
        if first_rate > self.decision_thresholds['infinity_threshold']:
            confidence = min(85.0, first_rate + 15)
            return StrategyType.INFINITY_CONSERVATIVE, confidence
        
        # Caso intermediário: comparar ROI potencial
        martingale_score = self._calculate_strategy_score(
            StrategyType.MARTINGALE_CONSERVATIVE, first_rate, g1_rate, g2_stop_rate
        )
        infinity_score = self._calculate_strategy_score(
            StrategyType.INFINITY_CONSERVATIVE, first_rate, g1_rate, g2_stop_rate
        )
        
        if martingale_score > infinity_score:
            confidence = min(75.0, abs(martingale_score - infinity_score) * 10 + 50)
            return StrategyType.MARTINGALE_CONSERVATIVE, confidence
        else:
            confidence = min(75.0, abs(infinity_score - martingale_score) * 10 + 50)
            return StrategyType.INFINITY_CONSERVATIVE, confidence
    
    def _calculate_strategy_score(self, strategy: StrategyType, first_rate: float, g1_rate: float, g2_stop_rate: float) -> float:
        """
        Calcula score de uma estratégia baseada nas condições atuais.
        
        Args:
            strategy: Tipo de estratégia
            first_rate: Taxa de 1ª tentativa
            g1_rate: Taxa de G1
            g2_stop_rate: Taxa de G2+STOP
            
        Returns:
            Score da estratégia (maior = melhor)
        """
        metrics = self.strategies[strategy]
        
        if strategy == StrategyType.MARTINGALE_CONSERVATIVE:
            # Martingale se beneficia de alta recuperação G1
            win_rate_adjusted = first_rate + (g1_rate * 0.7)  # G1 vale 70% de um win
            risk_penalty = g2_stop_rate * 0.5  # Penalizar G2+STOP
            
        elif strategy == StrategyType.INFINITY_CONSERVATIVE:
            # Infinity se beneficia de alta taxa de 1ª tentativa
            win_rate_adjusted = first_rate * 1.2  # Bonus para 1ª tentativa
            risk_penalty = g2_stop_rate * 0.3  # Menos penalidade pois usa menos capital
        
        else:
            return 0.0
        
        # Score final considera ROI potencial e ajustes de risco
        base_score = metrics.roi_monthly
        adjusted_score = base_score * (win_rate_adjusted / 100) - risk_penalty
        
        return max(0.0, adjusted_score)
    
    def should_change_strategy(self, new_conditions: MarketConditions) -> bool:
        """
        Determina se deve mudar a estratégia atual.
        
        Args:
            new_conditions: Novas condições do mercado
            
        Returns:
            True se deve mudar estratégia
        """
        # Se não há estratégia atual, sempre mudar
        if self.current_strategy is None:
            return True
        
        # Se a nova estratégia é diferente da atual
        if new_conditions.recommended_strategy != self.current_strategy:
            # Só mudar se a confiança for alta o suficiente
            return new_conditions.confidence_level >= self.decision_thresholds['confidence_threshold']
        
        return False
    
    def update_strategy(self, conditions: MarketConditions) -> bool:
        """
        Atualiza a estratégia atual baseada nas condições.
        
        Args:
            conditions: Condições atuais do mercado
            
        Returns:
            True se houve mudança de estratégia
        """
        changed = self.should_change_strategy(conditions)
        
        if changed:
            old_strategy = self.current_strategy
            self.current_strategy = conditions.recommended_strategy
            self.last_analysis_time = datetime.now(self.timezone)
            
            logger.info(f"🔄 Mudança de estratégia: {old_strategy} -> {self.current_strategy}")
            logger.info(f"📊 {conditions}")
            
            # Salvar no histórico
            self.analysis_history.append(conditions)
            
            return True
        
        return False
    
    def get_current_strategy_info(self) -> Dict[str, Any]:
        """
        Retorna informações da estratégia atual.
        
        Returns:
            Informações da estratégia
        """
        if self.current_strategy is None:
            return {
                'strategy': None,
                'status': 'Aguardando análise inicial',
                'metrics': None
            }
        
        if self.current_strategy == StrategyType.PAUSE:
            return {
                'strategy': self.current_strategy,
                'status': 'Trading pausado - condições desfavoráveis',
                'metrics': None
            }
        
        metrics = self.strategies[self.current_strategy]
        
        return {
            'strategy': self.current_strategy,
            'status': f'Ativo - {self.current_strategy.value.replace("_", " ").title()}',
            'metrics': metrics,
            'last_analysis': self.last_analysis_time
        }
    
    def get_analysis_summary(self) -> str:
        """
        Retorna resumo das análises recentes.
        
        Returns:
            Resumo formatado
        """
        if not self.analysis_history:
            return "📊 Nenhuma análise realizada ainda"
        
        recent = self.analysis_history[-5:]  # Últimas 5 análises
        
        summary = ["📊 Resumo das Análises Recentes:", ""]
        
        for i, analysis in enumerate(recent, 1):
            summary.append(f"{i}. {analysis}")
        
        summary.append("")
        summary.append(f"🎯 Estratégia Atual: {self.current_strategy.value.upper() if self.current_strategy else 'Indefinida'}")
        
        return "\n".join(summary) 