import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import talib
import yfinance as yf
from backtesting import Backtest, Strategy
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from skopt import BayesSearchCV
from skopt.space import Categorical, Integer, Real
from xgboost import XGBClassifier


# 1. 数据准备与特征工程
def prepare_data(ticker, start_date, end_date):
    """
    获取股票历史数据并计算技术指标
    """
    # 下载历史数据
    data = yf.download(ticker, start=start_date, end=end_date)

    # 计算价格变化率
    data["Returns"] = data["Close"].pct_change()

    # 计算技术指标
    # 趋势指标
    data["SMA_10"] = talib.SMA(data["Close"], timeperiod=10)
    data["SMA_20"] = talib.SMA(data["Close"], timeperiod=20)
    data["SMA_50"] = talib.SMA(data["Close"], timeperiod=50)
    data["EMA_12"] = talib.EMA(data["Close"], timeperiod=12)
    data["EMA_26"] = talib.EMA(data["Close"], timeperiod=26)
    data["ADX"] = talib.ADX(data["High"], data["Low"], data["Close"], timeperiod=14)
    data["MACD"], data["MACD_signal"], _ = talib.MACD(data["Close"])

    # 动量指标
    data["RSI"] = talib.RSI(data["Close"], timeperiod=14)
    data["Stoch_%K"], data["Stoch_%D"] = talib.STOCH(
        data["High"], data["Low"], data["Close"]
    )
    data["Momentum"] = talib.MOM(data["Close"], timeperiod=10)

    # 波动率指标
    data["ATR"] = talib.ATR(data["High"], data["Low"], data["Close"], timeperiod=14)
    data["Bollinger_Upper"], data["Bollinger_Middle"], data["Bollinger_Lower"] = (
        talib.BBANDS(data["Close"], timeperiod=20)
    )

    # 成交量指标
    data["OBV"] = talib.OBV(data["Close"], data["Volume"])
    data["Volume_Change"] = data["Volume"].pct_change()

    # 特征工程
    data["SMA_Crossover"] = np.where(data["SMA_10"] > data["SMA_20"], 1, 0)
    data["MACD_Crossover"] = np.where(data["MACD"] > data["MACD_signal"], 1, 0)
    data["Bollinger_Position"] = (data["Close"] - data["Bollinger_Lower"]) / (
        data["Bollinger_Upper"] - data["Bollinger_Lower"]
    )
    data["RSI_Overbought"] = np.where(data["RSI"] > 70, 1, 0)
    data["RSI_Oversold"] = np.where(data["RSI"] < 30, 1, 0)

    # 创建滞后特征
    for lag in [1, 2, 3, 5]:
        data[f"Return_lag_{lag}"] = data["Returns"].shift(lag)
        data[f"Volume_lag_{lag}"] = data["Volume"].shift(lag)

    # 目标变量 - 未来5天收益
    data["Future_Return"] = data["Returns"].shift(-5).rolling(5).sum()

    # 删除缺失值
    data = data.dropna()

    return data


# 2. 特征选择与目标变量定义
def create_features_and_labels(data, return_threshold=0.05):
    """
    创建特征矩阵和目标标签
    """
    # 特征集 - 选择最重要的特征
    features = data[
        [
            "SMA_10",
            "SMA_20",
            "SMA_50",
            "EMA_12",
            "EMA_26",
            "ADX",
            "MACD",
            "MACD_signal",
            "RSI",
            "Stoch_%K",
            "Stoch_%D",
            "Momentum",
            "ATR",
            "Bollinger_Position",
            "OBV",
            "Volume_Change",
            "SMA_Crossover",
            "MACD_Crossover",
            "Bollinger_Position",
            "RSI_Overbought",
            "RSI_Oversold",
            "Return_lag_1",
            "Return_lag_2",
            "Return_lag_3",
            "Volume_lag_1",
            "Volume_lag_2",
        ]
    ].copy()

    # 创建标签 - 基于未来收益
    data["Label"] = np.where(
        data["Future_Return"] > return_threshold,
        1,  # 买入信号
        np.where(data["Future_Return"] < -return_threshold, -1, 0),
    )  # 卖出信号

    labels = data["Label"]

    return features, labels


