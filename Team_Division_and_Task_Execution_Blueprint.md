# STAT7008 Final Group Project: 4-Member Quantitative Division of Labor & Execution Blueprint

本蓝图旨在量化界定四位小组成员的**工程职责、学术深度、交付物与答辩分工**，确保满足：
1. **Written Report (60%)** 章节内容平衡且深度扎实；
2. **Presentation Video (20%)** 每人独立获得最高答辩评分（每人均分 4~5 分钟，内容充沛不冷场）；
3. **Python Code (5%)** 具备模块化专业架构；
4. **Portfolio Performance (15%)** 规则合规且收益领先。

---

## 一、 角色与深度全景图

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                        STAT7008 量化投研团队架构 (Quantitative Team Hierarchy)                 │
├────────────────────────────┬────────────────────────────┬───────────────────────────────────────┤
│ 成员 1: 宏观量化研究员     │ 成员 2: 数据与量化工程架构 │ 成员 3: 微观量化与技术择时研究员      │
│ (Macro Regime & Strategy)  │ (Data & Backtest Engine)   │ (Technical & Concentration Signals)   │
│ • 宏观政治经济周期         │ • 标普500数据管道          │ • 日度尾盘抢筹指标 (Late-Day Surge)   │
│ • 中期选举不确定性消除     │ • Rolling Scheme 滚动验证  │ • 周度 Minervini VCP 动量突破         │
│ • 利率与 VIX 状态开关      │ • 资金配平与 Excel 导出    │ • 月度 Philosophy 4 筹码集中度        │
├────────────────────────────┴────────────────────────────┴───────────────────────────────────────┤
│                                 成员 4: 基本面风控与合规审计员 (Risk, Fundamentals & Governance)│
│                                 • 真实经营造血能力诊断 (FCF > 0, ROE, 负债率)                   │
│                                 • 除息日 (Ex-Dividend Date) 自动化排查与助教报备                │
│                                 • 实盘收益跟踪与 Brinson 风格归因分析                           │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 二、 各成员详细工作量、技术深度与交付物核定

### 👤 成员 1：宏观量化与状态开关 (Macro Regime & Market State)
* **技术深度**：
  - 从单纯的技术面提升为自上而下（Top-down）的对冲基金视角；
  - 建模量化：标普500 200日均线大盘多空体制（Bull/Bear Regime）、10年期美债收益率敏感度、VIX 恐慌指数压力测试；
  - 结合 **2026年11月美国中期选举** 周期，分析选举落地后“政策不确定性消除（Uncertainty Removed）”引致的机构资金回流。
* **负责代码资产**：
  - `member1_macro_regime.py`：自动输出 `Member1_Macro_Regime_Analysis.csv` 状态报告。
* **报告撰写工作量 (60%)**：
  - 执笔 **Chapter 1: Macroeconomic Environment & Dynamic Regime Switching**（约 1.5 页）。
* **视频答辩内容 (20% 个人分)**：
  - **时长**：4~5 分钟。
  - **讲点**：展示美债收益率与 VIX 压力图，解释为什么当前宏观大环境适宜进攻型的高 Beta 活跃资产。

---

### 👤 成员 2：数据管道与回测工程 (Data Pipeline & Rolling Backtest)
* **技术深度**：
  - 解决金融回测的“未来函数（Look-Ahead Bias）”问题，实现物理数据隔离；
  - 严格落地老师课件 `Philosophy_3` 的 **Rolling Scheme（滚动时序方案）**；
  - 实现精准资金配平算法（严格满仓 $1,000,000.00，精确计算碎股 Fractional Shares）。
* **负责代码资产**：
  - `run_portfolio_pipeline.py`（主选股与 Excel 自动填表器）
  - `run_backtest_validation.py`（滚动回测引擎）
  - `run_active_liquidity_backtest.py`（股性活跃度回测）
* **报告撰写工作量 (60%)**：
  - 执笔 **Chapter 2: Quantitative Data Pipeline & Rolling Validation Scheme**（约 1.5 页）。
  - 提供核心绩效表（累计收益率、年化夏普比率、最大回撤、胜率）。
* **视频答辩内容 (20% 个人分)**：
  - **时长**：4~5 分钟。
  - **讲点**：演示 Python 管道如何实现无缝数据抓取，展示周度和月度净值超越大盘的对比曲线图。

---

### 👤 成员 3：微观技术面与筹码集中度 (Technical & Concentration Signals)
* **技术深度**：
  - 融合学术界顶尖成果：De Bondt 反转假说、Larry Connors RSI-2、Mark Minervini VCP 波动率收缩；
  - 深度实现老师课件 `Philosophy_4` 核心：**Transaction Value（成交额与筹码集中度）**，寻找主力吸筹痕迹；
  - 建立 **股性活跃度过滤器（Dollar Volume > $1.5亿 + ATR% >= 2.0% + RVOL >= 1.2）**。
* **负责代码资产**：
  - `run_daily_tail_accumulation_backtest.py`（日度跨周末 240 次实盘回测，收益翻倍至 +51.3%~+66.7%）。
* **报告撰写工作量 (60%)**：
  - 执笔 **Chapter 3: Microstructure Factors & Concentration Analysis**（约 2 页）。
  - 展示数学公式推导与候选标的形态结构图。
* **视频答辩内容 (20% 个人分)**：
  - **时长**：4~5 分钟。
  - **讲点**：深入对比“超跌反转”与“尾盘抢筹”的微观机理，展示筹码集中度如何将月度最大回撤压低至 -4.73%。

---

### 👤 成员 4：基本面风控、除息审计与归因 (Fundamental Risk & Governance)
* **技术深度**：
  - 落地老师课件 `Philosophy_2` 价值投资理念：排查暴雷的价值陷阱（Value Trap）；
  - 建立真实经营造血模型：自由现金流（FCF > 0）、ROE、负债权益比；成功排查出 ORCL（失血）和高杠杆投行股；
  - **合规关键人**：自动扫描候选股票在 11/6~12/4 持有期内是否发生除息（Ex-Dividend Date），落实大作业明文规定的向助教报备流程。
* **负责代码资产**：
  - `check_fundamental_health.py`（财务造血与经营健康诊断）
  - `member4_dividend_event_tracker.py`（除息日自动排查与报备追踪）
* **报告撰写工作量 (60%)**：
  - 执笔 **Chapter 4: Fundamental Quality Filter & Risk Governance** 与 **Chapter 5: Performance Attribution**（约 1.5 页）。
* **视频答辩内容 (20% 个人分)**：
  - **时长**：4~5 分钟。
  - **讲点**：展示如何通过现金流指标剔除高风险伪绩优股，展示除息日审查合规报告，并做实盘收益反思。

---

## 三、 工作量均衡度总结评估

1. **深度完全对等**：四位成员各自手握专属的 Python 脚本，不存在“有人只写纯文字、有人只写代码”的失衡现象；
2. **答辩互为补充**：从“宏观 $\rightarrow$ 架构 $\rightarrow$ 信号 $\rightarrow$ 风控”，答辩过程如同一家严谨对冲基金的投委会会议，极具说服力；
3. **零踩坑保障**：成员 4 专职盯防除息报备与财务暴雷，确保整个项目不会因为低级规则疏忽被扣分。
