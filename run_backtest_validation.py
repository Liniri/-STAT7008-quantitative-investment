"""
STAT7008 Programming for Data Science - Final Group Project
Quantitative Backtesting & Rolling Validation Engine

Aligns with:
- Philosophy 3: Slide 15-22 (Fixed, Recursive, Rolling Validation Schemes)
- Philosophy 4: Slide 16 (Backtesting vs. Forward-testing)
- Performance Metrics: Cumulative Return, Annualized Sharpe Ratio, Max Drawdown, Win Rate
"""

import os
import sys
import datetime
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt

PROJECT_DIR = r"C:\Users\Linsiri\Desktop\Sem1\STAT7008 Programming for data science\Final Gourp Project"
CHART_DIR = os.path.join(PROJECT_DIR, "backtest_charts")
os.makedirs(CHART_DIR, exist_ok=True)

# Select a liquid cross-sector subset of US stocks for high-speed backtest
TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO", "AMD",
    "WMT", "COST", "PG", "KO", "PEP", "NKE", "MCD", "HD",
    "LLY", "JNJ", "UNH", "ABBV", "MRK", "PFE", "TMO",
    "JPM", "V", "MA", "BAC", "WFC", "MS", "GS", "AXP",
    "CAT", "GE", "HON", "BA", "XOM", "CVX", "VZ", "T"
]

def load_data(start_date="2022-01-01", end_date="2026-10-09"):
    """Fetch raw closing price and volume for the tickers and S&P 500 benchmark."""
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Downloading historical data from {start_date} to {end_date}...")
    tickers_with_bench = TICKERS + ["SPY"]
    df = yf.download(
        tickers=tickers_with_bench,
        start=start_date,
        end=end_date,
        group_by="ticker",
        auto_adjust=False,
        threads=True
    )
    return df

def calculate_rsi(series, period=2):
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    rs = avg_gain / (avg_loss + 1e-10)
    return 100 - (100 / (1 + rs))

