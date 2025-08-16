import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import {
  stockFilterSchema,
  macdParametersSchema,
  maParametersSchema,
  atrParametersSchema,
  volumeParametersSchema,
  BacktestRequest,
  StockBasicInfoFilter,
  StockBasicInfoSchema
} from "@shared/schema";
import type { Trade, StrategyType } from "@shared/schema";
import { z } from "zod";
import { randomUUID } from "crypto";

interface APIResponse<T> {
  code: number;
  message: string;
  data: T | null;
}

function createAPIResponse<T>(code: number, message: string, data: T | null = null): APIResponse<T> {
  return { code, message, data };
}

export async function registerRoutes(app: Express): Promise<Server> {
  // Status check
  app.get("/api/v1/status", (req, res) => {
    res.json(createAPIResponse(0, "OK"));
  });

  // Get backtest result
  app.get("/api/v1/backtest/:backtest_id", async (req, res) => {
    try {
      const result = await storage.getBacktestResult(req.params.backtest_id);
      if (!result) {
        return res.status(404).json(createAPIResponse(404, "Backtest result not found"));
      }
      if (result.stockCode==null){
        return res.status(404).json(createAPIResponse(404, "Backtest result not found"));
      }
      // Convert to BacktestResponse format
      const stock = await storage.getStock(result.stockCode);
      const stockData = await storage.generateStockData(
        result.stockCode,
        result.startDate.toISOString().split('T')[0],
        result.endDate.toISOString().split('T')[0]
      );

      const response = {
        id: result.id,
        stockCode: result.stockCode,
        stockName: stock?.name || "Unknown",
        return: result.return, // Map totalYield to return
        tradeCount: result.tradeCount,
        trades: result.trades,
        chartData: stockData,
        strategies: result.strategies,
      };

      res.json(createAPIResponse(0, "OK", response));
    } catch (error) {
      res.status(500).json(createAPIResponse(500, "Failed to fetch backtest result"));
    }
  });

  // Individual stock backtest
  app.post("/api/v1/backtest/stock", async (req, res) => {
    try {
      const request = req.body as BacktestRequest;

      // 尝试获取股票信息，如果不存在则使用默认值
      let stock = await storage.getStock(request.stockCode);
      if (!stock) {
        // 如果股票不存在，创建一个模拟的股票对象
        stock = {
          symbol: request.stockCode,
          name: `模拟股票 ${request.stockCode}`,
          exchange: "SH",
          industry: "综合",
          stockType: "A股",
          section: "主板",
          totalShares: 10000,
          floatShares: 8000,
          totalMarketValue: 100,
          floatMarketValue: 80,
          listingDate: new Date("2020-01-01").toISOString(),
          lastUpdate: new Date().toISOString()
        };
        console.log(`Stock not found: ${request.stockCode}, using mock data`);
      }

      // 生成股票数据（无论股票是否存在，都会生成模拟数据）
      const stockData = await storage.generateStockData(
        request.stockCode,
        request.startDate,
        request.endDate
      );

      // 执行回测计算
      const backtestResult = await performBacktest(stockData, request.strategies);

      // 存储回测结果
      const result = await storage.createBacktestResult({
        stockCode: request.stockCode,
        startDate: new Date(request.startDate),
        endDate: new Date(request.endDate),
        strategies: request.strategies,
        return: backtestResult.return, // Convert ratio to percentage for storage
        tradeCount: backtestResult.trades.length,
        trades: backtestResult.trades,
      });

      // 构建响应
      const response = {
        id: result.id,
        stockCode: request.stockCode,
        stockName: stock.name,
        return: backtestResult.return, // Already a ratio between 0 and 1
        tradeCount: backtestResult.trades.length,
        trades: backtestResult.trades,
        chartData: stockData,
        strategies: request.strategies,
      };

      res.json(createAPIResponse(0, "OK", response));
    } catch (error) {
      if (error instanceof z.ZodError) {
        return res.status(400).json(createAPIResponse(400, "Invalid request parameters", {
          detail: error.errors
        }));
      }
      console.error('Backtest error:', error);
      res.status(500).json(createAPIResponse(500, "Failed to perform backtest"));
    }
  });

  // Multiple stocks backtest
  app.post("/api/v1/backtest/stocks", async (req, res) => {
    try {
      const requests = req.body as BacktestRequest[];
      if (!Array.isArray(requests) || requests.length === 0) {
        return res.status(400).json(createAPIResponse(400, "At least one backtest request is required"));
      }

      // Generate mock results for each stock
      const results: any[] = [];
      for (const request of requests) {
        // 不再检查存储中是否存在该股票，直接生成模拟结果
        // Generate return as a ratio between 0 and 1
        const returnValue = Math.random().toFixed(2); // Random value between 0 and 1
        const signalTypes: Array<'BUY' | 'SELL' | 'HOLD'> = ['BUY', 'SELL', 'HOLD'];
        const signalType = signalTypes[Math.floor(Math.random() * signalTypes.length)];
        const buyCount = Math.floor(Math.random() * 10);
        const sellCount = Math.floor(Math.random() * 10);

        // Store a minimal backtest result (如果不需要存储，可以注释掉这部分)
        // 生成股票数据
        const stockData = await storage.generateStockData(
          request.stockCode,
          request.startDate,
          request.endDate
        );
        const backtestResult = await performBacktest(stockData, request.strategies);
        const backtest = await storage.createBacktestResult({
          stockCode: request.stockCode,
          startDate: new Date(request.startDate),
          endDate: new Date(request.endDate),
          strategies: request.strategies,
          return: parseFloat(returnValue), // Convert ratio to percentage for storage
          tradeCount: buyCount + sellCount,
          trades: backtestResult.trades
        });
        const backtestId = backtest.id
        const trades = backtestResult.trades
        results.push({
          stockCode: request.stockCode,
          backtestId,
          return: parseFloat(returnValue),
          signalType,
          buyCount,
          sellCount,
          trades
        });
        

      }

      // 如果结果数组为空，返回一个错误信息
      if (results.length === 0) {
        return res.status(400).json(createAPIResponse(400, "No valid backtest requests processed"));
      }

      res.json(createAPIResponse(0, "OK", results));
    } catch (error) {
      if (error instanceof z.ZodError) {
        return res.status(400).json(createAPIResponse(400, "Invalid request parameters", {
          detail: error.errors
        }));
      }
      console.error('Batch backtest error:', error);
      res.status(500).json(createAPIResponse(500, "Failed to perform batch backtest"));
    }
  });

  // List stocks
  app.get("/api/v1/stocks", async (req, res) => {
    try {
      const stocks = await storage.getStocks();
      res.json(createAPIResponse(0, "OK", stocks));
    } catch (error) {
      res.status(500).json(createAPIResponse(500, "Failed to fetch stocks"));
    }
  });

  // Filter stocks
  app.post("/api/v1/stocks/filter", async (req, res) => {
    try {
      const filter = req.body as StockBasicInfoFilter;
      const stocks = await storage.filterStocks(filter);
      res.json(createAPIResponse(0, "OK", stocks));
    } catch (error) {
      if (error instanceof z.ZodError) {
        return res.status(400).json(createAPIResponse(400, "Invalid request parameters", {
          detail: error.errors
        }));
      }
      res.status(500).json(createAPIResponse(500, "Failed to filter stocks"));
    }
  });

  // Get filter options
  app.get("/api/v1/stocks/filter-options", async (req, res) => {
    try {
      const mockOptions = {
        exchanges: ['SH', 'SZ', 'BJ'],
        sections: ['主板', '中小板', '创业板', '科创板'],
        stockTypes: ['A股', 'B股', 'H股'],
        industries: ['银行', '医药', '科技', '制造业', '房地产'],
      };
      res.json(createAPIResponse(0, "OK", mockOptions));
    } catch (error) {
      res.status(500).json(createAPIResponse(500, "Failed to get filter options"));
    }
  });

  const httpServer = createServer(app);
  return httpServer;
}

