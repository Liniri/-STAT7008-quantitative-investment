"""
STAT7008 Final Group Project: 基本面健康度排雷与除息/事件风险监控模板
深度结合 Harrison Cheung 老师 Philosophy 2 (价值投资与财务真伪) 与课程除息申报规则。

核心功能：
1. 核心财务健康度评分 (P/E, P/B, ROE, 净负债率, 现金覆盖率)
2. “廉价陷阱（Value Trap）”预警检测（防止买入财务造假或濒临破产的死股票）
3. 自动扫描 11月6日~12月4日 期间的除息日（Ex-dividend date）
4. 一键生成符合课程格式的“向教授及助教 Jiacheng 申报除息的邮件草稿”
"""

import os
import sys
import datetime
import pandas as pd

# 解决 Windows 控制台 GBK 编码报错问题
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from data_api_utils import get_stock_fundamentals, check_ex_dividend_date

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def analyze_fundamentals_and_dividends(tickers: list, start_eval: str = "2026-11-06", end_eval: str = "2026-12-04"):
    """
    全方位扫描候选股票的基本面健康度与除息日风险
    """
    print(f"\n[基本面与风控] 正在扫描 {len(tickers)} 只候选标的的财务健康度与除息日...")
    
    start_dt = pd.to_datetime(start_eval)
    end_dt = pd.to_datetime(end_eval)
    
    records = []
    ex_div_alerts = []

    for t in tickers:
        try:
            fund = get_stock_fundamentals(t)
            div = check_ex_dividend_date(t)
            
            pe = fund.get("Trailing_PE")
            pb = fund.get("Price_to_Book")
            roe = fund.get("ROE_%")
            de_ratio = fund.get("Debt_to_Equity_%")
            cash = fund.get("Total_Cash_B") or 0.0
            debt = fund.get("Total_Debt_B") or 0.0
            cash_cover = round(cash / (debt + 1e-5), 2) if debt > 0 else 99.0
            
            # 价值陷阱排雷规则 (Philosophy 2: "Many companies that look cheap deserve to be cheap!")
            is_trap = False
            trap_reasons = []
            if pe and pe < 0:
                is_trap = True
                trap_reasons.append("公司持续亏损 (负PE)")
            if roe and roe < 5:
                is_trap = True
                trap_reasons.append("ROE过低 (<5%) 资本回报极差")
            if de_ratio and de_ratio > 200:
                is_trap = True
                trap_reasons.append("杠杆率过高 (负债/权益 > 200%)")
            if cash_cover < 0.2 and debt > 10:
                is_trap = True
                trap_reasons.append("现金严重无法覆盖债务，有流动性危机")

            health_status = "SAFE (健康)" if not is_trap else f"WARNING ({'; '.join(trap_reasons)})"

            # 检查除息日是否落在考核窗口内
            ex_date_str = div.get("Ex_Dividend_Date")
            has_ex_in_window = False
            if ex_date_str and ex_date_str != "None Announced":
                try:
                    ex_d = pd.to_datetime(ex_date_str)
                    if start_dt <= ex_d <= end_dt:
                        has_ex_in_window = True
                        ex_div_alerts.append({
                            "Ticker": t,
                            "Ex_Date": ex_date_str,
                            "Dividend_Yield_%": div.get("Dividend_Yield_%")
                        })
                except Exception:
                    pass

            records.append({
                "Ticker": t,
                "Sector": fund.get("Sector"),
                "Trailing_PE": pe,
                "Price_to_Book": pb,
                "ROE_%": roe,
                "Debt_to_Equity_%": de_ratio,
                "Cash_to_Debt_Ratio": cash_cover,
                "Fundamental_Health": health_status,
                "Ex_Dividend_Date": ex_date_str,
                "Ex_Div_In_Window?": "YES (需向老师申报!)" if has_ex_in_window else "No"
            })
        except Exception as e:
            print(f"[{t}] 处理失败: {e}")

    df_res = pd.DataFrame(records)
    
    # 打印排雷报告
    print("\n" + "=" * 80)
    print(" 基本面健康度排雷与分红风险评估总表 (Philosophy 2 对齐)")
    print("=" * 80)
    print(df_res[["Ticker", "Sector", "Trailing_PE", "ROE_%", "Debt_to_Equity_%", "Fundamental_Health", "Ex_Div_In_Window?"]].to_string(index=False))
    print("=" * 80)

    # 保存 CSV
    csv_path = os.path.join(BASE_DIR, "Fundamental_and_Dividend_Summary.csv")
    df_res.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"完整分析表已保存至: Fundamental_and_Dividend_Summary.csv")

    # 如果有落在考核区间的除息日，自动生成申报邮件
    if ex_div_alerts:
        print("\n" + "!" * 80)
        print("[警告] 【必须执行】发现以下标的在考核期内发生除息！已自动生成向教授与助教申报的通知模板：")
        print("!" * 80)
        email_text = f"""
To: hcheung4@hku.hk, u3011679@connect.hku.hk
Subject: [STAT7008 Group Project] Notification of Dividend Payment / Ex-Dividend Dates

Dear Dr. Harrison Cheung and Tutor Jiacheng,

We are writing on behalf of our group to formally notify you of the upcoming ex-dividend payment(s) during our portfolio evaluation period (Nov 6 - Dec 4), in accordance with the project requirements:

"""
        for item in ex_div_alerts:
            email_text += f"- Stock: {item['Ticker']} | Ex-Dividend Date: {item['Ex_Date']} | Dividend Yield: {item['Dividend_Yield_%']}%\n"
            
        email_text += """
Please kindly take this into account when calculating our portfolio returns. Thank you!

Best regards,
STAT7008 Final Project Team
"""
        print(email_text)
        print("!" * 80)

if __name__ == "__main__":
    # 测试扫描候选股票池
    candidates = ["NVDA", "TSLA", "AAPL", "XOM", "KO", "JNJ", "T", "VZ", "PLTR"]
    analyze_fundamentals_and_dividends(candidates)
