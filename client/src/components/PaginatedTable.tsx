import * as React from "react";
import {
    Table,
    TableBody,
    TableCaption,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import {
    Select,
    SelectTrigger,
    SelectContent,
    SelectItem,
    SelectValue,
} from "@/components/ui/select";
import {
    ChevronsLeft,
    ChevronsRight,
    ChevronLeft,
    ChevronRight,
    ArrowUpDown,
    ChevronUp,
    ChevronDown,
} from "lucide-react";
import clsx from "clsx";

type SortDirection = "asc" | "desc";
type Mode = "client" | "server";

export interface Column<T> {
    /** 列唯一 id（用于排序状态） */
    id: string;
    /** 表头显示 */
    header: React.ReactNode;
    /** 取值器（默认用 id 去 row[id]，你也可传函数） */
    accessor?: keyof T | ((row: T) => unknown);
    /** 自定义单元格渲染（优先于 accessor 的显示） */
    cell?: (row: T, rowIndex: number) => React.ReactNode;
    /** 是否可排序 */
    sortable?: boolean;
    /** 自定义比较器（本地排序时用） */
    sortFn?: (a: T, b: T) => number;
    /** 额外的单元格类名 */
    className?: string;
    /** 表头类名 */
    headerClassName?: string;
    /** 对齐：left/center/right */
    align?: "left" | "center" | "right";
    /** 固定宽度/最小宽度等 */
    width?: string;
}

export interface PaginatedTableProps<T> {
    columns: Column<T>[];
    data: T[];

    /** 模式：client 本地分页与排序；server 受控分页/排序、外部请求 */
    mode?: Mode;

    /** 受控分页 */
    page?: number;
    onPageChange?: (page: number) => void;

    /** 受控每页条数 */
    pageSize?: number;
    onPageSizeChange?: (size: number) => void;

    /** 服务端模式下，用于计算页数 */
    totalItems?: number;

    /** 初始（非受控）排序 */
    initialSort?: { id: string; direction: SortDirection };

    /** 受控排序 */
    sort?: { id: string; direction: SortDirection };
    onSortChange?: (s: { id: string; direction: SortDirection }) => void;

    /** 表格标题、空态、行 Key 等 */
    caption?: React.ReactNode;
    emptyMessage?: React.ReactNode;
    rowKey?: (row: T, index: number) => string | number;

    /** 外层类名 */
    className?: string;

    /** 可选的 pageSize 列表 */
    pageSizeOptions?: number[];

    /** 表格是否紧凑 */
    dense?: boolean;
}

/** 默认比较：数字/日期优先，否则字符串比较 */
function defaultCompare(a: unknown, b: unknown): number {
    // 处理 undefined / null
    if (a == null && b == null) return 0;
    if (a == null) return -1;
    if (b == null) return 1;

    // Date
    if (a instanceof Date || b instanceof Date) {
        const av = a instanceof Date ? a.getTime() : new Date(String(a)).getTime();
        const bv = b instanceof Date ? b.getTime() : new Date(String(b)).getTime();
        return av - bv;
    }

    // number-like
    const an = typeof a === "number" ? a : Number(a);
    const bn = typeof b === "number" ? b : Number(b);
    if (!Number.isNaN(an) && !Number.isNaN(bn)) {
        return an - bn;
    }

    // fallback to string
    const as = String(a);
    const bs = String(b);
    return as.localeCompare(bs, "zh-CN", { numeric: true, sensitivity: "base" });
}

function getValue<T>(row: T, col: Column<T>): unknown {
    if (typeof col.accessor === "function") return col.accessor(row);
    if (typeof col.accessor === "string") return (row as any)[col.accessor];
    // 默认用 id 作为 key 取值
    return (row as any)[col.id];
}

export function PaginatedTable<T>({
    columns,
    data,
    mode = "client",
    page: controlledPage,
    onPageChange,
    pageSize: controlledPageSize,
    onPageSizeChange,
    totalItems,
    initialSort,
    sort: controlledSort,
    onSortChange,
    caption,
    emptyMessage = "暂无数据",
    rowKey,
    className,
    pageSizeOptions = [10, 20, 50, 100],
    dense = false,
}: PaginatedTableProps<T>) {
    // ---- 排序状态（受控 / 非受控）----
    const [internalSort, setInternalSort] = React.useState<{ id: string; direction: SortDirection } | null>(
        initialSort ?? null
    );
    const sortState = controlledSort ?? internalSort;

    // ---- 分页状态（受控 / 非受控）----
    const [internalPage, setInternalPage] = React.useState(1);
    const [internalPageSize, setInternalPageSize] = React.useState(pageSizeOptions[0] ?? 10);

    const page = controlledPage ?? internalPage;
    const pageSize = controlledPageSize ?? internalPageSize;

    React.useEffect(() => {
        // 数据变化时，若当前页超出范围则回退
        const items = mode === "server" ? (totalItems ?? data.length) : data.length;
        const totalPages = Math.max(1, Math.ceil(items / pageSize));
        if (page > totalPages) {
            handlePageChange(totalPages);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [data, totalItems, pageSize]);

    function handleSortClick(col: Column<T>) {
        if (!col.sortable) return;
        let next: SortDirection = "asc";
        if (sortState?.id === col.id && sortState.direction === "asc") {
            next = "desc";
        }
        const nextSort = { id: col.id, direction: next };
        if (onSortChange) onSortChange(nextSort);
        else setInternalSort(nextSort);
    }

    function handlePageChange(next: number) {
        if (onPageChange) onPageChange(next);
        else setInternalPage(next);
    }

    function handlePageSizeChange(nextSize: number) {
        if (onPageSizeChange) onPageSizeChange(nextSize);
        else {
            setInternalPageSize(nextSize);
            setInternalPage(1);
        }
    }

    // ---- 本地排序 ----
    const sortedData = React.useMemo(() => {
        if (mode === "server" || !sortState) return data;
        const col = columns.find((c) => c.id === sortState.id);
        if (!col || !col.sortable) return data;
        const cmp =
            col.sortFn ||
            ((ra: T, rb: T) => {
                const va = getValue(ra, col);
                const vb = getValue(rb, col);
                return defaultCompare(va, vb);
            });

        const arr = [...data].sort((a, b) => {
            const s = cmp(a, b);
            return sortState.direction === "asc" ? s : -s;
        });
        return arr;
    }, [mode, data, sortState, columns]);

    // ---- 分页切片（客户端模式）----
    const total = mode === "server" ? (totalItems ?? data.length) : sortedData.length;
    const totalPages = Math.max(1, Math.ceil(total / pageSize));
    const pagedData =
        mode === "server"
            ? data
            : sortedData.slice((page - 1) * pageSize, (page - 1) * pageSize + pageSize);

    const from = total === 0 ? 0 : (page - 1) * pageSize + 1;
    const to = total === 0 ? 0 : Math.min(page * pageSize, total);

    return (
        <div className={clsx("space-y-3", className)}>
            {/* 顶部工具条：pageSize 选择 + 排序提示 */}
            <div className="flex items-center justify-between">
                <div className="text-sm text-muted-foreground">{caption}</div>
                <div className="flex items-center gap-2">
                    <span className="text-sm text-muted-foreground">每页</span>
                    <Select
                        value={String(pageSize)}
                        onValueChange={(v) => handlePageSizeChange(Number(v))}
                    >
                        <SelectTrigger className="h-8 w-[90px]">
                            <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                            {pageSizeOptions.map((s) => (
                                <SelectItem key={s} value={String(s)}>
                                    {s}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                </div>
            </div>

            {/* 表格 */}
            <div className="overflow-x-auto rounded-md border">
                <Table className={clsx(dense && "text-sm")}>
                    {/* 这里不使用 TableCaption 占位，避免布局跳动；如需可放到外部 caption */}
                    <TableHeader>
                        <TableRow>
                            {columns.map((col) => {
                                const isSorted = sortState?.id === col.id;
                                const ariaSort = isSorted ? (sortState!.direction === "asc" ? "ascending" : "descending") : "none";
                                return (
                                    <TableHead
                                        key={col.id}
                                        style={col.width ? { width: col.width } : undefined}
                                        className={clsx(
                                            col.headerClassName,
                                            col.align === "center" && "text-center",
                                            col.align === "right" && "text-right",
                                            col.sortable && "cursor-pointer select-none"
                                        )}
                                        aria-sort={ariaSort}
                                        onClick={() => handleSortClick(col)}
                                    >
                                        <div className="inline-flex items-center gap-1">
                                            {col.header}
                                            {col.sortable && !isSorted && <ArrowUpDown className="h-3.5 w-3.5 opacity-60" />}
                                            {col.sortable && isSorted && sortState!.direction === "asc" && (
                                                <ChevronUp className="h-3.5 w-3.5" />
                                            )}
                                            {col.sortable && isSorted && sortState!.direction === "desc" && (
                                                <ChevronDown className="h-3.5 w-3.5" />
                                            )}
                                        </div>
                                    </TableHead>
                                );
                            })}
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {pagedData.length === 0 && (
                            <TableRow>
                                <TableCell colSpan={columns.length} className="h-24 text-center text-muted-foreground">
                                    {emptyMessage}
                                </TableCell>
                            </TableRow>
                        )}
                        {pagedData.map((row, rowIndex) => {
                            const key = rowKey ? rowKey(row, rowIndex) : rowIndex;
                            return (
                                <TableRow key={key}>
                                    {columns.map((col) => (
                                        <TableCell
                                            key={col.id}
                                            className={clsx(
                                                col.className,
                                                col.align === "center" && "text-center",
                                                col.align === "right" && "text-right"
                                            )}
                                        >
                                            {col.cell ? col.cell(row, rowIndex) : (() => {
                                                const v = getValue(row, col);
                                                return v as any as React.ReactNode;
                                            })()}
                                        </TableCell>
                                    ))}
                                </TableRow>
                            );
                        })}
                    </TableBody>
                </Table>
            </div>

            {/* 分页条 */}
            <div className="flex items-center justify-between">
                <div className="text-sm text-muted-foreground">
                    第 <span className="font-medium">{from}</span>–<span className="font-medium">{to}</span> 条，共{" "}
                    <span className="font-medium">{total}</span> 条
                </div>
                <div className="flex items-center gap-2">
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handlePageChange(1)}
                        disabled={page <= 1}
                    >
                        <ChevronsLeft className="h-4 w-4" />
                    </Button>
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handlePageChange(Math.max(1, page - 1))}
                        disabled={page <= 1}
                    >
                        <ChevronLeft className="h-4 w-4" />
                    </Button>
                    <div className="min-w-[60px] text-center text-sm">
                        {page} / {totalPages}
                    </div>
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handlePageChange(Math.min(totalPages, page + 1))}
                        disabled={page >= totalPages}
                    >
                        <ChevronRight className="h-4 w-4" />
                    </Button>
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handlePageChange(totalPages)}
                        disabled={page >= totalPages}
                    >
                        <ChevronsRight className="h-4 w-4" />
                    </Button>
                </div>
            </div>
        </div>
    );
}