"""
STAT7008 Programming for Data Science - Final Group Project
Daily Investment Horizon: Late-Day Accumulation Strategy (尾盘抢筹策略)

Testing Framework:
- Trading Pairs: Friday Close (Entry) -> Monday Close (Exit) across 2022-2026
- Core Indicators for Late-Day Accumulation (尾盘抢筹):
  1. Close-to-High Ratio: (Close - Low) / (High - Low) >= 0.85 (Strong buying into the close)
  2. Relative Volume Spike (RVOL): Volume >= 1.2 * SMA(Volume, 10) (Institutional buying footprint)
  3. Positive Daily Return: Close > Open (Confirmed green day)
  4. Macro Filter: Price > SMA(200) (Bullish regime)
"""

import os
import datetime
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt

PROJECT_DIR = r"C:\Users\Linsiri\Desktop\Sem1\STAT7008 Programming for data science\Final Gourp Project"
CHART_DIR = os.path.join(PROJECT_DIR, "backtest_charts")
os.makedirs(CHART_DIR, exist_ok=True)

TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO", "AMD", "ORCL",
    "WMT", "COST", "PG", "KO", "PEP", "NKE", "MCD", "HD", "TGT", "SBUX",
    "LLY", "JNJ", "UNH", "ABBV", "MRK", "PFE", "TMO", "AMGN", "ISRG", "GILD",
    "JPM", "V", "MA", "BAC", "WFC", "MS", "GS", "AXP", "BLK", "SPGI",
    "CAT", "GE", "HON", "BA", "XOM", "CVX", "COP", "VZ", "T", "UPS"
]

def load_data():
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Downloading OHLCV data for 50 tickers + SPY...")
    tickers_all = TICKERS + ["SPY"]
    df = yf.download(
        tickers=tickers_all,
        start="2022-01-01",
        end="2026-10-09",
        group_by="ticker",
        auto_adjust=False,
        threads=True
    )
    return df

def test_daily_weekend_strategies(df):
    """
    Evaluates Friday-to-Monday performance for:
    1. Benchmark (SPY hold over weekend)
    2. Late-Day Accumulation (尾盘抢筹)
    3. Connors RSI-2 Oversold Reversal (超跌反转)
    """
    # Build aligned dictionaries
    open_dict, high_dict, low_dict, close_dict, vol_dict = {}, {}, {}, {}, {}
    for t in TICKERS:
        try:
            sub = df[t].dropna()
            open_dict[t] = sub["Open"]
            high_dict[t] = sub["High"]
            low_dict[t] = sub["Low"]
            close_dict[t] = sub["Close"]
            vol_dict[t] = sub["Volume"]
        except Exception:
            continue
            
    close_df = pd.DataFrame(close_dict).dropna(how="all")
    open_df = pd.DataFrame(open_dict).reindex(close_df.index)
    high_df = pd.DataFrame(high_dict).reindex(close_df.index)
    low_df = pd.DataFrame(low_dict).reindex(close_df.index)
    vol_df = pd.DataFrame(vol_dict).reindex(close_df.index)
    spy_close = df["SPY"]["Close"].reindex(close_df.index).dropna()

    common_dates = close_df.index.intersection(spy_close.index)
    close_df = close_df.loc[common_dates]
    open_df = open_df.loc[common_dates]
    high_df = high_df.loc[common_dates]
    low_df = low_df.loc[common_dates]
    vol_df = vol_df.loc[common_dates]
    spy_close = spy_close.loc[common_dates]

    # Identify Friday to Monday pairs (dayofweek: 4 is Friday, 0 is Monday)
    weekend_pairs = []
    for i in range(len(common_dates) - 1):
        d_fri = common_dates[i]
        d_mon = common_dates[i + 1]
        # Check if Friday (4) and next available session is within 1 to 4 days (handling holidays)
        if d_fri.dayofweek == 4 and 1 <= (d_mon - d_fri).days <= 4:
            weekend_pairs.append((d_fri, d_mon))

    print(f"Total Friday -> Monday testing periods identified: {len(weekend_pairs)}")

    dates_record = []
    bench_returns = []
    accum_returns = []
    reversal_returns = []

    for d_fri, d_mon in weekend_pairs:
        # Benchmark return
        r_spy = (spy_close.loc[d_mon] / spy_close.loc[d_fri]) - 1.0
        bench_returns.append(r_spy)
        dates_record.append(d_mon)

        sub_close = close_df.loc[:d_fri]
        sub_open = open_df.loc[:d_fri]
        sub_high = high_df.loc[:d_fri]
        sub_low = low_df.loc[:d_fri]
        sub_vol = vol_df.loc[:d_fri]

        # -------------------------------------------------------------
        # Strategy A: Late-Day Accumulation (尾盘抢筹)
        # -------------------------------------------------------------
        accum_scores = {}
        for t in TICKERS:
            if t in sub_close and len(sub_close[t].dropna()) >= 200:
                c_ser = sub_close[t].dropna()
                o_ser = sub_open[t].dropna().reindex(c_ser.index)
                h_ser = sub_high[t].dropna().reindex(c_ser.index)
                l_ser = sub_low[t].dropna().reindex(c_ser.index)
                v_ser = sub_vol[t].dropna().reindex(c_ser.index)

                c = c_ser.iloc[-1]
                o = o_ser.iloc[-1]
                h = h_ser.iloc[-1]
                l = l_ser.iloc[-1]
                v = v_ser.iloc[-1]
                sma200 = c_ser.rolling(200).mean().iloc[-1]
                vol_sma10 = v_ser.rolling(10).mean().iloc[-1]

                # Filter: Upward trend + Positive day
                if c > sma200 and c > o and (h - l) > 1e-4:
                    # Close position in day's range (Higher means buying into close)
                    close_pos = (c - l) / (h - l)
                    # Relative volume
                    rvol = v / (vol_sma10 + 1e-10)
                    
                    if close_pos >= 0.80 and rvol >= 1.15:
                        accum_scores[t] = close_pos * rvol

        if accum_scores:
            top_accum = sorted(accum_scores.items(), key=lambda x: x[1], reverse=True)[:5]
            accum_picks = [x[0] for x in top_accum]
            r_acc = np.mean([
                (close_df[t].loc[d_mon] / close_df[t].loc[d_fri]) - 1.0
                for t in accum_picks if t in close_df
            ])
        else:
            r_acc = r_spy
        accum_returns.append(r_acc)

        # -------------------------------------------------------------
        # Strategy B: Connors RSI-2 Oversold Reversal (超跌反转)
        # -------------------------------------------------------------
        rev_scores = {}
        for t in TICKERS:
            if t in sub_close and len(sub_close[t].dropna()) >= 200:
                c_ser = sub_close[t].dropna()
                if c_ser.iloc[-1] > c_ser.rolling(200).mean().iloc[-1]:
                    # RSI 2
                    delta = c_ser.diff()
                    g = delta.where(delta > 0, 0).ewm(alpha=0.5, adjust=False).mean()
                    ls = (-delta.where(delta < 0, 0)).ewm(alpha=0.5, adjust=False).mean()
                    rsi = 100 - (100 / (1 + (g / (ls + 1e-10))))
                    rev_scores[t] = rsi.iloc[-1]

        if rev_scores:
            top_rev = sorted(rev_scores.items(), key=lambda x: x[1])[:5]
            rev_picks = [x[0] for x in top_rev]
            r_rev = np.mean([
                (close_df[t].loc[d_mon] / close_df[t].loc[d_fri]) - 1.0
                for t in rev_picks if t in close_df
            ])
        else:
            r_rev = r_spy
        reversal_returns.append(r_rev)

    res_df = pd.DataFrame({
        "Monday_Date": dates_record,
        "Benchmark_SPY": bench_returns,
        "Strat_Tail_Accumulation": accum_returns,
        "Strat_RSI2_Reversal": reversal_returns
    }).set_index("Monday_Date")

    return res_df