// Backtest calculation functions
async function performBacktest(stockData: any[], strategies: any[]): Promise<{ return: number; trades: Trade[] }> {
  const trades: Trade[] = [];
  let cash = 100000; // Starting cash: 100k
  let shares = 0;
  let totalValue = cash;


  for (let i = 20; i < stockData.length; i++) { // Start from index 20 to have enough history
    const currentData = stockData.slice(0, i + 1);

    // Generate signals from strategies
    const signals = strategies.map(strategy => generateSignal(currentData, strategy));

    const buySignals = signals.filter(s => s === 'BUY').length;
    const sellSignals = signals.filter(s => s === 'SELL').length;
    const currentPrice = stockData[i].close;

    // Buy if more buy signals than sell signals and we have cash
    if (buySignals > sellSignals && cash > currentPrice * 100) {
      const sharesToBuy = Math.floor(cash / currentPrice / 100) * 100; // Buy in lots of 100
      const cost = sharesToBuy * currentPrice;

      if (sharesToBuy > 0 && cost <= cash) {
        shares += sharesToBuy;
        cash -= cost;

        trades.push({
          date: stockData[i].date,
          type: 'BUY',
          price: currentPrice,
          quantity: sharesToBuy,
          commission: cost * 0.0003, // 0.03% commission
          marketValue: shares * currentPrice,
          cashBalance: cash,
        });
      }
    }

    // Sell if more sell signals than buy signals and we have shares
    if (sellSignals > buySignals && shares > 0) {
      const sharesToSell = shares;
      const proceeds = sharesToSell * currentPrice;

      shares = 0;
      cash += proceeds;

      trades.push({
        date: stockData[i].date,
        type: 'SELL',
        price: currentPrice,
        quantity: sharesToSell,
        commission: proceeds * 0.0003, // 0.03% commission
        marketValue: 0,
        cashBalance: cash,
      });
    }
  }

  // Calculate final value
  const finalPrice = stockData[stockData.length - 1].close;
  const finalValue = cash + (shares * finalPrice);
  const totalYield = ((finalValue - 100000) / 100000);

  return {
    return: Number(totalYield.toFixed(2)),
    trades,
  };
}

