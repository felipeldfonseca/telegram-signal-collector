#!/usr/bin/env python3
"""
Telegram Signal Collector - CLI Principal

Coletor automatizado de sinais de trading do Telegram
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path
import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
import asyncio
import logging
from typing import Optional
import pandas as pd

# Adicionar diretório do projeto ao path
sys.path.insert(0, str(Path(__file__).parent))

from collector import Config, Runner
from collector.regex import RegexPatterns

app = typer.Typer(
    name="telegram-signal-collector",
    help="🎯 Coletor automatizado de sinais de trading do Telegram",
    add_completion=False
)

console = Console()


def print_banner():
    """Imprime banner do aplicativo."""
    banner = Text("📈 Telegram Signal Collector", style="bold blue")
    subtitle = Text("Coletor automatizado de sinais de trading", style="dim")
    
    console.print(Panel(
        Text.assemble(banner, "\n", subtitle),
        title="🚀 Bem-vindo",
        border_style="blue"
    ))


def validate_date(date_str: str) -> datetime:
    """Valida e converte string de data."""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        console.print(f"❌ Data inválida: {date_str}. Use formato YYYY-MM-DD", style="bold red")
        raise typer.Exit(1)


@app.command("test")
def test_connection():
    """Testa conexão com Telegram e grupo."""
    print_banner()
    
    try:
        config = Config()
        config.setup_logging()
        
        console.print("🔍 Testando conexão...", style="yellow")
        
        runner = Runner(config)
        success = runner.test_connection()
        
        if not success:
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"❌ Erro: {e}", style="bold red")
        raise typer.Exit(1)


@app.command("collect")
def collect_signals(
    date: str = typer.Option(
        None,
        "--date",
        "-d",
        help="Data específica para coletar (YYYY-MM-DD)"
    ),
    from_date: str = typer.Option(
        None,
        "--from",
        "-f",
        help="Data inicial para intervalo (YYYY-MM-DD)"
    ),
    to_date: str = typer.Option(
        None,
        "--to",
        "-t",
        help="Data final para intervalo (YYYY-MM-DD)"
    ),
    export_format: str = typer.Option(
        "csv",
        "--export",
        "-e",
        help="Formato de exportação"
    ),
    live: bool = typer.Option(
        False,
        "--live",
        "-l",
        help="Modo listener em tempo real"
    )
):
    """Coleta sinais do Telegram (histórico ou tempo real)."""
    print_banner()
    
    # Validar argumentos
    if live and (date or from_date or to_date):
        console.print("❌ Modo --live não pode ser usado com datas", style="bold red")
        raise typer.Exit(1)
    
    if not live and not date and not from_date:
        console.print("❌ Especifique --date, --from/--to ou --live", style="bold red")
        raise typer.Exit(1)
    
    if (from_date and not to_date) or (to_date and not from_date):
        console.print("❌ Use --from e --to juntos para intervalo", style="bold red")
        raise typer.Exit(1)
    
    if export_format not in ['csv', 'pg', 'both']:
        console.print("❌ Formato deve ser: csv, pg ou both", style="bold red")
        raise typer.Exit(1)
    
    try:
        config = Config()
        config.setup_logging()
        
        # Verificar PostgreSQL se necessário
        if export_format in ['pg', 'both'] and not config.has_postgres:
            console.print("❌ PostgreSQL não configurado (PG_DSN)", style="bold red")
            raise typer.Exit(1)
        
        runner = Runner(config)
        
        if live:
            # Modo listener em tempo real
            console.print("🎯 Iniciando modo listener...", style="green")
            runner.run_live(export_format)
            
        elif date:
            # Coletar dia específico
            target_date = validate_date(date)
            console.print(f"📅 Coletando sinais de {date}...", style="green")
            runner.run_backfill(target_date, export_format=export_format)
            
        elif from_date and to_date:
            # Coletar intervalo
            start_date = validate_date(from_date)
            end_date = validate_date(to_date)
            
            if start_date > end_date:
                console.print("❌ Data inicial deve ser menor que data final", style="bold red")
                raise typer.Exit(1)
            
            console.print(f"📅 Coletando sinais de {from_date} até {to_date}...", style="green")
            runner.run_backfill(start_date, end_date, export_format)
            
    except KeyboardInterrupt:
        console.print("\n⏹️ Operação cancelada pelo usuário", style="yellow")
    except Exception as e:
        console.print(f"❌ Erro: {e}", style="bold red")
        raise typer.Exit(1)


@app.command("patterns")
def test_patterns():
    """Testa padrões regex de parsing."""
    print_banner()
    
    console.print("🧪 Testando padrões regex...", style="yellow")
    
    patterns = RegexPatterns()
    patterns.test_patterns()


@app.command("stats")
def show_stats(
    format: str = typer.Option(
        "pg",
        "--format",
        "-f",
        help="Formato dos dados (pg ou csv)"
    ),
    csv_file: str = typer.Option(
        None,
        "--file",
        help="Arquivo CSV específico"
    )
):
    """Mostra estatísticas dos dados coletados."""
    print_banner()
    
    try:
        config = Config()
        
        from collector.storage import Storage
        storage = Storage(config)
        
        if format == "pg":
            if not config.has_postgres:
                console.print("❌ PostgreSQL não configurado", style="bold red")
                raise typer.Exit(1)
            
            stats = storage.get_postgres_stats()
            
            if not stats:
                console.print("ℹ️ Nenhum dado encontrado no PostgreSQL", style="yellow")
                return
            
            console.print("📊 Estatísticas PostgreSQL", style="bold blue")
            console.print(f"Total de registros: {stats.get('total_records', 0)}")
            console.print(f"Assets únicos: {stats.get('unique_assets', 0)}")
            console.print(f"Total de wins: {stats.get('total_wins', 0)}")
            console.print(f"Total de losses: {stats.get('total_losses', 0)}")
            
            if 'first_signal' in stats and stats['first_signal']:
                console.print(f"Primeiro sinal: {stats['first_signal']}")
            if 'last_signal' in stats and stats['last_signal']:
                console.print(f"Último sinal: {stats['last_signal']}")
            
            attempts = stats.get('wins_by_attempt', {})
            if attempts:
                console.print("Wins por tentativa:")
                for attempt, count in attempts.items():
                    console.print(f"  G{attempt}: {count}")
        
        elif format == "csv":
            if not csv_file:
                console.print("❌ Especifique --file para CSV", style="bold red")
                raise typer.Exit(1)
            
            signals = storage.load_from_csv(csv_file)
            
            if not signals:
                console.print("ℹ️ Nenhum dado encontrado no CSV", style="yellow")
                return
            
            from collector.parser import SignalParser
            parser = SignalParser(config)
            parser.print_statistics(signals)
        
        else:
            console.print("❌ Formato deve ser 'pg' ou 'csv'", style="bold red")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"❌ Erro: {e}", style="bold red")
        raise typer.Exit(1)


@app.command("setup")
def setup_guide():
    """Mostra guia de configuração inicial."""
    print_banner()
    
    setup_text = """
