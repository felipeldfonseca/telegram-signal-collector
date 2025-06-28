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

# Configuração otimizada
st.set_page_config(
    page_title="Trading Dashboard",
    page_icon="📊",
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
    wins = len(df[df['result'] == 'W'])
    losses = len(df[df['result'] == 'L'])
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
        wins = len(hour_df[hour_df['result'] == 'W'])
        win_rate = (wins / total * 100) if total > 0 else 0
        
        # Métricas para recomendação
        first_attempt = len(hour_df[(hour_df['result'] == 'W') & (hour_df['attempt'] == 1)])
        g1_recovery = len(hour_df[(hour_df['result'] == 'W') & (hour_df['attempt'] == 2)])
        losses = len(hour_df[hour_df['result'] == 'L'])
        
        first_rate = (first_attempt / total * 100) if total > 0 else 0
        g1_rate = (g1_recovery / total * 100) if total > 0 else 0
        loss_rate = (losses / total * 100) if total > 0 else 0
        
        # Recomendação de estratégia para esta hora
        if total < 5:  # Poucos dados
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
    """Recomenda estratégia."""
    first_rate = metrics['first_attempt_rate']
    g1_rate = metrics['g1_recovery_rate']
    loss_rate = metrics['loss_rate']
    
    if loss_rate > 30:
        return "PAUSE - Condições desfavoráveis"
    elif g1_rate > 15 and first_rate < 60:
        return "Martingale Conservative"
    elif first_rate > 50:
        return "Infinity Conservative"
    else:
        return "Aguardar Mais Dados"

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
        wins = len(hour_df[hour_df['result'] == 'W'])
        win_rate = (wins / total * 100) if total > 0 else 0
        
        # Métricas para recomendação
        first_attempt = len(hour_df[(hour_df['result'] == 'W') & (hour_df['attempt'] == 1)])
        g1_recovery = len(hour_df[(hour_df['result'] == 'W') & (hour_df['attempt'] == 2)])
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

def main():
    st.title("Telegram Trading Signals")
    st.markdown("*Análise de performance e recomendações estratégicas*")
    
    # Sidebar
    st.sidebar.header("Configurações")
    
    # Buscar arquivos
    data_path = Path("data/trading ops")
    available_files = []
    
    if data_path.exists():
        for month_dir in data_path.iterdir():
            if month_dir.is_dir():
                for day_dir in month_dir.iterdir():
                    if day_dir.is_dir():
                        daily_ops = day_dir / "daily ops"
                        if daily_ops.exists():
                            for file in daily_ops.glob("signals_*.csv"):
                                available_files.append(str(file))
    
    if not available_files:
        st.error("Nenhum arquivo encontrado!")
        return
    
    # Seleção de arquivo
    selected_file = st.sidebar.selectbox(
        "Selecione o arquivo:",
        available_files,
        index=0
    )
    
    # Carregar dados
    with st.spinner("Carregando dados..."):
        df = load_data(selected_file)
        metrics = calculate_metrics(df)
        hourly_analysis = calculate_hourly_analysis(df)
        financial_metrics = calculate_financial_metrics(df)
        hourly_financial_analysis = calculate_hourly_financial_analysis(df)
        realistic_financial_metrics = calculate_realistic_financial_metrics(df)
        simulation_result = simulate_realistic_trading_day(df)
        realistic_daily_summary = calculate_realistic_daily_summary(simulation_result)
        real_operations_stats = calculate_real_operations_stats(df, simulation_result)
    
    # Extrair data
    date_str = Path(selected_file).stem.replace('signals_', '')
    st.sidebar.success(f"Data: {date_str}")
    st.sidebar.metric("Total de Sinais", len(df))
    
    # === SEÇÃO 1: RESUMO GERAL ===
    st.subheader("Resumo Geral")
    
    # Primeira linha: Total e Wins
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total de Sinais", metrics['total_signals'])
    with col2:
        st.metric("Wins Totais", metrics['wins'], f"{metrics['win_rate']:.1f}% Win Rate")
    
    # Segunda linha: Breakdown por tentativas
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("First Attempt Wins", metrics['first_attempt_wins'], f"{metrics['first_attempt_rate']:.1f}%")
    with col2:
        st.metric("G1 Wins", metrics['g1_wins'], f"{metrics['g1_recovery_rate']:.1f}%")
    with col3:
        st.metric("G2 Wins", metrics['g2_wins'], f"{metrics['g2_recovery_rate']:.1f}%")
    with col4:
        st.metric("Losses", metrics['losses'], f"{metrics['loss_rate']:.1f}%")
    
    # === SEÇÃO 1.5: SIMULAÇÃO REALISTA DE TRADING ===
    st.subheader("Performance Diária (17h-24h)")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        pnl_color = "normal" if realistic_daily_summary['total_pnl'] >= 0 else "inverse"
        target_status = "🎯" if realistic_daily_summary['target_achieved'] else "❌"
        st.metric("P&L Real", f"${realistic_daily_summary['total_pnl']:.2f}", 
                 f"{target_status} Meta: $12.00")
    with col2:
        st.metric("Horas Operadas", realistic_daily_summary['hours_operated'], 
                 f"Win Rate: {realistic_daily_summary['win_rate']:.1f}%")
    with col3:
        avg_pnl = realistic_daily_summary['avg_pnl_per_hour']
        st.metric("P&L Médio/Hora", f"${avg_pnl:.2f}", 
                 f"de 17h às 24h")
    with col4:
        status_icon = "🎯" if realistic_daily_summary['target_achieved'] else ("🛑" if realistic_daily_summary['stop_hit'] else "⏰")
        st.metric("Status do Dia", status_icon, 
                 realistic_daily_summary['end_reason'].split(':')[0])
    
    # Mostrar detalhes da simulação
    st.markdown("**Resultado da Simulação:**")
    if realistic_daily_summary['target_achieved']:
        st.success(f"✅ {realistic_daily_summary['end_reason']}")
    elif realistic_daily_summary['stop_hit']:
        st.error(f"🛑 {realistic_daily_summary['end_reason']}")
    else:
        st.info(f"⏰ {realistic_daily_summary['end_reason']}")
    
    # Estratégias utilizadas
    if realistic_daily_summary['strategies_used']:
        strategies_text = ", ".join([f"{k}: {v}h" for k, v in realistic_daily_summary['strategies_used'].items()])
        st.write(f"**Estratégias utilizadas:** {strategies_text}")
    
    # === SEÇÃO 2: BREAKDOWN DETALHADO ===
    st.subheader("Breakdown Detalhado de Assertividade")
    
    # Tabela de performance por tentativa
    st.markdown("**Performance por Tentativa:**")
    breakdown_data = {
        'Tentativa': ['1ª Tentativa (WIN)', 'G1 Recovery (WIN)', 'G2 Recovery (WIN)', 'Loss (após G2)'],
        'Quantidade': [
            metrics['first_attempt_wins'],
            metrics['g1_wins'], 
            metrics['g2_wins'],
            metrics['losses']
        ],
        'Percentual': [
            f"{metrics['first_attempt_rate']:.1f}%",
            f"{metrics['g1_recovery_rate']:.1f}%",
            f"{metrics['g2_recovery_rate']:.1f}%",
            f"{metrics['loss_rate']:.1f}%"
        ]
    }
    breakdown_df = pd.DataFrame(breakdown_data)
    st.dataframe(breakdown_df, hide_index=True, use_container_width=True)
    
    # Gráfico de breakdown (pizza)
    st.markdown("**Distribuição Visual:**")
    fig_breakdown = px.pie(
        values=[metrics['first_attempt_wins'], metrics['g1_wins'], metrics['g2_wins'], metrics['losses']],
        names=['1ª Tentativa WIN', 'G1 Recovery', 'G2 Recovery', 'Loss'],
        title="Distribuição de Resultados por Tentativa",
        color_discrete_sequence=['#2E8B57', '#32CD32', '#90EE90', '#DC143C']
    )
    fig_breakdown.update_layout(height=500)
    st.plotly_chart(fig_breakdown, use_container_width=True)
    
    # === SEÇÃO 3: RECOMENDAÇÃO ===
    st.subheader("Recomendação de Estratégia")
    strategy = recommend_strategy(metrics)
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"### **{strategy}**")
        st.write(f"**Base de análise:** {metrics['total_signals']} sinais")
        st.write(f"**Critérios:** 1ª Tentativa: {metrics['first_attempt_rate']:.1f}% | G1 Recovery: {metrics['g1_recovery_rate']:.1f}% | Losses: {metrics['loss_rate']:.1f}%")
    
    with col2:
        # Mostrar lógica da recomendação
        st.markdown("**Lógica de Decisão:**")
        if metrics['loss_rate'] > 30:
            st.error("Losses > 30% → PAUSE")
        elif metrics['g1_recovery_rate'] > 15 and metrics['first_attempt_rate'] < 60:
            st.success("G1 > 15% e 1ª < 60% → Martingale")
        elif metrics['first_attempt_rate'] > 50:
            st.success("1ª Tentativa > 50% → Infinity")
        else:
            st.warning("Critérios não atendidos → Aguardar")
    
    # === SEÇÃO 4: ANÁLISES DETALHADAS ===
    if st.checkbox("Mostrar Análises Detalhadas", value=False):
        
        # Análise por hora com recomendações
        st.subheader("Análise por Hora com Recomendações de Estratégia")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de Win Rate por hora
            fig_hourly = px.line(
                hourly_analysis, 
                x='hour', 
                y='win_rate',
                title='Win Rate por Hora',
                markers=True,
                line_shape='linear'
            )
            fig_hourly.update_layout(
                xaxis_title="Hora do Dia",
                yaxis_title="Win Rate (%)",
                yaxis=dict(range=[0, 100])
            )
            st.plotly_chart(fig_hourly, use_container_width=True)
        
        with col2:
            # Gráfico de estratégias recomendadas por hora
            strategy_counts = hourly_analysis['strategy'].value_counts()
            fig_strategies = px.bar(
                x=strategy_counts.index,
                y=strategy_counts.values,
                title='Estratégias Recomendadas por Hora',
                color=strategy_counts.values,
                color_continuous_scale='viridis'
            )
            fig_strategies.update_layout(
                xaxis_title="Estratégia",
                yaxis_title="Número de Horas"
            )
            st.plotly_chart(fig_strategies, use_container_width=True)
        
        # Tabela detalhada por hora
        st.subheader("Detalhamento por Hora")
        
        # Formatar tabela para exibição
        display_hourly = hourly_analysis.copy()
        display_hourly['win_rate'] = display_hourly['win_rate'].round(1)
        display_hourly['first_rate'] = display_hourly['first_rate'].round(1)
        display_hourly['g1_rate'] = display_hourly['g1_rate'].round(1)
        display_hourly['loss_rate'] = display_hourly['loss_rate'].round(1)
        
        display_hourly.columns = ['Hora', 'Total', 'Wins', 'Win Rate %', '1ª Tent %', 'G1 Rec %', 'Loss %', 'Estratégia Recomendada', 'Resultado']
        
        st.dataframe(display_hourly, hide_index=True, use_container_width=True)
        
        # Performance por ativo
        st.subheader("Performance por Ativo")
        
        col1, col2 = st.columns(2)
        
        with col1:
            asset_stats = df.groupby('asset')['result'].agg(['count', lambda x: (x == 'W').sum()])
            asset_stats.columns = ['total', 'wins']
            asset_stats['win_rate'] = (asset_stats['wins'] / asset_stats['total'] * 100).round(1)
            asset_stats = asset_stats.reset_index().sort_values('win_rate', ascending=False)
            
            fig_assets = px.bar(
                asset_stats, 
                x='asset', 
                y='win_rate',
                title='Win Rate por Ativo',
                color='win_rate',
                color_continuous_scale='RdYlGn'
            )
            st.plotly_chart(fig_assets, use_container_width=True)
        
        with col2:
            st.write("**Estatísticas por Ativo:**")
            asset_display = asset_stats.copy()
            asset_display.columns = ['Ativo', 'Total', 'Wins', 'Win Rate %']
            st.dataframe(asset_display, hide_index=True)
            
            # Encontrar hora onde meta foi atingida
            if len(hourly_analysis) > 0:
                # Verificar se meta foi atingida na simulação
                target_achieved_hour = None
                for _, log_entry in simulation_result['trading_log'].iterrows():
                    if log_entry['cumulative_pnl'] >= 12.0:  # Meta de $12
                        target_achieved_hour = log_entry['hour']
                        break
                
                if target_achieved_hour is not None:
                    st.write(f"**Operações da Hora da Meta ({target_achieved_hour}:00h - Meta atingida com ${simulation_result['trading_log'][simulation_result['trading_log']['hour'] == target_achieved_hour]['cumulative_pnl'].iloc[-1]:.2f}):**")
                    
                    # Filtrar operações da hora da meta
                    target_hour_ops = df[df['hour'] == target_achieved_hour].nlargest(10, 'timestamp')[['timestamp', 'asset', 'result', 'attempt']]
                    target_hour_ops['timestamp'] = target_hour_ops['timestamp'].dt.strftime('%H:%M')
                    target_hour_ops.columns = ['Horário', 'Ativo', 'Resultado', 'Tentativa']
                    st.dataframe(target_hour_ops, hide_index=True)
                else:
                    # Se meta não foi atingida, mostrar melhor hora como fallback
                    best_hour_data = hourly_analysis.sort_values(['win_rate', 'total'], ascending=[False, False]).iloc[0]
                    best_hour = int(best_hour_data['hour'])
                    best_win_rate = best_hour_data['win_rate']
                    best_total = int(best_hour_data['total'])
                    
                    st.write(f"**Meta não atingida - Melhor Hora ({best_hour}:00h - {best_win_rate:.1f}% WR, {best_total} ops):**")
                    
                    # Filtrar operações da melhor hora
                    best_hour_ops = df[df['hour'] == best_hour].nlargest(10, 'timestamp')[['timestamp', 'asset', 'result', 'attempt']]
                    best_hour_ops['timestamp'] = best_hour_ops['timestamp'].dt.strftime('%H:%M')
                    best_hour_ops.columns = ['Horário', 'Ativo', 'Resultado', 'Tentativa']
                    st.dataframe(best_hour_ops, hide_index=True)

    # === SEÇÃO 5: ANÁLISES FINANCEIRAS REALISTAS ===
    if st.checkbox("Mostrar Análises Financeiras", value=False):
        st.subheader("Análises Financeiras por Estratégia")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de P&L por hora (estratégias)
            fig_pnl_strategy = px.bar(
                realistic_financial_metrics, 
                x='hour', 
                y='pnl',
                title='P&L por Hora (Estratégias Aplicadas)',
                color='pnl',
                color_continuous_scale='RdYlGn',
                hover_data=['strategy', 'strategy_result']
            )
            fig_pnl_strategy.update_layout(
                xaxis_title="Hora do Dia",
                yaxis_title="P&L ($)"
            )
            st.plotly_chart(fig_pnl_strategy, use_container_width=True)
        
        with col2:
            # Gráfico de ROI por hora
            fig_roi_strategy = px.line(
                realistic_financial_metrics, 
                x='hour', 
                y='roi',
                title='ROI por Hora',
                markers=True,
                line_shape='linear'
            )
            fig_roi_strategy.update_layout(
                xaxis_title="Hora do Dia",
                yaxis_title="ROI (%)"
            )
            st.plotly_chart(fig_roi_strategy, use_container_width=True)
        
        # Distribuição de estratégias
        st.subheader("Distribuição de Estratégias e Resultados")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de pizza - estratégias usadas
            strategy_counts = realistic_financial_metrics['strategy'].value_counts()
            fig_strategies = px.pie(
                values=strategy_counts.values,
                names=strategy_counts.index,
                title='Distribuição de Estratégias por Hora'
            )
            st.plotly_chart(fig_strategies, use_container_width=True)
        
        with col2:
            # Gráfico de pizza - resultados
            result_counts = realistic_financial_metrics['strategy_result'].value_counts()
            fig_results = px.pie(
                values=result_counts.values,
                names=result_counts.index,
                title='Distribuição de Resultados'
            )
            st.plotly_chart(fig_results, use_container_width=True)
        
        # Tabela detalhada financeira por hora
        st.subheader("Detalhamento Financeiro por Estratégia")
        
        # Formatar tabela financeira realista
        display_realistic = realistic_financial_metrics.copy()
        display_realistic['pnl'] = display_realistic['pnl'].round(2)
        display_realistic['roi'] = display_realistic['roi'].round(2)
        display_realistic['win_rate'] = display_realistic['win_rate'].round(1)
        
        display_realistic.columns = ['Hora', 'Sinais', 'Win Rate %', 'Estratégia', 'Resultado', 'P&L ($)', 'ROI (%)']
        
        st.dataframe(display_realistic, hide_index=True, use_container_width=True)
        
        # Análise de performance por estratégia
        st.subheader("Performance por Estratégia")
        
        # Agrupar por estratégia
        strategy_performance = realistic_financial_metrics.groupby('strategy').agg({
            'pnl': ['sum', 'mean', 'count'],
            'roi': 'mean'
        }).round(2)
        
        strategy_performance.columns = ['P&L Total', 'P&L Médio', 'Horas Usada', 'ROI Médio']
        strategy_performance = strategy_performance.reset_index()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Performance por Estratégia:**")
            st.dataframe(strategy_performance, hide_index=True, use_container_width=True)
        
        with col2:
            st.markdown("**Interpretação:**")
            
            # Encontrar melhor estratégia
            best_strategy = strategy_performance.loc[strategy_performance['P&L Total'].idxmax()]
            st.success(f"🏆 Melhor estratégia: {best_strategy['strategy']}")
            st.info(f"📊 P&L Total: ${best_strategy['P&L Total']:.2f}")
            st.info(f"📈 ROI Médio: {best_strategy['ROI Médio']:.2f}%")
            
            # Resumo do dia
            if realistic_daily_summary['total_pnl'] > 0:
                st.success(f"💚 Dia positivo: +${realistic_daily_summary['total_pnl']:.2f}")
            else:
                st.error(f"🔴 Dia negativo: ${realistic_daily_summary['total_pnl']:.2f}")
            
            # Calcular win rate das horas operadas
            operations_count = realistic_daily_summary['hours_operated']
            winning_hours = len([h for h in simulation_result['trading_log'].iterrows() if h[1]['pnl'] > 0])
            win_rate_hours = (winning_hours / operations_count * 100) if operations_count > 0 else 0
            st.info(f"⏰ Taxa de sucesso: {win_rate_hours:.1f}% das horas operadas")
    
    # === SEÇÃO 6: LOG DA SIMULAÇÃO REALISTA ===
    if st.checkbox("Mostrar Log da Simulação Realista", value=False):
        st.subheader("Log Detalhado da Simulação")
        
        # Log completo da simulação (largura total)
        st.markdown("**Cronologia das Operações:**")
        
        # Formatar o log para exibição
        display_log = simulation_result['trading_log'].copy()
        
        # Adicionar formatação
        display_log['hour_formatted'] = display_log['hour'].apply(lambda x: f"{x}:00h")
        display_log['pnl_formatted'] = display_log['pnl'].apply(lambda x: f"${x:.2f}" if x != 0 else "-")
        display_log['cumulative_formatted'] = display_log['cumulative_pnl'].apply(lambda x: f"${x:.2f}")
        
        # Selecionar colunas para exibir
        display_columns = ['hour_formatted', 'strategy', 'action', 'pnl_formatted', 'cumulative_formatted', 'reason']
        display_log_filtered = display_log[display_columns]
        display_log_filtered.columns = ['Hora', 'Estratégia', 'Ação', 'P&L', 'P&L Acum.', 'Status']
        
        st.dataframe(display_log_filtered, hide_index=True, use_container_width=True)
        
        # Gráfico da evolução do P&L (largura total, abaixo da tabela)
        st.markdown("**Evolução do P&L:**")
        
        # Criar gráfico de linha do P&L acumulado
        fig_evolution = px.line(
            simulation_result['trading_log'],
            x='hour',
            y='cumulative_pnl',
            title='Evolução do P&L ao Longo do Dia',
            markers=True,
            line_shape='linear'
        )
        
        # Adicionar linha da meta
        fig_evolution.add_hline(y=12, line_dash="dash", line_color="green", 
                               annotation_text="Meta: $12")
        
        # Adicionar linhas de stop
        fig_evolution.add_hline(y=-36, line_dash="dash", line_color="red", 
                               annotation_text="Stop Martingale: -$36")
        fig_evolution.add_hline(y=-49, line_dash="dash", line_color="orange", 
                               annotation_text="Stop Infinity: -$49")
        
        fig_evolution.update_layout(
            xaxis_title="Hora do Dia",
            yaxis_title="P&L Acumulado ($)",
            height=500  # Aumentando altura do gráfico
        )
        
        st.plotly_chart(fig_evolution, use_container_width=True)
        
        # Resumo das regras aplicadas (abaixo do gráfico)
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Regras da Simulação:**")
            st.write("• **Horário:** 17h às 23h")
            st.write("• **Meta diária:** $12.00")
            st.write("• **Stop Martingale:** -$36 (3 losses em horas diferentes)")
            st.write("• **Stop Infinity:** -$49 (7 níveis)")
            st.write("• **Gestão:** Hora anterior como referência")
            st.write("• **Parada:** Meta, stop ou fim do horário")
        
        with col2:
            st.markdown("**Configurações de Risco:**")
            st.write("• **Capital base:** $540")
            st.write("• **Risco Martingale:** 6.7% do capital")
            st.write("• **Risco Infinity:** 9.1% do capital")
            st.write("• **Meta diária:** 2.2% do capital")
            st.write("• **Estratégia:** Conservadora")
            st.write("• **Win rate esperado:** 78-92%")
        
        # Análise de cenários (abaixo das regras)
        st.subheader("Análise de Cenários")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Operações Realizadas (CSV + Simulação):**")
            
            if real_operations_stats['total_operations'] > 0:
                stats_data = {
                    'Métrica': [
                        'Total de Operações', 
                        'Operações Vencedoras', 
                        'Operações Perdedoras', 
                        'Win Rate Real'
                    ],
                    'Valor': [
                        real_operations_stats['total_operations'],
                        real_operations_stats['winning_operations'],
                        real_operations_stats['losing_operations'],
                        f"{real_operations_stats['win_rate']:.1f}%"
                    ]
                }
                stats_df = pd.DataFrame(stats_data)
                st.dataframe(stats_df, hide_index=True, use_container_width=True)
                
                # Mostrar detalhes do cálculo
                st.markdown("**Metodologia:**")
                st.write("• Baseado nas operações reais do CSV")
                st.write("• Seguindo gestão da hora anterior")
                st.write("• Martingale: meta 3 wins ou 1 loss por sessão")
                st.write("• Infinity: até 2 ciclos (4 ops) por sessão")
            else:
                st.info("Nenhuma operação foi realizada neste dia.")
        
        with col2:
            st.markdown("**Interpretação do Resultado:**")
            
            if realistic_daily_summary['target_achieved']:
                st.success("🎯 **Meta Atingida!**")
                st.write("• Dia bem-sucedido")
                st.write("• Estratégia eficiente")
                st.write("• Risco controlado")
            elif realistic_daily_summary['stop_hit']:
                st.error("🛑 **Stop Acionado**")
                st.write("• Dia com perdas")
                st.write("• Revisar estratégias")
                st.write("• Controle de risco funcionou")
            else:
                if realistic_daily_summary['total_pnl'] > 0:
                    st.info("📈 **Dia Positivo**")
                    st.write("• Lucro sem atingir meta")
                    st.write("• Resultado satisfatório")
                elif realistic_daily_summary['total_pnl'] < 0:
                    st.warning("📉 **Dia Negativo**")
                    st.write("• Prejuízo controlado")
                    st.write("• Sem acionamento de stop")
                else:
                    st.info("➖ **Dia Neutro**")
                    st.write("• Sem operações ou resultado zero")
                    st.write("• Mercado desfavorável")

if __name__ == "__main__":
    main() 