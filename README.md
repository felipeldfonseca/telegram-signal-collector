# 🚀 Sistema de Trading Adaptativo - Telegram Signal Collector

## 📋 Visão Geral

Sistema inteligente que monitora sinais de trading do Telegram em tempo real e seleciona automaticamente a melhor estratégia baseada nas condições atuais do mercado.

### 🎯 Características Principais

- **Análise em Tempo Real**: Monitora sinais 24/7 durante horário de operação
- **Seleção Automática**: Escolhe a melhor estratégia a cada hora
- **3 Estratégias Otimizadas**: Martingale Conservative, Infinity Conservative e Pause
- **Relatórios Detalhados**: Logs completos e análises salvos automaticamente
- **Interface Intuitiva**: Console com informações em tempo real

## 🏆 Estratégias Disponíveis

### 🎲 Martingale Premium Conservative
- **ROI**: 56.0% mensal
- **Win Rate**: 78.7%
- **Risco**: $36 por sessão
- **Tentativas**: Até G1 (2 tentativas)
- **Ativação**: Quando G1 recovery > 65%

### ♾️ Infinity Conservative
- **ROI**: 45.1% mensal  
- **Win Rate**: 92.3% (sessões)
- **Risco**: $49 por sessão
- **Tentativas**: 7 níveis progressivos
- **Ativação**: Quando 1ª tentativa > 60%

### ⏸️ Pause
- **Função**: Preservar capital
- **Ativação**: Quando G2+STOP > 30%
- **Objetivo**: Evitar perdas em condições ruins

## 🧠 Sistema de Decisão Inteligente

### Critérios de Análise
- **Taxa de sucesso na 1ª tentativa**
- **Taxa de recuperação no G1**
- **Taxa de G2+STOP**
- **Confiança mínima de 70%**

### Workflow Automático
1. **Coleta**: Monitora sinais do Telegram
2. **Análise**: A cada hora avalia condições
3. **Decisão**: Seleciona melhor estratégia
4. **Execução**: Aplica estratégia escolhida
5. **Relatório**: Salva resultados e métricas

## ⚙️ Configuração

### 1. Pré-requisitos
```bash
pip install -r requirements.txt
```

### 2. Configuração do Telegram
1. Acesse https://my.telegram.org/auth
2. Crie uma aplicação
3. Obtenha API ID e API Hash

### 3. Arquivo de Configuração (.env)
```env
# Telegram API
TG_API_ID=seu_api_id
TG_API_HASH=seu_api_hash
TG_GROUP=nome_do_grupo

# Opcional
LOG_LEVEL=INFO
PG_DSN=postgresql://...  # Para PostgreSQL
```

## 🚀 Execução

### Modo Produção (Tempo Real)
```bash
python main_adaptive.py
```

### Dashboard Interativo
```bash
python3 -m streamlit run dashboard.py
```
- **Acesso**: http://localhost:8501
- **Análise visual completa** dos dados de trading
- **Simulação realista** do fluxo operacional (17h-24h)
- **Recomendações automáticas** de estratégia
- **Documentação completa**: Ver `DASHBOARD_README.md`

### Modo Teste (Análise de Cenários)
```bash
python main_adaptive.py --test
```

### Ajuda
```bash
python main_adaptive.py --help
```

## 📊 Interface do Sistema

### Tela Inicial
```
🚀===============================================================================
SISTEMA DE TRADING ADAPTATIVO - TELEGRAM SIGNAL COLLECTOR
================================================================================
🎯 Análise inteligente de mercado em tempo real
🔄 Seleção automática da melhor estratégia
📊 Monitoramento 24/7 com relatórios detalhados
================================================================================
```

### Monitor de Sinais
```
🎯 21:30:15 - NOVO SINAL
   💰 Asset: BTC/USDT
   📈 Resultado: ✅ WIN
   🎲 Tentativa: G1
   📊 Total da sessão: 15
   🎯 Estratégia: Ativo - Martingale Conservative
--------------------------------------------------
```

### Análise de Mercado
```
🔍===============================================================================
📊 ANÁLISE DE MERCADO CONCLUÍDA
================================================================================
⏰ Horário: 22:00:00
📈 🔍 Análise 21:00-22:00: 12 ops | 1ª: 45.0% | G1: 75.0% | G2: 10.0% | STOP: 5.0% | Win rate: 82.5% | 
    Estratégia: MARTINGALE_CONSERVATIVE (Confiança: 85.0%)
🔄 MUDANÇA DE ESTRATÉGIA DETECTADA!
🎯 Nova estratégia: Ativo - Martingale Conservative
📊 Métricas: Win Rate: 78.7% | ROI: 56.0% | Risk: $36.0
================================================================================
```

## 📁 Estrutura de Arquivos

```
collector/
├── __init__.py              # Módulo principal
├── config.py               # Configurações
├── parser.py               # Parser de sinais
├── storage.py              # Armazenamento
├── runner.py               # Executor Telegram
├── adaptive_strategy.py    # Sistema adaptativo
├── live_trader.py          # Trading em tempo real
└── regex.py               # Padrões de reconhecimento

data/
├── signals_YYYY-MM-DD.csv  # Sinais coletados
└── analysis_YYYY-MM-DD.jsonl # Análises realizadas

dashboard.py                # Dashboard interativo
DASHBOARD_README.md         # Documentação do dashboard
main_adaptive.py            # Script principal
```

## 🕐 Horário de Operação

- **Início**: 17:00 (horário de Brasília)
- **Fim**: 23:59 (horário de Brasília)
- **Análises**: A cada 60 minutos
- **Monitoramento**: Contínuo durante operação

## 📈 Métricas Monitoradas

### Por Sinal
- Asset negociado
- Resultado (WIN/LOSS)
- Tentativa (1ª, G1, G2, STOP)
- Timestamp preciso

### Por Análise
- Total de operações
- Taxa de sucesso 1ª tentativa
- Taxa de recuperação G1
- Taxa de G2+STOP
- Estratégia recomendada
- Nível de confiança

### Por Sessão
- Tempo total de operação
- Sinais processados
- Mudanças de estratégia
- Análises realizadas

## 🛡️ Segurança e Confiabilidade

- **Validação de Dados**: Verificação de integridade dos sinais
- **Tratamento de Erros**: Recovery automático de falhas
- **Backup Automático**: Dados salvos em tempo real
- **Logs Detalhados**: Rastreamento completo de atividades

## 🔧 Personalização

### Ajustar Critérios de Decisão
Edite `collector/adaptive_strategy.py`:
```python
self.decision_thresholds = {
    'pause_threshold': 30.0,      # % para pausar
    'martingale_threshold': 65.0, # % para Martingale
    'infinity_threshold': 60.0,   # % para Infinity
    'min_operations': 10,         # Mín. operações
    'confidence_threshold': 70.0  # Confiança mínima
}
```

### Ajustar Horário de Operação
Edite `collector/config.py`:
```python
self.start_hour = 17  # Hora de início
self.end_hour = 23    # Hora de fim
```

### Ajustar Intervalo de Análise
Edite `collector/live_trader.py`:
```python
self.analysis_interval = 60  # Minutos entre análises
```

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique os logs em tempo real
2. Execute modo teste: `python main_adaptive.py --test`
3. Analise arquivos em `data/`

## 🎯 Próximas Funcionalidades

- [ ] Dashboard web em tempo real
- [ ] Notificações via Telegram
- [ ] Backtesting automático
- [ ] API REST para integração
- [ ] Machine Learning para previsões

---

**🚀 Sistema desenvolvido para maximizar ROI através de análise inteligente e seleção automática de estratégias otimizadas!** 