# ---------------------------------------------------------------------------------
# Rolling Backtest Framework
# ---------------------------------------------------------------------------------
def run_rolling_backtest(df, split_date="2024-01-01", holding_days=5):
    """
    Simulates a Rolling Scheme investment strategy:
    - Every holding_days (e.g. 5 days for weekly, 1 day for daily, 20 days for monthly):
      1. Ranks stocks based on the chosen strategy indicator using past data up to time t
      2. Buys top 5 stocks equally ($200k each)
      3. Holds until t + holding_days and calculates realized return
    """
    # Extract Close and Volume matrices
    close_dict = {}
    vol_dict = {}
    for t in TICKERS:
        try:
            close_dict[t] = df[t]["Close"]
            vol_dict[t] = df[t]["Volume"]
        except Exception:
            continue
            
    close_df = pd.DataFrame(close_dict).dropna(how="all")
    vol_df = pd.DataFrame(vol_dict).reindex(close_df.index)
    spy_close = df["SPY"]["Close"].reindex(close_df.index).dropna()

    # Align dates
    common_dates = close_df.index.intersection(spy_close.index)
    close_df = close_df.loc[common_dates]
    vol_df = vol_df.loc[common_dates]
    spy_close = spy_close.loc[common_dates]

    # Filter for validation period (Post split_date)
    val_dates = [d for d in common_dates if d >= pd.to_datetime(split_date)]
    trade_indices = list(range(0, len(val_dates) - holding_days, holding_days))
    
    # Tracking performance series
    dates_record = []
    strat_reversal_returns = []
    strat_momentum_returns = []
    strat_concentration_returns = []
    benchmark_returns = []

    for idx in trade_indices:
        t_date = val_dates[idx]
        t_future = val_dates[idx + holding_days]
        
        # S&P 500 benchmark return
        bench_ret = (spy_close.loc[t_future] / spy_close.loc[t_date]) - 1.0
        benchmark_returns.append(bench_ret)
        dates_record.append(t_future)

        # Slice historical data up to t_date (Rolling information window)
        sub_close = close_df.loc[:t_date]
        sub_vol = vol_df.loc[:t_date]

        # --- Strategy 1: Short-term Reversal (Connors RSI-2) ---
        rsi_scores = {}
        for t in TICKERS:
            if t in sub_close and len(sub_close[t].dropna()) >= 200:
                c = sub_close[t].dropna()
                if c.iloc[-1] > c.rolling(200).mean().iloc[-1]: # Trend filter
                    rsi_scores[t] = calculate_rsi(c, period=2).iloc[-1]
        
        if rsi_scores:
            top_reversal = sorted(rsi_scores.items(), key=lambda x: x[1])[:5]
            rev_tickers = [x[0] for x in top_reversal]
            # Realized future return of these 5 stocks
            ret_rev = np.mean([
                (close_df[t].loc[t_future] / close_df[t].loc[t_date]) - 1.0
                for t in rev_tickers if t in close_df
            ])
        else:
            ret_rev = bench_ret
        strat_reversal_returns.append(ret_rev)

        # --- Strategy 2: Weekly Momentum (Minervini Stage 2 / 20D Return) ---
        mom_scores = {}
        for t in TICKERS:
            if t in sub_close and len(sub_close[t].dropna()) >= 60:
                c = sub_close[t].dropna()
                # 20-day momentum
                mom_scores[t] = (c.iloc[-1] / c.iloc[-21]) - 1.0
                
        if mom_scores:
            top_mom = sorted(mom_scores.items(), key=lambda x: x[1], reverse=True)[:5]
            mom_tickers = [x[0] for x in top_mom]
            ret_mom = np.mean([
                (close_df[t].loc[t_future] / close_df[t].loc[t_date]) - 1.0
                for t in mom_tickers if t in close_df
            ])
        else:
            ret_mom = bench_ret
        strat_momentum_returns.append(ret_mom)

        # --- Strategy 3: Concentration / Transaction Value Spikes (Philosophy 4) ---
        conc_scores = {}
        for t in TICKERS:
            if t in sub_close and t in sub_vol and len(sub_close[t].dropna()) >= 40:
                c = sub_close[t].dropna()
                v = sub_vol[t].dropna().reindex(c.index)
                tx_val = c * v
                tx_ratio = tx_val.iloc[-1] / (tx_val.rolling(20).mean().iloc[-1] + 1e-10)
                conc_scores[t] = tx_ratio
                
        if conc_scores:
            top_conc = sorted(conc_scores.items(), key=lambda x: x[1], reverse=True)[:5]
            conc_tickers = [x[0] for x in top_conc]
            ret_conc = np.mean([
                (close_df[t].loc[t_future] / close_df[t].loc[t_date]) - 1.0
                for t in conc_tickers if t in close_df
            ])
        else:
            ret_conc = bench_ret
        strat_concentration_returns.append(ret_conc)

    # Compile Results
    results_df = pd.DataFrame({
        "Date": dates_record,
        "Benchmark_SPY": benchmark_returns,
        "Strat_Reversal": strat_reversal_returns,
        "Strat_Momentum": strat_momentum_returns,
        "Strat_Concentration": strat_concentration_returns
    }).set_index("Date")

    return results_df

# ---------------------------------------------------------------------------------
# Performance Metric Calculation
# ---------------------------------------------------------------------------------
def evaluate_metrics(results_df, periods_per_year=52):
    """Calculates Total Return, Annualized Return, Sharpe Ratio, Max Drawdown, Win Rate."""
    metrics = []
    for col in results_df.columns:
        ret_series = results_df[col]
        cum_ret = (1 + ret_series).cumprod()
        total_return = (cum_ret.iloc[-1] - 1) * 100
        
        # Annualized metrics
        ann_return = ((1 + total_return/100) ** (periods_per_year / len(ret_series)) - 1) * 100
        ann_vol = ret_series.std() * np.sqrt(periods_per_year) * 100
        sharpe = (ann_return - 3.5) / (ann_vol + 1e-10) # Assuming 3.5% risk-free rate
        
        # Max Drawdown
        running_max = cum_ret.cummax()
        drawdown = (cum_ret - running_max) / running_max
        max_dd = drawdown.min() * 100
        
        # Win Rate
        win_rate = (ret_series > 0).mean() * 100
        
        metrics.append({
            "Strategy": col,
            "Total_Return_%": round(total_return, 2),
            "Ann_Return_%": round(ann_return, 2),
            "Sharpe_Ratio": round(sharpe, 2),
            "Max_Drawdown_%": round(max_dd, 2),
            "Win_Rate_%": round(win_rate, 2)
        })
    return pd.DataFrame(metrics)

