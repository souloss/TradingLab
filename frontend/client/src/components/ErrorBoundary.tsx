import React from "react";
import { toast } from "@/hooks/use-toast";

interface Props {
    children: React.ReactNode;
    fallback?: React.ReactNode;
}

interface State {
    hasError: boolean;
}

class ErrorBoundary extends React.Component<Props, State> {
    constructor(props: Props) {
        super(props);
        this.state = { hasError: false };
    }

    static getDerivedStateFromError() {
        return { hasError: true };
    }

    componentDidCatch(error: Error) {
        console.error("渲染错误:", error);
        toast({
            title: "页面错误",
            description: error.message,
            variant: "destructive",
        });
    }

    render() {
        if (this.state.hasError) {
            return this.props.fallback ?? (
                <div className="flex flex-col items-center justify-center h-screen text-center">
                    <h1 className="text-2xl font-bold">出错了</h1>
                    <p className="text-muted-foreground mt-2">请刷新页面或稍后再试。</p>
                </div>
            );
        }
        return this.props.children;
    }
}

export default ErrorBoundary;