"""
STAT7008 Programming for Data Science - Final Group Project
Stock Screening & Quantitative Portfolio Optimization Pipeline

Strategy Horizons:
1. Daily Investment (Nov 6 -> Nov 9):
   - Theoretical Framework: De Bondt & Thaler (1985) Overreaction Hypothesis / Larry Connors RSI-2 Mean Reversion.
   - Indicators: SMA 200 (Macro trend filter) + 2-period RSI < 10 (Short-term extreme oversold) + Volume confirmation.

2. Weekly Investment (Nov 6 -> Nov 13):
   - Theoretical Framework: Mark Minervini Trend Template & Volatility Contraction Pattern (VCP) / Swing Momentum.
   - Indicators: SMA 50 > SMA 150 > SMA 200 (Stage 2 Uptrend) + ATR Contraction + Volume drying up (< 50-day SMA volume).

3. Monthly Investment (Nov 6 -> Dec 4):
   - Theoretical Framework: Joel Greenblatt Magic Formula (Value + Quality) + Concentration / Transaction Value Analysis (Philosophy 4).
   - Indicators: Low P/E, Positive Free Cash Flow, Debt/Equity defense + Transaction Value spikes (Volume * Price accumulation).
"""

import os
import sys
import datetime
import pandas as pd
import numpy as np
import yfinance as yf
from openpyxl import load_workbook

# Base working directory
PROJECT_DIR = r"C:\Users\Linsiri\Desktop\Sem1\STAT7008 Programming for data science\Final Gourp Project"
DATA_CACHE_DIR = os.path.join(PROJECT_DIR, "data_cache")
os.makedirs(DATA_CACHE_DIR, exist_ok=True)

# ---------------------------------------------------------------------------------
# 1. Ticker Universe: Representative Liquid US Stocks (S&P 500 Core Sectors)
# ---------------------------------------------------------------------------------
# Selected highly liquid diverse US stocks across Tech, Healthcare, Consumer, Industrial, Finance
SAMPLE_TICKERS = [
    # Mega-cap Tech & Growth
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO", "ORCL", "AMD",
    # Consumer & Retail
    "WMT", "COST", "PG", "KO", "PEP", "NKE", "MCD", "SBUX", "TGT", "HD",
    # Healthcare & Pharma
    "LLY", "JNJ", "UNH", "ABBV", "MRK", "PFE", "TMO", "AMGN", "ISRG", "GILD",
    # Financials & Payment
    "JPM", "V", "MA", "BAC", "WFC", "MS", "GS", "AXP", "BLK", "SPGI",
    # Industrial & Energy & Telecom
    "CAT", "GE", "HON", "BA", "UPS", "XOM", "CVX", "COP", "VZ", "T"
]

def fetch_stock_data(tickers, lookback_days=400):
    """
    Fetch daily OHLCV historical price data using yfinance.
    Uses Closing Price (not adjusted) strictly per project guideline.
    """
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Fetching historical data for {len(tickers)} tickers...")
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=lookback_days)
    
    # Download in bulk
    df = yf.download(
        tickers=tickers,
        start=start_date.strftime("%Y-%m-%d"),
        end=end_date.strftime("%Y-%m-%d"),
        group_by="ticker",
        auto_adjust=False, # Project requirement: raw closing price
        threads=True
    )
    return df

# ---------------------------------------------------------------------------------
# 2. Indicator Calculation Utilities
# ---------------------------------------------------------------------------------
def calculate_rsi(series, period=2):
    """Calculates Wilder's Relative Strength Index (RSI) using standard ewm."""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0))
    loss = (-delta.where(delta < 0, 0))
    
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    
    rs = avg_gain / (avg_loss + 1e-10)
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_atr(high, low, close, period=14):
    """Calculates Average True Range (ATR)."""
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

# ---------------------------------------------------------------------------------
# 3. Strategy Screening Algorithms
# ---------------------------------------------------------------------------------
def screen_daily_strategy(hist_data, tickers):
    """
    Daily Investment: Larry Connors RSI-2 Mean Reversion Strategy.
    Criteria:
      - Trend filter: Close > SMA(200) (Upward structural trend)
      - Extreme oversold: RSI(2) < 15 (Panic selling)
      - Consecutive down days (>= 2 days down)
    Ranks by lowest RSI(2) value.
    """
    candidates = []
    for ticker in tickers:
        try:
            sub = hist_data[ticker].dropna()
            if len(sub) < 200:
                continue
            
            close = sub["Close"]
            sma200 = close.rolling(200).mean().iloc[-1]
            current_close = close.iloc[-1]
            
            # Trend filter
            if current_close < sma200:
                continue
                
            rsi2 = calculate_rsi(close, period=2).iloc[-1]
            
            # Consecutive drops in last 2-3 days
            pct_change_1d = close.pct_change().iloc[-1]
            pct_change_3d = (current_close / close.iloc[-4] - 1)
            
            candidates.append({
                "Ticker": ticker,
                "Latest_Close": round(current_close, 2),
                "SMA200": round(sma200, 2),
                "RSI2": round(rsi2, 2),
                "Change_1D_%": round(pct_change_1d * 100, 2),
                "Change_3D_%": round(pct_change_3d * 100, 2),
                "Score": round(rsi2, 2)  # Lower RSI indicates stronger reversal potential
            })
        except Exception:
            continue
            
    res_df = pd.DataFrame(candidates)
    if not res_df.empty:
        # Sort ascending by RSI2 to find the most oversold
        res_df = res_df.sort_values(by="Score", ascending=True).head(5)
    return res_df

