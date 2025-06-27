#!/usr/bin/env python3
"""
Análise do arquivo Excel de acompanhamento de capital do Felipe
Foco nas colunas A, B, C, G, J, M, N da sheet 'JUNHO, 25'
"""

import pandas as pd
import numpy as np
from datetime import datetime

def analyze_excel():
    print("📊 ANÁLISE COMPLETA DO EXCEL - JUNHO 2025")
    print("=" * 60)
    
    try:
        # Listar sheets disponíveis
        xl_file = pd.ExcelFile('excel/Meta diária - Felipe.xlsx')
        print("📋 Sheets disponíveis:", xl_file.sheet_names)
        
        # Carregar sheet JUNHO, 25
        df = pd.read_excel('excel/Meta diária - Felipe.xlsx', sheet_name='JUNHO, 25')
        
        print(f"\n📊 Dados carregados: {len(df)} linhas, {len(df.columns)} colunas")
        print("📋 Colunas:", list(df.columns))
        
        print("\n🔍 PREVIEW DOS DADOS:")
        print("-" * 40)
        print(df.head(10))
        
        # Análise das colunas importantes (A, B, C, G, J, M, N)
        print("\n📈 ANÁLISE DAS COLUNAS IMPORTANTES:")
        print("-" * 50)
        
        # Coluna A - Data
        if len(df.columns) > 0:
            col_a = df.iloc[:, 0]  # Primeira coluna (A)
            print(f"📅 Coluna A (Data): {col_a.head(10).tolist()}")
        
        # Coluna B - WIN
        if len(df.columns) > 1:
            col_b = df.iloc[:, 1]  # Segunda coluna (B)
            wins = (col_b == 'O').sum()
            print(f"🎯 Coluna B (WIN): {wins} dias com WIN (O)")
        
        # Coluna C - LOSS  
        if len(df.columns) > 2:
            col_c = df.iloc[:, 2]  # Terceira coluna (C)
            losses = (col_c == 'X').sum()
            print(f"❌ Coluna C (LOSS): {losses} dias com LOSS (X)")
        
        # Win Rate
        if len(df.columns) > 2:
            total_days = wins + losses
            if total_days > 0:
                win_rate = wins / total_days * 100
                print(f"📊 Win Rate: {win_rate:.1f}% ({wins}W/{losses}L)")
        
        # Coluna G - CAPITAL
        if len(df.columns) > 6:
            col_g = pd.to_numeric(df.iloc[:, 6], errors='coerce')  # Sétima coluna (G)
            capital_data = col_g.dropna()
            if len(capital_data) > 0:
                capital_inicial = capital_data.iloc[0]
                capital_atual = capital_data.iloc[-1]
                print(f"💰 Coluna G (CAPITAL):")
                print(f"   🏁 Inicial: ${capital_inicial:.2f}")
                print(f"   📊 Atual: ${capital_atual:.2f}")
        
        # Coluna J - P/L DIA
        if len(df.columns) > 9:
            col_j = pd.to_numeric(df.iloc[:, 9], errors='coerce')  # Décima coluna (J)
            pnl_data = col_j.dropna()
            if len(pnl_data) > 0:
                total_pnl = pnl_data.sum()
                avg_pnl = pnl_data.mean()
                best_day = pnl_data.max()
                worst_day = pnl_data.min()
                positive_days = (pnl_data > 0).sum()
                negative_days = (pnl_data < 0).sum()
                
                print(f"📈 Coluna J (P/L DIA):")
                print(f"   💰 Total: ${total_pnl:.2f}")
                print(f"   📊 Médio: ${avg_pnl:.2f}")
                print(f"   🏆 Melhor: ${best_day:.2f}")
                print(f"   ⚠️ Pior: ${worst_day:.2f}")
                print(f"   ✅ Dias positivos: {positive_days}")
                print(f"   ❌ Dias negativos: {negative_days}")
        
        # Coluna M - CAP FINAL
        if len(df.columns) > 12:
            col_m = pd.to_numeric(df.iloc[:, 12], errors='coerce')  # 13ª coluna (M)
            cap_data = col_m.dropna()
            if len(cap_data) > 0:
                capital_final = cap_data.iloc[-1]
                capital_inicial_m = cap_data.iloc[0]
                crescimento = capital_final - capital_inicial_m
                print(f"🎯 Coluna M (CAP FINAL):")
                print(f"   💰 Final: ${capital_final:.2f}")
                print(f"   📈 Crescimento: ${crescimento:.2f}")
        
        # Coluna N - % DIA
        if len(df.columns) > 13:
            col_n = pd.to_numeric(df.iloc[:, 13], errors='coerce')  # 14ª coluna (N)
            roi_data = col_n.dropna()
            if len(roi_data) > 0:
                avg_roi = roi_data.mean()
                best_roi = roi_data.max()
                worst_roi = roi_data.min()
                total_roi = roi_data.sum()
                
                print(f"📊 Coluna N (% DIA):")
                print(f"   📈 Médio: {avg_roi:.2f}%")
                print(f"   🏆 Melhor: {best_roi:.2f}%")
                print(f"   ⚠️ Pior: {worst_roi:.2f}%")
                print(f"   🎯 Total: {total_roi:.2f}%")
        
        # Resumo executivo
        print("\n" + "=" * 60)
        print("📋 RESUMO EXECUTIVO - JUNHO 2025")
        print("=" * 60)
        
        if 'wins' in locals() and 'losses' in locals():
            print(f"🎯 Performance: {win_rate:.1f}% win rate ({wins}W/{losses}L)")
        
        if 'total_pnl' in locals():
            print(f"💰 P/L Total: ${total_pnl:.2f}")
        
        if 'capital_inicial' in locals() and 'capital_final' in locals():
            roi_total = (capital_final - capital_inicial) / capital_inicial * 100
            print(f"📈 ROI Total: {roi_total:.2f}%")
            print(f"💎 Capital: ${capital_inicial:.2f} → ${capital_final:.2f}")
        
        if 'avg_roi' in locals():
            print(f"📊 ROI Médio Diário: {avg_roi:.2f}%")
        
        # Análise de hoje (27/06)
        print(f"\n🎯 ANÁLISE DO DIA ATUAL (27/06):")
        print("-" * 40)
        
        # Procurar linha do dia 27
        if len(df.columns) > 0:
            col_a = df.iloc[:, 0]
            day_27_idx = None
            
            for idx, date_val in enumerate(col_a):
                if str(date_val).strip() == '27' or str(date_val).strip() == '27/06':
                    day_27_idx = idx
                    break
            
            if day_27_idx is not None:
                print(f"📅 Encontrado dia 27 na linha {day_27_idx + 1}")
                
                # Dados do dia 27
                if len(df.columns) > 1:
                    win_today = df.iloc[day_27_idx, 1]
                    print(f"🎯 WIN hoje: {win_today}")
                
                if len(df.columns) > 2:
                    loss_today = df.iloc[day_27_idx, 2]
                    print(f"❌ LOSS hoje: {loss_today}")
                
                if len(df.columns) > 6:
                    capital_hoje = pd.to_numeric(df.iloc[day_27_idx, 6], errors='coerce')
                    print(f"💰 Capital inicial hoje: ${capital_hoje:.2f}")
                
                if len(df.columns) > 9:
                    pnl_hoje = pd.to_numeric(df.iloc[day_27_idx, 9], errors='coerce')
                    print(f"📈 P/L hoje: ${pnl_hoje:.2f}")
                
                if len(df.columns) > 12:
                    cap_final_hoje = pd.to_numeric(df.iloc[day_27_idx, 12], errors='coerce')
                    print(f"🎯 Capital final hoje: ${cap_final_hoje:.2f}")
                
                if len(df.columns) > 13:
                    roi_hoje = pd.to_numeric(df.iloc[day_27_idx, 13], errors='coerce')
                    print(f"📊 ROI hoje: {roi_hoje:.2f}%")
            else:
                print("⚠️ Dia 27 não encontrado ou ainda não preenchido")
        
        print("\n" + "=" * 60)
        print("✅ ANÁLISE CONCLUÍDA COM SUCESSO!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_excel() 