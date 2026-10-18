"""
STAT7008 Final Group Project: Unified Data API & Utility Module
Designed for teammates to easily download, cache, and clean financial data.

Features:
- Free & Fast: Powered by yfinance, zero API key required.
- Smart Disk Cache: Automatically saves downloaded data to `data_cache/` to avoid network lag.
- Course Compliance: Supports `auto_adjust=False` to strictly use Raw Closing Prices per project rules.
"""

import os
import datetime
import pandas as pd
import yfinance as yf

# Project directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "data_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

def get_stock_history(ticker: str, start: str = "2022-01-01", end: str = None, auto_adjust: bool = False, use_cache: bool = True) -> pd.DataFrame:
    """
    获取单只股票的日K线历史数据（包含 Open, High, Low, Close, Volume）
    
    参数:
        ticker: 股票代码，例如 'AAPL', 'NVDA', 'TSLA'
        start: 起始日期 (YYYY-MM-DD)，默认为 '2022-01-01'
        end: 结束日期 (YYYY-MM-DD)，默认 None 表示下载到最新交易日
        auto_adjust: 是否使用复权价。注意：STAT7008 项目要求使用原始收盘价，请保持 False！
        use_cache: 是否启用本地磁盘缓存。启用后重复调用无需重新联网。
        
    返回:
        pd.DataFrame: 包含 OHLCV 数据的 DataFrame，索引为 DatetimeIndex
    """
    ticker = ticker.upper().strip()
    cache_file = os.path.join(CACHE_DIR, f"{ticker}_{start}_{end if end else 'latest'}_raw.csv")
    
    if use_cache and os.path.exists(cache_file):
        try:
            df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
            if not df.empty:
                return df
        except Exception:
            pass
            
    print(f"[Data API] 正在从 Yahoo Finance 下载 {ticker} 的历史数据...")
    tk = yf.Ticker(ticker)
    df = tk.history(start=start, end=end, auto_adjust=auto_adjust)
    
    if df.empty:
        print(f"[警告] {ticker} 未能成功获取数据，请检查股票代码是否正确或网络是否畅通。")
        return pd.DataFrame()
        
    # 保留核心行情字段
    core_cols = [c for c in ["Open", "High", "Low", "Close", "Volume"] if c in df.columns]
    df = df[core_cols].copy()
    df.dropna(inplace=True)
    
    if use_cache and not df.empty:
        df.to_csv(cache_file)
        
    return df

def get_batch_history(tickers: list, start: str = "2022-01-01", end: str = None, auto_adjust: bool = False) -> pd.DataFrame:
    """
    批量下载多只股票的行情数据（自动并行下载，速度飞快）
    
    参数:
        tickers: 股票代码列表，例如 ['AAPL', 'MSFT', 'NVDA', 'SPY']
        start: 起始日期 (YYYY-MM-DD)
        end: 结束日期 (YYYY-MM-DD)
        
    返回:
        pd.DataFrame: 多层索引 DataFrame，外层列名为股票代码，内层为行情字段
    """
    tickers = [t.upper().strip() for t in tickers]
    print(f"[Data API] 正在批量下载 {len(tickers)} 只标的的数据: {tickers}...")
    df = yf.download(
        tickers=tickers,
        start=start,
        end=end,
        group_by="ticker",
        auto_adjust=auto_adjust,
        threads=True
    )
    return df

