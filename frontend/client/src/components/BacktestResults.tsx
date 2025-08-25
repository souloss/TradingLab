import React, { useState } from 'react';
import * as Tabs from '@radix-ui/react-tabs';
import * as Collapsible from '@radix-ui/react-collapsible';
import type { TradeRecord, EquityPoint, BacktestStats, StockData } from "@/types";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { format, parseISO } from 'date-fns';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table";
import StockChart from "@/components/StockChart";
import { useParams } from 'wouter';
import ReactMarkdown from "react-markdown";

// 格式化函数保持不变
const formatNumber = (num: number, decimals = 2) => {
    return new Intl.NumberFormat('zh-CN', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
    }).format(num);
};

export function parseDoc(doc: string | undefined) {
    if (!doc) {
        return {
            title: [],
            desc: ["暂无文档说明。"],
            params: [],
            buy: [],
            sell: [],
        };
    }

    const lines = doc.trim().split("\n").map((l) => l.trim());
    let section: keyof typeof parsed | null = null;

    const parsed: Record<"title" | "desc" | "params" | "buy" | "sell", string[]> = {
        title: [],
        desc: [],
        params: [],
        buy: [],
        sell: [],
    };

    for (const line of lines) {
        if (!line) continue; // 跳过空行

        if (line.startsWith("量价极端行情策略")) {
            parsed.title.push(line);
            continue;
        }

        if (line.startsWith("参数:")) {
            section = "params";
            continue;
        }

        if (line.startsWith("买入条件:")) {
            section = "buy";
            continue;
        }

        if (line.startsWith("卖出条件:")) {
            section = "sell";
            continue;
        }

        if (line.startsWith("买卖逻辑:")) {
            continue; // 忽略这个标签本身
        }

        if (section) {
            parsed[section].push(line.replace(/^[-•]\s*/, "")); // 去掉 - • 前缀
        } else {
            parsed.desc.push(line);
        }
    }

    return parsed;
}

const formatPercent = (num: number, decimals = 2) => {
    return `${formatNumber(num, decimals)}%`;
};

const formatCurrency = (num: number, currency = 'CNY') => {
    return new Intl.NumberFormat('zh-CN', {
        style: 'currency',
        currency,
        minimumFractionDigits: 2,
    }).format(num);
};

const formatDuration = (duration: string) => {
    return duration;
};

// 统计卡片组件
// 更新 StatCard 组件的 props 类型定义
interface StatCardProps {
    title: string;
    value: string;
    tooltip?: string;
    calculation?: string;
    color?: string;
}

// 更新 StatCard 组件定义
const StatCard: React.FC<StatCardProps> = ({
    title, value, tooltip, calculation, color = 'text-blue-600'
}) => {
    const [showTooltip, setShowTooltip] = useState(false);

    return (
        <Card className="bg-gradient-to-br from-white to-gray-50 rounded-xl shadow-md border border-gray-100 hover:shadow-lg transition-shadow duration-300 relative">
            <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-500 tracking-wide flex items-center">
                    {title}
                    {tooltip && (
                        <div className="relative ml-2">
                            <button
                                onMouseEnter={() => setShowTooltip(true)}
                                onMouseLeave={() => setShowTooltip(false)}
                                className="text-gray-400 hover:text-gray-600 focus:outline-none"
                            >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                            </button>
                            {showTooltip && (
                                <div className="absolute z-10 w-64 p-3 mt-2 text-sm text-white bg-gray-800 rounded-lg shadow-lg left-1/2 transform -translate-x-1/2">
                                    <div className="font-medium mb-1">{title}</div>
                                    <div className="text-xs text-gray-300">{tooltip}</div>
                                    {calculation && (
                                        <div className="mt-2 pt-2 border-t border-gray-700 text-xs text-gray-400">
                                            <div className="font-medium mb-1">计算方法:</div>
                                            <div>{calculation}</div>
                                        </div>
                                    )}
                                    <div className="absolute w-3 h-3 bg-gray-800 transform rotate-45 -top-1.5 left-1/2 -translate-x-1/2"></div>
                                </div>
                            )}
                        </div>
                    )}
                </CardTitle>
            </CardHeader>
            <CardContent>
                <div className={`text-2xl font-bold ${color}`}>{value}</div>
            </CardContent>
        </Card>
    );
};

