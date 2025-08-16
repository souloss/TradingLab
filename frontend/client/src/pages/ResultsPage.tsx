import { useState, useEffect } from "react";
import { useLocation, useParams } from "wouter";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import StockChart from "@/components/StockChart";
import type { APIResponse, BacktestResponse } from "../types";
import { apiRequest } from "@/lib/queryClient";
import { useQuery } from "@tanstack/react-query";

export default function ResultsPage() {
  const { id } = useParams();
  const [, setLocation] = useLocation();
  // const [backtestData, setBacktestData] = useState<BacktestResponse | null>(null);
  const [selectedPeriod, setSelectedPeriod] = useState("1y");

  // useEffect(() => {
  //   // Get backtest result from sessionStorage
  //   const storedResult = sessionStorage.getItem('backtestResult');
  //   if (storedResult) {
  //     try {
  //       const data = JSON.parse(storedResult) as BacktestResponse;
  //       setBacktestData(data);
  //     } catch (error) {
  //       console.error('Failed to parse backtest result:', error);
  //       setLocation('/individual');
  //     }
  //   } else {
  //     // Redirect back if no data
  //     setLocation('/individual');
  //   }
  // }, [setLocation]);

  const { data, isLoading, error } = useQuery({
    queryKey: ['backtest', id],
    queryFn: async () => {
      const response = await apiRequest<BacktestResponse>('GET', `/api/v1/backtest/${id}`);
      return response;
    },
    enabled: !!id,
  });

  const backtestData = data

  if (!backtestData) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">加载回测结果中...</p>
        </div>
      </div>
    );
  }

  const handleBackToTest = () => {
    sessionStorage.removeItem('backtestResult');
    setLocation('/individual');
  };

  const getTradeTypeBadge = (type: 'BUY' | 'SELL' | 'HOLD') => {
    return type === 'BUY' 
      ? <Badge className="bg-gray-900 text-white">买入</Badge>
      : <Badge variant="destructive" className="bg-red-500 text-white">卖出</Badge>;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return `${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
  };

  const formatCurrency = (amount: number) => {
    return `¥${amount.toFixed(2)}`;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">加载回测结果中...</p>
        </div>
      </div>
    );
  }

  if (error || !backtestData) {
    return (
      <div className="min-h-screen w-full flex items-center justify-center bg-gray-50">
        <Card className="w-full max-w-md mx-4">
          <CardContent className="pt-6">
            <div className="flex mb-4 gap-2">
              <i className="fas fa-exclamation-triangle text-red-500"></i>
              <h1 className="text-2xl font-bold text-gray-900">加载失败</h1>
            </div>
            <p className="mt-4 text-sm text-gray-600">
              {error?.message || '无法加载回测结果'}
            </p>
            <Button onClick={handleBackToTest} className="mt-4">
              返回回测页面
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center space-x-4 mb-4">
          <Button variant="ghost" onClick={handleBackToTest} className="text-muted-foreground hover:text-foreground">
            <i className="fas fa-arrow-left"></i>
          </Button>
          <div className="flex items-center space-x-3">
            <span className="text-sm text-muted-foreground">返回回测</span>
            <h1 className="text-2xl font-bold text-foreground">
              {backtestData.stockCode} 回测结果
            </h1>
            <Badge variant="secondary" className="bg-gray-900 text-white">日K线图</Badge>
          </div>
        </div>
        <p className="text-muted-foreground">
          {new Date(backtestData.chartData[0]?.date || '').toLocaleDateString('zh-CN')} - {new Date(backtestData.chartData[backtestData.chartData.length - 1]?.date || '').toLocaleDateString('zh-CN')}
        </p>
      </div>

      {/* Summary Statistics */}
      <div className="grid md:grid-cols-3 gap-6 mb-8">
        <Card className="bg-gradient-to-br from-blue-50 to-emerald-50 border-blue-200">
          <CardContent className="pt-6">
            <div className="flex items-center space-x-3 mb-4">
              <i className="fas fa-chart-line text-success"></i>
              <span className="text-blue-800 font-medium">总收益率</span>
            </div>
            <div className="text-3xl font-bold text-primary mb-2">
              {backtestData.return > 0 ? '+' : ''}{(backtestData.return * 100).toFixed(2)}%
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-blue-50 to-sky-50 border-blue-200">
          <CardContent className="pt-6">
            <div className="flex items-center space-x-3 mb-4">
              <i className="fas fa-exchange-alt text-primary"></i>
              <span className="text-blue-800 font-medium">交易次数</span>
            </div>
            <div className="text-3xl font-bold text-primary mb-2">{backtestData.tradeCount}</div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-purple-50 to-violet-50 border-purple-200">
          <CardContent className="pt-6">
            <div className="flex items-center space-x-3 mb-4">
              <i className="fas fa-cogs text-secondary"></i>
              <span className="text-purple-800 font-medium">使用策略</span>
            </div>
            <div className="text-3xl font-bold text-secondary mb-2">{backtestData.strategies.length}</div>
          </CardContent>
        </Card>
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Chart Section */}
        <div className="lg:col-span-2">
          <StockChart
            data={backtestData.chartData}
            trades={backtestData.trades}
            selectedPeriod={selectedPeriod}
            onPeriodChange={setSelectedPeriod}
          />
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Strategy Parameters */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <i className="fas fa-cogs text-primary"></i>
                <span>使用的策略</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {backtestData.strategies.map((strategy, index) => {
                  const getStrategyColor = (type: string) => {
                    switch (type) {
                      case 'MACD': return { bg: 'bg-blue-50', text: 'text-blue-900', label: 'text-blue-700' };
                      case 'MA': return { bg: 'bg-green-50', text: 'text-green-900', label: 'text-green-700' };
                      case 'ATR': return { bg: 'bg-orange-50', text: 'text-orange-900', label: 'text-orange-700' };
                      case 'VOLUME': return { bg: 'bg-purple-50', text: 'text-purple-900', label: 'text-purple-700' };
                      default: return { bg: 'bg-gray-50', text: 'text-gray-900', label: 'text-gray-700' };
                    }
                  };

                  const colors = getStrategyColor(strategy.type);
                  
                  return (
                    <div key={index} className={`${colors.bg} rounded-lg p-3`}>
                      <h4 className={`font-medium ${colors.text} mb-2`}>{strategy.type}</h4>
                      <div className={`space-y-1 text-sm ${colors.label}`}>
                        {Object.entries(strategy.parameters).map(([key, value]) => (
                          <div key={key} className="flex justify-between">
                            <span>{key}:</span>
                            <span>{value}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* Trading Records */}
          {/* <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <i className="fas fa-dollar-sign text-success"></i>
                <span>交易记录</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex justify-between items-center text-sm font-medium text-muted-foreground">
                  <span>日期</span>
                  <span>类型</span>
                  <span>价格</span>
                  <span>数量</span>
                </div>
                <div className="divide-y divide-border">
                  {backtestData.trades.slice(0, 10).map((trade, index) => (
                    <div key={index} className="flex justify-between items-center py-2 text-sm">
                      <span className="text-foreground">{formatDate(trade.date)}</span>
                      {getTradeTypeBadge(trade.type)}
                      <span className="text-foreground">{formatCurrency(trade.price)}</span>
                      <span className="text-foreground">{trade.quantity}</span>
                    </div>
                  ))}
                </div>
                {backtestData.trades.length > 10 && (
                  <div className="text-center pt-2">
                    <Button variant="ghost" size="sm" className="text-muted-foreground">
                      查看更多交易记录 <i className="fas fa-chevron-down ml-2"></i>
                    </Button>
                  </div>
                )}
              </div>
            </CardContent>
          </Card> */}
        </div>
      </div>

      {/* Detailed Trading Records Table */}
      {backtestData.trades.length > 0 && (
        <Card className="mt-8">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <i className="fas fa-table text-muted-foreground"></i>
              <span>详细交易记录</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>日期</TableHead>
                    <TableHead>类型</TableHead>
                    <TableHead>价格</TableHead>
                    <TableHead>数量</TableHead>
                    <TableHead>手续费</TableHead>
                    <TableHead>持仓市值</TableHead>
                    <TableHead>现金余额</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {backtestData.trades.map((trade, index) => (
                    <TableRow key={index}>
                      <TableCell>{new Date(trade.date).toLocaleDateString('zh-CN')}</TableCell>
                      <TableCell>{getTradeTypeBadge(trade.type)}</TableCell>
                      <TableCell>{formatCurrency(trade.price)}</TableCell>
                      <TableCell>{trade.quantity.toLocaleString()}</TableCell>
                      <TableCell>{trade.commission ? formatCurrency(trade.commission) : '-'}</TableCell>
                      <TableCell>{trade.marketValue ? formatCurrency(trade.marketValue) : '-'}</TableCell>
                      <TableCell>{trade.cashBalance ? formatCurrency(trade.cashBalance) : '-'}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
