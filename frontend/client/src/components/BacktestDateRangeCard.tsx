"use client";

import * as React from "react";
import { zhCN } from "date-fns/locale";
import { format } from "date-fns";
import { Calendar as CalendarIcon } from "lucide-react";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Popover, PopoverTrigger, PopoverContent } from "@/components/ui/popover";
import { Calendar } from "@/components/ui/calendar";
import { cn } from "@/lib/utils";

interface BacktestDateRangeCardProps {
    startDate: Date;
    endDate: Date;
    onChange: (range: { startDate: Date; endDate: Date }) => void;
}

export function BacktestDateRangeCard({
    startDate,
    endDate,
    onChange,
}: BacktestDateRangeCardProps) {
    const [start, setStart] = React.useState<Date>(startDate);
    const [end, setEnd] = React.useState<Date>(endDate);

    const handleStartChange = (date: Date | undefined) => {
        if (!date) return;
        setStart(date);
        onChange({ startDate: date, endDate: end });
    };

    const handleEndChange = (date: Date | undefined) => {
        if (!date) return;
        setEnd(date);
        onChange({ startDate: start, endDate: date });
    };

    return (
        <Card>
            <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                    <i className="fas fa-calendar-alt text-primary"></i>
                    <span>回测时间范围</span>
                </CardTitle>
                <p className="text-muted-foreground">选择回测的开始与结束日期</p>
            </CardHeader>
            <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* 开始时间 */}
                    <Popover>
                        <PopoverTrigger asChild>
                            <div className="relative">
                                <Input
                                    readOnly
                                    value={start ? format(start, "yyyy-MM-dd") : ""}
                                    className="pl-10 cursor-pointer"
                                />
                                <CalendarIcon className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                            </div>
                        </PopoverTrigger>
                        <PopoverContent align="start" className="p-0">
                            <Calendar
                                mode="single"
                                selected={start}
                                onSelect={handleStartChange}
                                locale={zhCN}
                            />
                        </PopoverContent>
                    </Popover>

                    {/* 结束时间 */}
                    <Popover>
                        <PopoverTrigger asChild>
                            <div className="relative">
                                <Input
                                    readOnly
                                    value={end ? format(end, "yyyy-MM-dd") : ""}
                                    className="pl-10 cursor-pointer"
                                />
                                <CalendarIcon className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                            </div>
                        </PopoverTrigger>
                        <PopoverContent align="start" className="p-0">
                            <Calendar
                                mode="single"
                                selected={end}
                                onSelect={handleEndChange}
                                locale={zhCN}
                            />
                        </PopoverContent>
                    </Popover>
                </div>
            </CardContent>
        </Card>
    );
}