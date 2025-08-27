import { useEffect, useState, startTransition } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { Skeleton } from "@/components/ui/skeleton";
import { PaginatedTable, type Column } from "@/components/PaginatedTable";
import LoadingOverlay from "@/components/LoadingOverlay";
import { Link } from "wouter";
import { apiRequest } from "@/lib/queryClient";
import { BacktestListItem, BacktestListResp } from "@/types";
import { Search } from "lucide-react";

const PAGE_SIZE = 10;

// 拉取分页数据
async function fetchBacktests(page: number, pageSize: number, keyword?: string): Promise<BacktestListResp> {
  const resp = await apiRequest<BacktestListResp>(
    "GET",
    `/api/v1/backtest?page=${page}&pageSize=${pageSize}&keyword=${keyword ?? ""}`
  );
  return resp;
}

export default function BacktestList() {
  const [page, setPage] = useState(1);
  const [keyword, setKeyword] = useState("");
  const [isFirstLoad, setIsFirstLoad] = useState(true); // 首次加载标记
  const [searchKeyword, setSearchKeyword] = useState(""); // 用于实际搜索的关键词

  const { data, isLoading, error, refetch, isFetching } = useQuery({
    queryKey: ["backtests", page, searchKeyword],
    queryFn: () => fetchBacktests(page, PAGE_SIZE, searchKeyword),
    enabled: !isFirstLoad, // 只在首次加载后启用，不依赖于keyword
  });

  // 首次加载页面，自动获取第一页数据
  useEffect(() => {
    if (isFirstLoad) {
      setIsFirstLoad(false);
      refetch();
    }
  }, [isFirstLoad, refetch]);

  // 点击搜索按钮触发请求
  const handleSearch = () => {
    setPage(1); // 搜索时重置页码
    setSearchKeyword(keyword); // 设置搜索关键词，触发查询
  };

  // 处理回车键搜索
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      handleSearch();
    }
  };

  if (error) return <div className="text-red-500">加载数据失败，请稍后重试</div>;

  const columns: Column<BacktestListItem>[] = [
    {
      id: "stockCode",
      header: "股票代码",
      accessor: "stockCode",
      sortable: true,
      className: "text-primary font-semibold",
    },
    {
      id: "stockName",
      header: "股票名称",
      accessor: "stockName",
      sortable: true,
    },
    {
      id: "strategy",
      header: "策略",
      cell: (row) => (
        <div className="space-y-1">
          <div className="font-medium">{row.strategy.name}</div>
          <Tooltip>
            <TooltipTrigger asChild>
              <div className="text-xs text-muted-foreground truncate max-w-[200px] cursor-help">
                {JSON.stringify(row.strategy.params)}
              </div>
            </TooltipTrigger>
            <TooltipContent side="top" className="max-w-sm">
              <pre className="text-xs whitespace-pre-wrap">
                {JSON.stringify(row.strategy.params, null, 2)}
              </pre>
            </TooltipContent>
          </Tooltip>
        </div>
      ),
    },
    {
      id: "dateRange",
      header: "日期范围",
      cell: (row) => (
        <span className="text-sm text-muted-foreground">
          {new Date(row.start).toLocaleDateString()} -{" "}
          {new Date(row.end).toLocaleDateString()}
        </span>
      ),
    },
    {
      id: "action",
      header: "操作",
      cell: (row) => (
        <Link href={`/results/${row.id}`} onClick={(e) => {
          e.preventDefault();
          startTransition(() => {
            window.location.href = `/results/${row.id}`;
          });
        }}>
          <Button variant="outline" size="sm">
            查看结果
          </Button>
        </Link>
      ),
    },
  ];

  return (
    <div className="container mx-auto py-10 space-y-6">
      <LoadingOverlay isVisible={isLoading || isFetching} />
      {/* 顶部操作栏 */}
      <div className="flex items-center justify-between gap-4">
        <h1 className="text-2xl font-bold tracking-tight">历史回测记录</h1>
        <div className="flex items-center gap-2">
          <Input
            placeholder="搜索股票或策略..."
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            onKeyDown={handleKeyDown}
            className="w-64"
          />
          <Button onClick={handleSearch}>
            <Search className="w-4 h-4 mr-1" /> 搜索
          </Button>
        </div>
      </div>
      {/* 数据卡片 */}
      <Card className="shadow-lg border rounded-2xl">
        <CardHeader className="pb-4">
          <CardTitle className="text-lg font-semibold">回测列表</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-10 w-full rounded-lg" />
              ))}
            </div>
          ) : (
            <PaginatedTable<BacktestListItem>
              columns={columns}
              data={data?.items ?? []}
              page={page}
              pageSize={PAGE_SIZE}
              totalItems={data?.total ?? 0}
              onPageChange={(p) => {
                setPage(p);
                // 翻页时不需要手动调用refetch，因为useQuery会自动响应page变化
              }}
              rowKey={(row) => row.id}
            />
          )}
        </CardContent>
      </Card>
    </div>
  );
}