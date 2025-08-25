import { useLocation, useParams } from "wouter";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import BacktestResults from "@/components/BacktestResults";
import type { APIResponse, BacktestResponse } from "../types";
import { apiRequest } from "@/lib/queryClient";
import { useQuery } from "@tanstack/react-query";

export default function ResultsPage() {
  const { id } = useParams();
  const [, setLocation] = useLocation();

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
          </div>
        </div>
      </div>

      {/* 回测结果组件 */}
      <BacktestResults 
        stats={backtestData.backtestStats}
        charts={backtestData.chartData}
      />
    </div>
  );
}
