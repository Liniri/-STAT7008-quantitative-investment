"""
STAT7008 Programming for Data Science - Final Group Project
Fundamental Operational Health & Quality Diagnostic Module

Aligns with:
- Philosophy 2: Value Investing Principles (Strong earnings, low debt, strong cash flow)
- Operational Health Metrics:
  1. Operating Quality: Return on Equity (ROE) & Operating Margin
  2. Financial Solvency: Debt-to-Equity Ratio & Current Ratio
  3. Real Earnings (No Fake Accounting): Free Cash Flow (FCF) > 0
  4. Growth Sustainability: Quarterly Revenue Growth YoY > 0%
"""

import os
import datetime
import pandas as pd
import numpy as np
import yfinance as yf

PROJECT_DIR = r"C:\Users\Linsiri\Desktop\Sem1\STAT7008 Programming for data science\Final Gourp Project"

# Universe for fundamental diagnostic
TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO", "AMD", "ORCL",
    "CAT", "GE", "BA", "HON", "DE", "URI", "ETN", "XOM", "CVX", "SLB",
    "JPM", "GS", "MS", "V", "MA", "AXP", "BLK", "COIN",
    "LLY", "UNH", "ISRG", "VRTX", "MRK", "COST", "HD", "TGT", "NKE", "SBUX"
]

def analyze_operational_health(tickers):
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Fetching fundamental operational metrics via yfinance...")
    records = []
    
    for t in tickers:
        try:
            tk = yf.Ticker(t)
            info = tk.info
            
            # 1. Solvency & Debt
            debt_to_equity = info.get("debtToEquity", None)
            if debt_to_equity is not None:
                debt_to_equity = debt_to_equity / 100.0 # Convert percentage to ratio
                
            # 2. Profitability & Moat
            roe = info.get("returnOnEquity", None)
            op_margin = info.get("operatingMargins", None)
            
            # 3. Cash Flow Quality (Real Cash, Not Accounting Gimmicks)
            fcf = info.get("freeCashflow", None)
            market_cap = info.get("marketCap", None)
            fcf_yield = (fcf / market_cap * 100) if (fcf and market_cap) else None
            
            # 4. Growth
            rev_growth = info.get("revenueGrowth", None)
            pe_ratio = info.get("trailingPE", None)
            
            # 5. Composite Health Score (0 - 100)
            score = 50.0 # Baseline
            
            # FCF bonus/penalty
            if fcf and fcf > 0:
                score += 15.0
                if fcf_yield and fcf_yield > 3.0:
                    score += 5.0
            else:
                score -= 20.0
                
            # Profitability bonus
            if roe and roe > 0.15:
                score += 15.0
            if op_margin and op_margin > 0.15:
                score += 10.0
                
            # Debt safety
            if debt_to_equity is not None:
                if debt_to_equity < 1.0:
                    score += 10.0
                elif debt_to_equity > 2.5:
                    score -= 15.0
                    
            # Growth bonus
            if rev_growth and rev_growth > 0:
                score += 10.0
                
            score = max(0.0, min(100.0, score))
            
            # Classification
            if score >= 75:
                rating = "Tier 1: Excellent (高质量强劲)"
            elif score >= 55:
                rating = "Tier 2: Moderate (良好稳健)"
            else:
                rating = "Tier 3: Weak / Warning (较弱需警惕)"

            records.append({
                "Ticker": t,
                "Company_Name": info.get("shortName", t),
                "Health_Score": round(score, 1),
                "Rating": rating,
                "ROE_%": round(roe * 100, 2) if roe else None,
                "Op_Margin_%": round(op_margin * 100, 2) if op_margin else None,
                "Debt_to_Equity": round(debt_to_equity, 2) if debt_to_equity else None,
                "FCF_Yield_%": round(fcf_yield, 2) if fcf_yield else None,
                "Rev_Growth_%": round(rev_growth * 100, 2) if rev_growth else None,
                "P/E": round(pe_ratio, 2) if pe_ratio else None
            })
        except Exception as e:
            continue
            
    df = pd.DataFrame(records)
    df = df.sort_values(by="Health_Score", ascending=False)
    return df

def main():
    print("=" * 70)
    print("STAT7008 Fundamental Health & Operational Quality Diagnostic")
    print("=" * 70)
    
    df_health = analyze_operational_health(TICKERS)
    
    print("\n--- Top 10 Best Operated Companies (Top Health Scores) ---")
    print(df_health[["Ticker", "Health_Score", "Rating", "ROE_%", "Op_Margin_%", "Debt_to_Equity", "FCF_Yield_%"]].head(10).to_string(index=False))
    
    print("\n--- Bottom Companies (High Debt / Cash Drain / Negative FCF) ---")
    print(df_health[["Ticker", "Health_Score", "Rating", "ROE_%", "Debt_to_Equity", "FCF_Yield_%"]].tail(5).to_string(index=False))
    
    out_csv = os.path.join(PROJECT_DIR, "Fundamental_Operational_Health.csv")
    df_health.to_csv(out_csv, index=False)
    print(f"\nFundamental diagnostic completed. Saved to: {out_csv}")

if __name__ == "__main__":
    main()
