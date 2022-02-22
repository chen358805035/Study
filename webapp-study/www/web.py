#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "Michael Liao"

import asyncio, os, inspect, logging, functools

from urllib import parse

from aiohttp import web
from apis import APIError


def get(path):
    """
    定义修饰符 @get('/path')
    """

    def decorator(func):
        # @functools.wraps(func)的作用就是保留原有函数的名称和docstring
        @functools.wraps(func)
        def wrapper(*args, **kw):
            # print("args= %s, kw=%s,path = %s" % (args, kw, path))
            # print("%s %s():" % (text, func.__name__))
            return func(*args, **kw)

        wrapper.__method__ = "GET"
        wrapper.__route__ = path
        # print("wrapper =%s" % wrapper.__name__)
        return wrapper

    # print("decorator= %s" % decorator)
    return decorator


# @get("/aa/sd")
# def test():
#     print("123456")


# if __name__ == "__main__":
#     test()
#     print(test.__name__)
def post(path):
    """
    Define decorator @post('/path')
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)

        wrapper.__method__ = "POST"
        wrapper.__route__ = path
        return wrapper

    return decorator


# 定义函数传递参数为函数，然后取出参数进行判断
# 如果函数参数包含关键字参数并且关键字参数值为空则返回关键字参数的元组
def get_required_kw_args(fn):
    args = []
    # inspect.signature(fn).parameters获取函数参数的参数名，参数的属性，参数的默认值
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if (
            param.kind == inspect.Parameter.KEYWORD_ONLY
            and param.default == inspect.Parameter.empty
        ):
            args.append(name)
    return tuple(args)


# 如果有关键字参数则取出返回元组
def get_named_kw_args(fn):
    args = []
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            args.append(name)
    return tuple(args)


# 判断函数是否有关键字参数，如果有则返回True
def has_named_kw_args(fn):
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            return True


# 判断函数是否有字典参数，如果有则返回True
def has_var_kw_arg(fn):
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            return True


# 判断函数的参数有没有request，如果有request参数则把found赋值为True并结束本次循环继续判断其他参数
# 如果其他参数不是可变参数，也不是关键字参数，也不是字典参数则抛出错误
# 例如响应函数index(request)只有一个参数request所以在执行第一个if以后就没有参数循环了，退出整个循环返回found的值为True
def has_request_arg(fn):
    sig = inspect.signature(fn)
    params = sig.parameters
    found = False
    for name, param in params.items():
        if name == "request":
            found = True
            continue
        if found and (
            param.kind != inspect.Parameter.VAR_POSITIONAL
            and param.kind != inspect.Parameter.KEYWORD_ONLY
            and param.kind != inspect.Parameter.VAR_KEYWORD
        ):
            raise ValueError(
                "request parameter must be the last named parameter in function: %s%s"
                % (fn.__name__, str(sig))
            )
    return found


# 请求处理
class RequestHandler(object):
    def __init__(self, app, fn):
        self._app = app
        self._func = fn
        self._has_request_arg = has_request_arg(fn)
        self._has_var_kw_arg = has_var_kw_arg(fn)
        self._has_named_kw_args = has_named_kw_args(fn)
        self._named_kw_args = get_named_kw_args(fn)
        self._required_kw_args = get_required_kw_args(fn)

    async def __call__(self, request):
        kw = None
        # 如果字典参数或者有关键字参数或者有关键字参数并且关键字参数值为空则
        if self._has_var_kw_arg or self._has_named_kw_args or self._required_kw_args:
            # 判断是否为POST请求
            if request.method == "POST":
                # 如果请求中没有content_type将返回错误信息
                if not request.content_type:
                    return web.HTTPBadRequest("Missing Content-Type.")
                # 将content_type转换为小写
                ct = request.content_type.lower()
                # startswith() 方法用于检查字符串是否是以指定子字符串开头，如果是则返回 True，否则返回 False。如果参数 beg 和 end 指定值，则在指定范围内检查。
                # 判断是否以"application/json"开头
                if ct.startswith("application/json"):
                    ## 假设url:http://0.0.0.0:18082/api/cluster/group?wzd=111&abc=cc;方法类型：POST，body是{"name":"abc"}
                    # 当请求的Content-Type`` 是`application/json的时候，该方法返回的是body中的json串，如果body中不是json会抛出异常：ValueError: No JSON object could be decoded，对应本例，返回：{"name":"abc"}
                    params = await request.json()
                    # 如果参数不是字典类型将返回
                    if not isinstance(params, dict):
                        return web.HTTPBadRequest("JSON body must be object.")
                    kw = params
                # 如果以"application/x-www-form-urlencoded"字符或者"multipart/form-data"字符开头
                elif ct.startswith(
                    "application/x-www-form-urlencoded"
                ) or ct.startswith("multipart/form-data"):
                    #
                    params = await request.post()
                    print("params = %s" % params)
                    kw = dict(**params)
                else:
                    return web.HTTPBadRequest(
                        "Unsupported Content-Type: %s" % request.content_type
                    )
            if request.method == "GET":
                # 假设url:http://0.0.0.0:18082/api/cluster/group?wzd=111&abc=cc;方法类型：POST，body是{"name":"abc"}
                # 它得到的是，url中？后面所有的值，最为一个字符串，即：wzd=111&abc=cc
                qs = request.query_string
                if qs:
                    kw = dict()
                    for k, v in parse.parse_qs(qs, True).items():
                        kw[k] = v[0]
        if kw is None:
            # 创建字典
            kw = dict(**request.match_info)
        else:
            if not self._has_var_kw_arg and self._named_kw_args:
                # remove all unamed kw:
                copy = dict()
                for name in self._named_kw_args:
                    if name in kw:
                        copy[name] = kw[name]
                kw = copy
            # check named arg:
            for k, v in request.match_info.items():
                if k in kw:
                    logging.warning(
                        "Duplicate arg name in named arg and kw args: %s" % k
                    )
                kw[k] = v
        if self._has_request_arg:
            kw["request"] = request
        # check required kw:
        if self._required_kw_args:
            for name in self._required_kw_args:
                if not name in kw:
                    return web.HTTPBadRequest("Missing argument: %s" % name)
        logging.info("call with args: %s" % str(kw))
        try:
            r = await self._func(**kw)
            return r
        except APIError as e:
            return dict(error=e.error, data=e.data, message=e.message)


def add_static(app):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
    app.router.add_static("/static/", path)
    print("add static %s => %s" % ("/static/", path))
    logging.info("add static %s => %s" % ("/static/", path))


def add_route(app, fn):
    method = getattr(fn, "__method__", None)
    path = getattr(fn, "__route__", None)
    if path is None or method is None:
        raise ValueError("@get or @post not defined in %s." % str(fn))
    if not asyncio.iscoroutinefunction(fn) and not inspect.isgeneratorfunction(fn):
        fn = asyncio.coroutine(fn)
    logging.info(
        "add route %s %s => %s(%s)"
        % (
            method,
            path,
            fn.__name__,
            ", ".join(inspect.signature(fn).parameters.keys()),
        )
    )
    app.router.add_route(method, path, RequestHandler(app, fn))


def add_routes(app, module_name):
    n = module_name.rfind(".")
    if n == (-1):
        mod = __import__(module_name, globals(), locals())
    else:
        name = module_name[n + 1 :]
        mod = getattr(__import__(module_name[:n], globals(), locals(), [name]), name)
    for attr in dir(mod):
        if attr.startswith("_"):
            continue
        fn = getattr(mod, attr)
        if callable(fn):
            method = getattr(fn, "__method__", None)
            path = getattr(fn, "__route__", None)
            if method and path:
                add_route(app, fn)
