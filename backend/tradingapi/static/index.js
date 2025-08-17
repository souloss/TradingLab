// server/index.ts
import express2 from "express";

// server/routes.ts
import { createServer } from "http";

// server/storage.ts
import { randomUUID } from "crypto";
var MemStorage = class {
  stocks;
  backtestResults;
  constructor() {
    this.stocks = /* @__PURE__ */ new Map();
    this.backtestResults = /* @__PURE__ */ new Map();
    this.initializeSampleData();
  }
  initializeSampleData() {
    const sampleStocks = [
      {
        symbol: "000001",
        name: "\u5E73\u5B89\u94F6\u884C",
        exchange: "\u6DF1\u4EA4\u6240",
        industry: "\u94F6\u884C",
        stockType: "A\u80A1",
        section: "\u4E3B\u677F",
        totalShares: 19405.24,
        floatShares: 19405.24,
        totalMarketValue: 399.49,
        floatMarketValue: 399.49,
        listingDate: /* @__PURE__ */ new Date("1991-04-03")
      },
      {
        symbol: "000002",
        name: "\u4E07\u79D1A",
        exchange: "\u6DF1\u4EA4\u6240",
        industry: "\u623F\u5730\u4EA7\u5F00\u53D1",
        stockType: "A\u80A1",
        section: "\u4E3B\u677F",
        totalShares: 11039.15,
        floatShares: 11039.15,
        totalMarketValue: 2847.23,
        floatMarketValue: 2847.23,
        listingDate: /* @__PURE__ */ new Date("1991-01-29")
      },
      {
        symbol: "600000",
        name: "\u6D66\u53D1\u94F6\u884C",
        exchange: "\u4E0A\u4EA4\u6240",
        industry: "\u94F6\u884C",
        stockType: "A\u80A1",
        section: "\u4E3B\u677F",
        totalShares: 29348.07,
        floatShares: 29348.07,
        totalMarketValue: 2156.87,
        floatMarketValue: 2156.87,
        listingDate: /* @__PURE__ */ new Date("1999-11-10")
      },
      {
        symbol: "600519",
        name: "\u8D35\u5DDE\u8305\u53F0",
        exchange: "\u4E0A\u4EA4\u6240",
        industry: "\u767D\u9152",
        stockType: "A\u80A1",
        section: "\u4E3B\u677F",
        totalShares: 12.56,
        floatShares: 12.56,
        totalMarketValue: 18750.45,
        floatMarketValue: 18750.45,
        listingDate: /* @__PURE__ */ new Date("2001-08-27")
      }
    ];
    for (let i = 5; i <= 60; i++) {
      const paddedCode = i.toString().padStart(6, "0");
      const stock = {
        symbol: paddedCode,
        name: `\u6D4B\u8BD5\u80A1\u7968${i}`,
        exchange: i % 2 === 0 ? "\u4E0A\u4EA4\u6240" : "\u6DF1\u4EA4\u6240",
        industry: ["\u94F6\u884C", "\u8F6F\u4EF6", "\u6C7D\u8F66", "\u751F\u7269\u533B\u836F", "\u623F\u5730\u4EA7\u5F00\u53D1"][i % 5],
        stockType: "A\u80A1",
        section: ["\u4E3B\u677F", "\u4E2D\u5C0F\u677F", "\u521B\u4E1A\u677F"][i % 3],
        totalShares: Math.random() * 1e4 + 1e3,
        floatShares: Math.random() * 8e3 + 800,
        totalMarketValue: Math.random() * 1e3 + 50,
        floatMarketValue: Math.random() * 800 + 40,
        listingDate: new Date(2e3 + Math.floor(Math.random() * 24), Math.floor(Math.random() * 12), Math.floor(Math.random() * 28) + 1)
      };
      sampleStocks.push(stock);
    }
    sampleStocks.forEach((stock) => {
      const id = randomUUID();
      this.stocks.set(stock.symbol, { ...stock, id });
    });
  }
  async getStocks() {
    return Array.from(this.stocks.values()).map((stock) => this.convertToStockBasicInfoSchema(stock));
  }
  async getStock(code) {
    const stock = this.stocks.get(code);
    return stock ? this.convertToStockBasicInfoSchema(stock) : void 0;
  }
  async filterStocks(filter) {
    let stocks = Array.from(this.stocks.values());
    if (filter.exchange && filter.exchange.length > 0) {
      stocks = stocks.filter((s) => {
        const exchangeCode = s.exchange === "\u4E0A\u4EA4\u6240" ? "SH" : s.exchange === "\u6DF1\u4EA4\u6240" ? "SZ" : "BJ";
        return filter.exchange.includes(exchangeCode);
      });
    }
    if (filter.sections && filter.sections.length > 0) {
      stocks = stocks.filter((s) => filter.sections.includes(s.section));
    }
    if (filter.stock_type && filter.stock_type.length > 0) {
      stocks = stocks.filter((s) => filter.stock_type.includes(s.stockType || ""));
    }
    if (filter.industries && filter.industries.length > 0) {
      stocks = stocks.filter((s) => filter.industries.includes(s.industry || ""));
    }
    if (filter.start_listing_date) {
      const startDate = new Date(filter.start_listing_date);
      stocks = stocks.filter((s) => s.listingDate && new Date(s.listingDate) >= startDate);
    }
    if (filter.end_listing_date) {
      const endDate = new Date(filter.end_listing_date);
      stocks = stocks.filter((s) => s.listingDate && new Date(s.listingDate) <= endDate);
    }
    if (filter.min_market_cap !== void 0) {
      stocks = stocks.filter((s) => s.totalMarketValue && s.totalMarketValue >= filter.min_market_cap);
    }
    if (filter.max_market_cap !== void 0) {
      stocks = stocks.filter((s) => s.totalMarketValue && s.totalMarketValue <= filter.max_market_cap);
    }
    return stocks.map((stock) => this.convertToStockBasicInfoSchema(stock));
  }
  async createBacktestResult(insertResult) {
    const id = randomUUID();
    const result = {
      ...insertResult,
      id,
      createdAt: /* @__PURE__ */ new Date(),
      stockCode: insertResult.stockCode ?? null
    };
    this.backtestResults.set(id, result);
    return result;
  }
  async getBacktestResult(id) {
    return this.backtestResults.get(id);
  }
  async getBacktestResultIds() {
    return Array.from(this.backtestResults.values()).map((result) => result.id);
  }
  async generateStockData(stockCode, startDate, endDate) {
    const start = new Date(startDate);
    const end = new Date(endDate);
    const data = [];
    let currentPrice = 10 + Math.random() * 20;
    let currentVolume = 1e4 + Math.random() * 5e4;
    for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
      if (d.getDay() === 0 || d.getDay() === 6) continue;
      const volatility = 0.03;
      const change = (Math.random() - 0.5) * volatility;
      const open = currentPrice;
      const close = currentPrice * (1 + change);
      const high = Math.max(open, close) * (1 + Math.random() * 0.02);
      const low = Math.min(open, close) * (1 - Math.random() * 0.02);
      const volume = currentVolume * (0.5 + Math.random());
      data.push({
        date: d.toISOString().split("T")[0],
        open: Number(open.toFixed(2)),
        high: Number(high.toFixed(2)),
        low: Number(low.toFixed(2)),
        close: Number(close.toFixed(2)),
        volume: Math.floor(volume),
        extra_fields: {
          \u6210\u4EA4\u989D: Math.floor(Math.random() * 1e7) + 5e5,
          \u632F\u5E45: (Math.random() * 20).toFixed(2),
          \u6DA8\u8DCC\u5E45: (Math.random() * 20 - 10).toFixed(2),
          \u6362\u624B\u7387: (Math.random() * 15).toFixed(2),
          ATR: (Math.random() * 10).toFixed(2),
          Signal_ATR: Math.random() > 0.5 ? 1 : 0,
          Confidence_ATR: 0,
          Signal_Combined: Math.random() > 0.5 ? 1 : 0,
          Signal_Confidence: 0
        }
      });
      currentPrice = close;
      currentVolume = volume;
    }
    return data;
  }
  // Helper method to convert Stock to StockBasicInfoSchema
  convertToStockBasicInfoSchema(stock) {
    return {
      symbol: stock.symbol,
      name: stock.name,
      exchange: stock.exchange === "\u4E0A\u4EA4\u6240" ? "SH" : stock.exchange === "\u6DF1\u4EA4\u6240" ? "SZ" : "BJ",
      section: stock.section,
      stockType: stock.stockType,
      listingDate: stock.listingDate ? stock.listingDate.toISOString().split("T")[0] : void 0,
      industry: stock.industry,
      totalShares: stock.totalShares,
      floatShares: stock.floatShares,
      totalMarketValue: stock.totalMarketValue ? stock.totalMarketValue * 1e8 : void 0,
      // Convert from 亿元 to 元
      floatMarketValue: stock.floatMarketValue ? stock.floatMarketValue * 1e8 : void 0,
      // Convert from 亿元 to 元
      lastUpdate: (/* @__PURE__ */ new Date()).toISOString()
    };
  }
};
var storage = new MemStorage();

