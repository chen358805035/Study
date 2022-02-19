#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging, aiomysql, asyncio


def log(sql, args=()):
    logging.info("SQL: %s" % sql)


# *args用于接受传入的值，无限制，但是不能接收key类型的，如c=2
# **kwargs可以接收key类型的，:
# 创建内存池
async def create_pool(loop, **kw):
    logging.info("create database connection pool...")
    # 全局变量
    global __pool
    __pool = await aiomysql.create_pool(
        # 若kw中没有host则使用localhost
        host=kw.get("host", "localhost"),
        port=kw.get("port", 3306),
        user=kw["user"],
        password=kw["password"],
        db=kw["db"],
        charset=kw.get("charset", "utf8"),
        autocommit=kw.get("autocommit", True),
        # 默认长度10
        maxsize=kw.get("maxsize", 10),
        minsize=kw.get("minsize", 1),
        loop=loop,
    )


# 数据库数据选择
async def select(sql, args, size=None):
    log(sql, args)
    global __pool
    # 这个get每搞懂
    async with __pool.get() as conn:
        # print（conn.type()）
        # cursor光标
        async with conn.cursor(aiomysql.DictCursor) as cur:
            # execute(self, query, args):执行单条sql语句,接收的参数为sql语句本身和使用的参数列表,返回值为受影响的行数
            await cur.execute(sql.replace("?", "%s"), args or ())
            if size:
                # fetchmany(self, size=None):接收size条返回结果行.如果size的值大于返回的结果行的数量,则会返回cursor.arraysize条数据
                rs = await cur.fetchmany(size)
            else:
                # fetchall(self):接收全部的返回结果行.
                rs = await cur.fetchall()
            logging.info("rows returned : %s" % len(rs))


# 数据库执行函数
async def execute(sql, args, autocommit=True):
    log(sql, args)
    async with __pool.get() as conn:
        # 如果不是自动提交就
        if not autocommit:
            await conn.begin()
        try:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(sql.replace("?", "%s"), args)
                # 行数
                affected = cur.rowcount
            if not autocommit:
                await conn.commit()
        except BaseException as e:
            if not autocommit:
                await conn.rollback()
            # 抛出异常
            raise
        else:
            pass
        return affected


def create_args_string(num):

    L = []
    # range(num)创建一个整数列表,循环num次
    for n in range(num):
        # 添加占位符["?","?","?"...]
        L.append("?")
    # Python join() 方法用于将序列中的元素以指定的字符连接生成一个新的字符串。
    # ?, ?, ?, ?, ?...
    # print(L)
    # print(type(L))
    return ", ".join(L)


# a = create_args_string(5)
# print(a)
# print(type(a))
class Field(object):
    def __init__(self, name, column_type, primary_key, default):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default

    def __str__(self):
        return "<%s, %s:%s>" % (self.__class__.__name__, self.column_type, self.name)


class StringField(Field):
    def __init__(self, name=None, primary_key=False, default=None, ddl="varchar(100)"):
        # StringField__init__为父类调用Field__init__；self.__class__.__name__为StringField
        super().__init__(name, ddl, primary_key, default)


class BooleanField(Field):
    def __init__(self, name=None, default=False):
        super().__init__(name, "boolean", False, default)


# a = StringField()
# print(a)
# print(type(a))
# a = BooleanField()
# print(a)
# print(type(a))