# 3. 模型训练与优化
def train_optimized_model(features, labels):
    """
    使用贝叶斯优化训练多个模型并选择最佳模型
    """
    # 时间序列分割
    tscv = TimeSeriesSplit(n_splits=5)

    # 定义模型和搜索空间
    models = {
        "RandomForest": {
            "model": RandomForestClassifier(random_state=42, class_weight="balanced"),
            "params": {
                "n_estimators": Integer(50, 300),
                "max_depth": Integer(3, 15),
                "min_samples_split": Integer(2, 10),
                "min_samples_leaf": Integer(1, 5),
            },
        },
        "XGBoost": {
            "model": XGBClassifier(
                random_state=42, use_label_encoder=False, eval_metric="logloss"
            ),
            "params": {
                "n_estimators": Integer(50, 300),
                "max_depth": Integer(3, 10),
                "learning_rate": Real(0.01, 0.3, prior="log-uniform"),
                "subsample": Real(0.6, 1.0),
                "colsample_bytree": Real(0.6, 1.0),
            },
        },
        "GradientBoosting": {
            "model": GradientBoostingClassifier(random_state=42),
            "params": {
                "n_estimators": Integer(50, 300),
                "learning_rate": Real(0.01, 0.3, prior="log-uniform"),
                "max_depth": Integer(3, 10),
                "min_samples_split": Integer(2, 10),
            },
        },
        "SVM": {
            "model": make_pipeline(
                StandardScaler(),
                SVC(probability=True, class_weight="balanced", random_state=42),
            ),
            "params": {
                "svc__C": Real(1e-3, 1e3, prior="log-uniform"),
                "svc__gamma": Real(1e-4, 1e-1, prior="log-uniform"),
                "svc__kernel": Categorical(["rbf", "poly", "sigmoid"]),
            },
        },
    }

    best_score = -np.inf
    best_model = None
    best_model_name = ""

    # 训练并优化每个模型
    for model_name, model_info in models.items():
        print(f"\n=== 训练 {model_name} 模型 ===")

        opt = BayesSearchCV(
            model_info["model"],
            model_info["params"],
            n_iter=30,
            cv=tscv,
            scoring="f1_weighted",
            n_jobs=-1,
            random_state=42,
        )

        opt.fit(features, labels)

        print(f"{model_name} 最佳参数: {opt.best_params_}")
        print(f"{model_name} 最佳分数: {opt.best_score_:.4f}")

        if opt.best_score_ > best_score:
            best_score = opt.best_score_
            best_model = opt.best_estimator_
            best_model_name = model_name

    print(f"\n最佳模型: {best_model_name} (F1分数: {best_score:.4f})")

    # 在整个数据集上训练最佳模型
    best_model.fit(features, labels)

    return best_model


# 4. 策略开发与回测
class AIOptimizedStrategy(Strategy):
    """
    基于AI预测的优化交易策略
    """

    def init(self):
        # 预计算特征
        self.df = self.data.df
        self.buy_signals = self.I(lambda: np.zeros(len(self.data)), name="buy_signals")
        self.sell_signals = self.I(
            lambda: np.zeros(len(self.data)), name="sell_signals"
        )

        # 设置参数
        self.risk_per_trade = 0.02  # 每笔交易风险2%
        self.take_profit_multiplier = 2.0  # 止盈倍数

    def next(self):
        # 每天运行策略
        current_idx = len(self.data) - 1

        # 获取当天的预测信号
        buy_signal = self.buy_signals[current_idx]
        sell_signal = self.sell_signals[current_idx]

        # 交易逻辑
        if not self.position:
            if buy_signal > 0.7:  # 强买入信号
                # 基于ATR计算头寸大小和止损
                atr = self.df["ATR"].iloc[current_idx]
                stop_loss = self.data.Close[-1] - 1.5 * atr

                # 计算头寸大小 (基于风险比例)
                risk_per_share = self.data.Close[-1] - stop_loss
                position_size = (self.equity * self.risk_per_trade) / risk_per_share

                # 计算止盈
                take_profit = (
                    self.data.Close[-1] + self.take_profit_multiplier * risk_per_share
                )

                # 买入
                self.buy(size=position_size, sl=stop_loss, tp=take_profit)

        elif self.position.is_long:
            # 强卖出信号
            if sell_signal > 0.7:
                self.position.close()

            # 动态止损
            elif self.data.Close[-1] < self.position.sl:
                self.position.close()

            # 部分止盈
            elif self.data.Close[-1] >= self.position.tp * 0.8:
                # 平掉一半仓位
                self.position.close(0.5)
                # 移动止损到盈亏平衡点
                self.position.sl = self.position.entry_price


