import { QueryClient, QueryFunction, QueryFunctionContext } from "@tanstack/react-query";
import { APIResponse } from "@/types";

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
  data?: unknown | undefined,
): Promise<T> {
  const fullUrl = `${API_BASE_URL}${url}`;
  
  const res = await fetch(fullUrl, {
    method,
    headers: data ? { "Content-Type": "application/json" } : {},
    body: data ? JSON.stringify(data) : undefined,
    credentials: "include",
  });
  console.log("00000000000000000000")
  await throwIfResNotOk(res);
  // 解析响应为 APIResponse 结构
  const response: APIResponse<T> = await res.json();
  console.log("11111111111111")
  // 检查响应状态码
  if (response.code !== 0) {
    throw new Error(response.message || `API request failed with code ${response.code}`);
  }
  console.log("22222222")
  // 返回解包后的数据
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
});