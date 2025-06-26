# 📈 Telegram Signal Collector

Um sistema automatizado para coletar e armazenar sinais de trading de opções binárias do Telegram com suporte a PostgreSQL e análise de dados.

## 🚀 Funcionalidades

- 📊 Coleta automática de sinais WIN/STOP com gestão Martingale
- 🗄️ Armazenamento dual: CSV + PostgreSQL
- ⏰ Modo backfill (histórico) e listener em tempo real
- 📈 Análise de performance com notebook Jupyter
- 🔄 Tratamento robusto de rate limits (FloodWait)
- 🌍 Timezone América/São Paulo

## 📁 Estrutura do Projeto

```
telegram_signal_collector/
├── README.md
├── .env.example
├── requirements.txt
├── main.py
├── collector/
│   ├── __init__.py
│   ├── config.py
│   ├── regex.py
│   ├── parser.py
│   ├── storage.py
│   └── runner.py
└── notebooks/
    └── Exploratory.ipynb
```

## 🔧 Configuração Inicial

### 1. Obter Credenciais da API do Telegram

1. Acesse [my.telegram.org](https://my.telegram.org)
2. Faça login com seu número de telefone
3. Vá em "API Development Tools"
4. Crie uma nova aplicação:
   - **App title**: Telegram Signal Collector
   - **Short name**: signal_collector
   - **Platform**: Desktop
5. Anote o `API_ID` e `API_HASH`

### 2. Configurar Ambiente

```bash
# Clone ou baixe o projeto
cd telegram_signal_collector

# Crie ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Instale dependências
pip install -r requirements.txt

# Configure variáveis de ambiente
cp .env.example .env
# Edite o arquivo .env com suas credenciais
```

### 3. Configurar PostgreSQL (Opcional)

Se você quiser usar PostgreSQL, execute este script SQL:

```sql
-- Criar banco de dados
CREATE DATABASE telegram_signals;

-- Conectar ao banco criado
\c telegram_signals;

-- Criar tabela de sinais
CREATE TABLE IF NOT EXISTS signals (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    asset VARCHAR(20) NOT NULL,
    result CHAR(1) NOT NULL CHECK (result IN ('W', 'L')),
    attempt INTEGER CHECK (attempt IN (1, 2, 3)),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(timestamp, asset, result, attempt)
);

-- Criar índices para performance
CREATE INDEX idx_signals_timestamp ON signals(timestamp);
CREATE INDEX idx_signals_asset ON signals(asset);
CREATE INDEX idx_signals_result ON signals(result);
```

### 4. Configurar .env

```env
# Telegram API
TG_API_ID=seu_api_id_aqui
TG_API_HASH=seu_api_hash_aqui
TG_SESSION=telegram_session
TG_GROUP=nome_do_grupo_ou_@username

# PostgreSQL (opcional)
PG_DSN=postgresql://usuario:senha@localhost:5432/telegram_signals
```

## 📊 Uso

### Coletar Histórico de um Dia Específico

```bash
# Coletar ontem e salvar em CSV
python main.py --date 2025-01-15 --export csv

# Coletar ontem e salvar no PostgreSQL
python main.py --date 2025-01-15 --export pg

# Coletar intervalo de datas
python main.py --from 2025-01-10 --to 2025-01-15 --export pg
```

### Listener em Tempo Real

```bash
# Escutar novos sinais e salvar em CSV
python main.py --live --export csv

# Escutar novos sinais e salvar no PostgreSQL
python main.py --live --export pg
```

### Opções Disponíveis

```bash
python main.py --help
```

- `--date YYYY-MM-DD`: Coleta histórico de um dia específico
- `--from YYYY-MM-DD`: Data inicial para coleta de intervalo
- `--to YYYY-MM-DD`: Data final para coleta de intervalo
- `--live`: Modo listener em tempo real
- `--export {csv,pg}`: Formato de exportação (padrão: csv)

## 📈 Análise de Dados

Execute o notebook Jupyter para análise dos dados coletados:

```bash
jupyter notebook notebooks/Exploratory.ipynb
```

O notebook inclui:
- 📊 Estatísticas de win/loss por tentativa
- 💰 Cálculo de P&L com gestão 1-2-4
- 📈 Gráficos de performance cumulativa
- 📅 Análise temporal dos sinais

## 🎯 Formatos de Mensagem Suportados

| Tipo | Regex Pattern | Exemplo |
|------|---------------|---------|
| Win 1ª | `✅ WIN em \`([A-Z]+/[A-Z]+)\` ✅` | `✅ WIN em \`ADA/USDT\` ✅` |
| Win 2ª | `✅ WIN \(G1\) em \`([A-Z]+/[A-Z]+)\` ✅` | `✅ WIN (G1) em \`BTC/USDT\` ✅` |
| Win 3ª | `✅ WIN \(G2\) em \`([A-Z]+/[A-Z]+)\` ✅` | `✅ WIN (G2) em \`ETH/USDT\` ✅` |
| Loss | `❎ STOP em \`([A-Z]+/[A-Z]+)\` ❎` | `❎ STOP em \`DOT/USDT\` ❎` |

## ⚠️ Limitações e Avisos

1. **Histórico Limitado**: Se "Chat History for New Members" estiver desabilitado no grupo, você só verá mensagens a partir de quando entrou
2. **Rate Limits**: O sistema trata automaticamente os limites de rate do Telegram
3. **Privacidade**: Não compartilhe conteúdo do grupo externamente (Termos do Telegram)
4. **Horário de Operação**: Sistema coleta sinais entre 17:00-23:59:59 (America/Sao_Paulo)

## 🔍 Troubleshooting

### Erro de Autenticação
- Verifique se `API_ID` e `API_HASH` estão corretos no `.env`
- Delete o arquivo `.session` e tente novamente

### Grupo Não Encontrado
- Certifique-se de que `TG_GROUP` está correto (nome ou @username)
- Verifique se você é membro do grupo

### Erro de Conexão PostgreSQL
- Verifique se o PostgreSQL está rodando
- Confirme as credenciais no `PG_DSN`
- Teste a conexão: `psql "postgresql://usuario:senha@localhost:5432/telegram_signals"`

## 📝 Logs

O sistema gera logs detalhados de:
- Mensagens processadas
- Sinais identificados
- Erros de parsing
- Resumos de execução

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto é apenas para uso educacional e pessoal. Respeite os Termos de Serviço do Telegram.

---

🚀 **Desenvolvido para automatizar a coleta de sinais de trading com precisão e eficiência!** 