# 5. 寻找最佳买卖点
def find_best_entry_exit(data, predictions):
    """
    分析预测结果，找到最佳买卖点
    """
    # 计算累积收益
    data["Cumulative_Return"] = (1 + data["Returns"]).cumprod()

    # 标记预测的买卖点
    data["Pred_Buy"] = np.where(predictions["Buy_Prob"] > 0.7, 1, 0)
    data["Pred_Sell"] = np.where(predictions["Sell_Prob"] > 0.7, 1, 0)

    # 找到所有买入信号点
    buy_points = data[data["Pred_Buy"] == 1].copy()
    buy_points["Entry_Index"] = buy_points.index

    best_trades = []

    # 分析每个买入点的后续表现
    for idx, row in buy_points.iterrows():
        # 获取买入后的数据
        future_data = data.loc[idx:]

        # 找到下一个卖出信号
        next_sell = future_data[future_data["Pred_Sell"] == 1]

        if not next_sell.empty:
            first_sell = next_sell.iloc[0]
            hold_period = (first_sell.name - idx).days
            buy_price = row["Close"]
            sell_price = first_sell["Close"]
            return_pct = (sell_price - buy_price) / buy_price * 100

            # 计算最大回撤
            min_price = future_data.loc[: first_sell.name]["Close"].min()
            max_drawdown = (
                (min_price - buy_price) / buy_price * 100
                if min_price < buy_price
                else 0
            )

            # 添加到结果
            best_trades.append(
                {
                    "Buy_Date": idx,
                    "Sell_Date": first_sell.name,
                    "Hold_Period": hold_period,
                    "Return_Pct": return_pct,
                    "Max_Drawdown": max_drawdown,
                    "Buy_Confidence": row["Buy_Prob"],
                    "Sell_Confidence": first_sell["Sell_Prob"],
                }
            )

    # 转换为DataFrame并排序
    trades_df = pd.DataFrame(best_trades)

    if trades_df.empty:
        print("未找到有效的买卖组合")
        return None

    # 按收益率排序
    best_by_return = trades_df.sort_values("Return_Pct", ascending=False).iloc[0]

    # 按夏普比率排序 (收益率/回撤)
    trades_df["Sharpe_Ratio"] = trades_df["Return_Pct"] / (
        abs(trades_df["Max_Drawdown"]) + 1e-5
    )
    best_by_sharpe = trades_df.sort_values("Sharpe_Ratio", ascending=False).iloc[0]

    # 按持有期排序
    best_by_hold_period = trades_df.sort_values(
        ["Return_Pct", "Hold_Period"], ascending=[False, True]
    ).iloc[0]

    return {
        "by_return": best_by_return,
        "by_sharpe": best_by_sharpe,
        "by_hold_period": best_by_hold_period,
    }


