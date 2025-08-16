import { type Stock, type InsertStock, type BacktestResult, type InsertBacktestResult, type StockFilter, type Trade} from "@shared/schema";
import { StockBasicInfoSchema, StockBasicInfoFilter, BacktestResponse, BacktestResultItem } from "@shared/schema";
import { randomUUID } from "crypto";

export interface IStorage {
  // Stock methods
  getStocks(): Promise<StockBasicInfoSchema[]>;
  getStock(code: string): Promise<StockBasicInfoSchema | undefined>;
  filterStocks(filter: StockBasicInfoFilter): Promise<StockBasicInfoSchema[]>;

  // Backtest methods
  createBacktestResult(result: InsertBacktestResult): Promise<BacktestResult>;
  getBacktestResult(id: string): Promise<BacktestResult | undefined>;
  getBacktestResultIds(): Promise<string[]>;

  // Market data simulation
  generateStockData(stockCode: string, startDate: string, endDate: string): Promise<any[]>;
}

export class MemStorage implements IStorage {
  private stocks: Map<string, Stock>;
  private backtestResults: Map<string, BacktestResult>;

  constructor() {
    this.stocks = new Map();
    this.backtestResults = new Map();
    this.initializeSampleData();
  }

  private initializeSampleData() {
    // Initialize sample stocks
    const sampleStocks: InsertStock[] = [
      {
        symbol: "000001",
        name: "平安银行",
        exchange: "深交所",
        industry: "银行",
        stockType: "A股",
        section: "主板",
        totalShares: 19405.24,
        floatShares: 19405.24,
        totalMarketValue: 399.49,
        floatMarketValue: 399.49,
        listingDate: new Date("1991-04-03"),
      },
      {
        symbol: "000002",
        name: "万科A",
        exchange: "深交所",
        industry: "房地产开发",
        stockType: "A股",
        section: "主板",
        totalShares: 11039.15,
        floatShares: 11039.15,
        totalMarketValue: 2847.23,
        floatMarketValue: 2847.23,
        listingDate: new Date("1991-01-29"),
      },
      {
        symbol: "600000",
        name: "浦发银行",
        exchange: "上交所",
        industry: "银行",
        stockType: "A股",
        section: "主板",
        totalShares: 29348.07,
        floatShares: 29348.07,
        totalMarketValue: 2156.87,
        floatMarketValue: 2156.87,
        listingDate: new Date("1999-11-10"),
      },
      {
        symbol: "600519",
        name: "贵州茅台",
        exchange: "上交所",
        industry: "白酒",
        stockType: "A股",
        section: "主板",
        totalShares: 12.56,
        floatShares: 12.56,
        totalMarketValue: 18750.45,
        floatMarketValue: 18750.45,
        listingDate: new Date("2001-08-27"),
      },
    ];

    // Create more sample stocks to reach 50+ stocks
    for (let i = 5; i <= 60; i++) {
      const paddedCode = i.toString().padStart(6, '0');
      const stock: InsertStock = {
        symbol: paddedCode,
        name: `测试股票${i}`,
        exchange: i % 2 === 0 ? "上交所" : "深交所",
        industry: ["银行", "软件", "汽车", "生物医药", "房地产开发"][i % 5],
        stockType: "A股",
        section: ["主板", "中小板", "创业板"][i % 3],
        totalShares: Math.random() * 10000 + 1000,
        floatShares: Math.random() * 8000 + 800,
        totalMarketValue: Math.random() * 1000 + 50,
        floatMarketValue: Math.random() * 800 + 40,
        listingDate: new Date(2000 + Math.floor(Math.random() * 24), Math.floor(Math.random() * 12), Math.floor(Math.random() * 28) + 1),
      };
      sampleStocks.push(stock);
    }

    sampleStocks.forEach(stock => {
      const id = randomUUID();
      this.stocks.set(stock.symbol, { ...stock, id });
    });
  }

  async getStocks(): Promise<StockBasicInfoSchema[]> {
    return Array.from(this.stocks.values()).map(stock => this.convertToStockBasicInfoSchema(stock));
  }

  async getStock(code: string): Promise<StockBasicInfoSchema | undefined> {
    const stock = this.stocks.get(code);
    return stock ? this.convertToStockBasicInfoSchema(stock) : undefined;
  }

