import { useEffect, useRef } from "react";
import type { StockData } from "../types";

interface StockChartProps {
  data: StockData[];
  trades: Array<{
    date: string;
    type: 'BUY' | 'SELL';
    price: number;
    quantity: number;
  }>;
  selectedPeriod: string;
  onPeriodChange: (period: string) => void;
}

export default function StockChart({ data, trades, selectedPeriod, onPeriodChange }: StockChartProps) {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<any>(null);

  const periods = [
    { value: "1d", label: "1天" },
    { value: "1w", label: "1周" },
    { value: "1m", label: "1月" },
    { value: "3m", label: "3月" },
    { value: "6m", label: "6月" },
    { value: "1y", label: "1年" },
  ];

  useEffect(() => {
    if (!chartRef.current || !data || data.length === 0) return;

    // Dynamically import Highcharts to avoid SSR issues
    import('highcharts/highstock').then((Highcharts) => {
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }

      // Prepare price data for candlestick chart
      const priceData = data.map(item => [
        new Date(item.date).getTime(),
        item.open,
        item.high,
        item.low,
        item.close
      ]);

      // Prepare volume data
      const volumeData = data.map(item => [
        new Date(item.date).getTime(),
        item.volume
      ]);

      type Tick = { date: string | Date; close: number };

      const calculateMA = (
        data: Tick[],
        period: number
      ): Array<[number, number]> => {
        if (period <= 0 || data.length < period) return [];

        const result: Array<[number, number]> = [];
        let sum = 0;

        for (let i = 0; i < data.length; i++) {
          const close = Number(data[i].close);
          if (isNaN(close)) continue;          // 跳过非法值

          sum += close;
          if (i >= period) sum -= Number(data[i - period].close);

          if (i >= period - 1) {
            result.push([
              new Date(data[i].date).getTime(),
              sum / period
            ]);
          }
        }
        return result;
      };

      const ma5Data = calculateMA(data, 5);
      const ma10Data = calculateMA(data, 10);
      const ma20Data = calculateMA(data, 20);

      try {
        if (!chartRef.current) return;
        chartInstance.current = Highcharts.default.stockChart(chartRef.current, {
          chart: {
            height: 400,
            backgroundColor: 'transparent',
          },
          title: {
            text: null
          },
          credits: {
            enabled: false
          },
          rangeSelector: {
            enabled: false
          },
          scrollbar: {
            enabled: false
          },
          navigator: {
            enabled: false
          },
          plotOptions: {
            candlestick: {
              color: '#ef4444',
              upColor: '#22c55e',
              lineColor: '#ef4444',
              upLineColor: '#22c55e'
            },
            column: {
              color: '#8b5cf6'
            }
          },
          yAxis: [{
            title: {
              text: '价格'
            },
            height: '70%',
            resize: {
              enabled: true
            }
          }, {
            title: {
              text: '成交量'
            },
            top: '75%',
            height: '25%',
            offset: 0
          }],
          series: [{
            type: 'candlestick',
            name: '股价',
            data: priceData,
            yAxis: 0
          }, {
            type: 'line',
            name: 'MA5',
            data: ma5Data,
            color: '#f59e0b',
            lineWidth: 1,
            yAxis: 0
          }, {
            type: 'line',
            name: 'MA10',
            data: ma10Data,
            color: '#06b6d4',
            lineWidth: 1,
            yAxis: 0
          }, {
            type: 'line',
            name: 'MA20',
            data: ma20Data,
            color: '#8b5cf6',
            lineWidth: 1,
            yAxis: 0
          }, {
            type: 'column',
            name: '成交量',
            data: volumeData,
            yAxis: 1
          }]
        });

        // Add trade signals as markers
        if (trades && trades.length > 0) {
          const buyPoints = trades
            .filter(trade => trade.type === 'BUY')
            .map(trade => ({
              x: new Date(trade.date).getTime(),
              y: trade.price,
              marker: {
                symbol: 'circle',
                fillColor: '#22c55e',
                lineColor: '#22c55e',
                lineWidth: 2,
                radius: 6
              },
              dataLabels: {
                enabled: true,
                format: 'B',
                style: {
                  color: '#22c55e',
                  fontWeight: 'bold'
                }
              }
            }));

          const sellPoints = trades
            .filter(trade => trade.type === 'SELL')
            .map(trade => ({
              x: new Date(trade.date).getTime(),
              y: trade.price,
              marker: {
                symbol: 'circle',
                fillColor: '#ef4444',
                lineColor: '#ef4444',
                lineWidth: 2,
                radius: 6
              },
              dataLabels: {
                enabled: true,
                format: 'S',
                style: {
                  color: '#ef4444',
                  fontWeight: 'bold'
                }
              }
            }));

          if (buyPoints.length > 0) {
            chartInstance.current.addSeries({
              type: 'scatter',
              name: '买入信号',
              data: buyPoints,
              yAxis: 0,
              showInLegend: false
            });
          }

          if (sellPoints.length > 0) {
            chartInstance.current.addSeries({
              type: 'scatter',
              name: '卖出信号',
              data: sellPoints,
              yAxis: 0,
              showInLegend: false
            });
          }
        }

      } catch (error) {
        console.error('Failed to create chart:', error);
      }
    }).catch(error => {
      console.error('Failed to load Highcharts:', error);
    });

    return () => {
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }
    };
  }, [data, trades]);

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
              className={`time-filter px-3 py-1 rounded text-sm transition-colors ${
                selectedPeriod === period.value
                  ? "active bg-gray-900 text-white"
                  : "bg-muted text-muted-foreground hover:bg-accent"
              }`}
            >
              {period.label}
            </button>
          ))}
        </div>
      </div>
      
      <div ref={chartRef} className="h-96 w-full bg-muted/30 rounded-lg"></div>
    </div>
  );
}