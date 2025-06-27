#!/usr/bin/env python3
"""
Análise CORRIGIDA do Excel - Foco na linha 32 com fórmulas
"""

import pandas as pd
import numpy as np

def analyze_excel_corrected():
    print("📊 ANÁLISE CORRIGIDA - JUNHO 2025")
    print("=" * 60)
    
    try:
        # Carregar dados
        df = pd.read_excel('excel/Meta diária - Felipe.xlsx', sheet_name='JUNHO, 25')
        
        print("🔍 DADOS DA LINHA 32 (FÓRMULAS/TOTAIS):")
        print("-" * 50)
        
        # Linha 32 (índice 31) - Fórmulas
        if len(df) > 31:
            linha_32 = df.iloc[31]
            
            print(f"📅 Data (A32): {linha_32.iloc[0]}")
            print(f"🎯 Total WIN (B32): {linha_32.iloc[1]}")
            print(f"❌ Total LOSS (C32): {linha_32.iloc[2]}")
            print(f"💰 Total P/L Mês (J32): {linha_32.iloc[9]}")
            print(f"📊 Média por dia (N32): {linha_32.iloc[13]}")
            
            # Linha 33 (índice 32) - Resultado % do mês
            if len(df) > 32:
                linha_33 = df.iloc[32]
                resultado_mes = linha_33.iloc[13]
                print(f"📈 Resultado % Mês (N33): {resultado_mes}")
        
        print("\n🔍 ANÁLISE CORRIGIDA DOS DADOS INDIVIDUAIS:")
        print("-" * 50)
        
        # Analisar apenas os dias (linhas 0-30, excluindo totais)
        dados_dias = df.iloc[:31]  # Primeiras 31 linhas (dias 1-31)
        
        # Colunas importantes
        col_b = dados_dias.iloc[:, 1]  # WIN
        col_c = dados_dias.iloc[:, 2]  # LOSS
        col_j = pd.to_numeric(dados_dias.iloc[:, 9], errors='coerce')  # P/L DIA
        col_n = pd.to_numeric(dados_dias.iloc[:, 13], errors='coerce')  # % DIA
        
        # Contar wins e losses
        wins = (col_b == 'O').sum()
        losses = (col_c == 'X').sum()
        total_days = wins + losses
        
        print(f"🎯 Wins individuais: {wins}")
        print(f"❌ Losses individuais: {losses}")
        
        if total_days > 0:
            win_rate = wins / total_days * 100
            print(f"📊 Win Rate Real: {win_rate:.1f}% ({wins}W/{losses}L)")
        
        # P/L por dia (apenas dados válidos)
        pnl_validos = col_j.dropna()
        pnl_dias = pnl_validos[pnl_validos != 0]  # Excluir zeros
        
        if len(pnl_dias) > 0:
            total_pnl = pnl_dias.sum()
            media_pnl = pnl_dias.mean()
            melhor_dia = pnl_dias.max()
            pior_dia = pnl_dias.min()
            dias_positivos = (pnl_dias > 0).sum()
            dias_negativos = (pnl_dias < 0).sum()
            
            print(f"\n💰 P/L INDIVIDUAL POR DIA:")
            print(f"   📊 Total Real: ${total_pnl:.2f}")
            print(f"   📈 Média por dia: ${media_pnl:.2f}")
            print(f"   🏆 Melhor dia: ${melhor_dia:.2f}")
            print(f"   ⚠️ Pior dia: ${pior_dia:.2f}")
            print(f"   ✅ Dias positivos: {dias_positivos}")
            print(f"   ❌ Dias negativos: {dias_negativos}")
        
        # % por dia
        roi_validos = col_n.dropna()
        roi_dias = roi_validos[roi_validos != 0]
        
        if len(roi_dias) > 0:
            roi_total = roi_dias.sum()
            roi_medio = roi_dias.mean()
            melhor_roi = roi_dias.max()
            pior_roi = roi_dias.min()
            
            print(f"\n📈 ROI INDIVIDUAL POR DIA:")
            print(f"   🎯 Total: {roi_total:.4f}")
            print(f"   📊 Médio: {roi_medio:.4f}")
            print(f"   🏆 Melhor: {melhor_roi:.4f}")
            print(f"   ⚠️ Pior: {pior_roi:.4f}")
        
        print("\n" + "=" * 60)
        print("📋 RESUMO EXECUTIVO CORRIGIDO")
        print("=" * 60)
        
        if 'win_rate' in locals():
            print(f"🎯 Performance: {win_rate:.1f}% win rate ({wins}W/{losses}L)")
        
        if 'total_pnl' in locals():
            print(f"💰 P/L Total: ${total_pnl:.2f}")
            print(f"📊 P/L Médio Diário: ${media_pnl:.2f}")
        
        if 'roi_total' in locals():
            print(f"📈 ROI Total Mês: {roi_total:.2f}%")
            print(f"📊 ROI Médio Diário: {roi_medio:.4f}%")
        
        # Comparação com dados da linha 32
        print(f"\n🔍 COMPARAÇÃO COM FÓRMULAS (LINHA 32):")
        print("-" * 40)
        if len(df) > 31:
            formula_pnl = df.iloc[31, 9]  # J32
            formula_media = df.iloc[31, 13]  # N32
            
            print(f"💰 Fórmula P/L (J32): {formula_pnl}")
            print(f"📊 Fórmula Média (N32): {formula_media}")
            
            if len(df) > 32:
                formula_roi_mes = df.iloc[32, 13]  # N33
                print(f"📈 Fórmula ROI Mês (N33): {formula_roi_mes}")
        
        # Análise do dia atual (27/06)
        print(f"\n🎯 ANÁLISE DO DIA 27/06:")
        print("-" * 30)
        
        # Procurar dia 27
        col_a = df.iloc[:, 0]
        day_27_found = False
        
        for idx, date_val in enumerate(col_a):
            if pd.isna(date_val):
                continue
            
            # Verificar se é datetime ou string
            if hasattr(date_val, 'day'):
                if date_val.day == 27:
                    day_27_found = True
                    print(f"📅 Dia 27 encontrado na linha {idx + 1}")
                    
                    # Dados do dia 27
                    win_27 = df.iloc[idx, 1] if idx < len(df) else None
                    loss_27 = df.iloc[idx, 2] if idx < len(df) else None
                    pnl_27 = pd.to_numeric(df.iloc[idx, 9], errors='coerce') if idx < len(df) else None
                    roi_27 = pd.to_numeric(df.iloc[idx, 13], errors='coerce') if idx < len(df) else None
                    
                    print(f"🎯 WIN hoje: {win_27}")
                    print(f"❌ LOSS hoje: {loss_27}")
                    print(f"💰 P/L hoje: ${pnl_27:.2f}" if pd.notna(pnl_27) else "💰 P/L hoje: Não preenchido")
                    print(f"📊 ROI hoje: {roi_27:.4f}%" if pd.notna(roi_27) else "📊 ROI hoje: Não preenchido")
                    break
        
        if not day_27_found:
            print("⚠️ Dia 27 não encontrado ou não preenchido ainda")
            print("💡 Seus $7.80 hoje representam ~1.42% - excelente resultado!")
        
        print("\n" + "=" * 60)
        print("✅ ANÁLISE CORRIGIDA CONCLUÍDA!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_excel_corrected() 