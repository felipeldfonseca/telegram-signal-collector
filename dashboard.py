#!/usr/bin/env python3
"""
📊 TRADING SIGNALS DASHBOARD - OTIMIZADO
Dashboard com carregamento mais rápido e interface progressiva
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime, date
import os
import json
import shutil
from collections import defaultdict

# Configuração otimizada
st.set_page_config(
    page_title="📊 Dashboard Trading",
    page_icon="📈",
    layout="wide"
)

@st.cache_data
def load_data(file_path):
    """Carrega dados com cache para performance."""
    df = pd.read_csv(file_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['hour'] = df['timestamp'].dt.hour
    return df

@st.cache_data
def calculate_metrics(df):
    """Calcula métricas com cache."""
    total_signals = len(df)
    # Conforme estratégias: apenas 1ª tentativa e G1 são wins, G2 e STOP são losses
    first_attempt_wins = len(df[(df['result'] == 'W') & (df['attempt'] == 1)])
    g1_wins = len(df[(df['result'] == 'W') & (df['attempt'] == 2)])
    wins = first_attempt_wins + g1_wins  # Apenas 1ª tentativa + G1
    losses = len(df[df['result'] == 'L']) + len(df[(df['result'] == 'W') & (df['attempt'] == 3)])  # Losses + G2
    win_rate = (wins / total_signals * 100) if total_signals > 0 else 0
    
    # Breakdown detalhado por tentativas
    first_attempt_wins = len(df[(df['result'] == 'W') & (df['attempt'] == 1)])
    g1_wins = len(df[(df['result'] == 'W') & (df['attempt'] == 2)])
    g2_wins = len(df[(df['result'] == 'W') & (df['attempt'] == 3)])
    
    # Taxas percentuais
    first_attempt_rate = (first_attempt_wins / total_signals * 100) if total_signals > 0 else 0
    g1_recovery_rate = (g1_wins / total_signals * 100) if total_signals > 0 else 0
    g2_recovery_rate = (g2_wins / total_signals * 100) if total_signals > 0 else 0
    loss_rate = (losses / total_signals * 100) if total_signals > 0 else 0
    g2_plus_stop_rate = loss_rate  # Para compatibilidade com função de recomendação
    
    return {
        'total_signals': total_signals,
        'wins': wins,
        'losses': losses,
        'win_rate': win_rate,
        'first_attempt_wins': first_attempt_wins,
        'g1_wins': g1_wins,
        'g2_wins': g2_wins,
        'first_attempt_rate': first_attempt_rate,
        'g1_recovery_rate': g1_recovery_rate,
        'g2_recovery_rate': g2_recovery_rate,
        'loss_rate': loss_rate,
        'g2_plus_stop_rate': g2_plus_stop_rate
    }

@st.cache_data
def calculate_hourly_analysis(df):
    """Calcula análise por hora com recomendações de estratégia e simulação de resultados."""
    hourly_data = []
    
    for hour in range(24):
        hour_df = df[df['hour'] == hour]
        if len(hour_df) == 0:
            continue
            
        total = len(hour_df)
        # Conforme estratégias: apenas 1ª tentativa e G1 são wins
        first_attempt = len(hour_df[(hour_df['result'] == 'W') & (hour_df['attempt'] == 1)])
        g1_recovery = len(hour_df[(hour_df['result'] == 'W') & (hour_df['attempt'] == 2)])
        wins = first_attempt + g1_recovery  # Apenas 1ª tentativa + G1
        win_rate = (wins / total * 100) if total > 0 else 0
        
        # Métricas para recomendação
        losses = len(hour_df[hour_df['result'] == 'L'])
        
        first_rate = (first_attempt / total * 100) if total > 0 else 0
        # G1 rate deve ser taxa de recuperação relativa (dos que não ganharam na primeira)
        g1_rate = (g1_recovery / max(1, total - first_attempt) * 100) if total > first_attempt else 0
        loss_rate = (losses / total * 100) if total > 0 else 0
        
        # Recomendação de estratégia usando mesma lógica do AdaptiveStrategy
        # Calcular G2+STOP rate
        g2_stops = len(hour_df[(hour_df['result'] == 'W') & (hour_df['attempt'] == 3)]) + losses
        g2_stop_rate = (g2_stops / total * 100) if total > 0 else 0
        
        if total < 10:  # Poucos dados (mesmo threshold do AdaptiveStrategy)
            strategy = "PAUSE"
        elif g2_stop_rate > 30:  # Se G2+STOP > 30%, pausar
            strategy = "PAUSE"
        elif g1_rate > 65:  # Se G1 recovery > 65%, usar Martingale (rate relativa, não absoluta)
            strategy = "Martingale Conservative"
        elif first_rate > 60:  # Se 1ª tentativa > 60%, usar Infinity
            strategy = "Infinity Conservative"
        else:
            strategy = "Infinity Conservative"
        
        # Simular resultado da estratégia
        strategy_result = simulate_strategy_result(hour_df, strategy)
        
        hourly_data.append({
            'hour': hour,
            'total': total,
            'wins': wins,
            'win_rate': win_rate,
            'first_rate': first_rate,
            'g1_rate': g1_rate,
            'loss_rate': loss_rate,
            'strategy': strategy,
            'strategy_result': strategy_result
        })
    
    return pd.DataFrame(hourly_data)

def simulate_strategy_result(hour_df, strategy):
    """Simula o resultado da aplicação da estratégia nas operações da hora."""
    if strategy in ["PAUSE", "Dados Insuficientes", "Aguardar Mais Dados"]:
        return "Sem Operações"
    
    # Ordenar operações por timestamp para simular em ordem cronológica
    operations = hour_df.sort_values('timestamp')
    
    if strategy == "Martingale Conservative":
        return simulate_martingale_conservative(operations)
    elif strategy == "Infinity Conservative":
        return simulate_infinity_conservative(operations)
    
    return "N/A"

def simulate_martingale_conservative(operations):
    """
    Simula Martingale Conservative:
    - Vitória: 3 wins seguidos sem nenhum loss entre eles
    - Derrota: qualquer loss (de primeira ou entre vitórias)
    """
    consecutive_wins = 0
    
    for _, op in operations.iterrows():
        if op['result'] == 'W':
            consecutive_wins += 1
            if consecutive_wins >= 3:
                return "Vitória"
        else:  # Loss
            return "Derrota"
    
    # Se chegou ao fim sem 3 wins consecutivos nem loss
    if consecutive_wins < 3:
        return "Incompleto"
    
    return "Vitória"

def simulate_infinity_conservative(operations):
    """
    Simula Infinity Conservative:
    - Vitória: 2 ciclos completos vitoriosos (2 vitórias seguidas, duas vezes)
    - Derrota: falha em completar os ciclos
    """
    cycles_completed = 0
    consecutive_wins = 0
    
    for _, op in operations.iterrows():
        if op['result'] == 'W':
            consecutive_wins += 1
            if consecutive_wins >= 2:  # Ciclo completo
                cycles_completed += 1
                consecutive_wins = 0  # Reset para próximo ciclo
                if cycles_completed >= 2:
                    return "Vitória"
        else:  # Loss
            consecutive_wins = 0  # Reset na sequência
    
    # Se não completou 2 ciclos
    if cycles_completed < 2:
        return "Incompleto"
    
    return "Vitória"

def recommend_strategy(metrics):
    """Recomenda estratégia usando mesma lógica do AdaptiveStrategy."""
    total = metrics['total_signals']
    first_rate = metrics['first_attempt_rate']
    g1_rate = metrics['g1_recovery_rate']
    loss_rate = metrics['loss_rate']
    g2_rate = metrics['g2_recovery_rate']
    
    # Calcular G2+STOP rate para consistência com AdaptiveStrategy
    g2_stop_rate = g2_rate + loss_rate
    
    if total < 10:  # Poucos dados
        return "PAUSE - Dados Insuficientes"
    elif g2_stop_rate > 30:  # Se G2+STOP > 30%, pausar
        return "PAUSE - Condições Desfavoráveis"
    elif g1_rate > 65:  # Se G1 recovery > 65%, usar Martingale
        return "Martingale Conservative"
    elif first_rate > 60:  # Se 1ª tentativa > 60%, usar Infinity
        return "Infinity Conservative"
    else:
        return "Infinity Conservative"

@st.cache_data
def calculate_financial_metrics(df, initial_capital=540):
    """Calcula métricas financeiras baseadas nas operações."""
    # Valores de aposta por tentativa (baseado nas estratégias)
    bet_values = {1: 4, 2: 8, 3: 16}  # 1ª tentativa: $4, G1: $8, G2: $16
    
    # Calcular P&L para cada operação
    df_financial = df.copy().sort_values('timestamp')
    df_financial['bet_amount'] = df_financial['attempt'].map(bet_values)
    df_financial['pnl'] = df_financial.apply(
        lambda row: row['bet_amount'] if row['result'] == 'W' else -row['bet_amount'], 
        axis=1
    )
    df_financial['cumulative_pnl'] = df_financial['pnl'].cumsum()
    df_financial['capital'] = initial_capital + df_financial['cumulative_pnl']
    
    # ROI total
    total_pnl = df_financial['pnl'].sum()
    roi_percent = (total_pnl / initial_capital * 100) if initial_capital > 0 else 0
    
    # Drawdown máximo
    running_max = df_financial['capital'].cummax()
    drawdown = (df_financial['capital'] - running_max) / running_max * 100
    max_drawdown = drawdown.min()
    
    # Sharpe Ratio (aproximado - usando retornos diários)
    returns = df_financial['pnl'] / initial_capital
    if len(returns) > 1 and returns.std() > 0:
        sharpe_ratio = (returns.mean() / returns.std()) * (252 ** 0.5)  # Anualizado
    else:
        sharpe_ratio = 0
    
    # Win/Loss Streaks
    df_financial['result_numeric'] = df_financial['result'].map({'W': 1, 'L': -1})
    
    # Calcular streaks
    streaks = []
    current_streak = 0
    current_type = None
    
    for result in df_financial['result_numeric']:
        if current_type is None:
            current_type = result
            current_streak = 1
        elif result == current_type:
            current_streak += 1
        else:
            streaks.append(current_streak if current_type == 1 else -current_streak)
            current_type = result
            current_streak = 1
    
    # Adicionar último streak
    if current_type is not None:
        streaks.append(current_streak if current_type == 1 else -current_streak)
    
    win_streaks = [s for s in streaks if s > 0]
    loss_streaks = [abs(s) for s in streaks if s < 0]
    
    max_win_streak = max(win_streaks) if win_streaks else 0
    max_loss_streak = max(loss_streaks) if loss_streaks else 0
    
    return {
        'total_pnl': total_pnl,
        'roi_percent': roi_percent,
        'max_drawdown': max_drawdown,
        'sharpe_ratio': sharpe_ratio,
        'max_win_streak': max_win_streak,
        'max_loss_streak': max_loss_streak,
        'final_capital': df_financial['capital'].iloc[-1] if len(df_financial) > 0 else initial_capital,
        'df_financial': df_financial
    }

@st.cache_data
def calculate_hourly_financial_analysis(df, initial_capital=540):
    """Calcula análise financeira por hora."""
    bet_values = {1: 4, 2: 8, 3: 16}
    hourly_financial = []
    
    for hour in range(24):
        hour_df = df[df['hour'] == hour]
        if len(hour_df) == 0:
            continue
        
        # Calcular P&L da hora
        hour_df_calc = hour_df.copy()
        hour_df_calc['bet_amount'] = hour_df_calc['attempt'].map(bet_values)
        hour_df_calc['pnl'] = hour_df_calc.apply(
            lambda row: row['bet_amount'] if row['result'] == 'W' else -row['bet_amount'], 
            axis=1
        )
        
        hour_pnl = hour_df_calc['pnl'].sum()
        hour_roi = (hour_pnl / initial_capital * 100) if initial_capital > 0 else 0
        
        # Risco da hora (máximo que poderia perder)
        max_risk = hour_df_calc['bet_amount'].sum()
        
        hourly_financial.append({
            'hour': hour,
            'pnl': hour_pnl,
            'roi_percent': hour_roi,
            'max_risk': max_risk,
            'operations': len(hour_df)
        })
    
    return pd.DataFrame(hourly_financial)

@st.cache_data
def calculate_realistic_financial_metrics(df):
    """Calcula métricas financeiras realistas baseadas nas estratégias recomendadas por hora."""
    hourly_results = []
    
    for hour in range(24):
        hour_df = df[df['hour'] == hour]
        if len(hour_df) == 0:
            continue
            
        total = len(hour_df)
        # Conforme estratégias: apenas 1ª tentativa e G1 são wins
        first_attempt = len(hour_df[(hour_df['result'] == 'W') & (hour_df['attempt'] == 1)])
        g1_recovery = len(hour_df[(hour_df['result'] == 'W') & (hour_df['attempt'] == 2)])
        wins = first_attempt + g1_recovery  # Apenas 1ª tentativa + G1
        win_rate = (wins / total * 100) if total > 0 else 0
        
        # Métricas para recomendação
        losses = len(hour_df[hour_df['result'] == 'L'])
        
        first_rate = (first_attempt / total * 100) if total > 0 else 0
        g1_rate = (g1_recovery / total * 100) if total > 0 else 0
        loss_rate = (losses / total * 100) if total > 0 else 0
        
        # Recomendação de estratégia para esta hora
        if total < 5:
            strategy = "Dados Insuficientes"
        elif loss_rate > 30:
            strategy = "PAUSE"
        elif g1_rate > 15 and first_rate < 60:
            strategy = "Martingale Conservative"
        elif first_rate > 50:
            strategy = "Infinity Conservative"
        else:
            strategy = "Aguardar Mais Dados"
        
        # Simular resultado da estratégia
        strategy_result = simulate_strategy_result(hour_df, strategy)
        
        # Calcular P&L baseado na estratégia e resultado
        pnl = calculate_strategy_pnl(strategy, strategy_result)
        roi = (pnl / 540 * 100) if pnl != 0 else 0  # ROI baseado em capital de $540
        
        hourly_results.append({
            'hour': hour,
            'total_signals': total,
            'win_rate': win_rate,
            'strategy': strategy,
            'strategy_result': strategy_result,
            'pnl': pnl,
            'roi': roi
        })
    
    return pd.DataFrame(hourly_results)

def calculate_strategy_pnl(strategy, result):
    """Calcula P&L baseado na estratégia e resultado."""
    if strategy in ["PAUSE", "Dados Insuficientes", "Aguardar Mais Dados"]:
        return 0.0
    
    if result == "Sem Operações":
        return 0.0
    elif result == "Incompleto":
        return 0.0
    elif result == "Vitória":
        if strategy == "Martingale Conservative":
            # Martingale: $4 + $8 = $12 de lucro (3 wins: $4, depois $8, depois $4)
            return 12.0
        elif strategy == "Infinity Conservative":
            # Infinity: 2 ciclos de 2 wins = $6 por ciclo = $12 total
            return 12.0
    elif result == "Derrota":
        if strategy == "Martingale Conservative":
            # Martingale: perda máxima $4 + $8 = $12
            return -12.0
        elif strategy == "Infinity Conservative":
            # Infinity: perda média por sessão (baseado na progressão de níveis)
            return -8.0
    
    return 0.0

@st.cache_data
def calculate_daily_summary(hourly_financial_df):
    """Calcula resumo diário baseado nas estratégias por hora."""
    if len(hourly_financial_df) == 0:
        return {
            'total_hours_traded': 0,
            'hours_with_strategy': 0,
            'total_pnl': 0,
            'average_roi_per_hour': 0,
            'winning_hours': 0,
            'losing_hours': 0,
            'no_operation_hours': 0
        }
    
    # Filtrar apenas horas com operações
    traded_hours = hourly_financial_df[
        ~hourly_financial_df['strategy'].isin(['PAUSE', 'Dados Insuficientes', 'Aguardar Mais Dados'])
    ]
    
    winning_hours = len(hourly_financial_df[hourly_financial_df['pnl'] > 0])
    losing_hours = len(hourly_financial_df[hourly_financial_df['pnl'] < 0])
    no_op_hours = len(hourly_financial_df[hourly_financial_df['pnl'] == 0])
    
    total_pnl = hourly_financial_df['pnl'].sum()
    avg_roi = hourly_financial_df[hourly_financial_df['roi'] != 0]['roi'].mean() if len(traded_hours) > 0 else 0
    
    return {
        'total_hours_analyzed': len(hourly_financial_df),
        'hours_with_strategy': len(traded_hours),
        'total_pnl': total_pnl,
        'average_roi_per_hour': avg_roi,
        'winning_hours': winning_hours,
        'losing_hours': losing_hours,
        'no_operation_hours': no_op_hours
    }

@st.cache_data
def simulate_realistic_trading_day(df):
    """Simula um dia real de trading seguindo o fluxo operacional do usuário."""
    
    # Configurações do usuário
    START_HOUR = 17  # Início das operações
    END_HOUR = 23    # Fim das operações
    DAILY_TARGET = 12.0  # Meta diária em $
    MARTINGALE_STOP = -36.0  # 3 losses diários: -12 * 3
    INFINITY_STOP = -49.0    # Stop loss conforme tabela de níveis ($49)
    
    # Resultado da simulação
    trading_log = []
    cumulative_pnl = 0.0
    current_hour = START_HOUR
    day_ended = False
    end_reason = ""
    martingale_daily_losses = 0  # Contador de losses diários para Martingale
    
    # Calcular estratégias por hora (para usar como referência)
    hourly_strategies = {}
    for hour in range(24):
        hour_df = df[df['hour'] == hour]
        if len(hour_df) < 5:
            hourly_strategies[hour] = "Dados Insuficientes"
            continue
            
        total = len(hour_df)
        losses = len(hour_df[hour_df['result'] == 'L'])
        first_attempt = len(hour_df[(hour_df['result'] == 'W') & (hour_df['attempt'] == 1)])
        g1_recovery = len(hour_df[(hour_df['result'] == 'W') & (hour_df['attempt'] == 2)])
        
        loss_rate = (losses / total * 100)
        first_rate = (first_attempt / total * 100)
        g1_rate = (g1_recovery / total * 100)
        
        if loss_rate > 30:
            hourly_strategies[hour] = "PAUSE"
        elif g1_rate > 15 and first_rate < 60:
            hourly_strategies[hour] = "Martingale Conservative"
        elif first_rate > 50:
            hourly_strategies[hour] = "Infinity Conservative"
        else:
            hourly_strategies[hour] = "Aguardar Mais Dados"
    
    while current_hour <= END_HOUR and not day_ended:
        # Usar estratégia da hora anterior (ou 16h para primeira operação)
        reference_hour = current_hour - 1 if current_hour > START_HOUR else 16
        strategy = hourly_strategies.get(reference_hour, "Dados Insuficientes")
        
        # Se estratégia não permite operar, pular para próxima hora
        if strategy in ["PAUSE", "Dados Insuficientes", "Aguardar Mais Dados"]:
            trading_log.append({
                'hour': current_hour,
                'strategy': strategy,
                'action': 'Sem Operação',
                'pnl': 0.0,
                'cumulative_pnl': cumulative_pnl,
                'reason': f'Estratégia: {strategy}'
            })
            current_hour += 1
            continue
        
        # Verificar se Martingale já atingiu 3 losses diários
        if strategy == "Martingale Conservative" and martingale_daily_losses >= 3:
            trading_log.append({
                'hour': current_hour,
                'strategy': strategy,
                'action': 'Stop Diário',
                'pnl': 0.0,
                'cumulative_pnl': cumulative_pnl,
                'reason': 'Martingale: 3 losses diários atingidos'
            })
            current_hour += 1
            continue
        
        # Simular resultado da operação na hora atual
        hour_df = df[df['hour'] == current_hour]
        if len(hour_df) == 0:
            trading_log.append({
                'hour': current_hour,
                'strategy': strategy,
                'action': 'Sem Sinais',
                'pnl': 0.0,
                'cumulative_pnl': cumulative_pnl,
                'reason': 'Nenhum sinal nesta hora'
            })
            current_hour += 1
            continue
        
        # Simular resultado baseado na estratégia escolhida
        strategy_result = simulate_strategy_result(hour_df, strategy)
        hour_pnl = calculate_strategy_pnl(strategy, strategy_result)
        
        # Se Martingale teve loss nesta sessão, incrementar contador diário
        if strategy == "Martingale Conservative" and hour_pnl < 0:
            martingale_daily_losses += 1
        
        cumulative_pnl += hour_pnl
        
        # Verificar condições de parada
        if cumulative_pnl >= DAILY_TARGET:
            day_ended = True
            end_reason = f"Meta atingida: ${cumulative_pnl:.2f}"
        elif strategy == "Martingale Conservative" and martingale_daily_losses >= 3:
            day_ended = True
            end_reason = f"Stop Martingale: 3 losses diários (${cumulative_pnl:.2f})"
        elif strategy == "Infinity Conservative" and cumulative_pnl <= INFINITY_STOP:
            day_ended = True
            end_reason = f"Stop Infinity: ${cumulative_pnl:.2f}"
        
        trading_log.append({
            'hour': current_hour,
            'strategy': strategy,
            'action': 'Operação',
            'result': strategy_result,
            'pnl': hour_pnl,
            'cumulative_pnl': cumulative_pnl,
            'reason': end_reason if day_ended else 'Continuando'
        })
        
        if day_ended:
            break
            
        current_hour += 1
    
    # Se chegou ao fim sem atingir meta nem stop
    if not day_ended:
        end_reason = f"Fim do horário de operações: ${cumulative_pnl:.2f}"
    
    return {
        'trading_log': pd.DataFrame(trading_log),
        'final_pnl': cumulative_pnl,
        'end_reason': end_reason,
        'hours_traded': len([log for log in trading_log if log['action'] == 'Operação']),
        'target_achieved': cumulative_pnl >= DAILY_TARGET,
        'stopped_out': 'Stop' in end_reason
    }

@st.cache_data
def calculate_realistic_daily_summary(simulation_result):
    """Calcula resumo baseado na simulação realista."""
    log_df = simulation_result['trading_log']
    
    # Filtrar apenas operações reais
    operations = log_df[log_df['action'] == 'Operação']
    
    if len(operations) == 0:
        return {
            'total_pnl': 0,
            'hours_operated': 0,
            'target_achieved': False,
            'stop_hit': False,
            'end_reason': 'Nenhuma operação realizada',
            'avg_pnl_per_hour': 0,
            'strategies_used': [],
            'win_rate': 0
        }
    
    winning_operations = len(operations[operations['pnl'] > 0])
    win_rate = (winning_operations / len(operations) * 100) if len(operations) > 0 else 0
    
    strategies_used = operations['strategy'].value_counts().to_dict()
    
    return {
        'total_pnl': simulation_result['final_pnl'],
        'hours_operated': len(operations),
        'target_achieved': simulation_result['target_achieved'],
        'stop_hit': simulation_result['stopped_out'],
        'end_reason': simulation_result['end_reason'],
        'avg_pnl_per_hour': operations['pnl'].mean() if len(operations) > 0 else 0,
        'strategies_used': strategies_used,
        'win_rate': win_rate
    }

@st.cache_data
def calculate_real_operations_stats(df, simulation_result):
    """Calcula estatísticas reais de operações baseadas no CSV e fluxo da simulação."""
    
    total_operations = 0
    winning_operations = 0
    losing_operations = 0
    
    # Percorrer o log da simulação para contar operações reais
    for _, log_entry in simulation_result['trading_log'].iterrows():
        if log_entry['action'] == 'Operação':
            hour = log_entry['hour']
            strategy = log_entry['strategy']
            result = log_entry['result']
            
            # Filtrar operações do CSV para esta hora
            hour_operations = df[df['hour'] == hour]
            
            if len(hour_operations) > 0:
                if strategy == "Martingale Conservative":
                    # Martingale: simular até 3 wins ou 3 losses consecutivos
                    operations_count, wins, losses = simulate_martingale_operations(hour_operations)
                elif strategy == "Infinity Conservative":
                    # Infinity: simular 2 ciclos (4 operações) até meta ou stop
                    operations_count, wins, losses = simulate_infinity_operations(hour_operations)
                else:
                    # Estratégias que não operam
                    operations_count, wins, losses = 0, 0, 0
                
                total_operations += operations_count
                winning_operations += wins
                losing_operations += losses
    
    return {
        'total_operations': total_operations,
        'winning_operations': winning_operations,
        'losing_operations': losing_operations,
        'win_rate': (winning_operations / total_operations * 100) if total_operations > 0 else 0
    }

def simulate_martingale_operations(hour_operations):
    """Simula operações Martingale Conservative para uma hora específica."""
    operations = hour_operations.copy().reset_index(drop=True)
    
    total_ops = 0
    wins = 0
    session_lost = False
    
    i = 0
    while i < len(operations) and wins < 3 and not session_lost:
        total_ops += 1
        
        if operations.iloc[i]['result'] == 'W':
            wins += 1
            
            if wins == 3:
                break  # Meta atingida: 3 wins
        else:
            # Primeiro loss na sessão = fim da sessão (-$12)
            session_lost = True
            break
        
        i += 1
    
    # Retornar: total_ops, wins, losses (0 ou 1 por sessão)
    losses = 1 if session_lost else 0
    
    return total_ops, wins, losses

def simulate_infinity_operations(hour_operations):
    """Simula operações Infinity Conservative para uma hora específica."""
    operations = hour_operations.copy().reset_index(drop=True)
    
    total_ops = 0
    wins = 0
    losses = 0
    cycles_completed = 0
    
    i = 0
    while i < len(operations) and cycles_completed < 2:  # Meta: 2 ciclos
        # Simular um ciclo (2 operações)
        cycle_wins = 0
        
        for j in range(2):  # 2 operações por ciclo
            if i + j >= len(operations):
                break
                
            total_ops += 1
            
            if operations.iloc[i + j]['result'] == 'W':
                cycle_wins += 1
            else:
                # Loss - ciclo falhou
                losses += 1
                i += j + 1
                break
        else:
            # Completou 2 operações do ciclo
            if cycle_wins == 2:
                cycles_completed += 1
                wins += 2
            else:
                losses += (2 - cycle_wins)
            
            i += 2
    
    return total_ops, wins, losses

# ==================== SISTEMA DE TRADING LOG REAL ====================

def get_trading_log_path(selected_date):
    """Retorna o caminho para o arquivo de trading log da data selecionada."""
    month_name = selected_date.strftime('%B')
    day = selected_date.day
    log_dir = f"data/trading ops/{month_name}/{day}/trading log"
    
    # Criar diretório se não existir
    os.makedirs(log_dir, exist_ok=True)
    
    filename = f"real_trading_log_{selected_date.strftime('%Y-%m-%d')}.csv"
    return os.path.join(log_dir, filename)

def load_trading_log(selected_date):
    """Carrega o log de trading real da data selecionada."""
    log_path = get_trading_log_path(selected_date)
    
    if os.path.exists(log_path):
        return pd.read_csv(log_path)
    else:
        # Criar DataFrame vazio com estrutura correta
        return pd.DataFrame(columns=[
            'date', 'hour_start', 'hour_end', 'timestamp', 'asset', 
            'result', 'attempt', 'amount_bet', 'executed', 'pnl', 
            'strategy_used', 'notes'
        ])

def save_trading_log(df_log, selected_date):
    """Salva o log de trading real com backup automático."""
    log_path = get_trading_log_path(selected_date)
    
    # Backup do arquivo existente
    if os.path.exists(log_path):
        backup_path = log_path.replace('.csv', f'_backup_{datetime.now().strftime("%H%M%S")}.csv')
        shutil.copy2(log_path, backup_path)
    
    # Salvar novo arquivo
    df_log.to_csv(log_path, index=False)
    return log_path

def validate_trading_log_data(operations_data, hour_signals):
    """Valida os dados do trading log para detectar inconsistências."""
    warnings = []
    
    # 1. Verificar se o número de operações executadas é razoável
    executed_ops = sum(1 for op in operations_data if op['executed'])
    total_signals = len(hour_signals)
    
    if executed_ops > total_signals:
        warnings.append(f"⚠️ {executed_ops} operações executadas, mas apenas {total_signals} sinais disponíveis")
    
    # 2. Verificar wins consecutivos excessivos
    consecutive_wins = 0
    max_consecutive = 0
    for op in operations_data:
        if op['executed'] and op['result'] == 'W':
            consecutive_wins += 1
            max_consecutive = max(max_consecutive, consecutive_wins)
        else:
            consecutive_wins = 0
    
    if max_consecutive > 10:
        warnings.append(f"⚠️ {max_consecutive} vitórias consecutivas pode ser inconsistente")
    
    # 3. Verificar P&L muito alto
    total_pnl = sum(op['pnl'] for op in operations_data if op['executed'])
    if total_pnl > 50:
        warnings.append(f"⚠️ P&L de ${total_pnl:.2f} parece muito alto para uma sessão")
    
    # 4. Verificar operações em horários sem sinais
    executed_times = {op['timestamp'] for op in operations_data if op['executed']}
    signal_times = {row['timestamp'].strftime('%H:%M') for _, row in hour_signals.iterrows()}
    
    for exec_time in executed_times:
        if exec_time not in signal_times:
            warnings.append(f"⚠️ Operação executada às {exec_time} mas sem sinal correspondente")
    
    return warnings

def calculate_real_vs_theoretical_comparison(real_log, theoretical_simulation):
    """Calcula comparação entre performance real e teórica."""
    if len(real_log) == 0:
        return None
    
    # Dados reais
    real_operations = real_log[real_log['executed'] == True]
    real_pnl = real_operations['pnl'].sum() if len(real_operations) > 0 else 0
    real_hours = len(real_log['hour_start'].unique()) if len(real_log) > 0 else 0
    real_win_rate = (len(real_operations[real_operations['pnl'] > 0]) / len(real_operations) * 100) if len(real_operations) > 0 else 0
    
    # Dados teóricos
    theoretical_pnl = theoretical_simulation['total_pnl'] if theoretical_simulation else 0
    theoretical_hours = theoretical_simulation['hours_operated'] if theoretical_simulation else 0
    theoretical_win_rate = theoretical_simulation['win_rate'] if theoretical_simulation else 0
    
    return {
        'real': {
            'pnl': real_pnl,
            'hours': real_hours,
            'win_rate': real_win_rate,
            'operations': len(real_operations)
        },
        'theoretical': {
            'pnl': theoretical_pnl,
            'hours': theoretical_hours,
            'win_rate': theoretical_win_rate
        },
        'difference': {
            'pnl': real_pnl - theoretical_pnl,
            'pnl_percent': ((real_pnl - theoretical_pnl) / abs(theoretical_pnl) * 100) if theoretical_pnl != 0 else 0,
            'hours': real_hours - theoretical_hours,
            'win_rate': real_win_rate - theoretical_win_rate
        }
    }

def render_trading_log_interface(selected_date, df):
    """Renderiza a interface expandida de trading log no sidebar."""
    st.sidebar.markdown("---")
    st.sidebar.subheader("📝 Registro de Operação Real")
    
    # Carregar log existente
    trading_log = load_trading_log(selected_date)
    
    # Status da sessão
    session_saved = len(trading_log) > 0
    if session_saved:
        st.sidebar.success("✅ Sessão já registrada")
        if st.sidebar.button("🔄 Editar/Atualizar"):
            st.session_state.editing_log = True
    else:
        st.sidebar.info("📝 Registrar nova sessão")
        st.session_state.editing_log = True
    
    # Interface de edição
    if st.session_state.get('editing_log', False):
        st.sidebar.markdown("### 🎯 Configuração da Sessão")
        
        # Seleção do horário de operação
        available_hours = sorted(df['hour'].unique())
        if len(available_hours) == 0:
            st.sidebar.warning("❌ Nenhum sinal disponível para esta data")
            return None
        
        selected_hours = st.sidebar.multiselect(
            "⏰ Horários operados:",
            options=available_hours,
            default=available_hours[:1] if len(available_hours) > 0 else [],
            format_func=lambda x: f"{x}:00-{x+1}:00"
        )
        
        if not selected_hours:
            st.sidebar.warning("⚠️ Selecione pelo menos um horário")
            return None
        
        # Estratégia usada
        strategy_used = st.sidebar.selectbox(
            "🎲 Estratégia utilizada:",
            ["Martingale Conservative", "Infinity Conservative", "Estratégia Própria", "Mista"]
        )
        
        # Container para operações de cada hora
        all_operations_data = []
        total_pnl = 0
        
        for hour in selected_hours:
            st.sidebar.markdown(f"#### 🕐 {hour}:00-{hour+1}:00")
            
            # Sinais da hora
            hour_signals = df[df['hour'] == hour].sort_values('timestamp')
            
            if len(hour_signals) == 0:
                st.sidebar.warning(f"Nenhum sinal disponível para {hour}:00")
                continue
            
            # Operações da hora
            hour_operations = []
            
            for idx, (_, signal) in enumerate(hour_signals.iterrows()):
                timestamp_str = signal['timestamp'].strftime('%H:%M')
                
                col1, col2 = st.sidebar.columns([3, 1])
                
                with col1:
                    # Checkbox para operação executada
                    executed = st.checkbox(
                        f"{signal['asset']} {timestamp_str}",
                        key=f"exec_{selected_date}_{hour}_{idx}",
                        help=f"Resultado original: {signal['result']} (Tent. {signal['attempt']})"
                    )
                
                with col2:
                    if executed:
                        # Input de valor apostado
                        default_amount = 4.0 if signal['attempt'] == 1 else (8.0 if signal['attempt'] == 2 else 16.0)
                        amount = st.number_input(
                            "$",
                            min_value=0.0,
                            value=default_amount,
                            step=0.5,
                            key=f"amount_{selected_date}_{hour}_{idx}"
                        )
                        
                        # Calcular P&L baseado no resultado
                        if signal['result'] == 'W':
                            pnl = amount
                        else:
                            pnl = -amount
                        
                        hour_operations.append({
                            'timestamp': timestamp_str,
                            'asset': signal['asset'],
                            'result': signal['result'],
                            'attempt': signal['attempt'],
                            'amount_bet': amount,
                            'executed': executed,
                            'pnl': pnl
                        })
                        
                        total_pnl += pnl
            
            # P&L da hora
            hour_pnl = sum(op['pnl'] for op in hour_operations if op['executed'])
            if len([op for op in hour_operations if op['executed']]) > 0:
                color = "normal" if hour_pnl >= 0 else "inverse"
                st.sidebar.metric(f"P&L {hour}:00", f"${hour_pnl:.2f}")
            
            all_operations_data.extend(hour_operations)
        
        # P&L Total
        st.sidebar.markdown("---")
        color = "normal" if total_pnl >= 0 else "inverse"
        st.sidebar.metric("💰 P&L Total", f"${total_pnl:.2f}")
        
        # Notas da sessão
        notes = st.sidebar.text_area(
            "📝 Notas da sessão:",
            placeholder="Observações, motivos de pausa, etc.",
            key=f"notes_{selected_date}"
        )
        
        # Validação
        all_hour_signals = df[df['hour'].isin(selected_hours)]
        warnings = validate_trading_log_data(all_operations_data, all_hour_signals)
        
        if warnings:
            st.sidebar.warning("⚠️ Avisos de Validação:")
            for warning in warnings:
                st.sidebar.write(f"• {warning}")
        
        # Botão de salvar
        if st.sidebar.button("💾 Salvar Registro", type="primary"):
            # Preparar DataFrame
            log_data = []
            for hour in selected_hours:
                for op in all_operations_data:
                    if op['timestamp'].startswith(f"{hour:02d}:"):
                        log_data.append({
                            'date': selected_date.strftime('%Y-%m-%d'),
                            'hour_start': hour,
                            'hour_end': hour + 1,
                            'timestamp': op['timestamp'],
                            'asset': op['asset'],
                            'result': op['result'],
                            'attempt': op['attempt'],
                            'amount_bet': op['amount_bet'],
                            'executed': op['executed'],
                            'pnl': op['pnl'],
                            'strategy_used': strategy_used,
                            'notes': notes
                        })
            
            # Salvar
            if log_data:
                new_log = pd.DataFrame(log_data)
                saved_path = save_trading_log(new_log, selected_date)
                st.sidebar.success(f"✅ Registro salvo!")
                st.session_state.editing_log = False
                st.rerun()
            else:
                st.sidebar.warning("⚠️ Nenhuma operação registrada")
    
    return trading_log

def main():
    """Função principal do dashboard."""
    st.set_page_config(
        page_title="📊 Dashboard Trading",
        page_icon="📈",
        layout="wide"
    )
    
    st.title("📊 Dashboard de Análise de Trading")
    st.markdown("Análise detalhada dos sinais coletados e performance das estratégias")
    
    # Sidebar para controle de data e configurações
    with st.sidebar:
        st.header("⚙️ Configurações")
        
        # Seleção de data
        selected_date = st.date_input(
            "Selecionar Data",
            value=datetime.now().date()
        )
        
        # NOVA FUNCIONALIDADE: Controle de operação real
        st.subheader("📈 Status de Operação")
        st.info("💡 Informe se você realmente operou neste dia para simulações mais precisas")
        
        really_traded = st.radio(
            "Você operou neste dia?",
            ("Não definido", "Sim, operei", "Não, pausei"),
            help="Isso afetará as simulações financeiras mostradas no dashboard"
        )
        
        # Configurações adicionais baseadas na escolha
        if really_traded == "Sim, operei":
            st.success("✅ Simulações mostram resultado real")
            # Opcional: permitir definir estratégia específica usada
            strategy_used = st.selectbox(
                "Estratégia utilizada:",
                ("Auto (baseado na recomendação)", "Martingale Conservative", "Infinity Conservative"),
                help="Estratégia que você realmente usou durante o trading"
            )
        elif really_traded == "Não, pausei":
            st.warning("⏸️ Dashboard mostrará apenas análise, sem simulação de P&L")
            pause_reason = st.text_area(
                "Motivo da pausa (opcional):",
                placeholder="Ex: Volume baixo, mercado instável, etc."
            )
        else:
            st.info("🔍 Dashboard mostra simulação teórica padrão")
    
    # Carregar dados - buscar na estrutura de pastas
    month_name = selected_date.strftime('%B')  # Nome do mês em inglês
    day = selected_date.day
    filename = f"signals_{selected_date.strftime('%Y-%m-%d')}.csv"
    
    # Tentar diferentes caminhos possíveis
    possible_paths = [
        f"data/trading ops/{month_name}/{day}/daily ops/{filename}",
        f"data/trading ops/{month_name}/{day:02d}/daily ops/{filename}",
        f"data/trading ops/{month_name}/{day}/06/{filename}",  # Estrutura alternativa
        f"data/trading ops/{month_name}/{day:02d}/06/{filename}",  # Estrutura alternativa com zero
        f"data/{filename}",  # Fallback para estrutura antiga
        f"data/signals_{selected_date.strftime('%Y-%m-%d')}.csv"  # Fallback original
    ]
    
    file_path = None
    for path in possible_paths:
        if os.path.exists(path):
            file_path = path
            break
    
    # Verificar se arquivo existe
    if file_path is None:
        st.error(f"❌ Arquivo não encontrado para a data {selected_date.strftime('%d/%m/%Y')}")
        st.info("💡 Execute primeiro o sistema de coleta para gerar os dados.")
        
        with st.expander("🔍 Ver caminhos verificados"):
            st.write("O dashboard tentou encontrar o arquivo nos seguintes locais:")
            for i, path in enumerate(possible_paths, 1):
                st.write(f"{i}. `{path}`")
            st.write("\n**💡 Dica:** Os dados são salvos automaticamente na estrutura:")
            st.code("data/trading ops/{Mês}/{Dia}/daily ops/signals_YYYY-MM-DD.csv")
        return
    
    # Carregar dados com base na configuração de operação
    with st.spinner("Carregando dados..."):
        df = load_data(file_path)
        metrics = calculate_metrics(df)
        hourly_analysis = calculate_hourly_analysis(df)
        
        # Mostrar dados diferentes baseado no status de operação
        if really_traded == "Não, pausei":
            # Apenas análise, sem simulação financeira
            financial_metrics = None
            simulation_result = None
            realistic_daily_summary = {
                'total_pnl': 0,
                'target_achieved': False,
                'stop_hit': False,
                'end_reason': 'Não operou - mercado pausado',
                'hours_operated': 0,
                'win_rate': 0,
                'avg_pnl_per_hour': 0
            }
        else:
            # Simulação normal
            financial_metrics = calculate_financial_metrics(df)
            realistic_financial_metrics = calculate_realistic_financial_metrics(df)
            simulation_result = simulate_realistic_trading_day(df)
            realistic_daily_summary = calculate_realistic_daily_summary(simulation_result)
    
    # Interface principal
    st.sidebar.success(f"📅 Data: {selected_date.strftime('%d/%m/%Y')}")
    st.sidebar.metric("Total de Sinais", len(df))
    
    # Mostrar status baseado na configuração
    if really_traded == "Sim, operei":
        st.sidebar.success("✅ Operou neste dia")
    elif really_traded == "Não, pausei":
        st.sidebar.warning("⏸️ Não operou neste dia")
        if 'pause_reason' in locals() and pause_reason:
            st.sidebar.write(f"**Motivo:** {pause_reason}")
    else:
        st.sidebar.info("🔍 Simulação teórica")
    
    # === SISTEMA DE TRADING LOG REAL ===
    # Renderizar interface quando "operei" estiver selecionado
    trading_log = None
    if really_traded == "Sim, operei":
        trading_log = render_trading_log_interface(selected_date, df)
    
    # === SEÇÃO 1: RESUMO GERAL ===
    st.subheader("📊 Resumo Geral")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total de Sinais", metrics['total_signals'])
    with col2:
        st.metric("Wins Totais", metrics['wins'], f"{metrics['win_rate']:.1f}% Win Rate")
    with col3:
        st.metric("1ª Tentativa", metrics['first_attempt_wins'], f"{metrics['first_attempt_rate']:.1f}%")
    with col4:
        st.metric("Losses", metrics['losses'], f"{metrics['loss_rate']:.1f}%")
    
    # === SEÇÃO 2: PERFORMANCE DIÁRIA ===
    st.subheader("💰 Performance Diária")
    
    if really_traded == "Não, pausei":
        # Mostrar análise sem performance financeira
        col1, col2 = st.columns(2)
        with col1:
            st.info("⏸️ **Dia pausado** - Nenhuma operação realizada")
            st.write("**Motivo:** Condições desfavoráveis identificadas")
        with col2:
            st.metric("P&L Real", "$0.00", "Não operou")
            
        # Mostrar o que teria acontecido se operasse
        if st.checkbox("🔍 Ver simulação hipotética (se tivesse operado)"):
            temp_simulation = simulate_realistic_trading_day(df)
            temp_summary = calculate_realistic_daily_summary(temp_simulation)
            
            col1, col2 = st.columns(2)
            with col1:
                st.info("💭 **Resultado hipotético:**")
                pnl_color = "normal" if temp_summary['total_pnl'] >= 0 else "inverse"
                st.metric("P&L Hipotético", f"${temp_summary['total_pnl']:.2f}")
            with col2:
                if temp_summary['target_achieved']:
                    st.success("✅ Teria atingido a meta")
                elif temp_summary['stop_hit']:
                    st.error("🛑 Teria acionado stop")
                else:
                    st.warning("⏰ Teria encerrado no horário")
    else:
        # Performance normal
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            pnl_color = "normal" if realistic_daily_summary['total_pnl'] >= 0 else "inverse"
            target_status = "🎯" if realistic_daily_summary['target_achieved'] else "❌"
            st.metric("P&L Total", f"${realistic_daily_summary['total_pnl']:.2f}", 
                     f"{target_status} Meta: $12.00")
        with col2:
            st.metric("Horas Operadas", realistic_daily_summary['hours_operated'], 
                     f"Win Rate: {realistic_daily_summary['win_rate']:.1f}%")
        with col3:
            avg_pnl = realistic_daily_summary['avg_pnl_per_hour']
            st.metric("P&L Médio/Hora", f"${avg_pnl:.2f}")
        with col4:
            status_icon = "🎯" if realistic_daily_summary['target_achieved'] else ("🛑" if realistic_daily_summary['stop_hit'] else "⏰")
            st.metric("Status", status_icon, realistic_daily_summary['end_reason'].split(':')[0])
    
    # === SEÇÃO 3: RECOMENDAÇÃO ===
    st.subheader("🎯 Recomendação de Estratégia")
    strategy = recommend_strategy(metrics)
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"### **{strategy}**")
        st.write(f"**Base de análise:** {metrics['total_signals']} sinais")
        st.write(f"**Métricas:** 1ª: {metrics['first_attempt_rate']:.1f}% | G1: {metrics['g1_recovery_rate']:.1f}% | Losses: {metrics['loss_rate']:.1f}%")
    
    with col2:
        # Mostrar consistência com script principal
        if really_traded == "Sim, operei" and 'strategy_used' in locals():
            if strategy_used != "Auto (baseado na recomendação)":
                st.info(f"✅ Estratégia usada: {strategy_used}")
                if strategy_used.replace(" ", "_").upper() != strategy.replace(" ", "_").upper():
                    st.warning("⚠️ Diferente da recomendação")
    
    # === SEÇÃO 4: ANÁLISES DETALHADAS ===
    if st.checkbox("📈 Mostrar Análises Detalhadas", value=True):
        
        # Análise por hora
        st.subheader("⏰ Análise por Hora")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de Win Rate por hora
            fig_hourly = px.line(
                hourly_analysis, 
                x='hour', 
                y='win_rate',
                title='Win Rate por Hora',
                markers=True
            )
            fig_hourly.update_layout(
                xaxis_title="Hora do Dia",
                yaxis_title="Win Rate (%)",
                yaxis=dict(range=[0, 100])
            )
            st.plotly_chart(fig_hourly, use_container_width=True)
        
        with col2:
            # Estratégias recomendadas
            strategy_counts = hourly_analysis['strategy'].value_counts()
            fig_strategies = px.pie(
                values=strategy_counts.values,
                names=strategy_counts.index,
                title='Estratégias Recomendadas por Hora'
            )
            st.plotly_chart(fig_strategies, use_container_width=True)
        
        # Tabela detalhada
        st.subheader("📋 Detalhamento por Hora")
        display_hourly = hourly_analysis.copy()
        display_hourly['win_rate'] = display_hourly['win_rate'].round(1)
        display_hourly['first_rate'] = display_hourly['first_rate'].round(1)
        display_hourly['g1_rate'] = display_hourly['g1_rate'].round(1)
        display_hourly['loss_rate'] = display_hourly['loss_rate'].round(1)
        
        display_hourly.columns = ['Hora', 'Total', 'Wins', 'Win Rate %', '1ª Tent %', 'G1 Rec %', 'Loss %', 'Estratégia', 'Resultado']
        st.dataframe(display_hourly, hide_index=True, use_container_width=True)
    
    # Análises financeiras apenas se operou ou simulação teórica
    if really_traded != "Não, pausei" and st.checkbox("💲 Análises Financeiras", value=False):
        if simulation_result is not None:
            st.subheader("💰 Simulação Financeira Detalhada")
            
            # Log da simulação
            display_log = simulation_result['trading_log'].copy()
            display_log['hour_formatted'] = display_log['hour'].apply(lambda x: f"{x}:00h")
            display_log['pnl_formatted'] = display_log['pnl'].apply(lambda x: f"${x:.2f}" if x != 0 else "-")
            display_log['cumulative_formatted'] = display_log['cumulative_pnl'].apply(lambda x: f"${x:.2f}")
            
            display_columns = ['hour_formatted', 'strategy', 'action', 'pnl_formatted', 'cumulative_formatted', 'reason']
            display_log_filtered = display_log[display_columns]
            display_log_filtered.columns = ['Hora', 'Estratégia', 'Ação', 'P&L', 'P&L Acum.', 'Status']
            
            st.dataframe(display_log_filtered, hide_index=True, use_container_width=True)
            
            # Gráfico de evolução
            fig_evolution = px.line(
                simulation_result['trading_log'],
                x='hour',
                y='cumulative_pnl',
                title='Evolução do P&L ao Longo do Dia',
                markers=True
            )
            fig_evolution.add_hline(y=12, line_dash="dash", line_color="green", annotation_text="Meta: $12")
            fig_evolution.add_hline(y=-36, line_dash="dash", line_color="red", annotation_text="Stop: -$36")
            st.plotly_chart(fig_evolution, use_container_width=True)
    
    # === SEÇÃO NOVA: COMPARAÇÃO REAL VS TEÓRICO ===
    if trading_log is not None and len(trading_log) > 0 and really_traded == "Sim, operei":
        if st.checkbox("📊 Comparação Real vs Teórico", value=True):
            st.subheader("🎯 Performance Real vs Simulação Teórica")
            
            # Calcular comparação
            comparison = calculate_real_vs_theoretical_comparison(trading_log, realistic_daily_summary)
            
            if comparison:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("### 💰 Real (Você)")
                    st.metric("P&L", f"${comparison['real']['pnl']:.2f}")
                    st.metric("Horas Operadas", f"{comparison['real']['hours']}")
                    st.metric("Win Rate", f"{comparison['real']['win_rate']:.1f}%")
                    st.metric("Operações", f"{comparison['real']['operations']}")
                
                with col2:
                    st.markdown("### 🤖 Teórico (Simulação)")
                    st.metric("P&L", f"${comparison['theoretical']['pnl']:.2f}")
                    st.metric("Horas", f"{comparison['theoretical']['hours']}")
                    st.metric("Win Rate", f"{comparison['theoretical']['win_rate']:.1f}%")
                
                with col3:
                    st.markdown("### 📈 Diferença")
                    diff_pnl = comparison['difference']['pnl']
                    diff_color = "🟢" if diff_pnl >= 0 else "🔴"
                    st.metric("P&L", f"{diff_color} ${diff_pnl:.2f}")
                    
                    if comparison['difference']['pnl_percent'] != 0:
                        st.metric("% Diferente", f"{comparison['difference']['pnl_percent']:.1f}%")
                    
                    diff_hours = comparison['difference']['hours']
                    st.metric("Horas", f"{'+'if diff_hours >= 0 else ''}{diff_hours}")
                    
                    diff_wr = comparison['difference']['win_rate']
                    st.metric("Win Rate", f"{'+'if diff_wr >= 0 else ''}{diff_wr:.1f}%")
                
                # Análise textual
                st.markdown("---")
                st.subheader("🔍 Análise da Performance")
                
                if comparison['difference']['pnl'] > 0:
                    st.success(f"🎉 **Excelente!** Você performou ${comparison['difference']['pnl']:.2f} acima da simulação teórica!")
                elif comparison['difference']['pnl'] == 0:
                    st.info("🎯 **Perfeito!** Sua performance foi exatamente igual à simulação teórica.")
                else:
                    st.warning(f"📉 Você ficou ${abs(comparison['difference']['pnl']):.2f} abaixo da simulação teórica.")
                
                # Insights
                if comparison['real']['hours'] > comparison['theoretical']['hours']:
                    st.info(f"🕐 Você operou {comparison['difference']['hours']} hora(s) a mais que a simulação")
                elif comparison['real']['hours'] < comparison['theoretical']['hours']:
                    st.info(f"⏰ Você operou {abs(comparison['difference']['hours'])} hora(s) a menos que a simulação")
                
                # Mostrar log das operações reais
                if st.checkbox("📋 Ver Log de Operações Reais"):
                    st.subheader("📝 Operações Registradas")
                    display_trading_log = trading_log.copy()
                    display_trading_log = display_trading_log[display_trading_log['executed'] == True]
                    
                    if len(display_trading_log) > 0:
                        display_trading_log['pnl_formatted'] = display_trading_log['pnl'].apply(lambda x: f"${x:.2f}")
                        display_trading_log['amount_formatted'] = display_trading_log['amount_bet'].apply(lambda x: f"${x:.2f}")
                        
                        cols_to_show = ['timestamp', 'asset', 'result', 'attempt', 'amount_formatted', 'pnl_formatted', 'strategy_used']
                        display_cols = ['Horário', 'Ativo', 'Resultado', 'Tentativa', 'Valor Apostado', 'P&L', 'Estratégia']
                        
                        display_trading_log_filtered = display_trading_log[cols_to_show]
                        display_trading_log_filtered.columns = display_cols
                        
                        st.dataframe(display_trading_log_filtered, hide_index=True, use_container_width=True)
                        
                        # Resumo das operações reais
                        total_bet = display_trading_log['amount_bet'].sum()
                        total_pnl = display_trading_log['pnl'].sum()
                        win_ops = len(display_trading_log[display_trading_log['pnl'] > 0])
                        total_ops = len(display_trading_log)
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Total Apostado", f"${total_bet:.2f}")
                        with col2:
                            st.metric("P&L Final", f"${total_pnl:.2f}")
                        with col3:
                            st.metric("Operações", f"{total_ops}")
                        with col4:
                            st.metric("Win Rate Real", f"{(win_ops/total_ops*100):.1f}%")
                    else:
                        st.warning("⚠️ Nenhuma operação foi marcada como executada")
            else:
                st.warning("⚠️ Não foi possível calcular a comparação. Verifique se o trading log está completo.")

if __name__ == "__main__":
    main() 