# TradingLab 🧪⚡

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/react-%2320232a.svg?logo=react&logoColor=%2361DAFB)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![TypeScript](https://img.shields.io/badge/typescript-%23007ACC.svg?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![TailwindCSS](https://img.shields.io/badge/tailwindcss-%2338B2AC.svg?logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)]()
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)]()

**当金融遇上极客精神，量化交易从此变成一场高能实验！**

> *"在 TradingLab，没有'韭菜'，只有尚未完成实验的交易研究员。"*  
> —— 实验室墙上的涂鸦

## 📚 简介

TradingLab 是一个功能强大的股票数据获取与回测平台，让你像科学家一样严谨地验证交易策略。无论你是量化交易新手还是经验丰富的交易员，TradingLab 都能帮助你构建、测试和优化交易策略，降低投资风险，提高收益率。

## ✨ 特性

- 📊 **可视化实验室**：一键生成专业级回测报告，收益率、交易记录、价格走势与信号图表一目了然
- 🌐 **全市场覆盖**：内置数据提取器，可通过多个数据源获取需要的股票数据，并且智能切换可用的数据源
- 🧪 **策略实验室**：5+经典策略模板（动量、均值回归、套利等），开箱即用
- 🔄 **批量回测**：支持多股票、多策略、多参数的批量回测，快速找出最优组合
- 📈 **性能分析**：全面的回测统计指标，包括夏普比率、最大回撤、胜率等，帮助你评估策略表现
- 🔍 **策略优化**：内置参数优化工具，自动寻找最佳参数组合
- 🕒 **定时任务**：支持定时拉取股票数据，定时执行回测策略并保存结果

## 🛠️ 技术栈

### 前端技术

| 技术 | 描述 |
| --- | --- |
| React | 用户界面库 |
| TypeScript | 类型安全的 JavaScript 超集 |
| Tailwind CSS | 实用优先的 CSS 框架 |
| Shadcn/ui | 基于 Radix UI 的组件库 |
| TanStack Query | 数据获取和缓存库 |
| Recharts & Highcharts | 数据可视化图表库 |
| Wouter | 轻量级路由库 |
| Zod | TypeScript 优先的模式验证 |
| React Hook Form | 表单处理库 |

### 后端技术

| 技术 | 描述 |
| --- | --- |
| FastAPI | 高性能 Python API 框架 |
| SQLAlchemy | Python SQL 工具包和 ORM |
| Pydantic | 数据验证和设置管理 |
| SQLite | 轻量级数据库 |
| AkShare | 金融数据接口 |
| Backtesting.py | 回测框架 |
| TA-Lib | 技术分析库 |
| Scikit-learn | 机器学习库 |
| APScheduler | 任务调度库 |

## 🚀 快速开始

### 系统要求

- [Python 3.13+](https://www.python.org/)
- [uv](https://github.com/astral-sh/uv) (Python 包管理工具)
- [Node.js 23.2.0+](https://nodejs.org/)
- [pnpm](https://pnpm.io/) (推荐的 Node.js 包管理工具)
- [SQLite](https://sqlite.org/) (内置)

### 安装与运行

```bash
# 克隆实验室仓库
git clone https://github.com/souloss/TradingLab.git
cd TradingLab

# 安装后端依赖
cd backend
uv venv
uv pip install -e .

# 运行后端服务
cd tradingapi
uvicorn main:app --reload

# 在新终端中安装前端依赖
cd frontend
pnpm install

# 运行前端服务
pnpm dev
```

或者使用 Makefile 简化操作：

```bash
# 安装并运行后端
make run-backend

# 安装并运行前端
make run-frontend
```

## 📖 使用指南

### 获取股票数据

1. 访问主页，点击「数据管理」
2. 输入股票代码（如：000001 平安银行）
3. 选择日期范围
4. 点击「获取数据」
5. 数据将自动保存到本地数据库

### 运行回测

1. 访问「策略回测」页面
2. 选择股票和日期范围
3. 选择策略（如：双均线交叉）
4. 设置策略参数（如：快线周期=5，慢线周期=20）
5. 点击「开始回测」
6. 查看回测结果和性能指标

## 🧩 API 参考

TradingLab 提供了完整的 RESTful API，可用于获取股票数据、运行回测和管理策略。

### 主要 API 端点

- `GET /api/v1/stocks`: 获取股票列表
- `GET /api/v1/stocks/{code}`: 获取单个股票信息
- `GET /api/v1/stocks/{code}/daily`: 获取股票日线数据
- `POST /api/v1/backtest/single`: 运行单股票回测
- `POST /api/v1/backtest/multiple`: 运行多股票回测
- `GET /api/v1/strategies`: 获取可用策略列表

完整 API 文档请访问：[http://localhost:8000/docs](http://localhost:8000/docs)

## 🤝 如何贡献

我们欢迎各种形式的贡献，无论是新功能、文档改进还是 bug 修复。

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

### 贡献指南

- 添加新策略：在 `backend/tradingapi/strategy/strategies` 目录下创建新策略
- 添加新指标：在 `backend/tradingapi/strategy/indicators` 目录下添加新指标
- 添加新数据源：在 `backend/tradingapi/fetcher/datasources` 目录下实现新的数据源

## 📄 许可证

本项目采用 MIT 许可证 - 详情请参阅 [LICENSE](LICENSE) 文件

## 📊 项目截图

### 主页
![主页截图](screenshots/homepage.png)

### 单股策略回测
![个股回测截图](screenshots/single-stock-backtest.png)

### 多股策略回测
![选股回测截图](screenshots/mul-stock-backtest.png)

### 回测结果
![回测页面截图](screenshots/backtest.png)

---

<div align="center">
<strong>TradingLab</strong> - 让量化交易成为一场激动人心的科学实验！
</div>

### 参考
- [财报狗](https://statementdog.com/)： 这是一个优秀的参考案例！