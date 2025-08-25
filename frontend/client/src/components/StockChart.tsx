import { useEffect, useMemo, useRef, useState } from "react";
import type { StockData, BacktestStats, TradeRecord, EquityPoint } from "../types";;

interface StockChartProps {
  data: StockData[];
  backtestStats: BacktestStats; // 使用回测结果替代原来的 trades
  selectedPeriod: string; // "1d" | "1w" | "1m" | "3m" | "6m" | "1y"
  onPeriodChange: (period: string) => void;
}

const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone; 
console.log("用户时区为:" + userTimezone)
// ---- 工具函数 ----
/**
 * 将北京时间（Asia/Shanghai）转换为 UTC 毫秒时间戳
 * @param beijingTime - 北京时间字符串，如 "2024-08-23" 或 "2024-08-23 00:00:00"
 * @returns UTC 毫秒时间戳
 */
function beijingDateToUtc(dateStr: string): number {
  // 强制补上 00:00:00
  if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
    dateStr += "T00:00:00";
  }
  // 用 Date.UTC 构造 UTC 时间戳，再减去 8 小时（得到北京时间）
  const d = new Date(dateStr);
  return Date.UTC(
    d.getFullYear(),
    d.getMonth(),
    d.getDate(),
    d.getHours()-8,
    d.getMinutes(),
    d.getSeconds()
  );
}
type Tick = { date: string | Date; close: number };
const calculateMA = (data: Tick[], period: number): Array<[number, number]> => {
  if (period <= 0 || data.length < period) return [];
  const result: Array<[number, number]> = [];
  let sum = 0;
  for (let i = 0; i < data.length; i++) {
    const close = Number((data[i] as any).close);
    if (isNaN(close)) continue;
    sum += close;
    if (i >= period) sum -= Number((data[i - period] as any).close);
    if (i >= period - 1) {
      const maValue = sum / period;
      result.push([new Date((data[i] as any).date).getTime(), Math.round(maValue * 100) / 100]);
    }
  }
  return result;
};

type OHLC = { date: string | Date; high: number; low: number; close: number };

const calculateATR = (data: OHLC[], period = 14): Array<[number, number]> => {
  if (data.length < period + 1) return [];
  const result: Array<[number, number]> = [];
  const trs: number[] = [];

  for (let i = 1; i < data.length; i++) {
    const prevClose = data[i - 1].close;
    const high = data[i].high;
    const low = data[i].low;

    const tr = Math.max(
      high - low,
      Math.abs(high - prevClose),
      Math.abs(low - prevClose)
    );
    trs.push(tr);

    if (trs.length >= period) {
      const atr = trs.slice(-period).reduce((a, b) => a + b, 0) / period;
      result.push([
        new Date(data[i].date).getTime(),
        Math.round(atr * 100) / 100,
      ]);
    }
  }
  return result;
};

const getRangeMs = (period: string): number => {
  const day = 24 * 60 * 60 * 1000;
  switch (period) {
    case "1d":
      return 1 * day;
    case "1w":
      return 7 * day;
    case "1m":
      return 30 * day;
    case "3m":
      return 90 * day;
    case "6m":
      return 180 * day;
    case "1y":
      return 365 * day;
    default:
      return Number.POSITIVE_INFINITY; // 全部
  }
};