def compute_daily_stats(res_df):
    stats = []
    for col in res_df.columns:
        s = res_df[col]
        cum_ret = (1 + s).cumprod()
        total_ret = (cum_ret.iloc[-1] - 1) * 100
        win_rate = (s > 0).mean() * 100
        avg_trade = s.mean() * 100
        ann_vol = s.std() * np.sqrt(52) * 100
        sharpe = (s.mean() * 52 * 100 - 3.5) / (ann_vol + 1e-10)
        
        # Max Drawdown
        running_max = cum_ret.cummax()
        drawdown = (cum_ret - running_max) / running_max
        max_dd = drawdown.min() * 100

        stats.append({
            "Strategy": col,
            "Total_Return_%": round(total_ret, 2),
            "Win_Rate_%": round(win_rate, 2),
            "Avg_Trade_Return_%": round(avg_trade, 3),
            "Sharpe_Ratio": round(sharpe, 2),
            "Max_Drawdown_%": round(max_dd, 2),
            "Trades_Count": len(s)
        })
    return pd.DataFrame(stats)

def plot_daily_performance(res_df):
    cum_ret = (1 + res_df).cumprod()
    plt.figure(figsize=(12, 6))
    plt.plot(cum_ret.index, cum_ret["Benchmark_SPY"], label="Benchmark (SPY Friday->Monday)", color="gray", linestyle="--")
    plt.plot(cum_ret.index, cum_ret["Strat_RSI2_Reversal"], label="RSI-2 Oversold Reversal", color="orange", linewidth=2)
    plt.plot(cum_ret.index, cum_ret["Strat_Tail_Accumulation"], label="Late-Day Accumulation (尾盘抢筹)", color="purple", linewidth=2.5)
    
    plt.title("Daily Strategy: Friday Close to Monday Close Performance (2022-2026)", fontsize=14, fontweight="bold")
    plt.xlabel("Execution Monday Date", fontsize=12)
    plt.ylabel("Cumulative Growth of $1.00", fontsize=12)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(fontsize=11)
    plt.tight_layout()
    
    chart_path = os.path.join(CHART_DIR, "daily_tail_accumulation_backtest.png")
    plt.savefig(chart_path, dpi=300)
    plt.close()
    print(f"Chart saved to: {chart_path}")

def main():
    print("=" * 70)
    print("Testing Friday -> Monday Late-Day Accumulation (尾盘抢筹) Strategy")
    print("=" * 70)
    df = load_data()
    res_df = test_daily_weekend_strategies(df)
    stats_df = compute_daily_stats(res_df)
    print("\n[Friday -> Monday Holding Performance Summary]")
    print(stats_df.to_string(index=False))
    plot_daily_performance(res_df)
    
    # Save CSV
    out_csv = os.path.join(PROJECT_DIR, "Daily_Tail_Accumulation_Summary.csv")
    stats_df.to_csv(out_csv, index=False)
    print(f"Daily summary saved to: {out_csv}")

if __name__ == "__main__":
    main()
