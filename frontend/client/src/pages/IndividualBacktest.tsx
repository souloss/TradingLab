import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useLocation } from "wouter";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import StrategyCard from "@/components/StrategyCard";
import LoadingOverlay from "@/components/LoadingOverlay";
import { apiRequest } from "@/lib/queryClient";
import type { BacktestResponse } from "../types";

interface StrategyConfig {
  id: string;
  name: string;
  type: 'MACD' | 'MA' | 'ATR' | 'VOLUME';
  description: string;
  icon: string;
  color: string;
  bgColor: string;
  borderColor: string;
}

const strategies: StrategyConfig[] = [
  {
    id: 'macd',
    name: 'MACD策略',
    type: 'MACD',
    description: '移动平均收敛发散指标，适用于趋势跟踪',
    icon: 'fas fa-chart-line',
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200'
  },
  {
    id: 'ma',
    name: '双均线策略',
    type: 'MA',
    description: '短期与长期均线交叉信号',
    icon: 'fas fa-chart-area',
    color: 'text-green-600',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200'
  },
  {
    id: 'atr',
    name: 'ATR策略',
    type: 'ATR',
    description: '平均真实波动范围，用于止损和趋势判断',
    icon: 'fas fa-signal',
    color: 'text-orange-600',
    bgColor: 'bg-orange-50',
    borderColor: 'border-orange-200'
  },
  {
    id: 'volume',
    name: '成交量策略',
    type: 'VOLUME',
    description: '基于成交量变化的买卖信号',
    icon: 'fas fa-volume-up',
    color: 'text-purple-600',
    bgColor: 'bg-purple-50',
    borderColor: 'border-purple-200'
  }
];

export default function IndividualBacktest() {
  const [, setLocation] = useLocation();
  const [stockCode, setStockCode] = useState("001335");
  // 取今天的日期
  const today = new Date();
  // 取一年前的同一天
  const oneYearAgo = new Date();
  oneYearAgo.setFullYear(today.getFullYear() - 1);
  // 转成 YYYY-MM-DD 的字符串（本地时区）
  const formatDate = (date: Date) => date.toISOString().split('T')[0];
  const [startDate, setStartDate] = useState(formatDate(oneYearAgo));
  const [endDate, setEndDate] = useState(formatDate(today));

  const [selectedStrategies, setSelectedStrategies] = useState<Set<string>>(new Set(["volume"]));
  const [strategyParameters, setStrategyParameters] = useState<Record<string, Record<string, any>>>({
    macd: { fastPeriod: 12, slowPeriod: 26, signalPeriod: 9 },
    ma: { shortPeriod: 5, longPeriod: 20 },
    atr: { atrPeriod: 14, highLowPeriod: 20, atrMultiplier: 1.5 },
    volume: { timeRange: 60, buyVolumeMultiplier: 0.4, sellVolumeMultiplier: 3 }
  });

  const backtestMutation = useMutation({
    mutationFn: async () => {
      const selectedStrategyConfigs = Array.from(selectedStrategies).map(strategyId => {
        const strategy = strategies.find(s => s.id === strategyId)!;
        return {
          type: strategy.type,
          parameters: strategyParameters[strategyId]
        };
      });
      const response = await apiRequest<BacktestResponse>('POST', '/api/v1/backtest/stock', {
        stockCode,
        startDate,
        endDate,
        strategies: selectedStrategyConfigs
      });
      return response;
    },
    onSuccess: (data) => {
      setLocation("/results/" + data.id);
    }
  });

  const handleStrategyToggle = (strategyId: string) => {
    const newSelected = new Set(selectedStrategies);
    if (newSelected.has(strategyId)) {
      newSelected.delete(strategyId);
    } else {
      newSelected.add(strategyId);
    }
    setSelectedStrategies(newSelected);
  };

  const handleParameterChange = (strategyId: string, paramName: string, value: any) => {
    setStrategyParameters(prev => ({
      ...prev,
      [strategyId]: {
        ...prev[strategyId],
        [paramName]: value
      }
    }));
  };

  const handleBacktest = () => {
    if (selectedStrategies.size === 0) {
      alert('请至少选择一个策略');
      return;
    }
    backtestMutation.mutate();
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <LoadingOverlay isVisible={backtestMutation.isPending} />
      
      <div className="mb-8">
        <div className="flex items-center space-x-3 mb-4">
          <div className="bg-success text-success-foreground rounded-lg p-2">
            <i className="fas fa-search-dollar"></i>
          </div>
          <h1 className="text-2xl font-bold text-foreground">个股回测</h1>
        </div>
        <p className="text-muted-foreground">针对单只股票进行精确的策略回测分析，支持多种技术指标组合运用</p>
      </div>

      {/* Basic Info Card */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <i className="fas fa-info-circle text-primary"></i>
            <span>基本信息</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-3 gap-6">
            <div>
              <Label htmlFor="stock-code" className="text-sm font-medium">股票代码 *</Label>
              <Input
                id="stock-code"
                placeholder="请输入6位股票代码"
                value={stockCode}
                onChange={(e) => setStockCode(e.target.value)}
                className="mt-1"
              />
              <p className="text-xs text-muted-foreground mt-1">请输入6位股票代码</p>
            </div>
            <div>
              <Label htmlFor="start-date" className="text-sm font-medium">开始日期</Label>
              <Input
                id="start-date"
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="mt-1"
              />
            </div>
            <div>
              <Label htmlFor="end-date" className="text-sm font-medium">结束日期</Label>
              <Input
                id="end-date"
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="mt-1"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Strategy Configuration */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <i className="fas fa-cog text-primary"></i>
            <span>策略配置</span>
          </CardTitle>
          <p className="text-muted-foreground">选择并配置您的量化交易策略</p>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-2 gap-4 mb-6">
            {strategies.map((strategy) => (
              <div key={strategy.id} className="space-y-4">
                <StrategyCard
                  strategy={strategy}
                  isSelected={selectedStrategies.has(strategy.id)}
                  parameters={strategyParameters[strategy.id]}
                  onToggle={handleStrategyToggle}
                  onParameterChange={handleParameterChange}
                />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Action Buttons */}
      <div className="flex justify-center space-x-4">
        <Button variant="outline" onClick={() => setLocation('/')}>
          返回首页
        </Button>
        <Button 
          onClick={handleBacktest} 
          className="bg-success text-success-foreground hover:bg-success/90"
          disabled={backtestMutation.isPending || selectedStrategies.size === 0}
        >
          <i className="fas fa-play mr-2"></i>
          开始回测
        </Button>
      </div>
    </div>
  );
}
