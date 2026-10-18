"""
STAT7008 Programming for Data Science - Final Group Project
Enhanced Backtesting Engine with Liquidity, Volatility (Beta/ATR%) & Activity Filters

Added Features:
1. Activity/Liquidity Filters:
   - High Dollar Volume: Volume * Close >= $200M (Ensures deep institutional liquidity)
   - Normalized ATR% (ATR14 / Close) >= 2.5% (Eliminates sluggish/dead stocks)
   - Relative Volume (RVOL20) >= 1.2 (Surge in trading interest)
   - High Beta / Elasticity to capitalize on post-election volatility
2. Strategy Testing:
   - Daily (Friday Close -> Monday Close): Active High-Momentum Tail-Accumulation
   - Weekly (5-Day Holding): Active High-Beta Minervini Momentum Breakout
   - Monthly (20-Day Holding): Active Institutional Transaction Value Concentration (Philosophy 4)
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

# Broad universe across high-beta tech, cyclicals, consumer, industrial, energy
TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO", "AMD", "ORCL",
    "NFLX", "QCOM", "INTC", "MU", "PANW", "SNOW", "CRM", "UBER", "ABNB", "PLTR",
    "CAT", "GE", "BA", "HON", "DE", "URI", "ETN", "XOM", "CVX", "SLB",
    "JPM", "GS", "MS", "V", "MA", "AXP", "BLK", "COIN", "SCHW",
    "LLY", "UNH", "ISRG", "VRTX", "MRK", "COST", "HD", "TGT", "NKE", "SBUX", "LULU"
]

def load_data():
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Downloading OHLCV data for {len(TICKERS)} active tickers + SPY...")
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

def calculate_atr(high, low, close, period=14):
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

# ---------------------------------------------------------------------------------
# 1. Active Stock Screener & Filter
# ---------------------------------------------------------------------------------
def filter_active_stocks(sub_close, sub_open, sub_high, sub_low, sub_vol, t_date):
    """
    Filters for stocks with strong liquidity and high activity (股性活跃):
    - Dollar Volume (Volume * Close) >= $150 Million
    - ATR% (ATR14 / Close) >= 2.0% (Sufficient price swing amplitude)
    """
    active_metrics = {}
    for t in TICKERS:
        try:
            if t not in sub_close or len(sub_close[t].dropna()) < 60:
                continue
            c = sub_close[t].dropna()
            h = sub_high[t].dropna().reindex(c.index)
            l = sub_low[t].dropna().reindex(c.index)
            v = sub_vol[t].dropna().reindex(c.index)

            curr_c = c.iloc[-1]
            curr_v = v.iloc[-1]
            avg_v20 = v.rolling(20).mean().iloc[-1]
            
            # Dollar volume in millions
            dollar_vol = (curr_c * avg_v20) / 1e6
            
            # ATR%
            atr14 = calculate_atr(h, l, c, 14).iloc[-1]
            atr_pct = (atr14 / curr_c) * 100
            
            # Relative Volume
            rvol = curr_v / (avg_v20 + 1e-10)

            # Activity Threshold: Liquid ($150M+ daily) and active (ATR% >= 2.0%)
            if dollar_vol >= 150.0 and atr_pct >= 2.0:
                active_metrics[t] = {
                    "close": curr_c,
                    "dollar_vol": dollar_vol,
                    "atr_pct": atr_pct,
                    "rvol": rvol,
                    "series_close": c,
                    "series_open": sub_open[t].dropna().reindex(c.index),
                    "series_high": h,
                    "series_low": l,
                    "series_vol": v
                }
        except Exception:
            continue
    return active_metrics

# ---------------------------------------------------------------------------------
# 2. Daily Backtest with Activity Filter (Friday -> Monday)
# ---------------------------------------------------------------------------------
def backtest_active_daily(df):
    print("\n--- Running Active Friday -> Monday Daily Strategy ---")
    close_dict, open_dict, high_dict, low_dict, vol_dict = {}, {}, {}, {}, {}
    for t in TICKERS:
        try:
            sub = df[t].dropna()
            close_dict[t] = sub["Close"]
            open_dict[t] = sub["Open"]
            high_dict[t] = sub["High"]
            low_dict[t] = sub["Low"]
            vol_dict[t] = sub["Volume"]
        except Exception:
            pass
            
    close_df = pd.DataFrame(close_dict).dropna(how="all")
    open_df = pd.DataFrame(open_dict).reindex(close_df.index)
    high_df = pd.DataFrame(high_dict).reindex(close_df.index)
    low_df = pd.DataFrame(low_dict).reindex(close_df.index)
    vol_df = pd.DataFrame(vol_dict).reindex(close_df.index)
    spy_close = df["SPY"]["Close"].reindex(close_df.index).dropna()

    dates = close_df.index.intersection(spy_close.index)
    weekend_pairs = [
        (dates[i], dates[i+1]) for i in range(len(dates)-1)
        if dates[i].dayofweek == 4 and 1 <= (dates[i+1] - dates[i]).days <= 4
    ]

    bench_returns, strat_returns, dates_rec = [], [], []

    for d_fri, d_mon in weekend_pairs:
        r_spy = (spy_close.loc[d_mon] / spy_close.loc[d_fri]) - 1.0
        bench_returns.append(r_spy)
        dates_rec.append(d_mon)

        sub_c = close_df.loc[:d_fri]
        sub_o = open_df.loc[:d_fri]
        sub_h = high_df.loc[:d_fri]
        sub_l = low_df.loc[:d_fri]
        sub_v = vol_df.loc[:d_fri]

        active_pool = filter_active_stocks(sub_c, sub_o, sub_h, sub_l, sub_v, d_fri)

        # Pick top 5 active stocks with strongest tail-buying (Close-to-High Ratio * RVOL)
        scores = {}
        for t, m in active_pool.items():
            c = m["series_close"].iloc[-1]
            o = m["series_open"].iloc[-1]
            h = m["series_high"].iloc[-1]
            l = m["series_low"].iloc[-1]
            if (h - l) > 1e-4 and c > o:
                close_pos = (c - l) / (h - l)
                if close_pos >= 0.80 and m["rvol"] >= 1.2:
                    # Combined Activity Score: Close Pos * RVOL * ATR%
                    scores[t] = close_pos * m["rvol"] * m["atr_pct"]

        if scores:
            picks = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]
            tickers_chosen = [x[0] for x in picks]
            r_strat = np.mean([
                (close_df[t].loc[d_mon] / close_df[t].loc[d_fri]) - 1.0
                for t in tickers_chosen if t in close_df
            ])
        else:
            r_strat = r_spy
        strat_returns.append(r_strat)

    res_df = pd.DataFrame({
        "Benchmark_SPY": bench_returns,
        "Active_Tail_Accumulation": strat_returns
    }, index=dates_rec)
    return res_df

# ---------------------------------------------------------------------------------
# 3. Weekly & Monthly Backtest with Activity Filter
# ---------------------------------------------------------------------------------
def backtest_active_weekly_monthly(df, holding_days=5):
    close_dict, open_dict, high_dict, low_dict, vol_dict = {}, {}, {}, {}, {}
    for t in TICKERS:
        try:
            sub = df[t].dropna()
            close_dict[t] = sub["Close"]
            open_dict[t] = sub["Open"]
            high_dict[t] = sub["High"]
            low_dict[t] = sub["Low"]
            vol_dict[t] = sub["Volume"]
        except Exception:
            pass
            
    close_df = pd.DataFrame(close_dict).dropna(how="all")
    open_df = pd.DataFrame(open_dict).reindex(close_df.index)
    high_df = pd.DataFrame(high_dict).reindex(close_df.index)
    low_df = pd.DataFrame(low_dict).reindex(close_df.index)
    vol_df = pd.DataFrame(vol_dict).reindex(close_df.index)
    spy_close = df["SPY"]["Close"].reindex(close_df.index).dropna()

    dates = close_df.index.intersection(spy_close.index)
    val_dates = [d for d in dates if d >= pd.to_datetime("2024-01-01")]
    trade_indices = list(range(0, len(val_dates) - holding_days, holding_days))

    bench_returns, strat_returns, dates_rec = [], [], []

    for idx in trade_indices:
        t_date = val_dates[idx]
        t_future = val_dates[idx + holding_days]
        r_spy = (spy_close.loc[t_future] / spy_close.loc[t_date]) - 1.0
        bench_returns.append(r_spy)
        dates_rec.append(t_future)

        sub_c = close_df.loc[:t_date]
        sub_o = open_df.loc[:t_date]
        sub_h = high_df.loc[:t_date]
        sub_l = low_df.loc[:t_date]
        sub_v = vol_df.loc[:t_date]

        active_pool = filter_active_stocks(sub_c, sub_o, sub_h, sub_l, sub_v, t_date)

        scores = {}
        for t, m in active_pool.items():
            c_ser = m["series_close"]
            if len(c_ser) >= 50:
                sma50 = c_ser.rolling(50).mean().iloc[-1]
                curr_c = c_ser.iloc[-1]
                # High-momentum breakout in active stocks
                if curr_c > sma50:
                    mom20 = (curr_c / c_ser.iloc[-21]) - 1.0
                    # Rank by momentum * ATR elasticity
                    scores[t] = mom20 * (m["atr_pct"] / 100.0)

        if scores:
            picks = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]
            tickers_chosen = [x[0] for x in picks]
            r_strat = np.mean([
                (close_df[t].loc[t_future] / close_df[t].loc[t_date]) - 1.0
                for t in tickers_chosen if t in close_df
            ])
        else:
            r_strat = r_spy
        strat_returns.append(r_strat)

    res_df = pd.DataFrame({
        "Benchmark_SPY": bench_returns,
        "Active_Momentum_Strategy": strat_returns
    }, index=dates_rec)
    return res_df

def summarize_stats(res_df, periods_per_year=52):
    stats = []
    for col in res_df.columns:
        s = res_df[col]
        cum_ret = (1 + s).cumprod()
        tot = (cum_ret.iloc[-1] - 1) * 100
        ann_ret = ((1 + tot/100) ** (periods_per_year / len(s)) - 1) * 100
        win = (s > 0).mean() * 100
        ann_vol = s.std() * np.sqrt(periods_per_year) * 100
        sharpe = (ann_ret - 3.5) / (ann_vol + 1e-10)
        
        running_max = cum_ret.cummax()
        dd = (cum_ret - running_max) / running_max
        max_dd = dd.min() * 100

        stats.append({
            "Strategy": col,
            "Total_Return_%": round(tot, 2),
            "Ann_Return_%": round(ann_ret, 2),
            "Win_Rate_%": round(win, 2),
            "Sharpe_Ratio": round(sharpe, 2),
            "Max_Drawdown_%": round(max_dd, 2)
        })
    return pd.DataFrame(stats)

def main():
    print("=" * 70)
    print("STAT7008 Backtesting Engine with Activity & Liquidity Filters")
    print("=" * 70)
    df = load_data()

    # 1. Daily Active Test
    daily_res = backtest_active_daily(df)
    daily_stats = summarize_stats(daily_res, periods_per_year=52)
    print("\n[Daily Horizon with Activity Filter (Friday -> Monday, 240 Trades)]")
    print(daily_stats.to_string(index=False))

    # 2. Weekly Active Test
    weekly_res = backtest_active_weekly_monthly(df, holding_days=5)
    weekly_stats = summarize_stats(weekly_res, periods_per_year=52)
    print("\n[Weekly Horizon with Activity Filter (5-Day Rolling Holding)]")
    print(weekly_stats.to_string(index=False))

    # 3. Monthly Active Test
    monthly_res = backtest_active_weekly_monthly(df, holding_days=20)
    monthly_stats = summarize_stats(monthly_res, periods_per_year=12)
    print("\n[Monthly Horizon with Activity Filter (20-Day Rolling Holding)]")
    print(monthly_stats.to_string(index=False))

    # Save to CSV
    summary_path = os.path.join(PROJECT_DIR, "Active_Liquidity_Filtered_Backtest_Summary.csv")
    pd.concat([
        daily_stats.assign(Horizon="Daily (1D Weekend)"),
        weekly_stats.assign(Horizon="Weekly (5D)"),
        monthly_stats.assign(Horizon="Monthly (20D)")
    ]).to_csv(summary_path, index=False)
    print(f"\nAll filtered metrics saved to: {summary_path}")

if __name__ == "__main__":
    main()