// server/routes.ts
import { z } from "zod";
function createAPIResponse(code, message, data = null) {
  return { code, message, data };
}
async function registerRoutes(app2) {
  app2.get("/api/v1/status", (req, res) => {
    res.json(createAPIResponse(0, "OK"));
  });
  app2.get("/api/v1/backtest/:backtest_id", async (req, res) => {
    try {
      const result = await storage.getBacktestResult(req.params.backtest_id);
      if (!result) {
        return res.status(404).json(createAPIResponse(404, "Backtest result not found"));
      }
      if (result.stockCode == null) {
        return res.status(404).json(createAPIResponse(404, "Backtest result not found"));
      }
      const stock = await storage.getStock(result.stockCode);
      const stockData = await storage.generateStockData(
        result.stockCode,
        result.startDate.toISOString().split("T")[0],
        result.endDate.toISOString().split("T")[0]
      );
      const response = {
        id: result.id,
        stockCode: result.stockCode,
        stockName: stock?.name || "Unknown",
        return: result.return,
        // Map totalYield to return
        tradeCount: result.tradeCount,
        trades: result.trades,
        chartData: stockData,
        strategies: result.strategies
      };
      res.json(createAPIResponse(0, "OK", response));
    } catch (error) {
      res.status(500).json(createAPIResponse(500, "Failed to fetch backtest result"));
    }
  });
  app2.post("/api/v1/backtest/stock", async (req, res) => {
    try {
      const request = req.body;
      let stock = await storage.getStock(request.stockCode);
      if (!stock) {
        stock = {
          symbol: request.stockCode,
          name: `\u6A21\u62DF\u80A1\u7968 ${request.stockCode}`,
          exchange: "SH",
          industry: "\u7EFC\u5408",
          stockType: "A\u80A1",
          section: "\u4E3B\u677F",
          totalShares: 1e4,
          floatShares: 8e3,
          totalMarketValue: 100,
          floatMarketValue: 80,
          listingDate: (/* @__PURE__ */ new Date("2020-01-01")).toISOString(),
          lastUpdate: (/* @__PURE__ */ new Date()).toISOString()
        };
        console.log(`Stock not found: ${request.stockCode}, using mock data`);
      }
      const stockData = await storage.generateStockData(
        request.stockCode,
        request.startDate,
        request.endDate
      );
      const backtestResult = await performBacktest(stockData, request.strategies);
      const result = await storage.createBacktestResult({
        stockCode: request.stockCode,
        startDate: new Date(request.startDate),
        endDate: new Date(request.endDate),
        strategies: request.strategies,
        return: backtestResult.return,
        // Convert ratio to percentage for storage
        tradeCount: backtestResult.trades.length,
        trades: backtestResult.trades
      });
      const response = {
        id: result.id,
        stockCode: request.stockCode,
        stockName: stock.name,
        return: backtestResult.return,
        // Already a ratio between 0 and 1
        tradeCount: backtestResult.trades.length,
        trades: backtestResult.trades,
        chartData: stockData,
        strategies: request.strategies
      };
      res.json(createAPIResponse(0, "OK", response));
    } catch (error) {
      if (error instanceof z.ZodError) {
        return res.status(400).json(createAPIResponse(400, "Invalid request parameters", {
          detail: error.errors
        }));
      }
      console.error("Backtest error:", error);
      res.status(500).json(createAPIResponse(500, "Failed to perform backtest"));
    }
  });
  app2.post("/api/v1/backtest/stocks", async (req, res) => {
    try {
      const requests = req.body;
      if (!Array.isArray(requests) || requests.length === 0) {
        return res.status(400).json(createAPIResponse(400, "At least one backtest request is required"));
      }
      const results = [];
      for (const request of requests) {
        const returnValue = Math.random().toFixed(2);
        const signalTypes = ["BUY", "SELL", "HOLD"];
        const signalType = signalTypes[Math.floor(Math.random() * signalTypes.length)];
        const buyCount = Math.floor(Math.random() * 10);
        const sellCount = Math.floor(Math.random() * 10);
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
          return: parseFloat(returnValue),
          // Convert ratio to percentage for storage
          tradeCount: buyCount + sellCount,
          trades: backtestResult.trades
        });
        const backtestId = backtest.id;
        const trades = backtestResult.trades;
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
      console.error("Batch backtest error:", error);
      res.status(500).json(createAPIResponse(500, "Failed to perform batch backtest"));
    }
  });
  app2.get("/api/v1/stocks", async (req, res) => {
    try {
      const stocks = await storage.getStocks();
      res.json(createAPIResponse(0, "OK", stocks));
    } catch (error) {
      res.status(500).json(createAPIResponse(500, "Failed to fetch stocks"));
    }
  });
  app2.post("/api/v1/stocks/filter", async (req, res) => {
    try {
      const filter = req.body;
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
  app2.get("/api/v1/stocks/filter-options", async (req, res) => {
    try {
      const mockOptions = {
        exchanges: ["SH", "SZ", "BJ"],
        sections: ["\u4E3B\u677F", "\u4E2D\u5C0F\u677F", "\u521B\u4E1A\u677F", "\u79D1\u521B\u677F"],
        stockTypes: ["A\u80A1", "B\u80A1", "H\u80A1"],
        industries: ["\u94F6\u884C", "\u533B\u836F", "\u79D1\u6280", "\u5236\u9020\u4E1A", "\u623F\u5730\u4EA7"]
      };
      res.json(createAPIResponse(0, "OK", mockOptions));
    } catch (error) {
      res.status(500).json(createAPIResponse(500, "Failed to get filter options"));
    }
  });
  const httpServer = createServer(app2);
  return httpServer;
}
async function performBacktest(stockData, strategies) {
  const trades = [];
  let cash = 1e5;
  let shares = 0;
  let totalValue = cash;
  for (let i = 20; i < stockData.length; i++) {
    const currentData = stockData.slice(0, i + 1);
    const signals = strategies.map((strategy) => generateSignal(currentData, strategy));
    const buySignals = signals.filter((s) => s === "BUY").length;
    const sellSignals = signals.filter((s) => s === "SELL").length;
    const currentPrice = stockData[i].close;
    if (buySignals > sellSignals && cash > currentPrice * 100) {
      const sharesToBuy = Math.floor(cash / currentPrice / 100) * 100;
      const cost = sharesToBuy * currentPrice;
      if (sharesToBuy > 0 && cost <= cash) {
        shares += sharesToBuy;
        cash -= cost;
        trades.push({
          date: stockData[i].date,
          type: "BUY",
          price: currentPrice,
          quantity: sharesToBuy,
          commission: cost * 3e-4,
          // 0.03% commission
          marketValue: shares * currentPrice,
          cashBalance: cash
        });
      }
    }
    if (sellSignals > buySignals && shares > 0) {
      const sharesToSell = shares;
      const proceeds = sharesToSell * currentPrice;
      shares = 0;
      cash += proceeds;
      trades.push({
        date: stockData[i].date,
        type: "SELL",
        price: currentPrice,
        quantity: sharesToSell,
        commission: proceeds * 3e-4,
        // 0.03% commission
        marketValue: 0,
        cashBalance: cash
      });
    }
  }
  const finalPrice = stockData[stockData.length - 1].close;
  const finalValue = cash + shares * finalPrice;
  const totalYield = (finalValue - 1e5) / 1e5;
  return {
    return: Number(totalYield.toFixed(2)),
    trades
  };
}
function generateSignal(data, strategy) {
  const { type, parameters } = strategy;
  switch (type) {
    case "MACD":
      return generateMACDSignal(data, parameters);
    case "MA":
      return generateMASignal(data, parameters);
    case "ATR":
      return generateATRSignal(data, parameters);
    case "VOLUME":
      return generateVolumeSignal(data, parameters);
    default:
      return "HOLD";
  }
}
function generateMACDSignal(data, params) {
  if (data.length < Math.max(params.fastPeriod, params.slowPeriod, params.signalPeriod)) return "HOLD";
  const fastEMA = calculateEMA(data.map((d) => d.close), params.fastPeriod);
  const slowEMA = calculateEMA(data.map((d) => d.close), params.slowPeriod);
  if (fastEMA.length < 2 || slowEMA.length < 2) return "HOLD";
  const macdLine = fastEMA[fastEMA.length - 1] - slowEMA[slowEMA.length - 1];
  const prevMacdLine = fastEMA[fastEMA.length - 2] - slowEMA[slowEMA.length - 2];
  if (macdLine > 0 && prevMacdLine <= 0) return "BUY";
  if (macdLine < 0 && prevMacdLine >= 0) return "SELL";
  return "HOLD";
}
function generateMASignal(data, params) {
  if (data.length < Math.max(params.shortPeriod, params.longPeriod)) return "HOLD";
  const shortMA = calculateSMA(data.map((d) => d.close), params.shortPeriod);
  const longMA = calculateSMA(data.map((d) => d.close), params.longPeriod);
  if (shortMA.length < 2 || longMA.length < 2) return "HOLD";
  const currentShort = shortMA[shortMA.length - 1];
  const currentLong = longMA[longMA.length - 1];
  const prevShort = shortMA[shortMA.length - 2];
  const prevLong = longMA[longMA.length - 2];
  if (currentShort > currentLong && prevShort <= prevLong) return "BUY";
  if (currentShort < currentLong && prevShort >= prevLong) return "SELL";
  return "HOLD";
}
function generateATRSignal(data, params) {
  if (data.length < params.atrPeriod) return "HOLD";
  const atr = calculateATR(data, params.atrPeriod);
  const currentPrice = data[data.length - 1].close;
  const sma = calculateSMA(data.map((d) => d.close), params.highLowPeriod);
  if (atr.length === 0 || sma.length === 0) return "HOLD";
  const currentSMA = sma[sma.length - 1];
  const currentATR = atr[atr.length - 1];
  if (currentPrice > currentSMA + currentATR * params.atrMultiplier) return "BUY";
  if (currentPrice < currentSMA - currentATR * params.atrMultiplier) return "SELL";
  return "HOLD";
}
function generateVolumeSignal(data, params) {
  if (data.length < params.timeRange) return "HOLD";
  const volumes = data.slice(-params.timeRange).map((d) => d.volume);
  const avgVolume = volumes.reduce((sum, vol) => sum + vol, 0) / volumes.length;
  const currentVolume = data[data.length - 1].volume;
  if (currentVolume < avgVolume * params.buyVolumeMultiplier) return "BUY";
  if (currentVolume > avgVolume * params.sellVolumeMultiplier) return "SELL";
  return "HOLD";
}
function calculateSMA(prices, period) {
  const sma = [];
  for (let i = period - 1; i < prices.length; i++) {
    const sum = prices.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0);
    sma.push(sum / period);
  }
  return sma;
}
function calculateEMA(prices, period) {
  const ema = [];
  const multiplier = 2 / (period + 1);
  const firstSMA = prices.slice(0, period).reduce((a, b) => a + b, 0) / period;
  ema.push(firstSMA);
  for (let i = period; i < prices.length; i++) {
    const currentEMA = prices[i] * multiplier + ema[ema.length - 1] * (1 - multiplier);
    ema.push(currentEMA);
  }
  return ema;
}
function calculateATR(data, period) {
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

// server/vite.ts
import express from "express";
import fs from "fs";
import path2 from "path";
import { createServer as createViteServer, createLogger } from "vite";

// vite.config.ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";
import runtimeErrorOverlay from "@replit/vite-plugin-runtime-error-modal";
var vite_config_default = defineConfig({
  plugins: [
    react(),
    runtimeErrorOverlay(),
    ...process.env.NODE_ENV !== "production" && process.env.REPL_ID !== void 0 ? [
      await import("@replit/vite-plugin-cartographer").then(
        (m) => m.cartographer()
      )
    ] : []
  ],
  define: {
    // 将环境变量注入到客户端
    // 'import.meta.env.VITE_API_BASE_URL': JSON.stringify(env.VITE_API_BASE_URL || 'http://localhost:8000'),
  },
  resolve: {
    alias: {
      "@": path.resolve(import.meta.dirname, "client", "src"),
      "@shared": path.resolve(import.meta.dirname, "shared"),
      "@assets": path.resolve(import.meta.dirname, "attached_assets")
    }
  },
  root: path.resolve(import.meta.dirname, "client"),
  build: {
    outDir: path.resolve(import.meta.dirname, "dist/public"),
    emptyOutDir: true
  },
  server: {
    fs: {
      strict: true,
      deny: ["**/.*"]
    }
  }
});

// server/vite.ts
import { nanoid } from "nanoid";
var viteLogger = createLogger();
function log(message, source = "express") {
  const formattedTime = (/* @__PURE__ */ new Date()).toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
    second: "2-digit",
    hour12: true
  });
  console.log(`${formattedTime} [${source}] ${message}`);
}
async function setupVite(app2, server) {
  const serverOptions = {
    middlewareMode: true,
    hmr: { server },
    allowedHosts: true
  };
  const vite = await createViteServer({
    ...vite_config_default,
    configFile: false,
    customLogger: {
      ...viteLogger,
      error: (msg, options) => {
        viteLogger.error(msg, options);
        process.exit(1);
      }
    },
    server: serverOptions,
    appType: "custom"
  });
  app2.use(vite.middlewares);
  app2.use("*", async (req, res, next) => {
    const url = req.originalUrl;
    try {
      const clientTemplate = path2.resolve(
        import.meta.dirname,
        "..",
        "client",
        "index.html"
      );
      let template = await fs.promises.readFile(clientTemplate, "utf-8");
      template = template.replace(
        `src="/src/main.tsx"`,
        `src="/src/main.tsx?v=${nanoid()}"`
      );
      const page = await vite.transformIndexHtml(url, template);
      res.status(200).set({ "Content-Type": "text/html" }).end(page);
    } catch (e) {
      vite.ssrFixStacktrace(e);
      next(e);
    }
  });
}
function serveStatic(app2) {
  const distPath = path2.resolve(import.meta.dirname, "public");
  if (!fs.existsSync(distPath)) {
    throw new Error(
      `Could not find the build directory: ${distPath}, make sure to build the client first`
    );
  }
  app2.use(express.static(distPath));
  app2.use("*", (_req, res) => {
    res.sendFile(path2.resolve(distPath, "index.html"));
  });
}

