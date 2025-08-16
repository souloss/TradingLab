from functools import wraps

import requests


def get_proxy():
    """获取代理"""
    # 隧道域名:端口号
    tunnel = "t244.kdltpspro.com:15818"

    # 用户名密码方式
    username = "t15437111925845"
    password = "fqyhl83x"
    proxies = {
        "http": "http://%(user)s:%(pwd)s@%(proxy)s/"
        % {"user": username, "pwd": password, "proxy": tunnel},
        "https": "http://%(user)s:%(pwd)s@%(proxy)s/"
        % {"user": username, "pwd": password, "proxy": tunnel},
    }

    return proxies


# 在调用QuickProxy()前添加验证
def is_proxy_valid(proxy):
    """验证代理是否可用"""
    try:
        test_url = "http://www.baidu.com"
        response = requests.get(test_url, proxies=proxy, timeout=5)
        return response.status_code == 200
    except:
        return False


class RequestsGlobalProxy:
    """为 requests 库提供全局代理支持的猴子补丁管理器"""

    _instance = None
    _proxies = None
    _get_proxies_func = None
    _original_methods = {}
    _patched = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def set_global_proxies(self, proxies):
        """设置全局代理配置"""
        self._proxies = proxies
        if not self._patched:
            self._apply_monkey_patch()

    def set_global_get_proxies_function(self, get_proxies):
        """设置全局代理配置"""
        self._get_proxies_func = get_proxies
        if not self._patched:
            self._apply_monkey_patch()

    def clear_global_proxies(self):
        """清除全局代理设置"""
        self._proxies = None

    def restore_original(self):
        """恢复原始 requests 实现"""
        if self._patched:
            # 恢复 Session 方法
            requests.Session.request = self._original_methods.get("Session.request")
            requests.Session.send = self._original_methods.get("Session.send")

            # 恢复顶级方法
            for method in ["get", "post", "put", "delete", "head", "patch", "options"]:
                setattr(requests, method, self._original_methods.get(f"top_{method}"))

            self._patched = False
            self._proxies = None

    def _apply_monkey_patch(self):
        """应用猴子补丁到所有 requests 请求方法"""
        if self._patched:
            return

        # 1. 修补 Session 的核心方法
        self._original_methods["Session.request"] = requests.Session.request
        self._original_methods["Session.send"] = requests.Session.send

        @wraps(requests.Session.request)
        def patched_session_request(session, method, url, **kwargs):
            return self._apply_proxy(
                self._original_methods["Session.request"],
                session,
                method,
                url,
                **kwargs,
            )

        @wraps(requests.Session.send)
        def patched_session_send(session, request, **kwargs):
            return self._apply_proxy(
                self._original_methods["Session.send"], session, request, **kwargs
            )

        requests.Session.request = patched_session_request
        requests.Session.send = patched_session_send

        # 2. 修复闭包问题：为每个方法创建独立闭包
        for method in ["get", "post", "put", "delete", "head", "patch", "options"]:
            original = getattr(requests, method)
            self._original_methods[f"top_{method}"] = original

            # 使用工厂函数捕获当前循环变量
            def create_wrapper(orig_func):
                @wraps(orig_func)
                def wrapper(*args, **kwargs):
                    return self._apply_proxy(orig_func, *args, **kwargs)

                return wrapper

            setattr(requests, method, create_wrapper(original))

        self._patched = True

    def _apply_proxy(self, original_func, *args, **kwargs):
        """应用代理设置的通用逻辑（修复参数传递）"""
        # 如果已设置代理或明确不使用代理，则直接调用原始方法
        if "proxies" in kwargs:
            return original_func(*args, **kwargs)

        # 如果全局代理已设置且未显式覆盖，则注入代理
        if self._proxies is not None:
            kwargs["proxies"] = self._proxies
        elif self._get_proxies_func is not None:
            kwargs["proxies"] = self._get_proxies_func()

        return original_func(*args, **kwargs)


if __name__ == "__main__":
    # 创建代理管理器实例
    proxy_manager = RequestsGlobalProxy()
    # 设置代理
    proxies = get_proxy()
    print(f"代理设置为:\n {proxies}")
    response = requests.get("https://httpbin.org/ip", proxies=proxies)
    print("直接使用代理请求成功，返回IP信息:", response.json())

    proxy_manager.set_global_get_proxies_function(get_proxies=get_proxy)
    # 现在所有 requests 请求都会自动使用代理
    # 包括 akshare 库内部使用的 requests
    print("测试 requests.get 是否使用代理...")
    try:
        # 测试请求
        response = requests.get("https://httpbin.org/ip")
        print("请求成功，返回IP信息:", response.json())
    except Exception as e:
        print(f"请求失败: {str(e)}")
        print("请检查代理设置是否正确")

    # 清除代理设置
    print("\n清除代理设置...")
    proxy_manager.clear_global_proxies()

    # 测试是否已清除代理
    print("测试清除代理后的请求...")
    try:
        response = requests.get("https://httpbin.org/ip")
        print("请求成功，返回IP信息:", response.json())
    except Exception as e:
        print(f"请求失败: {str(e)}")

    # 恢复原始 requests 实现
    print("\n恢复原始 requests 实现...")
    proxy_manager.restore_original()

    # 最终测试
    print("测试恢复后的请求...")
    try:
        response = requests.get("https://httpbin.org/ip")
        print("请求成功，返回IP信息:", response.json())
    except Exception as e:
        print(f"请求失败: {str(e)}")