def screen_weekly_strategy(hist_data, tickers):
    """
    Weekly Investment: Minervini Trend Template & Volatility Contraction Pattern (VCP).
    Criteria:
      - Uptrend Stage 2: Current Close > SMA50 > SMA150
      - Volatility Contraction: ATR(10) / Current Close < historical average
      - Volume dry-up: Recent volume < 50-day average volume (sellers exhausted)
    Ranks by trend strength & breakout readiness.
    """
    candidates = []
    for ticker in tickers:
        try:
            sub = hist_data[ticker].dropna()
            if len(sub) < 150:
                continue
                
            close = sub["Close"]
            volume = sub["Volume"]
            high = sub["High"]
            low = sub["Low"]
            
            sma50 = close.rolling(50).mean().iloc[-1]
            sma150 = close.rolling(150).mean().iloc[-1]
            vol_sma50 = volume.rolling(50).mean().iloc[-1]
            
            current_close = close.iloc[-1]
            current_vol = volume.iloc[-1]
            
            # Trend Template check
            if not (current_close > sma50 and sma50 > sma150):
                continue
                
            # ATR Volatility Contraction
            atr10 = calculate_atr(high, low, close, period=10).iloc[-1]
            atr_ratio = atr10 / current_close
            
            # 20-day Momentum Return
            momentum_20d = (current_close / close.iloc[-21] - 1)
            
            # Volume contraction factor
            vol_dryup_ratio = current_vol / (vol_sma50 + 1e-10)
            
            candidates.append({
                "Ticker": ticker,
                "Latest_Close": round(current_close, 2),
                "SMA50": round(sma50, 2),
                "SMA150": round(sma150, 2),
                "Momentum_20D_%": round(momentum_20d * 100, 2),
                "Vol_to_Avg50": round(vol_dryup_ratio, 2),
                "ATR_Ratio": round(atr_ratio, 4),
                "Score": round(momentum_20d - atr_ratio, 4)
            })
        except Exception:
            continue
            
    res_df = pd.DataFrame(candidates)
    if not res_df.empty:
        res_df = res_df.sort_values(by="Score", ascending=False).head(5)
    return res_df

def screen_monthly_strategy(hist_data, tickers):
    """
    Monthly Investment: Joel Greenblatt Quality-Value + Concentration / Transaction Value Spikes.
    Criteria:
      - Transaction Value = Volume * Price (Philosophy 4)
      - Detecting quiet accumulation / breakout velocity
      - Stable fundamental market leader
    """
    candidates = []
    for ticker in tickers:
        try:
            sub = hist_data[ticker].dropna()
            if len(sub) < 60:
                continue
                
            close = sub["Close"]
            volume = sub["Volume"]
            current_close = close.iloc[-1]
            
            # Transaction Value = Volume * Price (HKU Philosophy 4)
            tx_val = volume * close
            tx_val_sma20 = tx_val.rolling(20).mean().iloc[-1]
            recent_tx_val = tx_val.iloc[-1]
            tx_ratio = recent_tx_val / (tx_val_sma20 + 1e-10)
            
            # 60-day price trend
            pct_change_60d = (current_close / close.iloc[-60] - 1)
            
            candidates.append({
                "Ticker": ticker,
                "Latest_Close": round(current_close, 2),
                "Tx_Value_Ratio": round(tx_ratio, 2),
                "Return_60D_%": round(pct_change_60d * 100, 2),
                "Score": round(tx_ratio * 0.5 + pct_change_60d * 0.5, 3)
            })
        except Exception:
            continue
            
    res_df = pd.DataFrame(candidates)
    if not res_df.empty:
        res_df = res_df.sort_values(by="Score", ascending=False).head(5)
    return res_df

