import { useState, useEffect, useMemo } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import StrategyCard from "@/components/StrategyCard";
import LoadingOverlay from "@/components/LoadingOverlay";
import { apiRequest } from "@/lib/queryClient";
import type { Stock, StockFilterOptions } from "@shared/schema";
import type { BacktestResults } from "../types";
import { useLocation } from "wouter";
import { PaginatedTable, type Column } from "@/components/PaginatedTable";
import { BacktestDateRangeCard } from "@/components/BacktestDateRangeCard";
import { addYears } from "date-fns";
import { DateRange } from "react-day-picker";
import dayjs from "dayjs";

const exchangeNameMap: Record<string, string> = {
  SZ: '深圳证券交易所',
  SH: '上海证券交易所',
  BJ: '北京证券交易所',
};

const strategies = [
  {
    id: 'macd',
    name: 'MACD策略',
    type: 'MACD' as const,
    description: '移动平均收敛发散指标，适用于趋势跟踪',
    icon: 'fas fa-chart-line',
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200'
  },
  {
    id: 'atr',
    name: 'ATR策略',
    type: 'ATR' as const,
    description: '平均真实波动范围，用于止损和趋势判断',
    icon: 'fas fa-signal',
    color: 'text-orange-600',
    bgColor: 'bg-orange-50',
    borderColor: 'border-orange-200'
  },
  {
    id: 'ma',
    name: '双均线策略',
    type: 'MA' as const,
    description: '短期与长期均线交叉信号',
    icon: 'fas fa-chart-area',
    color: 'text-green-600',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200'
  },
  {
    id: 'volume',
    name: '成交量策略',
    type: 'VOLUME' as const,
    description: '基于成交量变化的买卖信号',
    icon: 'fas fa-volume-up',
    color: 'text-purple-600',
    bgColor: 'bg-purple-50',
    borderColor: 'border-purple-200'
  }
];

