# 📝 Prompt‐Blueprint • Coletor de Sinais do Telegram

> **Objetivo do arquivo:**  
> Você vai copiar todo o conteúdo abaixo (incluindo estes blocos de citação) e colar como **prompt** para uma LLM (ex.: Claude 4, GPT-4o, etc.) dentro do **Cursor**.  
> O modelo deverá **gerar um projeto Python completo** que leia mensagens de um grupo do Telegram, identifique resultados de operações (WIN/STOP), salve os dados estruturados **(CSV + PostgreSQL)** e ofereça opções de execução em modo *back-fill* ou *real-time listener*.

---

## 1. Contexto do Problema

- **Eu participo** de um grupo de WhatsApp e de **um grupo de Telegram** onde uma IA envia sinais de trading em opções binárias.  
- Cada operação segue **gestão Martingale** (até 3 tentativas).  
- Quero **automatizar** a coleta dos resultados diários entre **17h e 00h (America/Sao_Paulo)**, mesmo sem ser administrador do grupo.

### Formatos de mensagem

| Caso | Texto exato (🔍 regex) |
|------|-----------------------|
| Win 1ª tentativa | `✅ WIN em \`([A-Z]+/[A-Z]+)\` ✅` |
| Win 2ª tentativa | `✅ WIN \(G1\) em \`([A-Z]+/[A-Z]+)\` ✅` |
| Win 3ª tentativa | `✅ WIN \(G2\) em \`([A-Z]+/[A-Z]+)\` ✅` |
| Loss (3 tentativas) | `❎ STOP em \`([A-Z]+/[A-Z]+)\` ❎` |

> Observação: dojis/empates **não** entram — são reembolsos.

### Campos desejados no dataset final

| Coluna | Tipo | Exemplo |
|--------|------|---------|
| `timestamp` | ISO local (America/Sao_Paulo) | `2025-06-26 18:07:03` |
| `asset` | str | `ADA/USDT` |
| `result` | str | `W` ou `L` |
| `attempt` | int ou `NULL` | `1`, `2`, `3` ou `NULL` (para loss) |

---

## 2. Entregáveis esperados da LLM

1. **Projeto Python** (carpeta ⬇️):
telegram_signal_collector/
├─ README.md
├─ .env.example
├─ requirements.txt
├─ main.py
├─ collector/
│ ├─ init.py
│ ├─ config.py
│ ├─ regex.py
│ ├─ parser.py
│ ├─ storage.py # CSV + opcional SQLite
│ └─ runner.py # modo histórico / modo listener
└─ notebooks/
└─ Exploratory.ipynb

2. **README.md** com instruções passo-a-passo:
- Como gerar `API_ID` e `API_HASH` em <https://my.telegram.org>.  
- Como preencher `.env` ( `TG_API_ID`, `TG_API_HASH`, `TG_SESSION`, `TG_GROUP`, **`PG_DSN`** ).  
- Como instalar (`pip install -r requirements.txt`) e executar:
  ```bash
  # Coletar histórico de ontem e gravar no PostgreSQL
  python main.py --date 2025-06-25 --export pg

  # Listener ao vivo
  python main.py --live --export pg
  ```
- Passo extra: **criar banco/tabela** no PostgreSQL e acessar pelo **pgAdmin 4** (script SQL incluso).  
- Explicação sobre limitação de histórico se “Chat History for New Members” estiver OFF.

3. **Código limpo e documentado**:
- PEP 8, tipagem (`typing`) e docstrings.
- **Telethon** como biblioteca de acesso.
- Tratamento de **FloodWait** com `retry_after`.
- Função utilitária de **parsing** usando as regex de cima.
- Classe `Storage` que:
  - Salva/atualiza CSV diário `signals_YYYY-MM-DD.csv`.
  - Grava em **PostgreSQL** usando `psycopg2` ou `asyncpg` (inserções em lote, `UPSERT`).  

4. **Notebook opcional** (`Exploratory.ipynb`):
- Consulta o banco PostgreSQL (ou lê CSV) de um dia.
- Mostra contagens de win/loss por tentativa.
- Calcula assertividade e lucro líquido sob a gestão 1-2-4.  
- Plota gráfico simples (matplotlib) de P&L cumulativo.

---

## 3. Restrições e Requisitos Técnicos

1. **Somente user-session** Telethon — **não** usar bot token.  
2. Timezone fixo `America/Sao_Paulo`.  
3. Regex deve ser **case-insensitive** e tolerante a espaços extras.  
4. Código deve rodar em Python ≥ 3.9.  
5. Dependências mínimas:
- `telethon`
- `python-dotenv`
- `pandas`
- `matplotlib`
- `tqdm`
- **`psycopg2-binary`** (ou `asyncpg`)  
6. Manter **arquivo de sessão** (`.session`) fora do versionamento (gitignore).  
7. CLI (`argparse` ou `typer`) com flags:
- `--date YYYY-MM-DD` → backfill daquele dia (17:00–23:59:59).  
- `--from YYYY-MM-DD --to YYYY-MM-DD` → backfill range.  
- `--live` → listener em tempo real.  
- `--export pg|csv` (default `csv`).  
8. Logs claros via `logging`: cada mensagem parseada + resumo final.  
9. Não compartilhar conteúdo do grupo externamente (Termos Telegram) — adicionar aviso no README.

---

## 4. Passos de raciocínio sugeridos para o modelo

1. **Pensar** na arquitetura de pacotes e dependências.  
2. **Esboçar** as regex e validar com exemplos-teste.  
3. **Implementar** `parser.parse(text) -> Tuple[result, attempt, asset] | None`.  
4. **Criar** função `collect_history(chat, start_dt, end_dt)` com `iter_messages`.  
5. **Criar** função `run_live(chat)` com handler `events.NewMessage`.  
6. **Persistir** dados:
- `pandas.DataFrame.to_csv(…, mode='a', header=not exists)`  
- Ou `INSERT ... ON CONFLICT DO NOTHING` no PostgreSQL via `psycopg2`.  
7. **CL​I**: amarrar tudo no `main.py`.  
8. **Testar** com mocks (mensagens fake) ≥ 4 casos.  
9. **Documentar** tudo no README com GIF ou screencast opcional.

---

## 5. Estilo de resposta esperado

> O modelo deve **responder com os arquivos completos** (use blocos ```file``` do Cursor, ou equivalente).  
> Cada arquivo já deve conter o código final; **não** apenas trechos soltos.  
> Após gerar, inclua um sumário curto de como rodar o projeto.

---

### Dica de ouro para a LLM

> Sempre que algo for opcional (ex.: exportar CSV), implemente de forma a não quebrar o fluxo principal se o usuário escolher apenas PostgreSQL.

---

Boa sorte, Claude! Crie o melhor coletor de sinais do Telegram que o mundo já viu. 🚀