🔧 Guia de Configuração

1️⃣ Obter credenciais do Telegram:
   • Acesse: https://my.telegram.org
   • Faça login e vá em "API Development Tools"
   • Crie uma aplicação e anote API_ID e API_HASH

2️⃣ Configurar ambiente:
   • Copie .env.example para .env
   • Preencha TG_API_ID, TG_API_HASH e TG_GROUP
   • Para PostgreSQL, configure PG_DSN

3️⃣ Instalar dependências:
   • pip install -r requirements.txt

4️⃣ Testar conexão:
   • python main.py test

5️⃣ Começar a coletar:
   • python main.py collect --date 2025-01-15 --export csv
   • python main.py collect --live --export pg
    """
    
    console.print(Panel(setup_text, title="📋 Setup", border_style="green"))


@app.command("analyze")
def analyze_manual_data(
    file_path: str = typer.Option(
        "docs/grouphistory copy.txt",
        "--file", "-f",
        help="Caminho para o arquivo de histórico manual"
    ),
    export_format: str = typer.Option(
        "csv",
        "--export", "-e",
        help="Formato de exportação (csv, pg, both)"
    ),
    show_details: bool = typer.Option(
        True,
        "--details/--no-details",
        help="Mostrar análise detalhada"
    )
):
    """📊 Analisa dados manuais coletados e gera relatório completo."""
    print_banner()
    
    console.print(f"📂 Processando arquivo: {file_path}", style="yellow")
    
    try:
        # Configurar sistema
        config = Config()
        runner = Runner(config)
        
        # Processar dados manuais
        signals = runner.parser.parse_manual_history_simple(file_path)
        
        if not signals:
            console.print("❌ Nenhum sinal encontrado no arquivo", style="red")
            return
        
        console.print(f"✅ {len(signals)} sinais processados", style="green")
        
        # Salvar dados estruturados
        runner.storage.save_signals(signals, export_format)
        
        # Gerar análise completa
        generate_detailed_analysis(signals, show_details)
        
        console.print("\n🎯 Análise completa! Verifique os arquivos gerados.", style="bold green")
        
    except Exception as e:
        console.print(f"❌ Erro durante análise: {e}", style="red")
        raise typer.Exit(1)


def generate_detailed_analysis(signals, show_details: bool = True):
    """
    Gera análise detalhada dos sinais.
    
    Args:
        signals: Lista de sinais
        show_details: Se deve mostrar detalhes completos
    """
    if not signals:
        return
    
    # Converter para DataFrame para análise
    df = pd.DataFrame([s.to_dict() for s in signals])
    
    # Calcular estatísticas básicas
    total_signals = len(df)
    wins = df[df['result'] == 'W'].shape[0]
    losses = df[df['result'] == 'L'].shape[0]
    win_rate = (wins / total_signals) * 100 if total_signals > 0 else 0
    
    # Estatísticas por tentativa
    win_attempts = df[df['result'] == 'W']['attempt'].value_counts().sort_index()
    
    # Calcular P&L Martingale (1-2-4)
    pnl_results = calculate_martingale_pnl(df)
    
    # Assets mais negociados
    top_assets = df['asset'].value_counts().head(5)
    
    # Análise temporal
    df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
    hourly_distribution = df['hour'].value_counts().sort_index()
    
    # Mostrar resultados
    console.print("\n📊 ANÁLISE COMPLETA DOS SINAIS", style="bold blue")
    console.print("=" * 50)
    
    # Tabela de estatísticas gerais
    stats_table = Table(title="📈 Estatísticas Gerais")
    stats_table.add_column("Métrica", style="cyan")
    stats_table.add_column("Valor", style="magenta")
    
    stats_table.add_row("Total de Sinais", str(total_signals))
    stats_table.add_row("Wins", f"{wins} ({win_rate:.1f}%)")
    stats_table.add_row("Losses", f"{losses} ({(losses/total_signals)*100:.1f}%)")
    stats_table.add_row("P&L Total", f"R$ {pnl_results['total_pnl']:.2f}")
    stats_table.add_row("P&L por Operação", f"R$ {pnl_results['avg_pnl']:.2f}")
    
    console.print(stats_table)
    
    # Tabela de wins por tentativa
    if not win_attempts.empty:
        attempts_table = Table(title="🎯 Wins por Tentativa")
        attempts_table.add_column("Tentativa", style="cyan")
        attempts_table.add_column("Quantidade", style="magenta")
        attempts_table.add_column("Percentual", style="green")
        
        for attempt, count in win_attempts.items():
            percentage = (count / wins) * 100 if wins > 0 else 0
            attempts_table.add_row(
                f"G{attempt}" if attempt else "N/A",
                str(count),
                f"{percentage:.1f}%"
            )
        
        console.print(attempts_table)
    
    # Assets mais negociados
    if not top_assets.empty:
        assets_table = Table(title="💰 Top Assets")
        assets_table.add_column("Asset", style="cyan")
        assets_table.add_column("Operações", style="magenta")
        assets_table.add_column("Percentual", style="green")
        
        for asset, count in top_assets.items():
            percentage = (count / total_signals) * 100
            assets_table.add_row(asset, str(count), f"{percentage:.1f}%")
        
        console.print(assets_table)
    
    # Análise de viabilidade (Martingale 1-2-4 com payout 90%)
    required_win_rate = 89.42  # Breakeven calculado com distribuição real
    
    console.print(f"\n🎯 ANÁLISE DE VIABILIDADE", style="bold yellow")
    console.print(f"Win Rate Atual: {win_rate:.1f}%")
    console.print(f"Win Rate Necessário: {required_win_rate:.1f}%")
    
    if win_rate >= required_win_rate:
        console.print("✅ Sistema LUCRATIVO! Pode prosseguir para automação.", style="bold green")
    else:
        deficit = required_win_rate - win_rate
        console.print(f"⚠️ Precisa melhorar {deficit:.1f}% para ser lucrativo", style="bold red")
    
    # Mostrar detalhes se solicitado
    if show_details:
        console.print(f"\n📊 DETALHES ADICIONAIS", style="bold cyan")
        console.print(f"Período: {df['timestamp'].min()} até {df['timestamp'].max()}")
        console.print(f"Horário de maior atividade: {hourly_distribution.idxmax()}h ({hourly_distribution.max()} sinais)")
        
        # P&L por dia
        df['date'] = pd.to_datetime(df['timestamp']).dt.date
        daily_pnl = df.groupby('date').apply(lambda x: calculate_martingale_pnl(x)['total_pnl'])
        console.print(f"Melhor dia: {daily_pnl.idxmax()} (R$ {daily_pnl.max():.2f})")
        console.print(f"Pior dia: {daily_pnl.idxmin()} (R$ {daily_pnl.min():.2f})")


def calculate_martingale_pnl(df):
    """
    Calcula P&L usando estratégia Martingale 1-2-4 com payout 90%.
    
    Args:
        df: DataFrame com os sinais
        
    Returns:
        Dict com resultados do P&L
    """
    if df.empty:
        return {'total_pnl': 0, 'avg_pnl': 0, 'operations': 0}
    
    total_pnl = 0
    operations = 0
    
    for _, signal in df.iterrows():
        operations += 1
        
        if signal['result'] == 'W':
            # Win: ganho baseado na tentativa com payout 90%
            if signal['attempt'] == 1:
                pnl = 0.90  # 90% de 1 dólar
            elif signal['attempt'] == 2:
                pnl = 1.8 - 1  # 90% de 2 dólares - 1 dólar perdido na G1 = 0.80
            elif signal['attempt'] == 3:
                pnl = 3.6 - 3  # 90% de 4 dólares - perdas anteriores (1+2) = 0.60
            else:
                pnl = 0.90  # Caso padrão (G1)
        else:
            # Loss: perda total da sequência Martingale
            pnl = -7  # -(1 + 2 + 4)
        
        total_pnl += pnl
    
    avg_pnl = total_pnl / operations if operations > 0 else 0
    
    return {
        'total_pnl': total_pnl,
        'avg_pnl': avg_pnl,
        'operations': operations
    }


if __name__ == "__main__":
    app() 