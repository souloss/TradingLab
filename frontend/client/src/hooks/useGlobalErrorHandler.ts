import { useEffect } from "react";
import { toast } from "@/hooks/use-toast";

export function useGlobalErrorHandler() {
    useEffect(() => {
        // 运行时错误
        const handleError = (event: ErrorEvent) => {
            toast({
                title: "运行时错误",
                description: event.message,
                variant: "destructive",
            });
        };

        // Promise 错误
        const handleRejection = (event: PromiseRejectionEvent) => {
            let message: string;

            if (event.reason instanceof Error) {
                message = event.reason.message;
            } else {
                message = String(event.reason);
            }

            // 🚨 处理网络错误 / 服务器挂掉
            if (message.includes("Failed to fetch") || message.includes("NetworkError")) {
                message = "无法连接服务器，请检查网络或稍后再试";
            }

            // 🚨 处理常见状态码错误（你可以根据后端返回格式调整）
            if (message.includes("401")) {
                message = "未登录或登录已过期，请重新登录";
            } else if (message.includes("500")) {
                message = "服务器内部错误，请稍后再试";
            }

            // 针对服务挂掉/返回HTML的情况进一步兜底
            if (message.includes("<!DOCTYPE") || message.includes("Unexpected token")) {
                message = "服务器可能已停止运行，返回了错误的响应。";
            }

            toast({
                title: "请求失败",
                description: message,
                variant: "destructive",
            });
        };

        window.addEventListener("error", handleError);
        window.addEventListener("unhandledrejection", handleRejection);

        return () => {
            window.removeEventListener("error", handleError);
            window.removeEventListener("unhandledrejection", handleRejection);
        };
    }, []);
}
