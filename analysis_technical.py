"""
STAT7008 Final Group Project: 通用技术面分析与策略回测模板
适合组员快速上手：仅需修改几行买卖信号代码，即可一键运行完整技术指标计算、收益分布统计与图表绘制！

涵盖指标：
- 趋势指标: SMA (20/50/200), EMA (12/26), MACD (12, 26, 9)
- 动量指标: RSI (14), 动量变化率 (ROC)
- 波动与通道: 布林带 (Bollinger Bands), ATR% (真实波动幅度比例)
- 流动性/筹码: 相对成交量 (RVOL), 成交金额 (Dollar Volume)
- 收益分布分析: 均值、中位数、标准差、偏度(Skew)、峰度(Kurt)、VaR95%、CVaR95%、盈亏比
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 解决 Windows 控制台 GBK 编码报错问题
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from data_api_utils import get_stock_history

# 确保图表目录存在
CHART_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backtest_charts")
os.makedirs(CHART_DIR, exist_ok=True)

# ==============================================================================
# 1. 基础技术指标计算引擎（全自动，无需手动修改）
# ==============================================================================
def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    # 1. 均线系统 (SMA & EMA)
    df["SMA20"] = close.rolling(20).mean()
    df["SMA50"] = close.rolling(50).mean()
    df["SMA200"] = close.rolling(200).mean()
    df["EMA12"] = close.ewm(span=12, adjust=False).mean()
    df["EMA26"] = close.ewm(span=26, adjust=False).mean()

    # 2. MACD (异同移动平均线)
    df["MACD"] = df["EMA12"] - df["EMA26"]
    df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_Hist"] = df["MACD"] - df["MACD_Signal"]

    # 3. RSI (相对强弱指标 14)
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / (avg_loss + 1e-10)
    df["RSI"] = 100 - (100 / (1 + rs))

    # 4. 布林带 (Bollinger Bands 20, 2)
    df["BB_Mid"] = df["SMA20"]
    bb_std = close.rolling(20).std()
    df["BB_Upper"] = df["BB_Mid"] + 2 * bb_std
    df["BB_Lower"] = df["BB_Mid"] - 2 * bb_std
    df["BB_PctB"] = (close - df["BB_Lower"]) / (df["BB_Upper"] - df["BB_Lower"] + 1e-10)

    # 5. ATR% (真实波动幅度比例 - 衡量股性活跃度)
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df["ATR14"] = tr.rolling(14).mean()
    df["ATR_Pct"] = (df["ATR14"] / close) * 100

    # 6. 成交量异动倍数 (RVOL) & 日成交额 (Dollar Volume 百万美元)
    avg_vol20 = volume.rolling(20).mean()
    df["RVOL"] = volume / (avg_vol20 + 1e-10)
    df["Dollar_Vol_M"] = (close * volume) / 1e6

    return df

# ==============================================================================
# 2. 策略买卖信号定义区（组员可在这里自定义自己的策略灵感！）
# ==============================================================================
def my_custom_strategy(df: pd.DataFrame) -> pd.Series:
    """
    【组员修改区】：定义你的买入信号规则 (返回布尔型 Series，True 表示发出买入信号)
    
    默认示例（经典均线动量突破）：
    - 条件 1: 股价位于 50 日均线上方 (Close > SMA50，处于中期多头排列)
    - 条件 2: RSI 处于蓄势拉升区间 (45 <= RSI <= 68，避免追高超买)
    - 条件 3: 成交量放量 (RVOL > 1.0，资金活跃介入)
    """
    signal = (df["Close"] > df["SMA50"]) & (df["RSI"] >= 45) & (df["RSI"] <= 68) & (df["RVOL"] > 1.0)
    return signal

# ==============================================================================
# 3. 策略回测与全维度收益分布评估
# ==============================================================================
def backtest_strategy(ticker: str = "NVDA", start: str = "2023-01-01", holding_days: int = 1):
    """
    回测指定股票，并计算详细的金融收益分布指标
    """
    raw_df = get_stock_history(ticker, start=start, auto_adjust=False)
    if raw_df.empty:
        return
        
    df = add_technical_indicators(raw_df)
    df["Signal"] = my_custom_strategy(df)

    # 计算未来持有 holding_days 天的收益率
    df["Future_Return"] = (df["Close"].shift(-holding_days) - df["Close"]) / df["Close"]
    
    # 提取所有触发买入信号的交易
    trades = df[df["Signal"].shift(1) == True]["Future_Return"].dropna()
    
    if len(trades) < 5:
        print(f"[{ticker}] 触发买入信号次数过少 (仅 {len(trades)} 次)，建议放宽信号阈值。")
        return

    # ---------------- 收益分布关键统计量 ----------------
    mean_ret = trades.mean() * 100
    median_ret = trades.median() * 100
    std_ret = trades.std() * 100
    skewness = trades.skew()
    kurt = trades.kurt()
    win_rate = (trades > 0).mean() * 100
    
    wins = trades[trades > 0]
    losses = trades[trades < 0]
    pl_ratio = (wins.mean() / abs(losses.mean())) if len(losses) > 0 and losses.mean() != 0 else np.nan
    
    var_95 = trades.quantile(0.05) * 100
    cvar_95 = trades[trades <= trades.quantile(0.05)].mean() * 100
    
    # 计算累计收益曲线
    df["Strat_Return"] = np.where(df["Signal"].shift(1) == True, df["Close"].pct_change(), 0.0)
    df["Cumulative_Strat"] = (1 + df["Strat_Return"]).cumprod()
    df["Cumulative_Benchmark"] = (1 + df["Close"].pct_change().fillna(0)).cumprod()
    
    # 最大回撤
    peak = df["Cumulative_Strat"].cummax()
    drawdown = (df["Cumulative_Strat"] - peak) / peak
    max_dd = drawdown.min() * 100
    
    # 年化收益率与夏普比率
    total_days = (df.index[-1] - df.index[0]).days
    ann_ret = (df["Cumulative_Strat"].iloc[-1] ** (365.25 / total_days) - 1) * 100
    ann_vol = df["Strat_Return"].std() * np.sqrt(252) * 100
    sharpe = (ann_ret - 3.0) / (ann_vol + 1e-10) # 假设无风险利率 3%

    # 输出结构化终端报告
    print("\n" + "=" * 65)
    print(f" 技术面策略回测报告: {ticker} (持有期: {holding_days}天)")
    print("=" * 65)
    print(f"样本区间: {df.index[0].strftime('%Y-%m-%d')} 至 {df.index[-1].strftime('%Y-%m-%d')}")
    print(f"总交易次数: {len(trades)} 次 | 胜率: {win_rate:.2f}% | 盈亏比: {pl_ratio:.2f}")
    print(f"累计收益率: {(df['Cumulative_Strat'].iloc[-1]-1)*100:.2f}% | 基准收益率: {(df['Cumulative_Benchmark'].iloc[-1]-1)*100:.2f}%")
    print(f"年化收益率: {ann_ret:.2f}% | 年化夏普比率: {sharpe:.2f} | 最大回撤: {max_dd:.2f}%")
    print("-" * 65)
    print("【收益分布与尾部风险特征 (Distributional Metrics)】:")
    print(f"  • 收益均值 (Mean):        {mean_ret:+.3f}%")
    print(f"  • 收益中位数 (Median):    {median_ret:+.3f}% (剔除极值影响的常态水平)")
    print(f"  • 波动标准差 (Std Dev):   {std_ret:.3f}%")
    print(f"  • 偏度系数 (Skewness):    {skewness:+.2f} ({'右偏/盈利空间大' if skewness > 0 else '左偏/谨防深度亏损'})")
    print(f"  • 峰度系数 (Kurtosis):    {kurt:+.2f} ({'厚尾黑天鹅特征显著' if kurt > 3 else '接近正态常态分布'})")
    print(f"  • 在险价值 (VaR 95%):     {var_95:.2f}% (95%置信度下的最差单笔收益)")
    print(f"  • 条件在险价值 (CVaR 95%):{cvar_95:.2f}% (击穿VaR后的平均极端亏损)")
    print("=" * 65)

    # 绘制收益曲线并保存
    plt.figure(figsize=(10, 5))
    plt.plot(df.index, df["Cumulative_Strat"], label="Custom Strategy", color="#1f77b4", lw=2)
    plt.plot(df.index, df["Cumulative_Benchmark"], label=f"Buy & Hold {ticker}", color="#7f7f7f", linestyle="--", alpha=0.7)
    plt.title(f"Technical Strategy Backtest: {ticker} (Holding {holding_days}D)")
    plt.xlabel("Date")
    plt.ylabel("Cumulative Growth")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    chart_path = os.path.join(CHART_DIR, f"tech_backtest_{ticker}.png")
    plt.savefig(chart_path, dpi=200)
    plt.close()
    print(f"[图表] 回测收益图表已保存至: {chart_path}\n")

if __name__ == "__main__":
    # 测试回测：针对 NVDA 回测 1 日持有期策略
    backtest_strategy(ticker="NVDA", start="2023-01-01", holding_days=1)
