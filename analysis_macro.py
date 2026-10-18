"""
STAT7008 Final Group Project: 宏观情境与历史事件对标压力测试模板
适合组员研究宏观经济、地缘冲突、极端气候等外部因素对股票市场的影响。

核心功能：
1. 宏观核心状态诊断 (SP500 均线牛熊、VIX 恐慌指数、美债 10 年期收益率、WTI 原油价格)
2. 历史同类宏观情境对标与压力测试 (Historical Analog Stress Test):
   - 情境 A: 2022 年美联储剧烈加息与全球高通胀冲击
   - 情境 B: 2023-2024 年中东地缘冲突与原油脉冲
   - 情境 C: 极端气候/厄尔尼诺事件对农业、电力公用事业与保险股的影响
3. 股票对宏观因子的敏感度（相关系数矩阵）分析
"""

import os
import sys
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt

# 解决 Windows 控制台 GBK 编码报错问题
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from data_api_utils import get_macro_series, get_batch_history

CHART_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backtest_charts")
os.makedirs(CHART_DIR, exist_ok=True)

# ==============================================================================
# 1. 当前市场宏观状态诊断 (Macro Regime Diagnostic)
# ==============================================================================
def diagnose_current_macro_regime():
    """
    诊断最新宏观环境标签（牛熊状态、避险情绪、无风险利率水平）
    """
    macro_df = get_macro_series(start="2023-01-01")
    if macro_df.empty:
        return
        
    latest_spy = macro_df["SPY"].iloc[-1]
    spy_sma200 = macro_df["SPY"].rolling(200).mean().iloc[-1]
    regime = "牛市多头 (Bullish)" if latest_spy > spy_sma200 else "熊市防御 (Bearish)"

    vix = macro_df["VIX"].iloc[-1]
    if vix < 16:
        vix_status = "低波动/贪婪进攻 (Low Volatility, Risk-On)"
    elif vix < 24:
        vix_status = "常态波动/中度谨慎 (Normal Volatility)"
    else:
        vix_status = "高恐慌/极端避险 (High Panic, Risk-Off)"

    yield_10y = macro_df["US_10Y_Yield"].iloc[-1]
    oil = macro_df["Crude_Oil_WTI"].iloc[-1]

    print("\n" + "=" * 65)
    print(" 最新宏观环境与状态开关诊断 (Macro Regime Summary)")
    print("=" * 65)
    print(f"• 标普500指数 (SPY):        {latest_spy:.2f} (200日均线: {spy_sma200:.2f}) -> 【{regime}】")
    print(f"• VIX 恐慌指数:             {vix:.2f} -> 【{vix_status}】")
    print(f"• 美国10年期国债收益率:     {yield_10y:.2f}% (无风险利率水平)")
    print(f"• WTI 原油期货价格:         ${oil:.2f}/桶 (能源与二次通胀敏感指标)")
    print("=" * 65)

# ==============================================================================
# 2. 历史同时期外部事件压力测试 (Historical Analog Stress Test)
# ==============================================================================
def run_macro_stress_test(candidate_tickers: list, event_name: str, start_date: str, end_date: str):
    """
    对标历史同类外部宏观事件，检验股票池在历史极端时期的抗风险与收益能力。
    
    参数:
        candidate_tickers: 待测试的股票列表
        event_name: 历史事件名称（如 '2022 高通胀与加息冲击'）
        start_date: 事件起始日期 (YYYY-MM-DD)
        end_date: 事件结束日期 (YYYY-MM-DD)
    """
    print(f"\n[压力测试] 正在对标历史情境: 【{event_name}】 ({start_date} 至 {end_date})")
    all_symbols = candidate_tickers + ["SPY"]
    raw = yf.download(all_symbols, start=start_date, end=end_date, auto_adjust=False, threads=True)
    
    close_prices = raw["Close"].dropna()
    if close_prices.empty:
        print("未能获取该历史区间的数据，请确认日期范围。")
        return

    # 计算各标的在此历史事件期间的总累计收益率
    period_returns = (close_prices.iloc[-1] - close_prices.iloc[0]) / close_prices.iloc[0] * 100
    spy_ret = period_returns.get("SPY", 0.0)

    results = []
    for t in candidate_tickers:
        if t in period_returns:
            r = period_returns[t]
            alpha = r - spy_ret # 相对标普大盘的超额收益
            results.append({
                "Ticker": t,
                "Event_Total_Return_%": round(r, 2),
                "Excess_Return_vs_SPY_%": round(alpha, 2),
                "Performance": "超越大盘 (Outperform)" if alpha > 0 else "落后大盘 (Underperform)"
            })

    res_df = pd.DataFrame(results).sort_values("Excess_Return_vs_SPY_%", ascending=False)
    
    print("-" * 65)
    print(f"标普500基准 (SPY) 在此期间表现: {spy_ret:+.2f}%")
    print(res_df.to_string(index=False))
    print("-" * 65)

    # 导出压力测试对比柱状图
    plt.figure(figsize=(10, 5))
    bars = plt.bar(res_df["Ticker"], res_df["Excess_Return_vs_SPY_%"], color=np.where(res_df["Excess_Return_vs_SPY_%"] > 0, "#2ca02c", "#d62728"))
    plt.axhline(0, color="black", linestyle="--", alpha=0.7)
    plt.title(f"Macro Stress Test: Excess Return vs SPY\n[{event_name}]")
    plt.xlabel("Ticker")
    plt.ylabel("Excess Return (%)")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    chart_name = f"macro_stress_{event_name.replace(' ', '_')[:20]}.png"
    plt.savefig(os.path.join(CHART_DIR, chart_name), dpi=200)
    plt.close()
    print(f"[图表] 宏观对标压力测试图已保存至: backtest_charts/{chart_name}\n")

if __name__ == "__main__":
    # 1. 运行宏观状态诊断
    diagnose_current_macro_regime()

    # 2. 候选测试股票池（跨越科技、能源、消费、公用事业）
    test_universe = ["NVDA", "AAPL", "XOM", "CVX", "KO", "JNJ", "T", "TSLA"]

    # 情境 1: 2022 年美联储激进加息与大通胀冲击
    run_macro_stress_test(
        candidate_tickers=test_universe,
        event_name="2022_Inflation_and_Rate_Hike_Shock",
        start_date="2022-01-03",
        end_date="2022-10-31"
    )

    # 情境 2: 2023-2024 中东地缘冲突原油波动期
    run_macro_stress_test(
        candidate_tickers=test_universe,
        event_name="2023_Middle_East_Geopolitical_Tension",
        start_date="2023-10-06",
        end_date="2024-04-15"
    )
