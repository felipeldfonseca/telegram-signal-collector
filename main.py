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

# Adicionar diretório do projeto ao path
sys.path.insert(0, str(Path(__file__).parent))

from collector import Config, Runner

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
    
    from collector.regex import RegexPatterns
    
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


if __name__ == "__main__":
    app() 