  async filterStocks(filter: StockBasicInfoFilter): Promise<StockBasicInfoSchema[]> {
    let stocks = Array.from(this.stocks.values());

    if (filter.exchange && filter.exchange.length > 0) {
      stocks = stocks.filter(s => {
        const exchangeCode = s.exchange === "上交所" ? "SH" : s.exchange === "深交所" ? "SZ" : "BJ";
        return filter.exchange!.includes(exchangeCode);
      });
    }

    if (filter.sections && filter.sections.length > 0) {
      stocks = stocks.filter(s => filter.sections!.includes(s.section));
    }

    if (filter.stock_type && filter.stock_type.length > 0) {
      stocks = stocks.filter(s => filter.stock_type!.includes(s.stockType || ""));
    }

    if (filter.industries && filter.industries.length > 0) {
      stocks = stocks.filter(s => filter.industries!.includes(s.industry || ""));
    }

    if (filter.start_listing_date) {
      const startDate = new Date(filter.start_listing_date);
      stocks = stocks.filter(s => s.listingDate && new Date(s.listingDate) >= startDate);
    }

    if (filter.end_listing_date) {
      const endDate = new Date(filter.end_listing_date);
      stocks = stocks.filter(s => s.listingDate && new Date(s.listingDate) <= endDate);
    }

    if (filter.min_market_cap !== undefined) {
      stocks = stocks.filter(s => s.totalMarketValue && s.totalMarketValue >= filter.min_market_cap!);
    }

    if (filter.max_market_cap !== undefined) {
      stocks = stocks.filter(s => s.totalMarketValue && s.totalMarketValue <= filter.max_market_cap!);
    }

    return stocks.map(stock => this.convertToStockBasicInfoSchema(stock));
  }

  async createBacktestResult(insertResult: InsertBacktestResult): Promise<BacktestResult> {
    const id = randomUUID();
    const result: BacktestResult = {
      ...insertResult,
      id,
      createdAt: new Date(),
    };
    this.backtestResults.set(id, result);
    return result;
  }

  async getBacktestResult(id: string): Promise<BacktestResult | undefined> {
    return this.backtestResults.get(id);
  }

  async getBacktestResultIds(): Promise<string[]> {
    return Array.from(this.backtestResults.values()).map(result => result.id);
  }

  async generateStockData(stockCode: string, startDate: string, endDate: string): Promise<any[]> {
    // Generate realistic stock price data
    const start = new Date(startDate);
    const end = new Date(endDate);
    const data = [];

    let currentPrice = 10 + Math.random() * 20; // Starting price between 10-30
    let currentVolume = 10000 + Math.random() * 50000;

    for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
      // Skip weekends
      if (d.getDay() === 0 || d.getDay() === 6) continue;

      // Generate OHLCV data with realistic movements
      const volatility = 0.03;
      const change = (Math.random() - 0.5) * volatility;

      const open = currentPrice;
      const close = currentPrice * (1 + change);
      const high = Math.max(open, close) * (1 + Math.random() * 0.02);
      const low = Math.min(open, close) * (1 - Math.random() * 0.02);
      const volume = currentVolume * (0.5 + Math.random());

      data.push({
        date: d.toISOString().split('T')[0],
        open: Number(open.toFixed(2)),
        high: Number(high.toFixed(2)),
        low: Number(low.toFixed(2)),
        close: Number(close.toFixed(2)),
        volume: Math.floor(volume),
      });

      currentPrice = close;
      currentVolume = volume;
    }

    return data;
  }

  // Helper method to convert Stock to StockBasicInfoSchema
  private convertToStockBasicInfoSchema(stock: Stock): StockBasicInfoSchema {
    return {
      symbol: stock.symbol,
      name: stock.name,
      exchange: stock.exchange === "上交所" ? "SH" : stock.exchange === "深交所" ? "SZ" : "BJ",
      section: stock.section,
      stockType: stock.stockType,
      listingDate: stock.listingDate ? stock.listingDate.toISOString().split('T')[0] : undefined,
      industry: stock.industry,
      totalShares: stock.totalShares,
      floatShares: stock.floatShares,
      totalMarketValue: stock.totalMarketValue ? stock.totalMarketValue * 100000000 : undefined, // Convert from 亿元 to 元
      floatMarketValue: stock.floatMarketValue ? stock.floatMarketValue * 100000000 : undefined, // Convert from 亿元 to 元
      lastUpdate: new Date().toISOString()
    };
  }
}

export const storage = new MemStorage();