# ---------------------------------------------------------------------------------
# Plot & Save Report Chart
# ---------------------------------------------------------------------------------
def plot_cumulative_performance(results_df, title, filename):
    cum_returns = (1 + results_df).cumprod()
    
    plt.figure(figsize=(12, 6))
    plt.plot(cum_returns.index, cum_returns["Benchmark_SPY"], label="Benchmark (S&P 500)", color="gray", linestyle="--", linewidth=1.5)
    plt.plot(cum_returns.index, cum_returns["Strat_Reversal"], label="Strategy: RSI-2 Reversal (Daily/Short-term)", color="orange", linewidth=2)
    plt.plot(cum_returns.index, cum_returns["Strat_Momentum"], label="Strategy: VCP Momentum (Weekly Swing)", color="blue", linewidth=2)
    plt.plot(cum_returns.index, cum_returns["Strat_Concentration"], label="Strategy: Transaction Value (Philosophy 4)", color="green", linewidth=2)
    
    plt.title(title, fontsize=14, fontweight="bold")
    plt.xlabel("Validation Date (Rolling Scheme)", fontsize=12)
    plt.ylabel("Cumulative Growth of $1.00", fontsize=12)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(fontsize=11, loc="upper left")
    plt.tight_layout()
    
    chart_path = os.path.join(CHART_DIR, filename)
    plt.savefig(chart_path, dpi=300)
    plt.close()
    print(f"Chart saved to: {chart_path}")

# ---------------------------------------------------------------------------------
# Main Backtest Run
# ---------------------------------------------------------------------------------
def main():
    print("=" * 70)
    print("STAT7008 Backtesting & Rolling Validation Engine")
    print("Training Period: 2022-01-01 to 2023-12-31")
    print("Validation Period (Rolling): 2024-01-01 to Present")
    print("=" * 70)

    # 1. Load Data
    df = load_data(start_date="2022-01-01", end_date="2026-10-09")

    # 2. Backtest Weekly Horizon (Holding = 5 days)
    print("\n--- Running Rolling Backtest for Weekly Horizon (5-Day Holding Period) ---")
    weekly_results = run_rolling_backtest(df, split_date="2024-01-01", holding_days=5)
    weekly_metrics = evaluate_metrics(weekly_results, periods_per_year=52)
    print("\n[Weekly Horizon Performance Summary]")
    print(weekly_metrics.to_string(index=False))
    plot_cumulative_performance(weekly_results, "Rolling Validation Performance - Weekly Horizon (2024-2026)", "weekly_rolling_backtest.png")

    # 3. Backtest Monthly Horizon (Holding = 20 days)
    print("\n--- Running Rolling Backtest for Monthly Horizon (20-Day Holding Period) ---")
    monthly_results = run_rolling_backtest(df, split_date="2024-01-01", holding_days=20)
    monthly_metrics = evaluate_metrics(monthly_results, periods_per_year=12)
    print("\n[Monthly Horizon Performance Summary]")
    print(monthly_metrics.to_string(index=False))
    plot_cumulative_performance(monthly_results, "Rolling Validation Performance - Monthly Horizon (2024-2026)", "monthly_rolling_backtest.png")

    # Save summary table to CSV
    summary_path = os.path.join(PROJECT_DIR, "Backtest_Performance_Summary.csv")
    pd.concat([
        weekly_metrics.assign(Horizon="Weekly (5D)"),
        monthly_metrics.assign(Horizon="Monthly (20D)")
    ]).to_csv(summary_path, index=False)
    print(f"\nAll metrics successfully saved to: {summary_path}")

if __name__ == "__main__":
    main()
