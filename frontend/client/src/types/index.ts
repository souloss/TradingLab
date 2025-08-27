
// ========== 回测相关定义
export interface TradeRecord {
  size: number;
  entry_bar: number;
  exit_bar: number;
  entry_price: number;
  exit_price: number;
  sl?: number;
  tp?: number;
  pnl: number;
  commission: number;
  return_pct: number;
  entry_time: string;
  exit_time: string;
  duration: string;
  tag?: string;
  extra: Record<string, any>;
}

export interface EquityPoint {
  timestamp: string;
  equity: number;
  drawdown_pct: number;
  drawdown_duration?: string;
}

export interface BacktestStats {
  start: string;
  end: string;
  duration: string;
  exposure_time_pct: number;
  equity_final: number;
  equity_peak: number;
  commissions: number;
  return_pct: number;
  buy_hold_return_pct: number;
  return_ann_pct: number;
  volatility_ann_pct: number;
  cagr_pct: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  calmar_ratio: number;
  alpha_pct: number;
  beta: number;
  max_drawdown_pct: number;
  avg_drawdown_pct: number;
  max_drawdown_duration: string;
  avg_drawdown_duration: string;
  n_trades: number;
  win_rate_pct: number;
  best_trade_pct: number;
  worst_trade_pct: number;
  avg_trade_pct: number;
  max_trade_duration: string;
  avg_trade_duration: string;
  profit_factor?: number;
  expectancy_pct: number;
  sqn: number;
  kelly_criterion?: number;
  equity_curve: EquityPoint[];
  trades: TradeRecord[];
  strategy: {
    name: string;
    doc?: string;
    params: Record<string, any>;
  };
}

// =================

interface ExtraFields {
  [key: string]: number | string | undefined;
}
export interface StockData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  extra_fields?: ExtraFields;
}

export interface ChartPoint {
  x: number;
  y: number;
}

export interface BacktestResponse {
  id: string;
  stockCode: string;
  stockName: string;
  backtestStats: BacktestStats;
  chartData: StockData[];
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

// 历史回测记录类型
export interface BacktestListItem {
  id: string;
  start: string;
  end: string;
  stockCode: string;
  stockName: string;
  strategy: {
    name: string;
    params: Record<string, any>;
  };
  // createdAt: string;
  // completedAt?: string;
  // status: "completed" | "running" | "failed";
}

export interface BacktestListResp {
  items: BacktestListItem[];
  total: number;
}

export interface APIResponse<T>{
  code: number;
  message: string;
  data: T|null;
}