def get_stock_fundamentals(ticker: str) -> dict:
    """
    获取单只股票的核心基本面财务数据（契合 Philosophy 2 价值投资指标）
    
    返回字段包含:
        公司名, 行业, 市值, P/E (市盈率), P/B (市净率), P/CF (市现率), 
        ROE (净资产收益率), 净利润率, 资产负债率等
    """
    ticker = ticker.upper().strip()
    tk = yf.Ticker(ticker)
    info = tk.info
    
    return {
        "Ticker": ticker,
        "Short_Name": info.get("shortName", "N/A"),
        "Sector": info.get("sector", "N/A"),
        "Industry": info.get("industry", "N/A"),
        "Market_Cap_B": round(info.get("marketCap", 0) / 1e9, 2) if info.get("marketCap") else None,
        "Trailing_PE": round(info.get("trailingPE", 0), 2) if info.get("trailingPE") else None,
        "Forward_PE": round(info.get("forwardPE", 0), 2) if info.get("forwardPE") else None,
        "Price_to_Book": round(info.get("priceToBook", 0), 2) if info.get("priceToBook") else None,
        "ROE_%": round(info.get("returnOnEquity", 0) * 100, 2) if info.get("returnOnEquity") else None,
        "Operating_Margin_%": round(info.get("operatingMargins", 0) * 100, 2) if info.get("operatingMargins") else None,
        "Total_Debt_B": round(info.get("totalDebt", 0) / 1e9, 2) if info.get("totalDebt") else None,
        "Total_Cash_B": round(info.get("totalCash", 0) / 1e9, 2) if info.get("totalCash") else None,
        "Debt_to_Equity_%": round(info.get("debtToEquity", 0), 2) if info.get("debtToEquity") else None,
        "Dividend_Yield_%": round(info.get("dividendYield", 0) * 100, 2) if info.get("dividendYield") else 0.0
    }

def check_ex_dividend_date(ticker: str) -> dict:
    """
    查询股票的最近除息日（完成 STAT7008 课程向教授与助教申报分红除息的强制要求）
    """
    ticker = ticker.upper().strip()
    tk = yf.Ticker(ticker)
    info = tk.info
    ex_ts = info.get("exDividendDate", None)
    
    if ex_ts:
        ex_date_str = datetime.datetime.fromtimestamp(ex_ts).strftime("%Y-%m-%d")
    else:
        ex_date_str = "None Announced"
        
    return {
        "Ticker": ticker,
        "Ex_Dividend_Date": ex_date_str,
        "Dividend_Rate": info.get("dividendRate", 0.0),
        "Dividend_Yield_%": round(info.get("dividendYield", 0.0) * 100, 2) if info.get("dividendYield") else 0.0
    }

def get_macro_series(start: str = "2022-01-01", end: str = None) -> pd.DataFrame:
    """
    获取全局宏观与跨资产核心序列:
    - SPY: 标普500基准
    - ^VIX: 恐慌指数 (市场避险/压力)
    - ^TNX: 美国10年期国债收益率 (利率水平)
    - CL=F: WTI原油期货 (能源/通胀敏感度)
    - GC=F: 黄金期货 (地缘避险)
    """
    symbols = {
        "SPY": "SPY",
        "^VIX": "VIX",
        "^TNX": "US_10Y_Yield",
        "CL=F": "Crude_Oil_WTI",
        "GC=F": "Gold"
    }
    print("[Data API] 正在下载宏观与跨资产基准序列 (SPY, VIX, 10Y Yield, Oil, Gold)...")
    raw = yf.download(list(symbols.keys()), start=start, end=end, auto_adjust=False)
    
    macro_df = pd.DataFrame()
    for sym, name in symbols.items():
        if sym in raw["Close"].columns:
            macro_df[name] = raw["Close"][sym]
            
    macro_df.dropna(inplace=True)
    return macro_df

if __name__ == "__main__":
    print("=== 测试 Data API 工具集 ===")
    sample_df = get_stock_history("AAPL", start="2024-01-01")
    print(f"AAPL 历史行情已获取，数据量: {len(sample_df)} 天")
    print(sample_df.tail(3))
    
    fundamentals = get_stock_fundamentals("NVDA")
    print("\nNVDA 核心基本面:")
    for k, v in fundamentals.items():
        print(f"  {k}: {v}")
        
    div_info = check_ex_dividend_date("JNJ")
    print(f"\nJNJ 分红除息信息: {div_info}")
