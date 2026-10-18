"""
STAT7008 Final Group Project: 一日交易专用决策与收益全分布分析工具
专门针对项目【日度投资练习 (Daily Investment)】：
- 考核规则：2026年11月6日（周五收盘价买入） -> 2026年11月9日（周一收盘价卖出）
- 核心特征：跨越整个周末（包含周六周日两天），需同时抵御周末隔夜消息跳空风险与捕捉周一溢价！

本工具输出：
1. 股票周五买入、周一卖出的历史全分布：均值、中位数、波动率、偏度(Skew)、峰度(Kurt)、VaR95%、胜率与盈亏比
2. 自动根据“综合夏普比率 + 胜率 + 收益期望”打分，推荐日度账户的 Top 5 候选标的
"""

import os
import sys
import pandas as pd
import numpy as np
import yfinance as yf

# 解决 Windows 控制台 GBK 编码报错问题
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from data_api_utils import get_batch_history

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def analyze_friday_to_monday_distributions(tickers: list, start_date: str = "2023-01-01"):
    """
    测算所有候选标的在历史上的“周五买入 -> 周一卖出”的精确收益分布特征
    """
    print(f"\n[一日交易决策] 正在计算 {len(tickers)} 只标的在历史周五至周一区间的完整收益分布...")
    raw = yf.download(tickers, start=start_date, auto_adjust=False, threads=True)
    close_prices = raw["Close"].dropna()
    volume_prices = raw["Volume"].dropna()
    
    distribution_records = []
    
    for t in tickers:
        try:
            if t not in close_prices.columns:
                continue
            c = close_prices[t].dropna()
            v = volume_prices[t].dropna()
            
            if len(c) < 60:
                continue
                
            c_df = pd.DataFrame({"Close": c, "Volume": v})
            c_df["Weekday"] = c_df.index.weekday # 4 表示周五 (Friday)
            
            # 找到所有周五
            fridays = c_df[c_df["Weekday"] == 4]
            
            weekend_returns = []
            for fri_date in fridays.index[:-1]:
                loc = c.index.get_loc(fri_date)
                # 下一个有效交易日通常是周一
                if loc + 1 < len(c):
                    r = (c.iloc[loc + 1] - c.iloc[loc]) / c.iloc[loc]
                    weekend_returns.append(r)
                    
            rets = pd.Series(weekend_returns)
            if len(rets) < 20:
                continue

            # ---------------- 核心分布指标计算 ----------------
            mean_ret = rets.mean() * 100
            median_ret = rets.median() * 100
            std_ret = rets.std() * 100
            skew = rets.skew()
            kurt = rets.kurt()
            win_rate = (rets > 0).mean() * 100
            
            wins = rets[rets > 0]
            losses = rets[rets < 0]
            pl_ratio = (wins.mean() / abs(losses.mean())) if len(losses) > 0 and losses.mean() != 0 else np.nan
            
            var_95 = rets.quantile(0.05) * 100
            cvar_95 = rets[rets <= rets.quantile(0.05)].mean() * 100
            
            # 日均成交金额 (百万美元)
            avg_vol20 = v.rolling(20).mean().iloc[-1]
            dollar_vol = (c.iloc[-1] * avg_vol20) / 1e6
            
            # 综合一日短线推荐评分: 胜率权重 + 期望收益 - 极值惩罚
            score = (win_rate * 0.4) + (mean_ret * 20) + (median_ret * 10) - (abs(var_95) * 2)

            distribution_records.append({
                "Ticker": t,
                "Latest_Price": round(c.iloc[-1], 2),
                "Dollar_Vol_M": round(dollar_vol, 1),
                "Mean_%": round(mean_ret, 3),
                "Median_%": round(median_ret, 3),
                "Std_%": round(std_ret, 3),
                "Skewness": round(skew, 2),
                "Kurtosis": round(kurt, 2),
                "Win_Rate_%": round(win_rate, 1),
                "PL_Ratio": round(pl_ratio, 2) if not np.isnan(pl_ratio) else 1.0,
                "VaR_95_%": round(var_95, 2),
                "CVaR_95_%": round(cvar_95, 2),
                "Score": round(score, 2)
            })
        except Exception as e:
            print(f"[{t}] 计算分布失败: {e}")

    df_dist = pd.DataFrame(distribution_records).sort_values("Score", ascending=False)
    
    print("\n" + "=" * 90)
    print(" 周五至周一 (一日交易) 历史全收益分布与评级榜单 (按综合得分排序)")
    print("=" * 90)
    cols_display = ["Ticker", "Latest_Price", "Dollar_Vol_M", "Mean_%", "Median_%", "Win_Rate_%", "Skewness", "VaR_95_%", "Score"]
    print(df_dist[cols_display].to_string(index=False))
    print("=" * 90)

    # 导出日度 Top 5 推荐
    top5 = df_dist.head(5)
    print("\n[推荐] 【日度账户推荐 Top 5 标的】 (建议平分 100 万美元虚拟资金):")
    for idx, row in top5.iterrows():
        shares = int(200000 / row["Latest_Price"])
        print(f"  * {row['Ticker']:<5} | 最新价: ${row['Latest_Price']:<7} | 建议买入股数: {shares:>5} 股 | 周一胜率: {row['Win_Rate_%']}% | 平均周一溢价: {row['Mean_%']:+}%")

    out_csv = os.path.join(BASE_DIR, "Daily_1Day_Decision_Distribution.csv")
    df_dist.to_csv(out_csv, index=False, encoding="utf-8-sig")
    print(f"\n完整分布表已保存至: Daily_1Day_Decision_Distribution.csv\n")

if __name__ == "__main__":
    candidates = [
        "NVDA", "TSLA", "AMD", "META", "AAPL", "MSFT", "AMZN", "GOOGL",
        "PLTR", "COIN", "XOM", "CVX", "JPM", "LLY", "COST", "KO", "T"
    ]
    analyze_friday_to_monday_distributions(candidates)
