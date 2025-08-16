"use client";

import * as React from "react";
import { DateRange } from "react-day-picker";
import { addYears } from "date-fns";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverTrigger, PopoverContent } from "@/components/ui/popover";
import { Button } from "@/components/ui/button";
import { CalendarIcon } from "lucide-react";
import { format } from "date-fns";
import { cn } from "@/lib/utils";

interface DatePickerWithRangeProps {
    value: DateRange;
    onChange: (range: DateRange) => void;
}

export function DatePickerWithRange({ value, onChange }: DatePickerWithRangeProps) {
    return (
        <Popover>
            <PopoverTrigger asChild>
                <Button
                    id="date"
                    variant={"outline"}
                    className={cn(
                        "w-[300px] justify-start text-left font-normal",
                        !value && "text-muted-foreground"
                    )}
                >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {value?.from ? (
                        value.to ? (
                            <>
                                {format(value.from, "yyyy-MM-dd")} - {format(value.to, "yyyy-MM-dd")}
                            </>
                        ) : (
                            format(value.from, "yyyy-MM-dd")
                        )
                    ) : (
                        <span>选择日期范围</span>
                    )}
                </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0" align="start">
                <Calendar
                    initialFocus
                    mode="range"
                    defaultMonth={value?.from}
                    selected={value}
                    onSelect={onChange}
                    numberOfMonths={2}
                />
            </PopoverContent>
        </Popover>
    );
}