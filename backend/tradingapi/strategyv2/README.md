## 基于 ta-lib 和 backtesting.py 的回测模块

### Backtesting.py 使用教程
`backtesting.py` 是一个非常适合做 量化策略回测 的 Python 库，主要特点是简单、易用，同时提供丰富的可扩展性。

#### 1. 安装
```python
pip install backtesting
```
#### 2. 基础概念
- Strategy：策略类，需要继承 backtesting.Strategy。
- data：历史数据对象，必须包含 Open, High, Low, Close, Volume 列。
- Position：当前持仓对象，提供 size, pl, pl_pct, close() 等方法。
- Broker：内部管理资金、手续费、杠杆等逻辑。
- Trade：每笔交易记录，包括 entry_price, exit_price, size 等。

#### 3. 基本回测流程
```python
import pandas as pd
from backtesting import Backtest, Strategy

# 1. 准备数据
data = pd.read_csv('your_data.csv', parse_dates=['Date'])
data.set_index('Date', inplace=True)

# 2. 定义策略
class MyStrategy(Strategy):
    def init(self):
        # 在回测开始时只运行一次，用于初始化指标
        self.sma10 = self.I(pd.Series.rolling, self.data.Close, 10).mean()

    def next(self):
        # 每个 bar 会调用一次
        if self.data.Close[-1] > self.sma10[-1] and not self.position:
            self.buy()  # 买入
        elif self.data.Close[-1] < self.sma10[-1] and self.position:
            self.position.close()  # 卖出

# 3. 执行回测
bt = Backtest(data, MyStrategy, cash=100_000, commission=.002)
stats = bt.run()
bt.plot()
```

##### 参数说明
- Backtest(data, strategy, cash, commission, margin, trade_on_close, exclusive_orders, hedging, ... )
- data: pd.DataFrame，必须包含 Open, High, Low, Close, Volume 列
- strategy: 继承 Strategy 的策略类
- cash: 初始资金
- commission: 每笔交易手续费比例
- margin: 保证金比例
- trade_on_close: 是否在收盘价交易
- exclusive_orders: 是否同一时间只允许一个持仓
- hedging: 是否允许对冲

#### 4. Strategy 类用法
##### 常用方法
```python
class MyStrategy(Strategy):
    def init(self):
        # 计算指标
        self.sma10 = self.I(pd.Series.rolling, self.data.Close, 10).mean()

    def next(self):
        # 当前价格
        price = self.data.Close[-1]

        # 下单
        self.buy(size=1.0)            # 买入，size=1.0 表示全仓
        self.sell(size=0.5)           # 卖出，半仓
        self.position.close()          # 平仓
```
##### Position 属性
- position.size：当前持仓量（正数多头，负数空头）
- position.is_long / position.is_short：是否多头/空头
- position.pl：浮动盈亏（现金）
- position.pl_pct：浮动盈亏百分比
- position.close(portion=1.0)：平掉部分或全部仓位

#### 5. 常用工具函数
backtesting.lib 包含许多常用指标函数：
- crossover(a, b)：判断 a 是否向上穿过 b
- crossunder(a, b)：判断 a 是否向下穿过 b
- resample_apply(series, period, func)：对时间序列按周期聚合
- signal_series：帮助生成买卖信号序列

##### 示例：
```python
from backtesting.lib import crossover

if crossover(self.sma10, self.sma20) and not self.position:
    self.buy()
```

#### 6. 高阶用法
##### 6.1 参数优化
```python
stats = bt.optimize(
    period1=range(5, 30, 5),
    period2=range(20, 100, 10),
    maximize='Equity Final [$]'
)
```
- maximize: 选择优化目标
- 支持整数参数搜索，也可以用 decimal 的列表

#### 6.2 标记特定日期

如果你希望在 next 中对特定日期做标记：
```python
class MarkDatesStrategy(Strategy):
    def init(self):
        self.marked_dates = []

    def next(self):
        today = self.data.index[-1]
        # 假设我们想标记 2025-01-15 和 2025-03-21
        if today in [pd.Timestamp("2025-01-15"), pd.Timestamp("2025-03-21")]:
            self.marked_dates.append(today)
```
回测后，你可以通过 strategy.marked_dates 查看标记：
```python
bt.run()
print(bt.strategy.marked_dates)
```

#### 6.3 绘图增强
bt.plot() 可以自动绘制：
- 价格曲线
- 交易标记
- 持仓变化
- 指标（通过 self.I() 生成的 Series）
- bt.plot(plot_volume=True) 显示成交量
- bt.plot(plot_equity=True) 显示权益曲线

#### 6.4 高阶功能
- 止损/止盈：在 buy 或 sell 中指定 sl 和 tp
- 部分平仓：self.position.close(portion=0.5)
- 多策略组合：用多个策略分别回测，或用优化函数自动调参
- 统计指标：回测结果 stats 包含：

```python
stats['Return [%]']           # 总收益
stats['CAGR [%]']             # 年化收益
stats['Max. Drawdown [%]']    # 最大回撤
stats['Sharpe Ratio']          # 夏普比率
stats['Sortino Ratio']         # 索提诺比率
stats['Profit Factor']         # 盈利因子
stats['_trades']               # 每笔交易记录 DataFrame
```

#### 6.5 自定义指标与函数

你可以在 init() 中通过 self.I() 注册任何函数：
```python
def my_indicator(series, n):
    return series.rolling(n).mean() + 5

self.custom_ind = self.I(my_indicator, self.data.Close, 10)
```

回测期间，self.custom_ind 会随着时间更新。

#### 7. 实战案例：多头量能策略 + 日期标记
```python
class VolumeSpikeLongMark(Strategy):
    period = 60
    high_multiplier = 2.0
    low_multiplier = 0.5
    mark_dates_list = [pd.Timestamp("2025-01-15"), pd.Timestamp("2025-03-21")]

    def init(self):
        self.vol_ma = self.I(pd.Series.rolling, self.data.Volume, self.period).mean()
        self.marked_dates = []

    def next(self):
        price = self.data.Close[-1]
        vol = self.data.Volume[-1]
        vol_ma = self.vol_ma[-1]

        price_min = self.data.Close[-self.period:].min()
        price_max = self.data.Close[-self.period:].max()

        # 标记特定日期
        today = self.data.index[-1]
        if today in self.mark_dates_list:
            self.marked_dates.append(today)

        # 买卖逻辑（多头）
        if not self.position and vol < vol_ma * self.low_multiplier and price <= price_min * 1.05:
            self.buy(size=1.0)
        elif self.position and vol > vol_ma * self.high_multiplier and price >= price_max * 0.95:
            self.position.close()
```

回测后查看标记日期：
```python
bt = Backtest(data, VolumeSpikeLongMark, cash=100_000, commission=0.001)
stats = bt.run()
print(bt.strategy.marked_dates)
```

#### ✅ 总结：
- init()：初始化指标，只执行一次
- next()：每个 Bar 执行一次，决定买卖
- self.I(func, *args)：注册指标，用于绘图
- self.position：管理当前仓位
- 多头策略只需要在买入信号时全仓买入，卖出信号时全仓卖出
- Backtest.optimize() 可以对策略参数进行网格搜索优化
- 可以在 next() 中标记特定日期，回测后直接查看