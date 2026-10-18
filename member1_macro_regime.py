"""
STAT7008 Programming for Data Science - Final Group Project
Member 1 Module: Macroeconomic Regime & Market State Switch (宏观因子与状态开关)

Focus:
1. Macro Trend: S&P 500 relative to 200-day Moving Average (Bullish vs Bearish Regime)
2. Interest Rate & Liquidity Proxy: 10-Year US Treasury Yield (^TNX) Sensitivity
3. Market Fear & Volatility Index: VIX Volatility Index (^VIX) Stress Level
4. Post-Election Dynamic Switch: Determines Risk-On (High Beta) vs Risk-Off (Defensive)
"""

import os
import datetime
import pandas as pd
import numpy as np
import yfinance as yf

PROJECT_DIR = r"C:\Users\Linsiri\Desktop\Sem1\STAT7008 Programming for data science\Final Gourp Project"

def analyze_macro_regime():
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Member 1: Fetching Macroeconomic Indicators (SPY, VIX, TNX)...")
    
    macro_tickers = ["SPY", "^VIX", "^TNX"]
    df = yf.download(macro_tickers, period="1y", auto_adjust=False)
    
    close_spy = df["Close"]["SPY"].dropna()
    close_vix = df["Close"]["^VIX"].dropna()
    close_tnx = df["Close"]["^TNX"].dropna()
    
    current_spy = close_spy.iloc[-1]
    spy_sma200 = close_spy.rolling(200).mean().iloc[-1]
    spy_regime = "BULLISH (牛市多头)" if current_spy > spy_sma200 else "BEARISH (熊市防守)"
    
    current_vix = close_vix.iloc[-1]
    vix_stress = "LOW VOLATILITY / RISK-ON (适宜进攻)" if current_vix < 20 else ("ELEVATED RISK (中度避险)" if current_vix < 28 else "EXTREME PANIC (极度恐慌)")
    
    current_tnx = close_tnx.iloc[-1]
    
    report = {
        "Analysis_Date": datetime.date.today().strftime("%Y-%m-%d"),
        "SP500_Close": round(current_spy, 2),
        "SP500_SMA200": round(spy_sma200, 2),
        "Market_Regime": spy_regime,
        "VIX_Level": round(current_vix, 2),
        "VIX_Sentiment": vix_stress,
        "US_10Y_Treasury_Yield_%": round(current_tnx, 2),
        "Recommended_Action": "Deploy High-Beta & Growth Momentum in Active Stocks" if (current_spy > spy_sma200 and current_vix < 25) else "Deploy Low-Beta Defensive Value"
    }
    
    df_macro = pd.DataFrame([report])
    out_csv = os.path.join(PROJECT_DIR, "Member1_Macro_Regime_Analysis.csv")
    df_macro.to_csv(out_csv, index=False)
    print(f"Member 1 macro report saved to: {out_csv}")
    return df_macro

if __name__ == "__main__":
    res = analyze_macro_regime()
    print("\n--- Member 1 Macro Diagnostic Output ---")
    print(res.to_string(index=False))