function generateSignal(data: any[], strategy: any): 'BUY' | 'SELL' | 'HOLD' {
  const { type, parameters } = strategy;
  switch (type) {
    case 'MACD':
      return generateMACDSignal(data, parameters);
    case 'MA':
      return generateMASignal(data, parameters);
    case 'ATR':
      return generateATRSignal(data, parameters);
    case 'VOLUME':
      return generateVolumeSignal(data, parameters);
    default:
      return 'HOLD';
  }
}

function generateMACDSignal(data: any[], params: any): 'BUY' | 'SELL' | 'HOLD' {
  if (data.length < Math.max(params.fastPeriod, params.slowPeriod, params.signalPeriod)) return 'HOLD';

  // Calculate MACD
  const fastEMA = calculateEMA(data.map(d => d.close), params.fastPeriod);
  const slowEMA = calculateEMA(data.map(d => d.close), params.slowPeriod);

  if (fastEMA.length < 2 || slowEMA.length < 2) return 'HOLD';

  const macdLine = fastEMA[fastEMA.length - 1] - slowEMA[slowEMA.length - 1];
  const prevMacdLine = fastEMA[fastEMA.length - 2] - slowEMA[slowEMA.length - 2];

  // Simple MACD crossover strategy
  if (macdLine > 0 && prevMacdLine <= 0) return 'BUY';
  if (macdLine < 0 && prevMacdLine >= 0) return 'SELL';

  return 'HOLD';
}

function generateMASignal(data: any[], params: any): 'BUY' | 'SELL' | 'HOLD' {
  if (data.length < Math.max(params.shortPeriod, params.longPeriod)) return 'HOLD';

  const shortMA = calculateSMA(data.map(d => d.close), params.shortPeriod);
  const longMA = calculateSMA(data.map(d => d.close), params.longPeriod);

  if (shortMA.length < 2 || longMA.length < 2) return 'HOLD';

  const currentShort = shortMA[shortMA.length - 1];
  const currentLong = longMA[longMA.length - 1];
  const prevShort = shortMA[shortMA.length - 2];
  const prevLong = longMA[longMA.length - 2];

  // Golden cross and death cross
  if (currentShort > currentLong && prevShort <= prevLong) return 'BUY';
  if (currentShort < currentLong && prevShort >= prevLong) return 'SELL';

  return 'HOLD';
}

function generateATRSignal(data: any[], params: any): 'BUY' | 'SELL' | 'HOLD' {
  if (data.length < params.atrPeriod) return 'HOLD';

  // Simple ATR-based signal
  const atr = calculateATR(data, params.atrPeriod);
  const currentPrice = data[data.length - 1].close;
  const sma = calculateSMA(data.map(d => d.close), params.highLowPeriod);

  if (atr.length === 0 || sma.length === 0) return 'HOLD';

  const currentSMA = sma[sma.length - 1];
  const currentATR = atr[atr.length - 1];

  // Buy if price is above SMA + ATR, sell if below SMA - ATR
  if (currentPrice > currentSMA + (currentATR * params.atrMultiplier)) return 'BUY';
  if (currentPrice < currentSMA - (currentATR * params.atrMultiplier)) return 'SELL';

  return 'HOLD';
}

function generateVolumeSignal(data: any[], params: any): 'BUY' | 'SELL' | 'HOLD' {
  if (data.length < params.timeRange) return 'HOLD';

  const volumes = data.slice(-params.timeRange).map(d => d.volume);
  const avgVolume = volumes.reduce((sum, vol) => sum + vol, 0) / volumes.length;
  const currentVolume = data[data.length - 1].volume;

  // Volume-based signals
  if (currentVolume < avgVolume * params.buyVolumeMultiplier) return 'BUY';
  if (currentVolume > avgVolume * params.sellVolumeMultiplier) return 'SELL';

  return 'HOLD';
}

// Technical indicator calculations
function calculateSMA(prices: number[], period: number): number[] {
  const sma = [];
  for (let i = period - 1; i < prices.length; i++) {
    const sum = prices.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0);
    sma.push(sum / period);
  }
  return sma;
}

function calculateEMA(prices: number[], period: number): number[] {
  const ema: number[] = [];
  const multiplier = 2 / (period + 1);

  // First EMA is SMA
  const firstSMA = prices.slice(0, period).reduce((a, b) => a + b, 0) / period;
  ema.push(firstSMA);

  for (let i = period; i < prices.length; i++) {
    const currentEMA = (prices[i] * multiplier) + (ema[ema.length - 1] * (1 - multiplier));
    ema.push(currentEMA);
  }

  return ema;
}

function calculateATR(data: any[], period: number): number[] {
  const trueRanges = [];

  for (let i = 1; i < data.length; i++) {
    const current = data[i];
    const previous = data[i - 1];

    const tr1 = current.high - current.low;
    const tr2 = Math.abs(current.high - previous.close);
    const tr3 = Math.abs(current.low - previous.close);

    trueRanges.push(Math.max(tr1, tr2, tr3));
  }

  return calculateSMA(trueRanges, period);
}