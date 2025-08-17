import { QueryClient, QueryFunction, QueryFunctionContext, QueryCache, MutationCache } from "@tanstack/react-query";
import { APIResponse } from "@/types";
import { toast } from "@/hooks/use-toast";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

async function throwIfResNotOk(res: Response) {
  if (!res.ok) {
    const text = (await res.text()) || res.statusText;
    throw new Error(`${res.status}: ${text}`);
  }
}

export async function apiRequest<T = any>(
  method: string,
  url: string,
  data?: unknown,
): Promise<T> {
  const fullUrl = `${API_BASE_URL}${url}`;

  const res = await fetch(fullUrl, {
    method,
    headers: data ? { "Content-Type": "application/json" } : {},
    body: data ? JSON.stringify(data) : undefined,
    credentials: "include",
  });

  // HTTP 层检查
  await throwIfResNotOk(res);

  // Content-Type 检查
  const contentType = res.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) {
    const text = await res.text(); // 兜底看一眼
    throw new Error(
      `期望 JSON 响应，但收到: ${contentType || "unknown"}\n内容预览: ${text.slice(0, 100)}`,
    );
  }

  let response: APIResponse<T>;
  try {
    response = (await res.json()) as APIResponse<T>;
  } catch (e) {
    throw new Error("响应内容不是合法的 JSON");
  }

  // 业务层检查
  if (response.code !== 0) {
    throw new Error(response.message || `API request failed with code ${response.code}`);
  }

  return response.data as T;
}

type UnauthorizedBehavior = "returnNull" | "throw";


// 修复 getQueryFn 的类型定义
export const getQueryFn: <T>(options: {
  on401: UnauthorizedBehavior;
}) => QueryFunction<T> =
  <T>({ on401: unauthorizedBehavior }: { on401: UnauthorizedBehavior }) =>
    async ({ queryKey }: QueryFunctionContext) => {
      const res = await fetch(queryKey.join("/") as string, {
        credentials: "include",
      });

      if (unauthorizedBehavior === "returnNull" && res.status === 401) {
        return null as unknown as T; // 使用类型断言解决类型不匹配
      }

      await throwIfResNotOk(res);

      // 解析响应为 APIResponse 结构
      const response: APIResponse<T> = await res.json();

      // 检查响应状态码
      if (response.code !== 200) {
        throw new Error(response.message || `API request failed with code ${response.code}`);
      }

      // 返回解包后的数据
      return response.data as T;
    };


export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      queryFn: getQueryFn({ on401: "throw" }),
      refetchInterval: false,
      refetchOnWindowFocus: false,
      staleTime: Infinity,
      retry: false,
    },
    mutations: {
      retry: false,
    },
  },
  queryCache: new QueryCache({
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : "未知错误";
      toast({
        title: "请求失败",
        description: message,
        variant: "destructive",
      });
    },
  }),
  mutationCache: new MutationCache({
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : "未知错误";
      toast({
        title: "操作失败",
        description: message,
        variant: "destructive",
      });
    },
  }),
});