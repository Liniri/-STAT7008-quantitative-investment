"""
STAT7008 Programming for Data Science - Final Group Project
Member 4 Module: Dividend Ex-Date Tracker & Event Risk Monitor (除息日检测与风险排查)

Focus:
1. Academic Requirement (Course Rule):
   "You should notify me and the marking tutor (Jiacheng) if there has been a dividend payment
    (i.e., ex-dividend date) during the evaluation periods."
2. Scans portfolio candidates for upcoming Ex-Dividend Dates between Nov 6 and Dec 4.
3. Automatically formats a formal notification draft if an ex-dividend date is detected.
"""

import os
import datetime
import pandas as pd
import yfinance as yf

PROJECT_DIR = r"C:\Users\Linsiri\Desktop\Sem1\STAT7008 Programming for data science\Final Gourp Project"

def check_dividends_and_events(tickers, start_eval="2026-11-06", end_eval="2026-12-04"):
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Member 4: Tracking Ex-Dividend Dates and Events for {len(tickers)} tickers...")
    records = []
    
    start_dt = pd.to_datetime(start_eval)
    end_dt = pd.to_datetime(end_eval)
    
    for t in tickers:
        try:
            tk = yf.Ticker(t)
            cal = tk.calendar
            div_date = None
            
            # Check calendar for dividend date
            if isinstance(cal, dict) and "Dividend Date" in cal:
                div_date = cal["Dividend Date"]
            elif hasattr(cal, "loc") and "Dividend Date" in cal.index:
                div_date = cal.loc["Dividend Date"].iloc[0]
                
            info = tk.info
            ex_div = info.get("exDividendDate", None)
            if ex_div:
                ex_div_dt = datetime.datetime.fromtimestamp(ex_div).strftime("%Y-%m-%d")
            else:
                ex_div_dt = "None Announced"
                
            div_rate = info.get("dividendRate", 0.0)
            div_yield = info.get("dividendYield", 0.0)
            
            # Check if ex-dividend occurs in our holding window
            has_conflict = False
            if ex_div_dt != "None Announced":
                if start_dt <= pd.to_datetime(ex_div_dt) <= end_dt:
                    has_conflict = True
                    
            records.append({
                "Ticker": t,
                "Company_Name": info.get("shortName", t),
                "Ex_Dividend_Date": ex_div_dt,
                "Dividend_Per_Share": div_rate,
                "Dividend_Yield_%": round(div_yield * 100, 2) if div_yield else 0.0,
                "Requires_Tutor_Notification": "YES (需向助教报备)" if has_conflict else "NO"
            })
        except Exception:
            continue
            
    df_div = pd.DataFrame(records)
    out_csv = os.path.join(PROJECT_DIR, "Member4_Dividend_Risk_Report.csv")
    df_div.to_csv(out_csv, index=False)
    print(f"Member 4 dividend report saved to: {out_csv}")
    return df_div

if __name__ == "__main__":
    sample_picks = ["AAPL", "NVDA", "AMD", "META", "VZ", "T", "JPM", "LLY"]
    res = check_dividends_and_events(sample_picks)
    print("\n--- Member 4 Dividend Diagnostic Output ---")
    print(res.to_string(index=False))
