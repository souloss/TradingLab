import { sql } from "drizzle-orm";
import { pgTable, text, varchar, real, integer, boolean, timestamp, jsonb } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

export const stocks = pgTable("stocks", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  symbol: varchar("symbol", { length: 10 }).notNull().unique(),
  name: text("name").notNull(),
  exchange: text("exchange").notNull(),
  industry: text("industry").notNull(),
  stockType: text("stock_type").notNull(),
  section: text("section").notNull(),
  totalShares: real("total_shares").notNull(),
  floatShares: real("float_shares").notNull(),
  totalMarketValue: real("market_cap").notNull(),
  floatMarketValue: real("float_market_cap").notNull(),
  listingDate: timestamp("listing_date").notNull(),
});

export const backtestResults = pgTable("backtest_results", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  stockCode: varchar("stock_code", { length: 10 }),
  startDate: timestamp("start_date").notNull(),
  endDate: timestamp("end_date").notNull(),
  strategies: jsonb("strategies").notNull(),
  return: real("return").notNull(),
  tradeCount: integer("trade_count").notNull(),
  trades: jsonb("trades").notNull(),
  createdAt: timestamp("created_at").default(sql`now()`),
});

// Insert schemas
export const insertStockSchema = createInsertSchema(stocks).omit({
  id: true,
});

export const insertBacktestResultSchema = createInsertSchema(backtestResults).omit({
  id: true,
  createdAt: true,
});

// Strategy parameter schemas
export const macdParametersSchema = z.object({
  fastPeriod: z.number().min(1).max(100).default(12),
  slowPeriod: z.number().min(1).max(100).default(26),
  signalPeriod: z.number().min(1).max(100).default(9),
});

export const maParametersSchema = z.object({
  shortPeriod: z.number().min(1).max(100).default(5),
  longPeriod: z.number().min(1).max(100).default(20),
});

export const atrParametersSchema = z.object({
  atrPeriod: z.number().min(1).max(100).default(14),
  highLowPeriod: z.number().min(1).max(100).default(20),
  atrMultiplier: z.number().min(0.1).max(10).default(1.5),
});

export const volumeParametersSchema = z.object({
  timeRange: z.number().min(1).max(100).default(20),
  buyVolumeMultiplier: z.number().min(0.1).max(5).default(0.3),
  sellVolumeMultiplier: z.number().min(1).max(10).default(3),
});

export const stockFilterSchema = z.object({
  exchange: z.string().optional(),
  sector: z.string().optional(),
  industry: z.string().optional(),
  stockType: z.string().optional(),
  board: z.string().optional(),
  minMarketCap: z.number().min(0).default(0),
  maxMarketCap: z.number().max(2000).default(2000),
  startListingDate: z.string().optional(),
  endListingDate: z.string().optional(),
});

// Types
export type Stock = typeof stocks.$inferSelect;
export type InsertStock = z.infer<typeof insertStockSchema>;
export type BacktestResult = typeof backtestResults.$inferSelect;
export type InsertBacktestResult = z.infer<typeof insertBacktestResultSchema>;

export type MACDParameters = z.infer<typeof macdParametersSchema>;
export type MAParameters = z.infer<typeof maParametersSchema>;
export type ATRParameters = z.infer<typeof atrParametersSchema>;
export type VolumeParameters = z.infer<typeof volumeParametersSchema>;
export type StockFilter = z.infer<typeof stockFilterSchema>;

export type StrategyType = 'MACD' | 'MA' | 'ATR' | 'VOLUME';

export interface Trade {
  date: string;
  type: 'BUY' | 'SELL' | 'HOLD';
  price: number;
  quantity: number;
  commission?: number;
  marketValue?: number;
  cashBalance?: number;
}

export interface StockFilterOptions {
  exchanges: string[];
  industries: string[];
  stockTypes: string[];
  sections: string[];
}

// API Request/Response types
export const backtestRequestSchema = z.object({
  stockCode: z.string(),
  startDate: z.string(),
  endDate: z.string(),
  strategies: z.array(z.object({
    type: z.enum(['MACD', 'MA', 'ATR', 'VOLUME']),
    parameters: z.record(z.any()),
  })),
});

export const stockBasicInfoFilterSchema = z.object({
  exchange: z.array(z.string()).optional().nullable(),
  sections: z.array(z.string()).optional().nullable(),
  stock_type: z.array(z.string()).optional().nullable(),
  industries: z.array(z.string()).optional().nullable(),
  start_listing_date: z.string().optional().nullable(),
  end_listing_date: z.string().optional().nullable(),
  min_market_cap: z.number().optional().nullable(),
  max_market_cap: z.number().optional().nullable(),
});

export interface BacktestRequest {
  stockCode: string;
  startDate: string;
  endDate: string;
  strategies: {
    type: StrategyType;
    parameters: MACDParameters | MAParameters | ATRParameters | VolumeParameters;
  }[];
}

export interface StockBasicInfoFilter {
  exchange?: string[] | null;
  sections?: string[] | null;
  stock_type?: string[] | null;
  industries?: string[] | null;
  start_listing_date?: string | null;
  end_listing_date?: string | null;
  min_market_cap?: number | null;
  max_market_cap?: number | null;
}

export interface StockBasicInfoSchema {
  symbol: string;
  name: string;
  exchange: string;
  section: string;
  stockType?: string | null;
  listingDate?: string | null;
  industry?: string | null;
  totalShares?: number | null;
  floatShares?: number | null;
  totalMarketValue?: number | null;
  floatMarketValue?: number | null;
  lastUpdate: string;
}

export interface BacktestResponse {
  id: string;
  stockCode: string;
  stockName: string;
  return: number;
  tradeCount: number;
  trades: Trade[];
  chartData: any[];
  strategies: any[];
}

export interface BacktestResultItem {
  stockCode: string;
  backtestId: string;
  return: number;
  signalType: 'BUY' | 'SELL' | 'HOLD';
  buyCount: number;
  sellCount: number;
}

export interface ChartData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}