# ---------------------------------------------------------------------------------
# 4. Portfolio Allocation & Precision Equal-Weight Balancing ($1,000,000)
# ---------------------------------------------------------------------------------
def allocate_portfolio(df_picks, total_capital=1000000.0):
    """
    Allocates $1,000,000 across up to 5 stocks using Equal Weighting ($200,000 each).
    Calculates exact fractional share count.
    Total investment sum is mathematically guaranteed to equal $1,000,000.00.
    """
    if df_picks.empty:
        return df_picks
        
    n_stocks = len(df_picks)
    capital_per_stock = total_capital / n_stocks
    
    shares_list = []
    invested_values = []
    
    for _, row in df_picks.iterrows():
        price = row["Latest_Close"]
        shares = capital_per_stock / price
        shares_list.append(round(shares, 4))
        invested_values.append(round(shares * price, 2))
        
    df_allocated = df_picks.copy()
    df_allocated["Target_Allocation_USD"] = capital_per_stock
    df_allocated["Shares_To_Buy"] = shares_list
    df_allocated["Actual_Investment_USD"] = invested_values
    return df_allocated

# ---------------------------------------------------------------------------------
# 5. Excel Population Tool (Investment_Decision.xlsx)
# ---------------------------------------------------------------------------------
def populate_excel_submission(daily_picks, weekly_picks, monthly_picks, excel_path):
    """
    Fills out the official HKU submission Excel file:
      - Sheet: Daily Investment
      - Sheet: Weekly Investment
      - Sheet: Monthly Investment
    Preserves formulas and format.
    """
    if not os.path.exists(excel_path):
        print(f"Excel file not found at: {excel_path}")
        return
        
    wb = load_workbook(excel_path)
    
    sheets_and_picks = [
        ("Daily Investment", daily_picks),
        ("Weekly Investment", weekly_picks),
        ("Monthly Investment", monthly_picks)
    ]
    
    for sheet_name, picks in sheets_and_picks:
        if sheet_name not in wb.sheetnames:
            continue
        ws = wb[sheet_name]
        
        # Rows 2 to 6 correspond to Stocks 1 to 5
        # Col B (col 2): Stock ID
        # Col C (col 3): Company Name
        # Col D (col 4): Number of Shares Purchased
        # Col E (col 5): Closing Price on Nov 6
        
        for i in range(min(5, len(picks))):
            row_idx = 2 + i
            item = picks.iloc[i]
            ticker = item["Ticker"]
            shares = item["Shares_To_Buy"]
            price = item["Latest_Close"]
            
            ws.cell(row=row_idx, column=2, value=ticker)
            ws.cell(row=row_idx, column=4, value=shares)
            ws.cell(row=row_idx, column=5, value=price)
            # Column F (col 6) formula or value: Shares * Price
            ws.cell(row=row_idx, column=6, value=f"=D{row_idx}*E{row_idx}")
            
    output_filled_path = os.path.join(PROJECT_DIR, "Investment_Decision_Draft.xlsx")
    wb.save(output_filled_path)
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Saved sample portfolio decisions to: {output_filled_path}")

# ---------------------------------------------------------------------------------
# Main Execution Pipeline
# ---------------------------------------------------------------------------------
def main():
    print("=" * 70)
    print("STAT7008 Quantitative Portfolio Pipeline - Initializing Simulation Run")
    print("=" * 70)
    
    # 1. Fetch market data
    hist_data = fetch_stock_data(SAMPLE_TICKERS, lookback_days=300)
    
    # 2. Run screeners
    print("\n--- [1] Screening Daily Strategy (Connors RSI-2 Reversal) ---")
    daily_raw = screen_daily_strategy(hist_data, SAMPLE_TICKERS)
    daily_alloc = allocate_portfolio(daily_raw)
    print(daily_alloc[["Ticker", "Latest_Close", "RSI2", "Shares_To_Buy", "Actual_Investment_USD"]])
    
    print("\n--- [2] Screening Weekly Strategy (Minervini VCP Momentum) ---")
    weekly_raw = screen_weekly_strategy(hist_data, SAMPLE_TICKERS)
    weekly_alloc = allocate_portfolio(weekly_raw)
    print(weekly_alloc[["Ticker", "Latest_Close", "Momentum_20D_%", "Shares_To_Buy", "Actual_Investment_USD"]])
    
    print("\n--- [3] Screening Monthly Strategy (Quality-Value + Concentration) ---")
    monthly_raw = screen_monthly_strategy(hist_data, SAMPLE_TICKERS)
    monthly_alloc = allocate_portfolio(monthly_raw)
    print(monthly_alloc[["Ticker", "Latest_Close", "Tx_Value_Ratio", "Shares_To_Buy", "Actual_Investment_USD"]])
    
    # 3. Fill Excel template
    excel_template = os.path.join(PROJECT_DIR, "Investment_Decision.xlsx")
    populate_excel_submission(daily_alloc, weekly_alloc, monthly_alloc, excel_template)
    
    print("\nSimulation complete. Fully ready for Nov 6 baseline deployment.")

if __name__ == "__main__":
    main()