// 交易记录表格组件
const TradesTable: React.FC<{ trades: TradeRecord[] }> = ({ trades }) => {
    return (
        <div className="rounded-lg border border-gray-200 shadow-sm overflow-hidden">
            <Table>
                <TableHeader className="bg-gray-50">
                    <TableRow>
                        <TableHead className="p-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">开仓时间</TableHead>
                        <TableHead className="p-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">平仓时间</TableHead>
                        <TableHead className="p-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">数量</TableHead>
                        <TableHead className="p-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">开仓价</TableHead>
                        <TableHead className="p-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">平仓价</TableHead>
                        <TableHead className="p-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">盈亏</TableHead>
                        <TableHead className="p-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">收益率</TableHead>
                        <TableHead className="p-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">持仓时间</TableHead>
                        <TableHead className="p-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">标签</TableHead>
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {trades.map((trade, index) => (
                        <TableRow key={index} className={index % 2 === 0 ? 'bg-white hover:bg-gray-50' : 'bg-gray-50 hover:bg-gray-100'}>
                            <TableCell className="p-4 whitespace-nowrap text-sm text-gray-600 font-medium">
                                {format(parseISO(trade.entry_time), 'yyyy-MM-dd HH:mm')}
                            </TableCell>
                            <TableCell className="p-4 whitespace-nowrap text-sm text-gray-600 font-medium">
                                {format(parseISO(trade.exit_time), 'yyyy-MM-dd HH:mm')}
                            </TableCell>
                            <TableCell className="p-4 whitespace-nowrap text-sm text-gray-900 font-semibold">{trade.size}</TableCell>
                            <TableCell className="p-4 whitespace-nowrap text-sm text-gray-900">{formatCurrency(trade.entry_price)}</TableCell>
                            <TableCell className="p-4 whitespace-nowrap text-sm text-gray-900">{formatCurrency(trade.exit_price)}</TableCell>
                            <TableCell className={`p-4 whitespace-nowrap text-sm font-semibold ${trade.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                {formatCurrency(trade.pnl)}
                            </TableCell>
                            <TableCell className={`p-4 whitespace-nowrap text-sm font-semibold ${trade.return_pct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                {formatPercent(trade.return_pct)}
                            </TableCell>
                            <TableCell className="p-4 whitespace-nowrap text-sm text-gray-600">{formatDuration(trade.duration)}</TableCell>
                            <TableCell className="p-4 whitespace-nowrap">
                                <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
                                    {trade.tag || '-'}
                                </span>
                            </TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </div>
    );
};

// 策略参数组件
const StrategyParams: React.FC<{ strategy: BacktestStats['strategy'] }> = ({ strategy }) => {
    const data = parseDoc(strategy.doc);
    return (
        <div className="space-y-8">
            <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border border-blue-100">
                <CardHeader>
                    <CardTitle className="text-xl font-bold text-gray-900">{strategy.name}</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="prose p-4 bg-white rounded-xl shadow">
                        <div className="space-y-4 p-4 bg-gray-50 rounded-xl">
                            <h2 className="text-xl font-bold">{data.title[0]}</h2>
                            <p className="text-gray-700">{data.desc.join(" ")}</p>

                            <div>
                                <h3 className="font-semibold">参数</h3>
                                <ul className="list-disc pl-5 text-gray-600">
                                    {data.params.map((p, i) => <li key={i}>{p}</li>)}
                                </ul>
                            </div>

                            <div>
                                <h3 className="font-semibold text-green-600">买入条件</h3>
                                <ul className="list-disc pl-5">
                                    {data.buy.map((p, i) => <li key={i}>{p}</li>)}
                                </ul>
                            </div>

                            <div>
                                <h3 className="font-semibold text-red-600">卖出条件</h3>
                                <ul className="list-disc pl-5">
                                    {data.sell.map((p, i) => <li key={i}>{p}</li>)}
                                </ul>
                            </div>
                        </div>
                    </div>
                </CardContent>
            </Card>

            <Card className="rounded-xl border border-gray-200 shadow-sm">
                <CardHeader>
                    <CardTitle className="text-lg font-semibold text-gray-900 flex items-center">
                        <svg className="w-5 h-5 mr-2 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                        策略参数
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {Object.entries(strategy.params).map(([key, value]) => (
                            <div key={key} className="flex justify-between items-center py-3 px-4 bg-gray-50 rounded-lg border border-gray-100">
                                <span className="text-gray-700 font-medium">{key}</span>
                                <span className="font-semibold text-gray-900 bg-white px-3 py-1 rounded-md border border-gray-200">{String(value)}</span>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>
        </div>
    );
};

// 主组件
const BacktestPanel: React.FC<{ 
    stats: BacktestStats
    charts: StockData[];
}> = ({ stats, charts }) => {
    const [activeTab, setActiveTab] = useState('overview');
    const { id } = useParams();
    const [selectedPeriod, setSelectedPeriod] = useState("1y");

    
    // 准备图表数据
    const chartData = stats.equity_curve.map(point => ({
        ...point,
        timestamp: format(parseISO(point.timestamp), 'MM-dd'),
    }));

    return (
        <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-2xl shadow-xl overflow-hidden border border-gray-200">
            {/* 头部 */}
            <div className="bg-gradient-to-r from-blue-600 to-indigo-700 px-8 py-6 text-white">
                <h2 className="text-3xl font-bold mb-2">策略回测结果</h2>
                <div className="flex flex-wrap items-center gap-4 text-blue-100">
                    <span className="flex items-center">
                        <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                        {format(parseISO(stats.start), 'yyyy年MM月dd日')} - {format(parseISO(stats.end), 'yyyy年MM月dd日')}
                    </span>
                    <span className="flex items-center">
                        <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        {stats.duration}
                    </span>
                </div>
            </div>

            {/* 标签页导航 */}
            <Tabs.Root value={activeTab} onValueChange={setActiveTab} className="w-full">
                <Tabs.List className="flex bg-white border-b border-gray-200">
                    <Tabs.Trigger
                        value="overview"
                        className="px-6 py-4 text-sm font-medium text-gray-600 hover:text-blue-600 data-[state=active]:text-blue-600 data-[state=active]:border-b-2 data-[state=active]:border-blue-600 focus:outline-none transition-colors duration-200"
                    >
                        概览
                    </Tabs.Trigger>
                    <Tabs.Trigger
                        value="trades"
                        className="px-6 py-4 text-sm font-medium text-gray-600 hover:text-blue-600 data-[state=active]:text-blue-600 data-[state=active]:border-b-2 data-[state=active]:border-blue-600 focus:outline-none transition-colors duration-200"
                    >
                        交易记录 ({stats.n_trades})
                    </Tabs.Trigger>
                    <Tabs.Trigger
                        value="equity"
                        className="px-6 py-4 text-sm font-medium text-gray-600 hover:text-blue-600 data-[state=active]:text-blue-600 data-[state=active]:border-b-2 data-[state=active]:border-blue-600 focus:outline-none transition-colors duration-200"
                    >
                        权益曲线
                    </Tabs.Trigger>
                    <Tabs.Trigger
                        value="kline"
                        className="px-6 py-4 text-sm font-medium text-gray-600 hover:text-blue-600 data-[state=active]:text-blue-600 data-[state=active]:border-b-2 data-[state=active]:border-blue-600 focus:outline-none transition-colors duration-200"
                    >
                        价格走势与技术指标
                    </Tabs.Trigger>
                    <Tabs.Trigger
                        value="strategy"
                        className="px-6 py-4 text-sm font-medium text-gray-600 hover:text-blue-600 data-[state=active]:text-blue-600 data-[state=active]:border-b-2 data-[state=active]:border-blue-600 focus:outline-none transition-colors duration-200"
                    >
                        策略详情
                    </Tabs.Trigger>
                </Tabs.List>

                {/* 概览标签页 */}
                <Tabs.Content value="overview" className="p-8">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
                        <StatCard
                            title="最终权益"
                            value={formatCurrency(stats.equity_final)}
                            tooltip="所有交易结束后的账户价值"
                            color="text-blue-600"
                        />
                        <StatCard
                            title="总收益率"
                            value={formatPercent(stats.return_pct)}
                            tooltip="整体投资回报率"
                            color={stats.return_pct >= 0 ? "text-green-600" : "text-red-600"}
                        />
                        <StatCard
                            title="年化收益率"
                            value={formatPercent(stats.return_ann_pct)}
                            tooltip="按年计算的收益率"
                            color={stats.return_ann_pct >= 0 ? "text-green-600" : "text-red-600"}
                        />
                        <StatCard
                            title="最大回撤"
                            value={formatPercent(stats.max_drawdown_pct)}
                            tooltip="账户价值从峰值到谷底的最大跌幅"
                            color="text-red-500"
                        />
                        <StatCard
                            title="夏普比率"
                            value={formatNumber(stats.sharpe_ratio)}
                            tooltip="风险调整后收益（越高越好）"
                            color={stats.sharpe_ratio >= 1 ? "text-green-600" : "text-yellow-600"}
                        />
                        <StatCard
                            title="胜率"
                            value={formatPercent(stats.win_rate_pct)}
                            tooltip="盈利交易占比"
                            color={stats.win_rate_pct >= 50 ? "text-green-600" : "text-yellow-600"}
                        />
                        <StatCard
                            title="盈亏比"
                            value={stats.profit_factor ? formatNumber(stats.profit_factor) : 'N/A'}
                            tooltip="总盈利与总亏损的比值"
                            color={stats.profit_factor && stats.profit_factor >= 1.5 ? "text-green-600" : "text-yellow-600"}
                        />
                        <StatCard
                            title="系统质量数"
                            value={formatNumber(stats.sqn)}
                            tooltip="SQN =（每笔交易的平均盈亏 * 交易次数的平方根）/ 盈亏标准差；3.0 到 5.0 的分数被认为是优秀的，而低于 1.6 的分数则是较差的"
                            color={stats.sqn >= 2 ? "text-green-600" : "text-yellow-600"}
                        />
                    </div>

                    <Collapsible.Root>
                        <Collapsible.Trigger asChild>
                            <button className="flex items-center text-blue-600 hover:text-blue-800 font-medium transition-colors duration-200">
                                <span>查看高级指标</span>
                                <svg className="ml-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                </svg>
                            </button>
                        </Collapsible.Trigger>
                        <Collapsible.Content className="mt-6">
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                <StatCard
                                    title="索提诺比率"
                                    value={formatNumber(stats.sortino_ratio)}
                                    color="text-indigo-600"
                                    tooltip="衡量每单位下行风险所获得的超额回报，与夏普比率类似，但只考虑下行波动率。"
                                    calculation="索提诺比率 = (年化收益率 - 无风险利率) / 下行标准差"
                                />
                                <StatCard
                                    title="卡玛比率"
                                    value={formatNumber(stats.calmar_ratio)}
                                    color="text-purple-600"
                                    tooltip="衡量策略收益与最大回撤之间的关系，反映策略承受最大回撤风险的能力。"
                                    calculation="卡玛比率 = 年化收益率 / 最大回撤率"
                                />
                                <StatCard
                                    title="阿尔法"
                                    value={formatPercent(stats.alpha_pct)}
                                    color={stats.alpha_pct >= 0 ? "text-green-600" : "text-red-600"}
                                    tooltip="策略相对于基准的超额收益率，正值表示策略表现优于基准。"
                                    calculation="阿尔法 = 策略年化收益率 - 基准年化收益率"
                                />
                                <StatCard
                                    title="贝塔"
                                    value={formatNumber(stats.beta)}
                                    color="text-blue-600"
                                    tooltip="衡量策略相对于市场的波动性，贝塔为1表示与市场波动相同，小于1表示波动小于市场。"
                                    calculation="贝塔 = 策略收益率与基准收益率的相关系数 × (策略标准差 / 基准标准差)"
                                />
                                <StatCard
                                    title="复合年增长率"
                                    value={formatPercent(stats.cagr_pct)}
                                    color={stats.cagr_pct >= 0 ? "text-green-600" : "text-red-600"}
                                    tooltip="考虑复利效应的年化增长率，反映长期投资的平均年收益率。"
                                    calculation="CAGR = (最终价值 / 初始价值)^(1/年数) - 1"
                                />
                                <StatCard
                                    title="年化波动率"
                                    value={formatPercent(stats.volatility_ann_pct)}
                                    color="text-yellow-600"
                                    tooltip="衡量策略收益率的波动程度，反映策略的风险水平。"
                                    calculation="年化波动率 = 日收益率标准差 × √252"
                                />
                                <StatCard
                                    title="平均回撤"
                                    value={formatPercent(stats.avg_drawdown_pct)}
                                    color="text-orange-600"
                                    tooltip="所有回撤期间的平均回撤幅度，反映策略的典型风险水平。"
                                    calculation="平均回撤 = 所有回撤期间回撤率的平均值"
                                />
                                <StatCard
                                    title="最大回撤持续时间"
                                    value={formatDuration(stats.max_drawdown_duration)}
                                    color="text-red-500"
                                    tooltip="从峰值到恢复所经历的最长时间，反映策略的恢复能力。"
                                    calculation="最大回撤持续时间 = 从峰值到恢复所经历的时间"
                                />
                                <StatCard
                                    title="平均回撤持续时间"
                                    value={formatDuration(stats.avg_drawdown_duration)}
                                    color="text-orange-500"
                                    tooltip="所有回撤期间的平均持续时间，反映策略从回撤中恢复的典型时间。"
                                    calculation="平均回撤持续时间 = 所有回撤期间持续时间的平均值"
                                />
                                <StatCard
                                    title="最佳交易收益率"
                                    value={formatPercent(stats.best_trade_pct)}
                                    color="text-green-600"
                                    tooltip="所有交易中最高的单笔收益率，反映策略的最佳表现。"
                                    calculation="最佳交易收益率 = max(所有交易的收益率)"
                                />
                                <StatCard
                                    title="最差交易收益率"
                                    value={formatPercent(stats.worst_trade_pct)}
                                    color="text-red-600"
                                    tooltip="所有交易中最低的单笔收益率，反映策略的最差表现。"
                                    calculation="最差交易收益率 = min(所有交易的收益率)"
                                />
                                <StatCard
                                    title="平均交易收益率"
                                    value={formatPercent(stats.avg_trade_pct)}
                                    color={stats.avg_trade_pct >= 0 ? "text-green-600" : "text-red-600"}
                                    tooltip="所有交易收益率的算术平均值，反映策略的典型交易表现。"
                                    calculation="平均交易收益率 = 所有交易收益率的平均值"
                                />
                                <StatCard
                                    title="最长持仓时间"
                                    value={formatDuration(stats.max_trade_duration)}
                                    color="text-blue-600"
                                    tooltip="所有交易中最长的持仓时间，反映策略的典型持仓周期上限。"
                                    calculation="最长持仓时间 = max(所有交易的持仓时间)"
                                />
                                <StatCard
                                    title="平均持仓时间"
                                    value={formatDuration(stats.avg_trade_duration)}
                                    color="text-indigo-600"
                                    tooltip="所有交易持仓时间的算术平均值，反映策略的典型持仓周期。"
                                    calculation="平均持仓时间 = 所有交易持仓时间的平均值"
                                />
                                <StatCard
                                    title="期望收益率"
                                    value={formatPercent(stats.expectancy_pct)}
                                    color={stats.expectancy_pct >= 0 ? "text-green-600" : "text-red-600"}
                                    tooltip="每笔交易的预期收益率，结合胜率和盈亏比的综合指标。"
                                    calculation="期望收益率 = 胜率 × 平均盈利收益率 + (1-胜率) × 平均亏损收益率"
                                />
                                <StatCard
                                    title="凯利准则"
                                    value={stats.kelly_criterion ? formatPercent(stats.kelly_criterion) : 'N/A'}
                                    color="text-purple-600"
                                    tooltip="在长期增长最大化的前提下，建议的单笔交易仓位比例。"
                                    calculation="凯利准则 = (胜率 × 平均盈利 - (1-胜率) × 平均亏损) / 平均盈利"
                                />
                                <StatCard
                                    title="持仓时间占比"
                                    value={formatPercent(stats.exposure_time_pct)}
                                    color="text-blue-600"
                                    tooltip="策略处于持仓状态的时间占总时间的比例，反映资金利用效率。"
                                    calculation="持仓时间占比 = 持仓时间总和 / 总回测时间 × 100%"
                                />
                            </div>
                        </Collapsible.Content>
                    </Collapsible.Root>
                </Tabs.Content>

                {/* 交易记录标签页 */}
                <Tabs.Content value="trades" className="p-8">
                    <TradesTable trades={stats.trades} />
                </Tabs.Content>

                {/* 权益曲线标签页 */}
                <Tabs.Content value="equity" className="p-8">
                    <Card className="rounded-xl shadow-sm border border-gray-200">
                        <CardContent className="p-6">
                            <div className="h-96">
                                <ResponsiveContainer width="100%" height="100%">
                                    <LineChart data={chartData}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                                        <XAxis dataKey="timestamp" stroke="#6b7280" />
                                        <YAxis yAxisId="left" stroke="#3b82f6" />
                                        <YAxis yAxisId="right" orientation="right" stroke="#ef4444" />
                                        <Tooltip
                                            formatter={(value, name) => {
                                                if (name === 'equity') return [formatCurrency(Number(value)), '账户权益'];
                                                if (name === 'drawdown_pct') return [formatPercent(Number(value)), '回撤率'];
                                                return [value, name];
                                            }}
                                            contentStyle={{
                                                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                                                border: '1px solid #e5e7eb',
                                                borderRadius: '0.5rem',
                                                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
                                            }}
                                        />
                                        <Legend />
                                        <Line
                                            yAxisId="left"
                                            type="monotone"
                                            dataKey="equity"
                                            name="账户权益"
                                            stroke="#3b82f6"
                                            strokeWidth={3}
                                            dot={false}
                                            activeDot={{ r: 6 }}
                                        />
                                        <Line
                                            yAxisId="right"
                                            type="monotone"
                                            dataKey="drawdown_pct"
                                            name="回撤率"
                                            stroke="#ef4444"
                                            strokeWidth={2}
                                            dot={false}
                                            activeDot={{ r: 6 }}
                                        />
                                    </LineChart>
                                </ResponsiveContainer>
                            </div>
                        </CardContent>
                    </Card>
                </Tabs.Content>

                {/* 价格走势与交易信号标签页 */}
                <Tabs.Content value="kline" className="p-8">
                    <div className="grid lg:grid-cols-3 gap-8">
                        {/* Chart Section */}
                        <div className="lg:col-span-2">
                            <StockChart
                                data={charts}
                                backtestStats={stats}
                                selectedPeriod={selectedPeriod}
                                onPeriodChange={setSelectedPeriod}
                            />
                        </div>
                    </div>
                </Tabs.Content>

                {/* 策略详情标签页 */}
                <Tabs.Content value="strategy" className="p-8">
                    <StrategyParams strategy={stats.strategy} />
                </Tabs.Content>
            </Tabs.Root>
        </div>
    );
};

export default BacktestPanel;