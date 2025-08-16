# TradingLab 🧪⚡
**当金融遇上极客精神，量化交易从此变成一场高能实验！**  
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/react-%2320232a.svg?logo=react)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)

> *“在 TradingLab，没有'韭菜'，只有尚未完成实验的交易研究员。”*  
> —— 实验室墙上的涂鸦

---


## 🌟 核心亮点
- 📊 **可视化实验室**：一键生成专业级回测报告，收益率，交易记录，价格走势与信号图表一目了然；
- 🌐 **全市场覆盖**：内置数据提取器，可通过多个数据源获取需要的股票数据；
- 🧪 **策略实验室**：5+经典策略模板（动量、均值回归、套利等），开箱即用！


## 🚀 5分钟极速安装

### 系统要求
- [Python 3.13+](https://www.python.org/)
- [uv](https://github.com/astral-sh/uv)
- [Node.js 23.2.0+](https://nodejs.org/)
- [SQLite (内置)](https://sqlite.org/)

### 后端安装启动
```bash
# 克隆实验室仓库
git clone https://github.com/souloss/TradingLab.git
cd TradingLab

# 安装前端和后端依赖
make run-backend

# 运行
make run-backend
```

### 🧪 使用
主页：
![主页截图](screenshots/homepage.png)

单股策略回测：
![个股回测截图](screenshots/single-stock-backtest.png)

多股策略回测：
![选股回测截图](screenshots/mul-stock-backtest.png)

回测结果：
![回测页面截图](screenshots/backtest.png)

### 📚 实验手册

#### 快速开始：你的第一个策略
- 在 backend/tradingapi/strategy 下定义你的技术指标和买卖策略；
- 通过 fetcher 抓取真正的交易数据；
- 验证你的策略！

<div align="center">
**TradingLab** - 让量化交易成为一场激动人心的科学实验！
</div>