export default function StockChart({
  data,
  backtestStats,
  selectedPeriod,
  onPeriodChange,
}: StockChartProps) {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<any>(null);
  const highchartsRef = useRef<any>(null);

  const [highchartsLoaded, setHighchartsLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const periods = [
    { value: "1d", label: "1天" },
    { value: "1w", label: "1周" },
    { value: "1m", label: "1月" },
    { value: "3m", label: "3月" },
    { value: "6m", label: "6月" },
    { value: "1y", label: "1年" },
  ];

  // ---- 数据预处理（排序，便于窗口裁剪和均线计算）----
  const sortedData = useMemo(() => {
    const d = Array.isArray(data) ? [...data] : [];
    d.sort(
      (a, b) =>
        new Date(a.date).getTime() - new Date(b.date).getTime()
    );
    return d;
  }, [data]);

  const latestTs = useMemo(() => {
    if (!sortedData.length) return NaN;
    return new Date(sortedData[sortedData.length - 1].date).getTime();
  }, [sortedData]);

  const cutoff = useMemo(() => {
    const range = getRangeMs(selectedPeriod);
    return isNaN(latestTs) ? NaN : latestTs - range;
  }, [latestTs, selectedPeriod]);

  // 全量价格/成交量（先算再裁剪）
  const priceDataAll = useMemo(
    () =>
      sortedData.map((item) => [
        beijingDateToUtc(item.date),
        item.open,
        item.high,
        item.low,
        item.close,
      ]) as Array<[number, number, number, number, number]>,
    [sortedData]
  );

  const volumeDataAll = useMemo(
    () =>
      sortedData.map((item) => [
        beijingDateToUtc(item.date),
        item.volume,
      ]) as Array<[number, number]>,
    [sortedData]
  );

  // 全量均线（按全量算，保证窗口开头的均线准确，再按窗口裁剪）
  const ma5All = useMemo(
    () => calculateMA(sortedData as unknown as Tick[], 5),
    [sortedData]
  );
  const ma10All = useMemo(
    () => calculateMA(sortedData as unknown as Tick[], 10),
    [sortedData]
  );
  const ma20All = useMemo(
    () => calculateMA(sortedData as unknown as Tick[], 20),
    [sortedData]
  );
  const atrAll = useMemo(
    () => calculateATR(sortedData as unknown as OHLC[], 14),
    [sortedData]
  );

  const atrLast = useMemo(() => {
    const atrAll = calculateATR(sortedData as unknown as OHLC[], 14);
    return atrAll.length > 0 ? atrAll[atrAll.length - 1][1] : null;
  }, [sortedData]);
  
  const [stopLossLine, stopWinLine] = useMemo(() => {
    if (!atrLast || sortedData.length === 0) return [[], []];

    const firstTs = new Date(sortedData[0].date).getTime();
    const lastTs = new Date(sortedData[sortedData.length - 1].date).getTime();
    const lastClose = sortedData[sortedData.length - 1].close;

    const stopLoss = lastClose - atrLast * 1.5;
    const stopWin = lastClose + atrLast * 3;

    return [
      [
        [firstTs, stopLoss],
        [lastTs, stopLoss],
      ],
      [
        [firstTs, stopWin],
        [lastTs, stopWin],
      ],
    ];
  }, [atrLast, sortedData]);

  // 根据 selectedPeriod 裁剪窗口数据
  const filterByCutoff = <T extends [number, ...any[]]>(arr: T[]) =>
    isNaN(cutoff) ? arr : arr.filter((row) => row[0] >= cutoff);

  // 主图指标（如果存在就画）
  const mainIndicators = [
    "ATR", 
    "RSI", 
    "K", 
    "D", 
    "J",
    "MACD",
    "MACD_Signal",
    "MACD_Hist",
    "BB_Upper",
    "BB_Middle",
    "BB_Lower",
    "Vol_MA5",
    "Vol_MA10",
    "Vol_MA20",
    "Vol_MA30",
    "Vol_MA60",
  ];
  const indicatorSeries = useMemo(() => {
    return mainIndicators
      .map(name => {
        const seriesData = sortedData
          .filter(item => item.extra_fields?.[name] != null)
          .map(item => [
            beijingDateToUtc(item.date),
            Number(item.extra_fields?.[name])
          ]) as Array<[number, number]>; 

        if (seriesData.length === 0) return null;
        return {
          type: "line" as const,
          name,
          data: filterByCutoff(seriesData),
          lineWidth: 1,
          yAxis: 2,
          tooltip: { valueDecimals: 2 },
        };
      })
      .filter(Boolean) as Highcharts.SeriesOptionsType[];
  }, [sortedData, cutoff]);
  const priceData = useMemo(() => filterByCutoff(priceDataAll), [priceDataAll, cutoff]);
  const volumeData = useMemo(() => filterByCutoff(volumeDataAll), [volumeDataAll, cutoff]);
  const ma5Data = useMemo(() => filterByCutoff(ma5All), [ma5All, cutoff]);
  const ma10Data = useMemo(() => filterByCutoff(ma10All), [ma10All, cutoff]);
  const ma20Data = useMemo(() => filterByCutoff(ma20All), [ma20All, cutoff]);

  const atrData = useMemo(() => filterByCutoff(atrAll), [atrAll, cutoff]);

  // 交易信号（仅 BUY/SELL，且按窗口裁剪）
  const tradePoints = useMemo(() => {
    if (!backtestStats || !backtestStats.trades) return { buyPoints: [], sellPoints: [], positionLines: [] };

    const buyPoints = backtestStats.trades.map((trade: TradeRecord) => ({
        x: beijingDateToUtc(trade.entry_time),
        y: trade.entry_price,
        marker: {
          symbol: "circle",
          fillColor: "#22c55e",
          lineColor: "#22c55e",
          lineWidth: 2,
          radius: 6,
        },
        dataLabels: {
          enabled: true,
          format: "B",
          style: { color: "#22c55e", fontWeight: "bold" },
        },
        // 添加自定义属性用于 tooltip
        trade: {
          type: "买入",
          price: trade.entry_price,
          size: trade.size,
        }
      }));

    const sellPoints = backtestStats.trades
      .map((trade: TradeRecord) => ({
        x: beijingDateToUtc(trade.exit_time),
        y: trade.exit_price,
        marker: {
          symbol: "circle",
          fillColor: "#ef4444",
          lineColor: "#ef4444",
          lineWidth: 2,
          radius: 6,
        },
        dataLabels: {
          enabled: true,
          format: "S",
          style: { color: "#ef4444", fontWeight: "bold" },
        },
        // 添加自定义属性用于 tooltip
        trade: {
          type: "卖出",
          price: trade.exit_price,
          size: trade.size,
        }
      }));

    // 创建持仓线
    const positionLines = backtestStats.trades.map((trade: TradeRecord) => ({
      type: "line" as const,
      name: `持仓 ${trade.tag || ''}`,
      data: [
        [beijingDateToUtc(trade.entry_time), trade.entry_price],
        [beijingDateToUtc(trade.exit_time), trade.exit_price]
      ],
      color: trade.pnl > 0 ? "#22c55e" : "#ef4444",
      lineWidth: 1,
      dashStyle: "Dash" as Highcharts.DashStyleValue,
      yAxis: 0,
      showInLegend: false,
      // 添加自定义属性用于 tooltip
      trade: {
        type: "持仓",
        entry_price: trade.entry_price,
        exit_price: trade.exit_price,
        size: trade.size,
        pnl: trade.pnl,
        return_pct: trade.return_pct,
        duration: trade.duration,
        tag: trade.tag,
        sl: trade.sl,
        tp: trade.tp
      }
    }));

    // 根据 selectedPeriod 裁剪数据
    const filteredBuyPoints = isNaN(cutoff) ? buyPoints : buyPoints.filter((p) => p.x >= cutoff);
    const filteredSellPoints = isNaN(cutoff) ? sellPoints : sellPoints.filter((p) => p.x >= cutoff);
    const filteredPositionLines = isNaN(cutoff)
      ? positionLines
      : positionLines.filter(line =>
        line.data[0][0] >= cutoff || line.data[1][0] >= cutoff
      );

    return {
      buyPoints: filteredBuyPoints,
      sellPoints: filteredSellPoints,
      positionLines: filteredPositionLines
    };
  }, [backtestStats, cutoff]);

  const initModule = (mod: any, Highcharts: any) => {
    if (typeof mod === "function") {
      mod(Highcharts);
    } else if (mod?.default && typeof mod.default === "function") {
      mod.default(Highcharts);
    }
  };

  // ---- 只加载一次 Highcharts（SSR 安全，且避免 default 导出差异）----
  useEffect(() => {
    let mounted = true;

    const loadHighcharts = async () => {
      try {
        // 1️⃣ 导入 Highstock 核心
        const mod = await import("highcharts/highstock");
        if (!mounted) return;
        const Highcharts = (mod as any).default || mod;

        // 2️⃣ 核心模块（必须先加载）
        const coreModules = await Promise.all([
          import("highcharts/modules/exporting"),
          import("highcharts/modules/export-data"),
          import("highcharts/modules/data"),
        ]);
        coreModules.forEach((m: any) => {
          // m 可能是函数模块或 { default: 函数 } 形式
          const fn = typeof m === "function" ? m : m?.default;
          if (typeof fn === "function") fn(Highcharts);
        });

        // 3️⃣ 扩展模块
        const extraModules = await Promise.all([
          import("highcharts/modules/full-screen"),
          import("highcharts/modules/drag-panes"),
          import("highcharts/modules/annotations"),
          import("highcharts/modules/price-indicator"),
          import("highcharts/modules/stock-tools"),
          import("highcharts/indicators/indicators-all"),
        ]);
        extraModules.forEach((m: any) => {
          const fn = typeof m === "function" ? m : m?.default;
          if (typeof fn === "function") fn(Highcharts);
        });
        // 4️⃣ 保存实例
        highchartsRef.current = Highcharts;
        setHighchartsLoaded(true);
        setError(null);
      } catch (err) {
        console.error("Failed to load Highcharts:", err);
        if (!mounted) return;
        setError("无法加载图表库，请刷新页面重试");
        setHighchartsLoaded(false);
      }
    };

    if (!highchartsRef.current && !highchartsLoaded) loadHighcharts();

    return () => {
      mounted = false;
    };
  }, [highchartsLoaded]);

  // ---- 根据依赖创建/更新图表 ----
  useEffect(() => {
    const Highcharts = highchartsRef.current;
    if (!Highcharts || !chartRef.current) return;

    // 没有数据或窗口裁剪后没有数据
    if (!priceData.length) {
      if (chartInstance.current) {
        chartInstance.current.destroy();
        chartInstance.current = null;
      }
      return;
    }

    // 清除旧图
    if (chartInstance.current) {
      chartInstance.current.destroy();
      chartInstance.current = null;
    }

    try {
      const chartOptions: Highcharts.Options = {
        time: {
          timezone: userTimezone, // 直接指定时区
        },
        accessibility: {
          enabled: false,
        },
        chart: {
          height: 400,
          backgroundColor: "transparent",
        },
        title: { text: "" },
        credits: { enabled: false },
        rangeSelector: { enabled: false },
        scrollbar: { enabled: false },
        navigator: { enabled: false },
        xAxis: {
          // 强制设置窗口范围（与数据裁剪一致，交互连贯）
          min: isNaN(cutoff) ? undefined : cutoff,
          max: latestTs,
        },
        tooltip: {
          shared: true,
          formatter: function () {
            const xValue = this.x; // 横坐标，已经是 number 类型

            const extra = sortedData.find(d => {
              const [year, month, day] = d.date.split("T")[0].split("-").map(Number);
              return Date.UTC(year, month - 1, day) === xValue; // 和 this.x 对齐
            })?.extra_fields;

            const SH_TZ_MINUTES = 8 * 60; // 上海 UTC+8
            const shanghaiTs = xValue + SH_TZ_MINUTES * 60 * 1000;
            let html = `<b>${Highcharts.dateFormat("%Y-%m-%d", shanghaiTs, true)}</b><br/>`;

            // 处理交易点信息
            const tradePoint = this.points?.find(p => {
              // 直接检查 Point 对象是否有自定义的 trade 属性
              return (p as any).trade ||
                // 或者检查是否是交易系列的点
                p.series.name === "买入信号" ||
                p.series.name === "卖出信号" ||
                p.series.name?.startsWith("持仓");
            });

            if (tradePoint) {
              // 直接从 Point 对象获取 trade 属性
              const trade = (tradePoint as any).trade;

              if (trade) {
                html += `<br/><b>交易信息:</b><br/>`;
                html += `类型: ${trade.type}<br/>`;
                html += `价格: ${trade.price}<br/>`;
                html += `数量: ${trade.size}<br/>`;
                html += `盈亏: ${trade.pnl}<br/>`;
                html += `收益率: ${trade.return_pct}%<br/>`;
                html += `持仓时间: ${trade.duration}<br/>`;
                if (trade.tag) html += `标签: ${trade.tag}<br/>`;
                if (trade.sl) html += `止损价: ${trade.sl}<br/>`;
                if (trade.tp) html += `止盈价: ${trade.tp}<br/>`;
              }
            }

            this.points?.forEach(p => {
              html += `<span style="color:${p.color}">\u25CF</span> ${p.series.name}: <b>${p.y}</b><br/>`;
            });

            if (extra) {
              const tooltipOnly = ["振幅", "涨跌幅", "涨跌额", "换手率"];
              let hasExtra = false;
              tooltipOnly.forEach(key => {
                if (extra[key] != null) {
                  if (!hasExtra) {
                    html += `<br/><b>其它指标:</b><br/>`;
                    hasExtra = true;
                  }
                  html += `${key}: ${extra[key]}<br/>`;
                }
              });
            }

            return html;
          },
        },
        plotOptions: {
          candlestick: {
            color: "#ef4444",
            upColor: "#22c55e",
            lineColor: "#ef4444",
            upLineColor: "#22c55e",
          },
          column: { color: "#8b5cf6" },
        },
        yAxis: [
          {
            title: { text: "价格" },
            height: "50%",
            resize: { enabled: true },
            // 设置Y轴标签格式，保留两位小数
            labels: {
              formatter: function () {
                return Highcharts.numberFormat(this.value as number, 2);
              }
            }
          },
          {
            title: { text: "成交量" },
            top: "55%",
            height: "20%",
            offset: 0,
          },
          {
            // 副图 - 技术指标
            title: { text: "技术指标" },
            top: "80%",
            height: "20%",
            offset: 0,
          },
        ],
        series: [
          {
            type: "candlestick",
            name: "股价",
            data: priceData,
            yAxis: 0,
          },
          {
            type: "line",
            name: "MA5",
            data: ma5Data,
            color: "#f59e0b",
            lineWidth: 1,
            yAxis: 0,
          },
          {
            type: "line",
            name: "MA10",
            data: ma10Data,
            color: "#06b6d4",
            lineWidth: 1,
            yAxis: 0,
          },
          {
            type: "line",
            name: "MA20",
            data: ma20Data,
            color: "#8b5cf6",
            lineWidth: 1,
            yAxis: 0,
          },
          {
            type: "column",
            name: "成交量",
            data: volumeData,
            yAxis: 1,
          },
          {
            type: "line",
            name: "止损线",
            data: stopLossLine,
            color: "#3b82f6", // 蓝色
            dashStyle: "Dash" as Highcharts.DashStyleValue,
            lineWidth: 1.5,
            yAxis: 0,
          },
          {
            type: "line",
            name: "止盈线",
            data: stopWinLine,
            color: "#ef4444", // 红色
            dashStyle: "Dash" as Highcharts.DashStyleValue,
            lineWidth: 1.5,
            yAxis: 0,
          },
          ...indicatorSeries,
          // 添加持仓线
          ...tradePoints.positionLines,
        ],
      };

      chartInstance.current = Highcharts.stockChart(chartRef.current, chartOptions);
      
      // 添加买入卖出点
      if (tradePoints.buyPoints.length) {
        chartInstance.current.addSeries({
          type: "scatter",
          name: "买入信号",
          data: tradePoints.buyPoints,
          yAxis: 0,
          showInLegend: false,
        });
      }

      if (tradePoints.sellPoints.length) {
        chartInstance.current.addSeries({
          type: "scatter",
          name: "卖出信号",
          data: tradePoints.sellPoints,
          yAxis: 0,
          showInLegend: false,
        });

      }
    } catch (err) {
      console.error("Failed to create chart:", err);
      setError("创建图表失败，请刷新页面重试");
    }

    return () => {
      if (chartInstance.current) {
        chartInstance.current.destroy();
        chartInstance.current = null;
      }
    };
  }, [
    highchartsLoaded,
    latestTs,
    cutoff,
    priceData,
    volumeData,
    ma5Data,
    ma10Data,
    ma20Data,
    tradePoints,
    indicatorSeries,
    stopLossLine,
    stopWinLine,
  ]);

  return (
    <div className="bg-card rounded-xl p-6 border border-border">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-2">
          <i className="fas fa-chart-bar text-muted-foreground"></i>
          <h3 className="text-lg font-semibold text-foreground">价格走势与交易信号</h3>
        </div>
        <div className="flex space-x-1">
          {periods.map((period) => (
            <button
              key={period.value}
              onClick={() => onPeriodChange(period.value)}
              className={`time-filter px-3 py-1 rounded text-sm transition-colors ${selectedPeriod === period.value
                  ? "active bg-gray-900 text-white"
                  : "bg-muted text-muted-foreground hover:bg-accent"
                }`}
            >
              {period.label}
            </button>
          ))}
        </div>
      </div>

      {error ? (
        <div className="h-96 w-full bg-muted/30 rounded-lg flex flex-col items-center justify-center p-4">
          <p className="text-red-500 mb-2">{error}</p>
          <button
            onClick={() => {
              setError(null);
              setHighchartsLoaded(false);
              highchartsRef.current = null;
            }}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
          >
            重试
          </button>
        </div>
      ) : !priceData.length ? (
        <div className="h-96 w-full bg-muted/30 rounded-lg flex items-center justify-center">
          <p className="text-muted-foreground">
            所选周期暂无数据
          </p>
        </div>
      ) : (
        <div ref={chartRef} className="h-96 w-full bg-muted/30 rounded-lg" />
      )}
    </div>
  );
}