export default function SelectionBacktest() {
  const [location, setLocation] = useLocation();
  const [currentStep, setCurrentStep] = useState(1);
  const [filterCriteria, setFilterCriteria] = useState({
    exchange: 'All',
    sections: 'All',
    industries: 'All',
    stockType: 'All',
    board: 'All',
    minMarketCap: 0,
    maxMarketCap: 2000,
    startListingDate: '2020-01-01',
    endListingDate: '2024-12-31'
  });
  const [filteredStocks, setFilteredStocks] = useState<Stock[]>([]);

  // 改为单选，存储当前选中的策略ID
  const [selectedStrategy, setSelectedStrategy] = useState<string | null>("macd");

  const [strategyParameters, setStrategyParameters] = useState<Record<string, Record<string, any>>>({
    macd: { fastPeriod: 12, slowPeriod: 26, signalPeriod: 9 },
    ma: { shortPeriod: 5, longPeriod: 20 },
    atr: { atr_period: 14, period: 20, atr_multiplier: 1.5 },
    volume: { period: 20, buyVolumeMultiplier: 0.3, sellVolumeMultiplier: 3 }
  });

  // 添加一个状态来标记是否使用自动参数优化
  const [autoOptimize, setAutoOptimize] = useState(false);

  const [backtestResults, setBacktestResults] = useState<BacktestResults>([]);
  const [stockFilterOptions, setStockFilterOptions] = useState<StockFilterOptions>({
    exchanges: [],
    industries: [],
    stockTypes: [],
    sections: []
  });

  // 创建股票代码到股票信息的映射
  const stockMap = useMemo(() => {
    const map = new Map<string, Stock>();
    filteredStocks.forEach(stock => {
      map.set(stock.symbol, stock);
    });
    return map;
  }, [filteredStocks]);

  // 计算汇总信息
  const summaryStats = useMemo(() => {
    if (backtestResults.length === 0) {
      return {
        stockCount: 0,
        buySignals: 0,
        sellSignals: 0,
        averageReturn: 0,
        totalBuyCount: 0,
        totalSellCount: 0
      };
    }
    const buySignals = backtestResults.filter(r => r.signalType === 'BUY').length;
    const sellSignals = backtestResults.filter(r => r.signalType === 'SELL').length;
    const totalBuyCount = backtestResults.reduce((sum, r) => sum + r.buyCount, 0);
    const totalSellCount = backtestResults.reduce((sum, r) => sum + r.sellCount, 0);
    const averageReturn = backtestResults.reduce((sum, r) => sum + r.return, 0) / backtestResults.length;
    return {
      stockCount: backtestResults.length,
      buySignals,
      sellSignals,
      averageReturn,
      totalBuyCount,
      totalSellCount
    };
  }, [backtestResults]);

  const toYi = (v: number | undefined | null) =>
    v == null ? "-" : (v / 100000000).toFixed(2);

  // 后端过滤器类型
  interface StockBasicInfoFilter {
    exchange?: string[];
    sections?: string[];
    stock_type?: string[];
    industries?: string[];
    start_listing_date?: string;
    end_listing_date?: string;
    min_market_cap?: number;
    max_market_cap?: number;
  }

  // 转换函数：将前端状态转换为后端格式
  const convertToBackendFilter = (criteria: typeof filterCriteria): StockBasicInfoFilter => {
    const isAll = (value: string) => value === 'All' || value === '';
    return {
      exchange: isAll(criteria.exchange) ? undefined : [criteria.exchange],
      sections: isAll(criteria.board) ? undefined : [criteria.board],
      stock_type: isAll(criteria.stockType) ? undefined : [criteria.stockType],
      industries: isAll(criteria.industries) ? undefined : [criteria.industries],
      start_listing_date: criteria.startListingDate || undefined,
      end_listing_date: criteria.endListingDate || undefined,
      min_market_cap: criteria.minMarketCap > 0 ? criteria.minMarketCap * 100000000 : undefined,
      max_market_cap: 2000 * 100000000,
    };
  };

  // Step 1：筛选结果表 列定义
  const stockColumns: Column<Stock>[] = [
    {
      id: "symbol",
      header: "股票代码",
      accessor: "symbol",
      sortable: true,
      className: "text-primary font-medium",
    },
    {
      id: "name",
      header: "股票名称",
      accessor: "name",
      sortable: true,
    },
    {
      id: "exchange",
      header: "交易所",
      sortable: true,
      cell: (row) => exchangeNameMap[row.exchange] || row.exchange,
      // 排序按照原始值
      sortFn: (a, b) => (a.exchange || "").localeCompare(b.exchange || "", "zh-CN"),
    },
    {
      id: "section",
      header: "板块",
      accessor: "section",
      sortable: true,
    },
    {
      id: "industry",
      header: "行业",
      accessor: "industry",
      sortable: true,
    },
    {
      id: "totalMarketValue",
      header: "总市值(亿)",
      sortable: true,
      cell: (row) => toYi(row.totalMarketValue),
      sortFn: (a, b) => (a.totalMarketValue ?? 0) - (b.totalMarketValue ?? 0),
      align: "right",
      width: "140px",
    },
    {
      id: "floatMarketValue",
      header: "流通市值(亿)",
      sortable: true,
      cell: (row) => toYi(row.floatMarketValue),
      sortFn: (a, b) => (a.floatMarketValue ?? 0) - (b.floatMarketValue ?? 0),
      align: "right",
      width: "140px",
    },
  ];

  type BacktestRow = BacktestResults[number];
  const backtestColumns: Column<BacktestRow>[] = [
    {
      id: "stockCode",
      header: "股票代码",
      accessor: "stockCode",
      sortable: true,
      className: "text-primary font-medium",
    },
    {
      id: "name",
      header: "股票名称",
      sortable: true,
      cell: (row) => {
        const stock = stockMap.get(row.stockCode);
        return stock ? stock.name : "-";
      },
      // 排序依据名称字符串
      sortFn: (a, b) => {
        const sa = stockMap.get(a.stockCode)?.name ?? "";
        const sb = stockMap.get(b.stockCode)?.name ?? "";
        return sa.localeCompare(sb, "zh-CN");
      },
    },
    {
      id: "industry",
      header: "行业",
      sortable: true,
      cell: (row) => {
        const stock = stockMap.get(row.stockCode);
        return stock ? stock.industry : "-";
      },
      sortFn: (a, b) => {
        const sa = stockMap.get(a.stockCode)?.industry ?? "";
        const sb = stockMap.get(b.stockCode)?.industry ?? "";
        return sa.localeCompare(sb, "zh-CN");
      },
    },
    {
      id: "signalType",
      header: "今日信号",
      sortable: true,
      cell: (row) => getSignalBadge(row.signalType),
      sortFn: (a, b) => (a.signalType || "").localeCompare(b.signalType || "", "zh-CN"),
      align: "center",
      width: "120px",
    },
    {
      id: "return",
      header: "收益率",
      sortable: true,
      cell: (row) => (
        <span className={row.return >= 0 ? "text-success font-medium" : "text-destructive font-medium"}>
          {row.return >= 0 ? "+" : ""}
          {row.return.toFixed(2)}%
        </span>
      ),
      sortFn: (a, b) => (a.return ?? 0) - (b.return ?? 0),
      align: "right",
      width: "120px",
    },
    {
      id: "marketCap",
      header: "市值(亿)",
      sortable: true,
      cell: (row) => {
        const stock = stockMap.get(row.stockCode);
        return stock ? (stock.totalMarketValue / 1e8).toFixed(2) : "-";
      },
      sortFn: (a, b) => {
        const va = stockMap.get(a.stockCode)?.totalMarketValue ?? 0;
        const vb = stockMap.get(b.stockCode)?.totalMarketValue ?? 0;
        return va - vb;
      },
      align: "right",
      width: "120px",
    },
    {
      id: "action",
      header: "操作",
      cell: (row) => (
        <Button
          variant="ghost"
          size="sm"
          className="text-primary hover:text-primary/80"
          onClick={() => window.open(`/results/${row.backtestId}`)}
        >
          <i className="fas fa-chart-line mr-1"></i>查看详情
        </Button>
      ),
      // 操作列不参与排序
      sortable: false,
      align: "center",
      width: "120px",
    },
  ];

  const [dateRange, setDateRange] = useState({
    startDate: addYears(new Date(), -1),
    endDate: new Date(),
  });

  // 添加获取过滤器选项的useQuery
  const filterOptionsQuery = useQuery({
    queryKey: ['stockFilterOptions'],
    queryFn: async () => {
      const response = await apiRequest<StockFilterOptions>('GET', '/api/v1/stocks/filter-options');
      return response;
    }
  });

  // 3. 数据获取成功时更新状态
  useEffect(() => {
    if (filterOptionsQuery.isSuccess && filterOptionsQuery.data) {
      setStockFilterOptions(filterOptionsQuery.data); // 数据成功时更新状态
    }
  }, [filterOptionsQuery.isSuccess, filterOptionsQuery.data]); // 依赖项确保及时触发

  const filterStocksMutation = useMutation({
    mutationFn: async () => {
      const backendFilter = convertToBackendFilter(filterCriteria);
      const response = await apiRequest<Stock[]>('POST', '/api/v1/stocks/filter', backendFilter);
      return response
    },
    onSuccess: (data) => {
      setFilteredStocks(data);
    }
  });

  const selectionBacktestMutation = useMutation({
    mutationFn: async () => {
      // 如果没有选中策略，则返回错误
      if (!selectedStrategy) {
        throw new Error('请选择一个策略');
      }

      const strategy = strategies.find(s => s.id === selectedStrategy)!;

      // 构建单个策略配置对象
      const selectedStrategyConfig = {
        type: strategy.type,
        parameters: autoOptimize ? {} : strategyParameters[selectedStrategy],
        optimize: autoOptimize
      };

      // 为每只股票创建回测请求
      const backtestRequests = filteredStocks.map(stock => ({
        stockCode: stock.symbol, // 使用股票代码
        startDate: dayjs(dateRange.startDate).format("YYYY-MM-DD"),
        endDate: dayjs(dateRange.endDate).format("YYYY-MM-DD"),
        strategy: selectedStrategyConfig // 使用单个策略对象而不是数组
      }));

      // 发送批量回测请求
      const response = await apiRequest<BacktestResults>(
        'POST',
        '/api/v1/backtest/stocks',
        backtestRequests
      );
      return response;
    },
    onSuccess: (data) => {
      setBacktestResults(data);
      setCurrentStep(3);
    },
    onError: (error) => {
      console.error('回测失败:', error);
      // 可以在这里添加错误处理逻辑，比如显示错误提示
    }
  });

  const handleInitialFilter = () => {
    filterStocksMutation.mutate();
  };

  // 修改策略选择处理函数，改为单选
  const handleStrategySelect = (strategyId: string) => {
    setSelectedStrategy(selectedStrategy === strategyId ? null : strategyId);
    // 当选择新策略时，关闭自动优化
    if (autoOptimize) {
      setAutoOptimize(false);
    }
  };

  const handleParameterChange = (strategyId: string, paramName: string, value: any) => {
    setStrategyParameters(prev => ({
      ...prev,
      [strategyId]: {
        ...prev[strategyId],
        [paramName]: value
      }
    }));
    // 当手动修改参数时，关闭自动优化
    if (autoOptimize) {
      setAutoOptimize(false);
    }
  };

  // 处理自动参数优化
  const handleAutoOptimize = () => {
    if (!selectedStrategy) {
      alert('请先选择一个策略');
      return;
    }
    setAutoOptimize(true);
  };

  const handleStartBacktest = () => {
    if (!selectedStrategy) {
      alert('请选择一个策略');
      return;
    }
    selectionBacktestMutation.mutate();
  };

  const stepNavigation = [
    { id: 1, label: "基本选股", icon: "fas fa-search", active: currentStep === 1 },
    { id: 2, label: "技术面配置", icon: "fas fa-cog", active: currentStep === 2 },
    { id: 3, label: "回测结果", icon: "fas fa-chart-bar", active: currentStep === 3 }
  ];

  const getSignalBadge = (signalType: string) => {
    switch (signalType) {
      case 'BUY':
        return <Badge variant="secondary" className="bg-gray-100 text-gray-700">买入</Badge>;
      case 'SELL':
        return <Badge variant="destructive" className="bg-red-100 text-red-700">卖出</Badge>;
      default:
        return <Badge variant="outline">观望</Badge>;
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <LoadingOverlay isVisible={filterStocksMutation.isPending || selectionBacktestMutation.isPending} />

      <div className="mb-8">
        <div className="flex items-center space-x-3 mb-4">
          <div className="bg-secondary text-secondary-foreground rounded-lg p-2">
            <i className="fas fa-filter"></i>
          </div>
          <h1 className="text-2xl font-bold text-foreground">选股回测</h1>
        </div>
        <p className="text-muted-foreground">基于多条件筛选来进行策略分析和批量回测投资</p>
      </div>

      {/* Step Navigation */}
      <div className="flex mb-8">
        <div className="flex items-center">
          {stepNavigation.map((step, index) => (
            <div key={step.id} className="flex items-center">
              <div className={`step-nav px-4 py-2 rounded-lg text-sm font-medium transition-colors ${step.active
                  ? step.id === 3
                    ? "active bg-secondary text-secondary-foreground"
                    : "active bg-success text-success-foreground"
                  : step.id < currentStep
                    ? "bg-green-100 text-green-700"
                    : "bg-muted text-muted-foreground"
                }`}>
                <i className={`${step.icon} mr-2`}></i>
                {step.label}
              </div>
              {index < stepNavigation.length - 1 && (
                <div className="w-8 h-0.5 bg-border mx-2"></div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Step 1: Basic Stock Selection */}
      {currentStep === 1 && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <i className="fas fa-filter text-secondary"></i>
                <span>股票筛选条件</span>
              </CardTitle>
              <p className="text-muted-foreground">设置筛选条件对股票条件先进行基本筛选</p>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-4 gap-6 mb-6">
                <div>
                  <Label htmlFor="exchange">交易所</Label>
                  <Select value={filterCriteria.exchange} onValueChange={(v) => setFilterCriteria(p => ({ ...p, exchange: v }))}>
                    <SelectTrigger><SelectValue placeholder="所有交易所" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="All">所有交易所</SelectItem>
                      {stockFilterOptions.exchanges.map(ex => (
                        <SelectItem key={ex} value={ex}>
                          {exchangeNameMap[ex] || ex}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="sector">行业</Label>
                  <Select value={filterCriteria.industries} onValueChange={(v) => setFilterCriteria(p => ({ ...p, industries: v }))}>
                    <SelectTrigger><SelectValue placeholder="所有行业" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="All">所有行业</SelectItem>
                      {stockFilterOptions.industries.map(ind => (
                        <SelectItem key={ind} value={ind}>{ind}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="stockType">股票类型</Label>
                  <Select value={filterCriteria.stockType} onValueChange={(v) => setFilterCriteria(p => ({ ...p, stockType: v }))}>
                    <SelectTrigger><SelectValue placeholder="所有类型" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="All">所有类型</SelectItem>
                      {stockFilterOptions.stockTypes.map(st => (
                        <SelectItem key={st} value={st}>{st}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="board">板块</Label>
                  <Select value={filterCriteria.board} onValueChange={(v) => setFilterCriteria(p => ({ ...p, board: v }))}>
                    <SelectTrigger><SelectValue placeholder="所有板块" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="All">所有板块</SelectItem>
                      {stockFilterOptions.sections.map(b => (
                        <SelectItem key={b} value={b}>{b}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="mb-6">
                <Label className="text-sm font-medium">市值范围 (亿元): {filterCriteria.minMarketCap} - {filterCriteria.maxMarketCap}</Label>
                <div className="mt-2">
                  <Slider
                    value={[filterCriteria.minMarketCap, filterCriteria.maxMarketCap]}
                    onValueChange={([min, max]) => setFilterCriteria(prev => ({ ...prev, minMarketCap: min, maxMarketCap: max }))}
                    max={2000}
                    min={0}
                    step={1}
                    className="w-full"
                  />
                </div>
              </div>
              <div className="grid md:grid-cols-2 gap-6 mb-6">
                <div>
                  <Label htmlFor="startListingDate">上市起始日期</Label>
                  <Input
                    id="startListingDate"
                    type="date"
                    value={filterCriteria.startListingDate}
                    onChange={(e) => setFilterCriteria(prev => ({ ...prev, startListingDate: e.target.value }))}
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label htmlFor="endListingDate">上市截止日期</Label>
                  <Input
                    id="endListingDate"
                    type="date"
                    value={filterCriteria.endListingDate}
                    onChange={(e) => setFilterCriteria(prev => ({ ...prev, endListingDate: e.target.value }))}
                    className="mt-1"
                  />
                </div>
              </div>
              <Button
                onClick={handleInitialFilter}
                className="bg-secondary text-secondary-foreground hover:bg-secondary/90"
                disabled={filterStocksMutation.isPending}
              >
                <i className="fas fa-search mr-2"></i>
                初步筛选
              </Button>
            </CardContent>
          </Card>

          {/* Selection Results */}
          {filteredStocks.length > 0 && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <i className="fas fa-list text-muted-foreground"></i>
                    <CardTitle>筛选结果</CardTitle>
                    <Badge variant="secondary">共 {filteredStocks.length} 只股票</Badge>
                  </div>
                  <Button
                    onClick={() => setCurrentStep(2)}
                    className="bg-success text-success-foreground hover:bg-success/90"
                  >
                    下一步：策略配置 <i className="fas fa-arrow-right ml-2"></i>
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <PaginatedTable<Stock>
                  columns={stockColumns}
                  data={filteredStocks}
                  caption="已按照当前筛选条件展示"
                  pageSizeOptions={[10, 20, 50]}
                  dense
                  rowKey={(row) => row.id}
                />
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Step 2: Strategy Configuration */}
      {currentStep === 2 && (
        <div className="space-y-6">
          <Card className="bg-green-50 border-green-200">
            <CardContent className="pt-6">
              <div className="flex items-center space-x-2 mb-4">
                <i className="fas fa-check-circle text-success"></i>
                <h3 className="text-lg font-semibold text-success">已筛选股票</h3>
                <Badge className="bg-green-100 text-green-800">{filteredStocks.length} 只股票</Badge>
              </div>
              <p className="text-green-700">基于筛选条件，共筛选出 {filteredStocks.length} 只股票，现在请设置技术分析配置对以上股票进行回测。</p>
            </CardContent>
          </Card>

          <BacktestDateRangeCard
            startDate={dateRange.startDate}
            endDate={dateRange.endDate}
            onChange={setDateRange}
          />

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <i className="fas fa-cog text-primary"></i>
                <span>策略配置</span>
              </CardTitle>
              <p className="text-muted-foreground">选择并配置您的量化交易策略</p>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-2 gap-4">
                {strategies.map((strategy) => (
                  <StrategyCard
                    key={strategy.id}
                    strategy={strategy}
                    isSelected={selectedStrategy === strategy.id}
                    parameters={strategyParameters[strategy.id]}
                    onToggle={handleStrategySelect} // 改为单选处理函数
                    onParameterChange={handleParameterChange}
                    isSingleSelect={true} // 添加单选模式标志
                  />
                ))}
              </div>

              {/* 自动参数优化按钮 */}
              <div className="mt-6 flex justify-center">
                <Button
                  variant={autoOptimize ? "default" : "outline"}
                  className={`${autoOptimize ? "bg-indigo-600 hover:bg-indigo-700" : "border-indigo-600 text-indigo-600 hover:bg-indigo-50"}`}
                  onClick={handleAutoOptimize}
                  disabled={!selectedStrategy}
                >
                  <i className={`fas ${autoOptimize ? "fa-check-circle" : "fa-magic"} mr-2`}></i>
                  {autoOptimize ? "已启用自动参数优化" : "自动策略参数调优"}
                </Button>
              </div>

              {autoOptimize && (
                <div className="mt-4 p-4 bg-indigo-50 rounded-lg border border-indigo-200">
                  <div className="flex items-start">
                    <i className="fas fa-info-circle text-indigo-600 mt-1 mr-2"></i>
                    <div>
                      <p className="text-sm font-medium text-indigo-800">自动参数优化已启用</p>
                      <p className="text-sm text-indigo-600 mt-1">
                        系统将自动为选定的策略寻找最优参数组合，无需手动调整。回测时间可能会稍长，但结果更加客观准确。
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          <div className="flex justify-center space-x-4">
            <Button variant="outline" onClick={() => setCurrentStep(1)}>
              返回选股
            </Button>
            <Button
              onClick={handleStartBacktest}
              className="bg-secondary text-secondary-foreground hover:bg-secondary/90"
              disabled={selectionBacktestMutation.isPending || !selectedStrategy}
            >
              <i className="fas fa-play mr-2"></i>
              开始选股回测
            </Button>
          </div>
        </div>
      )}

      {/* Step 3: Backtest Results */}
      {currentStep === 3 && backtestResults && (
        <div className="space-y-8">
          {/* Summary Statistics */}
          <div className="grid md:grid-cols-4 gap-6">
            <Card className="text-center">
              <CardContent className="pt-6">
                <div className="bg-blue-100 text-blue-600 rounded-lg p-3 w-12 h-12 flex items-center justify-center mx-auto mb-4">
                  <i className="fas fa-chart-bar"></i>
                </div>
                <div className="text-2xl font-bold text-primary mb-1">{summaryStats.stockCount}</div>
                <div className="text-sm text-muted-foreground">筛选股票数</div>
              </CardContent>
            </Card>
            <Card className="text-center">
              <CardContent className="pt-6">
                <div className="bg-green-100 text-success rounded-lg p-3 w-12 h-12 flex items-center justify-center mx-auto mb-4">
                  <i className="fas fa-arrow-up"></i>
                </div>
                <div className="text-2xl font-bold text-success mb-1">{summaryStats.buySignals}</div>
                <div className="text-sm text-muted-foreground">买入信号</div>
              </CardContent>
            </Card>
            <Card className="text-center">
              <CardContent className="pt-6">
                <div className="bg-red-100 text-destructive rounded-lg p-3 w-12 h-12 flex items-center justify-center mx-auto mb-4">
                  <i className="fas fa-arrow-down"></i>
                </div>
                <div className="text-2xl font-bold text-destructive mb-1">{summaryStats.sellSignals}</div>
                <div className="text-sm text-muted-foreground">卖出信号</div>
              </CardContent>
            </Card>
            <Card className="text-center">
              <CardContent className="pt-6">
                <div className="bg-purple-100 text-secondary rounded-lg p-3 w-12 h-12 flex items-center justify-center mx-auto mb-4">
                  <i className="fas fa-chart-line"></i>
                </div>
                <div className="text-2xl font-bold text-success mb-1">{summaryStats.averageReturn.toFixed(2)}%</div>
                <div className="text-sm text-muted-foreground">平均收益率</div>
              </CardContent>
            </Card>
          </div>

          {/* Results Table */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <i className="fas fa-chart-bar text-secondary"></i>
                  <CardTitle>回测结果</CardTitle>
                  <Badge variant="secondary">今日个股策略</Badge>
                </div>
                <Button variant="ghost" onClick={() => setCurrentStep(1)}>
                  <i className="fas fa-arrow-left mr-2"></i>返回选股
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <PaginatedTable<BacktestRow>
                columns={backtestColumns}
                data={backtestResults}
                caption="可点击列头进行排序"
                pageSizeOptions={[10, 20, 50]}
                dense
                rowKey={(row) => row.backtestId}
              />
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}