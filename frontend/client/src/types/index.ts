export interface StockData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface ChartPoint {
  x: number;
  y: number;
}

export interface BacktestResponse {
  id: string;
  stockCode: string;
  stockName: string;
  return: number;
  tradeCount: number;
  trades: Array<{
    date: string;
    type: 'BUY' | 'SELL' | 'HOLD';
    price: number;
    quantity: number;
    commission?: number;
    marketValue?: number;
    cashBalance?: number;
  }>;
  chartData: StockData[];
  strategies: Array<{
    type: string;
    parameters: Record<string, any>;
  }>;
}

// 简化后的响应类型
export type BacktestResultItem = {
  stockCode: string;
  backtestId: string;
  return: number;
  signalType: 'BUY' | 'SELL' | 'HOLD';
  buyCount: number;
  sellCount: number;
};
export type BacktestResults = BacktestResultItem[];

export interface APIResponse<T>{
  code: number;
  message: string;
  data: T|null;
}