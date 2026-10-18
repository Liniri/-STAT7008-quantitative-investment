# STAT7008 Final Group Project: Quantitative US Equity Investment System
> **The University of Hong Kong (HKU) | Department of Statistics and Actuarial Science**  
> **Course:** STAT7008 Programming for Data Science  
> **Instructor:** Dr. Harrison Cheung  

---

## 📌 目录 (Table of Contents)
1. [项目背景与学术约束](#-项目背景与学术约束)
2. [代码仓库架构](#-代码仓库架构)
3. [快速开始 (Quick Start)](#-快速开始-quick-start)
4. [四位小组成员分工与脚本指南](#-四位小组成员分工与脚本指南)
   - [成员 1: 宏观分析与历史对标 (Macro & Stress Test)](#1-成员-1-宏观分析与历史对标)
   - [成员 2: 数据接口与综合回测 (Data & Backtest Engine)](#2-成员-2-数据接口与综合回测)
   - [成员 3: 技术指标与策略回测 (Technical & Portfolio)](#3-成员-3-技术指标与策略回测)
   - [成员 4: 基本面排雷与除息申报 (Fundamentals & Risk)](#4-成员-4-基本面排雷与除息申报)
5. [数据接口使用说明 (小白友好)](#-数据接口使用说明-小白友好)
6. [常见问题与避坑指南 (FAQ)](#-常见问题与避坑指南-faq)

---

## 📖 项目背景与学术约束

本项目要求运用 Python 对美股市场进行量化投资决策，总计管理 **300 万虚拟美元**，分为三个独立的投资练习：
* **日度投资 (Daily Investment)**: 100 万美元 | **11月6日（周五收盘价买入） $\to$ 11月9日（周一收盘价结算）**
* **周度投资 (Weekly Investment)**: 100 万美元 | **11月6日（周五收盘价买入） $\to$ 11月13日（周五收盘价结算）**
* **月度投资 (Monthly Investment)**: 100 万美元 | **11月6日（周五收盘价买入） $\to$ 12月4日（周五收盘价结算）**

### ⚠️ 核心刚性纪律 (Violations = Grade Penalties):
1. **禁止做空、禁止借贷加杠杆、禁止持有现金（必须全仓买入股票）**；
2. **禁止投资 ETF 或指数基金**，仅能投资美股上市个股单票；
3. **每个投资账户最多选择 5 家公司**（支持购买碎股以精确配平 100 万美元）；
4. **必须使用原始收盘价（Raw Closing Price）**，不得使用后复权价；
5. **分红除息强制申报**：若选定股票在考核期内发生除息（Ex-dividend date），必须提前向 Harrison 老师及助教 Jiacheng 发邮件申报。

---

## 📂 代码仓库架构

```text
├── README.md                              # 本说明文档（项目全景与使用手册）
├── requirements.txt                      # Python 依赖库清单
├── .gitignore                            # Git 忽略文件配置
│
├── data_api_utils.py                     # 核心数据工具库 (支持 yfinance 本地磁盘缓存)
├── analysis_1day_decision.py             # 一日交易专用决策与收益全分布分析工具
├── analysis_technical.py                 # 通用技术指标计算与策略自定义回测模板
├── analysis_macro.py                     # 宏观环境诊断与历史事件对标压力测试模板
├── analysis_fundamental_news.py          # 基本面健康度评分与除息日自动排查模板
│
├── run_portfolio_pipeline.py             # 核心流水线：一键生成最终提交的 Excel 决策表
├── run_backtest_validation.py            # 学术级滚动回测验证 (Rolling Scheme)
│
├── data_cache/                           # 自动缓存的原始行情 CSV（避免重复网络下载）
└── backtest_charts/                      # 自动保存的回测收益曲线与分析柱状图
```

---

## 🚀 快速开始 (Quick Start)

### 第一步：克隆仓库并安装环境
确保电脑安装了 Python 3.9+，在终端运行：
```bash
git clone <本仓库地址>
cd "Final Gourp Project"
pip install -r requirements.txt
```

### 第二步：运行一键测试
直接运行数据接口测试，验证网络与基础环境：
```bash
python data_api_utils.py
```
若能成功输出 `AAPL 历史行情已获取` 和 `NVDA 核心基本面`，即代表配置成功！

---

## 👥 四位小组成员分工与脚本指南

每位组员都可以独立运行并修改自己负责的脚本，互不冲突：

### 1. 成员 1: 宏观分析与历史对标
* **使用脚本**：`analysis_macro.py`
* **如何修改**：
  * 打开 `analysis_macro.py`，定位到最下方的 `run_macro_stress_test()`；
  * 可以修改或新增历史极端时期（如高通胀、中东地缘、极端天气）：
    ```python
    run_macro_stress_test(
        candidate_tickers=["NVDA", "XOM", "KO"],
        event_name="2022_Inflation_Shock",
        start_date="2022-01-03",
        end_date="2022-10-31"
    )
    ```
* **输出成果**：自动生成宏观状态诊断表格以及各股票相对标普的超额收益图表（存入 `backtest_charts/`）。

---

### 2. 成员 2: 数据接口与综合回测
* **使用脚本**：`data_api_utils.py` & `run_portfolio_pipeline.py`
* **工作要点**：
  * 维护基础数据管道，管理 `data_cache/` 缓存；
  * 在 11月6日 收盘后，运行 `run_portfolio_pipeline.py`，一键生成用于提交给 Harrison 老师的 `Investment_Decision.xlsx` 官方表格。

---

### 3. 成员 3: 技术指标与策略回测
* **使用脚本**：`analysis_technical.py` & `analysis_1day_decision.py`
* **如何修改**：
  * 打开 `analysis_technical.py`，找到第 78 行的 `my_custom_strategy(df)` 函数；
  * 自由编写你的买入规则（支持 RSI, MACD, 均线金叉, 布林带等）：
    ```python
    def my_custom_strategy(df: pd.DataFrame) -> pd.Series:
        # 示例：RSI超卖反弹且站上20日均线
        buy_signal = (df["RSI"] < 40) & (df["Close"] > df["SMA20"])
        return buy_signal
    ```
  * 运行后将自动输出包含**均值、中位数、偏度、峰度、VaR 95%、胜率与盈亏比**在内的专业金融分布报告，并绘制累计收益走势图！

---

### 4. 成员 4: 基本面排雷与除息申报
* **使用脚本**：`analysis_fundamental_news.py`
* **工作要点**：
  * 在选股候选池确定后，运行此脚本：
    ```bash
    python analysis_fundamental_news.py
    ```
  * 脚本会自动计算市盈率(P/E)、ROE、负债率，排查“低估值陷阱（Value Trap）”；
  * **重点防错**：若发现有股票在 11月6日~12月4日 期间除息，脚本会在控制台直接生成一封**英文邮件草稿**，队长直接复制发送给老师即可！

---

## 💡 数据接口使用说明 (小白友好)

为了让大家省去写复杂爬虫的烦恼，我们封装了 `data_api_utils.py`。你在自己的任何脚本里都可以直接引用：

```python
from data_api_utils import get_stock_history, get_stock_fundamentals, check_ex_dividend_date

# 1. 获取某只股票历史日K线（自动本地缓存，不卡顿）
df = get_stock_history("NVDA", start="2023-01-01")
print(df[["Close", "Volume"]].tail())

# 2. 查看基本面（P/E, ROE, 负债率等）
fund = get_stock_fundamentals("AAPL")
print("苹果市盈率:", fund["Trailing_PE"])

# 3. 查看最近除息日
div = check_ex_dividend_date("JNJ")
print("强生除息日:", div["Ex_Dividend_Date"])
```

---

## ❓ 常见问题与避坑指南 (FAQ)

### Q1: 运行脚本时提示下载超时 (Timeout) 怎么办？
* Yahoo Finance 在国内网络偶有波动。`data_api_utils.py` 内部自带重试机制，并且只要成功下载过一次，数据就会被保存在 `data_cache/` 文件夹中，后续使用不再消耗网络流量。如遇网络阻断，可多运行一次或开启代理。

### Q2: 为什么我们不能使用 Adjusted Close (后复权价)？
* Harrison 老师在 Project Description 和课件中反复强调：`"We use closing price (not adjusted closing price) in this project."`。因此我们在所有函数中均强制设定 `auto_adjust=False`。请勿手动将其改成 True！

### Q3: 为什么“尾盘抢筹”在日度回测中的胜率大约在 54%~60% 之间？
* 因为我们的一日交易是从 **周五收盘到周一收盘**，中间跨越了周六和周日，存在周末消息发酵与隔夜跳空（Overnight Gap）。运行 `analysis_1day_decision.py` 可以观察到标的在周五至周一的真实收益分布，请优先选取中位数为正、偏度系数为正的强势标的。