// server/index.ts
import cors from "cors";
import "dotenv/config";
var app = express2();
app.use(express2.json());
app.use(express2.urlencoded({ extended: false }));
app.use(cors());
app.use((req, res, next) => {
  const start = Date.now();
  const path3 = req.path;
  let capturedJsonResponse = void 0;
  const originalResJson = res.json;
  res.json = function(bodyJson, ...args) {
    capturedJsonResponse = bodyJson;
    return originalResJson.apply(res, [bodyJson, ...args]);
  };
  res.on("finish", () => {
    const duration = Date.now() - start;
    if (path3.startsWith("/api")) {
      let logLine = `${req.method} ${path3} ${res.statusCode} in ${duration}ms`;
      if (capturedJsonResponse) {
        logLine += ` :: ${JSON.stringify(capturedJsonResponse)}`;
      }
      if (logLine.length > 80) {
        logLine = logLine.slice(0, 79) + "\u2026";
      }
      log(logLine);
    }
  });
  next();
});
(async () => {
  const server = await registerRoutes(app);
  app.use((err, _req, res, _next) => {
    const status = err.status || err.statusCode || 500;
    const message = err.message || "Internal Server Error";
    res.status(status).json({ message });
    throw err;
  });
  if (app.get("env") === "development") {
    await setupVite(app, server);
  } else {
    serveStatic(app);
  }
  const port = parseInt(process.env.PORT || "5000", 10);
  server.listen({
    port,
    host: "0.0.0.0",
    reusePort: true
  }, () => {
    log(`serving on port ${port}`);
  });
})();
