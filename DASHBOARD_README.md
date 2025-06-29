# 📊 Dashboard de Trading - Telegram Signal Collector

## 🎯 Visão Geral

Dashboard interativo desenvolvido em Streamlit para análise de performance de sinais de trading do Telegram. Oferece simulação realista do fluxo operacional, análise financeira detalhada e recomendações estratégicas baseadas em dados históricos.

## ✨ Principais Funcionalidades

### 📈 **Análise Geral**
- Resumo executivo de sinais (total, wins, breakdown por tentativas)
- Distribuição visual de resultados (gráficos de pizza)
- Métricas de win rate por categoria

### 🎯 **Simulação Realista (17h-24h)**
- Simula exatamente seu fluxo operacional real
- Usa estratégias recomendadas da hora anterior
- Para quando atinge meta ($12) ou stop loss
- Considera regras específicas de cada gestão

### 🎮 **Controle de Operação Real** ⭐ **NOVO**
Interface na sidebar para indicar se você operou realmente:
- **"Não definido"**: Simulação teórica completa
- **"Sim, operei"**: 
  - Mostra P&L real baseado na estratégia selecionada
  - Permite escolher qual estratégia foi usada
  - Indica se atingiu meta ou parou por stop loss
- **"Não, pausei"**: 
  - P&L = $0 (preservação de capital)
  - Permite informar motivo da pausa
  - Opção de ver simulação hipotética
  - Evita "falsos positivos" de meta atingida

### 🔄 **Estratégias Implementadas**

#### **Martingale Conservative**
- Meta: 3 wins por sessão
- Stop: 1 loss por sessão (-$12)
- Stop diário: 3 losses em horas diferentes (-$36)
- P&L: +$12 (vitória) / -$12 (derrota por sessão)

#### **Infinity Conservative**
- Meta: 2 ciclos completos (4 operações)
- Stop: Conforme progressão de níveis (-$49)
- P&L: +$12 (vitória) / -$8 (derrota média)

### 📊 **Análises Detalhadas**
- Performance por hora com recomendações
- Análise por ativo (ADA, BTC, ETH, SOL, XRP)
- Operações da hora onde meta foi atingida
- Estratégias recomendadas por horário

### 💰 **Análises Financeiras**
- P&L por estratégia aplicada
- ROI por hora de operação
- Distribuição de estratégias e resultados
- Performance comparativa entre gestões

### 📋 **Log da Simulação**
- Cronologia detalhada das operações
- Evolução do P&L ao longo do dia
- Gráfico com linhas de meta e stop loss
- Estatísticas de operações realizadas
- Interpretação automática dos resultados

## 🚀 **Como Usar**

### **Instalação**
```bash
# Instalar dependências
pip install -r requirements.txt

# Executar dashboard
python3 -m streamlit run dashboard.py
```

### **Acesso**
- **Local**: http://localhost:8501
- **Rede**: http://[seu-ip]:8501

### **Seleção de Dados**
1. Use a sidebar para selecionar arquivo de sinais
2. **Configure seu status de operação** (Não definido/Sim, operei/Não, pausei) ⭐
3. Dados são carregados automaticamente de `data/trading ops/`
4. Formato esperado: `signals_YYYY-MM-DD.csv`

## 📁 **Estrutura de Dados**

### **Diretório Esperado**
```
data/
└── trading ops/
    └── [Mês]/
        └── [Dia]/
            └── daily ops/
                └── signals_*.csv
```

### **Formato CSV**
- `timestamp`: Data/hora da operação
- `asset`: Ativo (ADA/USDT, BTC/USDT, etc.)
- `result`: Resultado (W/L)
- `attempt`: Tentativa (1, 2, 3)

## 🎛️ **Configurações**

### **Parâmetros de Trading**
- **Capital inicial**: $540
- **Horário de operação**: 17h-23h
- **Meta diária**: $12.00
- **Valores de aposta**: $4 (1ª), $8 (G1), $16 (G2)

### **Critérios de Recomendação** ⭐ **UNIFICADOS**
- **PAUSE**: 
  - Total < 10 operações (dados insuficientes)
  - G2+STOP > 30% (condições desfavoráveis)
- **Martingale Conservative**: G1 recovery > 65%
- **Infinity Conservative**: 1ª tentativa > 60%
- **Default**: Infinity Conservative

### **Cálculo de Win Rate** ⭐ **CORRIGIDO**
- **Wins**: Apenas 1ª tentativa + G1 (recuperação)
- **Losses**: G2 + STOP
- **G1 Rate**: Taxa de recuperação relativa = (G1 wins / max(1, total - 1ª wins)) * 100

## 📊 **Seções do Dashboard**

1. **Resumo Geral**: Métricas principais
2. **Performance Diária**: Simulação realista 17h-24h
3. **Controle de Operação**: Status real vs. teórico ⭐ **NOVO**
4. **Breakdown Detalhado**: Distribuição por tentativas
5. **Recomendação**: Estratégia sugerida com lógica unificada
6. **Análises Detalhadas**: Performance por hora e ativo
7. **Análises Financeiras**: P&L por estratégia
8. **Log da Simulação**: Cronologia e evolução

## 🔧 **Recursos Técnicos**

### **Performance**
- Cache inteligente com `@st.cache_data`
- Carregamento otimizado (3-5 segundos)
- Visualizações interativas com Plotly
- Layout responsivo

### **Análise Realista**
- Simula fluxo operacional real
- Considera gestão da hora anterior
- Para em condições reais (meta/stop)
- Conta operações individuais do CSV
- **Suporte para operação real vs. teórica** ⭐

### **Visualizações**
- Gráficos de linha para evolução temporal
- Gráficos de pizza para distribuições
- Gráficos de barras para comparações
- Tabelas interativas com formatação

## 🎯 **Casos de Uso**

### **Análise Diária**
- Verificar se teria atingido meta no dia
- Identificar melhor estratégia para o período
- Analisar operações da hora de sucesso
- **Comparar resultado real vs. teórico** ⭐

### **Controle de Performance Real** ⭐ **NOVO**
- Registrar se operou ou pausou
- Acompanhar P&L real vs. simulação
- Identificar padrões de pausa
- Evitar "metas falsas" quando não operou

### **Otimização de Estratégia**
- Comparar performance entre gestões
- Identificar horários mais produtivos
- Ajustar critérios de recomendação

### **Gestão de Risco**
- Monitorar frequência de stops
- Analisar drawdowns por estratégia
- Verificar efetividade dos controles

## 📈 **Potencial de Expansão**

### **Funcionalidades Futuras**
- Análise multi-dias
- Backtesting automatizado
- Alertas em tempo real
- Integração com APIs de exchange
- Dashboard comercial (SaaS)

### **Melhorias Técnicas**
- Banco de dados para histórico
- Cache persistente
- Exportação de relatórios
- Configurações personalizáveis

## ⚡ **Comandos Rápidos**

```bash
# Executar dashboard
python3 -m streamlit run dashboard.py

# Instalar dependências
pip install streamlit plotly pandas

# Verificar dados
ls data/trading\ ops/*/*/daily\ ops/signals_*.csv
```

---

**Desenvolvido para otimizar análise de trading com simulação realista do fluxo operacional e controle de operação real.**

*Dashboard integrado ao Telegram Signal Collector - Versão 2.1* ⭐ 