# 主程序
if __name__ == "__main__":
    # 参数设置
    TICKER = "AAPL"
    START_DATE = "2022-01-01"
    END_DATE = "2023-01-01"
    RETURN_THRESHOLD = 0.05  # 5%收益阈值

    print(f"分析 {TICKER} 在 {START_DATE} 至 {END_DATE} 的最佳买卖点...")

    # 1. 准备数据
    stock_data = prepare_data(TICKER, START_DATE, END_DATE)
    features, labels = create_features_and_labels(stock_data, RETURN_THRESHOLD)

    # 2. 训练模型
    print("\n训练和优化AI模型...")
    model = train_optimized_model(features, labels)

    # 3. 生成预测
    buy_probs = model.predict_proba(features)[:, 2]  # 买入概率 (类别2)
    sell_probs = model.predict_proba(features)[:, 0]  # 卖出概率 (类别0)

    # 保存预测结果
    predictions = pd.DataFrame(
        {"Date": stock_data.index, "Buy_Prob": buy_probs, "Sell_Prob": sell_probs}
    ).set_index("Date")

    # 合并到主数据
    stock_data = stock_data.join(predictions)

    # 4. 寻找最佳买卖点
    print("\n分析最佳买卖点...")
    best_points = find_best_entry_exit(stock_data, predictions)

    if best_points:
        print("\n===== 最佳买卖点分析 =====")
        print(
            f"按收益率最佳: 买入 {best_points['by_return']['Buy_Date'].date()}, "
            f"卖出 {best_points['by_return']['Sell_Date'].date()}, "
            f"收益: {best_points['by_return']['Return_Pct']:.2f}%"
        )

        print(
            f"按风险回报比最佳: 买入 {best_points['by_sharpe']['Buy_Date'].date()}, "
            f"卖出 {best_points['by_sharpe']['Sell_Date'].date()}, "
            f"夏普比率: {best_points['by_sharpe']['Sharpe_Ratio']:.2f}"
        )

        print(
            f"按持有期最佳: 买入 {best_points['by_hold_period']['Buy_Date'].date()}, "
            f"卖出 {best_points['by_hold_period']['Sell_Date'].date()}, "
            f"持有: {best_points['by_hold_period']['Hold_Period']}天, "
            f"收益: {best_points['by_hold_period']['Return_Pct']:.2f}%"
        )

    # 5. 可视化结果
    plt.figure(figsize=(14, 10))

    # 价格和买卖点
    plt.subplot(2, 1, 1)
    plt.plot(stock_data["Close"], label="价格", alpha=0.7)

    # 标记买入点
    buy_signals = stock_data[stock_data["Buy_Prob"] > 0.7]
    plt.scatter(
        buy_signals.index,
        buy_signals["Close"],
        marker="^",
        color="g",
        s=100,
        label="买入信号",
    )

    # 标记卖出点
    sell_signals = stock_data[stock_data["Sell_Prob"] > 0.7]
    plt.scatter(
        sell_signals.index,
        sell_signals["Close"],
        marker="v",
        color="r",
        s=100,
        label="卖出信号",
    )

    if best_points:
        # 标记最佳买卖点
        plt.scatter(
            best_points["by_return"]["Buy_Date"],
            stock_data.loc[best_points["by_return"]["Buy_Date"], "Close"],
            marker="*",
            color="blue",
            s=200,
            label="最佳买入(收益)",
        )
        plt.scatter(
            best_points["by_return"]["Sell_Date"],
            stock_data.loc[best_points["by_return"]["Sell_Date"], "Close"],
            marker="*",
            color="purple",
            s=200,
            label="最佳卖出(收益)",
        )

        plt.scatter(
            best_points["by_sharpe"]["Buy_Date"],
            stock_data.loc[best_points["by_sharpe"]["Buy_Date"], "Close"],
            marker="*",
            color="cyan",
            s=200,
            label="最佳买入(风险回报)",
        )
        plt.scatter(
            best_points["by_sharpe"]["Sell_Date"],
            stock_data.loc[best_points["by_sharpe"]["Sell_Date"], "Close"],
            marker="*",
            color="magenta",
            s=200,
            label="最佳卖出(风险回报)",
        )

    plt.title(f"{TICKER} 价格与买卖信号")
    plt.legend()

    # 预测概率
    plt.subplot(2, 1, 2)
    plt.plot(stock_data["Buy_Prob"], label="买入概率", color="g", alpha=0.7)
    plt.plot(stock_data["Sell_Prob"], label="卖出概率", color="r", alpha=0.7)
    plt.axhline(y=0.7, color="gray", linestyle="--", alpha=0.5)
    plt.title("买卖信号概率")
    plt.legend()

    plt.tight_layout()
    plt.savefig(f"{TICKER}_trading_signals.png", dpi=300)
    plt.show()

    # 6. 回测策略
    print("\n回测AI策略...")

    class BacktestStrategy(AIOptimizedStrategy):
        def init(self):
            super().init()
            self.df = self.data.df
            self.buy_signals = self.I(
                lambda: self.df["Buy_Prob"].values, name="buy_signals"
            )
            self.sell_signals = self.I(
                lambda: self.df["Sell_Prob"].values, name="sell_signals"
            )

    bt_data = stock_data.copy().reset_index()
    bt_data.columns = [col.capitalize() for col in bt_data.columns]

    bt = Backtest(
        bt_data,
        BacktestStrategy,
        cash=10000,
        commission=0.001,  # 0.1% 手续费
        exclusive_orders=True,
    )

    results = bt.run()
    print("\n===== 回测结果 =====")
    print(f"最终资产: ${results['Equity Final'][0]:.2f}")
    print(f"总收益率: {results['Return [%]']:.2f}%")
    print(f"最大回撤: {results['Max Drawdown [%]']:.2f}%")
    print(f"夏普比率: {results['Sharpe Ratio']:.2f}")
    print(f"交易次数: {results['# Trades']}")

    # 可视化回测结果
    bt.plot()
