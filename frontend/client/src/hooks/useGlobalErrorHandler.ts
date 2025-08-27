import { useEffect, useCallback } from "react";
import { toast } from "@/hooks/use-toast";

/**
 * 全局错误统一处理器
 * 1. 捕获运行时错误（error）与未捕获的 Promise 错误（unhandledrejection）
 * 2. 支持「错误码映射」「白名单过滤」「日志上报」「自定义回调」
 * 3. 所有新增能力均通过 options 配置，保持高可扩展性
 */
export function useGlobalErrorHandler(options?: ErrorHandlerOptions) {
    /* ================== 默认配置 ================== */
    const {
        // 是否把错误上报到远程（默认 false）
        enableReporting = false,
        // 远程上报地址
        reportUrl = "/api/clientError",
        // 白名单：命中后静默处理，不再弹 Toast
        whiteList = [],
        // 自定义错误码映射表
        errorMap = defaultErrorMap,
        // 钩子：在 Toast 之前执行，返回 false 可阻止后续 Toast
        beforeToast,
        // 钩子：在错误发生后执行，可做额外逻辑
        onError,
    } = options || {};

    /* ================== 工具函数 ================== */
    /** 判断是否在白名单内 */
    const isWhiteListed = (msg: string) =>
        whiteList.some((rule) =>
            typeof rule === "string"
                ? msg.includes(rule)
                : rule instanceof RegExp
                    ? rule.test(msg)
                    : false
        );

    /** 统一包装的错误上报 */
    const reportError = useCallback(
        (payload: ReportPayload) => {
            if (!enableReporting) return;
            fetch(reportUrl, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ ...payload, ts: Date.now() }),
            }).catch(() => {
                /* 上报失败静默处理，避免二次死循环 */
            });
        },
        [enableReporting, reportUrl]
    );

    /** 生成统一错误对象 */
    const buildPayload = (type: ErrorType, message: string, error?: any) => ({
        type,
        message,
        stack: error?.stack,
        url: window.location.href,
        ua: navigator.userAgent,
    });

    /* ================== 错误处理器 ================== */
    /** 运行时 error 事件 */
    const handleError = useCallback(
        (event: ErrorEvent) => {
            const payload = buildPayload("runtime", event.message, event.error);
            if (isWhiteListed(payload.message)) return;

            // 自定义钩子
            if (beforeToast && beforeToast(payload) === false) return;
            onError?.(payload);

            // 根据映射表生成友好提示
            const toastMsg = mapErrorMsg(payload.message, errorMap);
            toast({
                title: "运行时错误",
                description: toastMsg,
                variant: "destructive",
            });

            // 日志上报
            reportError(payload);
        },
        [whiteList, errorMap, beforeToast, onError, reportError]
    );

    /** 未捕获的 Promise 错误 */
    const handleRejection = useCallback(
        (event: PromiseRejectionEvent) => {
            let message: string;
            let error = event.reason;

            if (error instanceof Error) {
                message = error.message;
            } else {
                message = String(error);
                error = new Error(message);
            }

            const payload = buildPayload("promise", message, error);
            if (isWhiteListed(payload.message)) return;

            if (beforeToast && beforeToast(payload) === false) return;
            onError?.(payload);

            const toastMsg = mapErrorMsg(payload.message, errorMap);
            toast({
                title: "网络/逻辑错误",
                description: toastMsg,
                variant: "destructive",
            });

            reportError(payload);
        },
        [whiteList, errorMap, beforeToast, onError, reportError]
    );

    /* ================== 注册 & 卸载 ================== */
    useEffect(() => {
        window.addEventListener("error", handleError);
        window.addEventListener("unhandledrejection", handleRejection);

        return () => {
            window.removeEventListener("error", handleError);
            window.removeEventListener("unhandledrejection", handleRejection);
        };
    }, [handleError, handleRejection]);
}

/* ================== 类型定义 ================== */
type ErrorType = "runtime" | "promise";

interface ReportPayload {
    type: ErrorType;
    message: string;
    stack?: string;
    url: string;
    ua: string;
    ts?: number;
}

interface ErrorHandlerOptions {
    enableReporting?: boolean;
    reportUrl?: string;
    whiteList?: (string | RegExp)[];
    errorMap?: Record<string, string>;
    beforeToast?: (payload: ReportPayload) => boolean | void;
    onError?: (payload: ReportPayload) => void;
}

/* ================== 默认错误映射 ================== */
const defaultErrorMap: Record<string, string> = {
    "Failed to fetch": "无法连接服务器，请检查网络或稍后再试",
    "NetworkError": "无法连接服务器，请检查网络或稍后再试",
    "401": "未登录或登录已过期，请重新登录",
    "500": "服务器内部错误，请稍后再试",
    "<!DOCTYPE": "服务器可能已停止运行，返回了错误的响应",
    "Unexpected token": "服务器可能已停止运行，返回了错误的响应",
};

/** 根据映射表 + 正则匹配转换错误信息 */
function mapErrorMsg(original: string, mapObj: Record<string, string>): string {
    for (const [key, value] of Object.entries(mapObj)) {
        if (original.includes(key)) return value;
    }
    return original;
}