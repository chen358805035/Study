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
            return rs


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


# 字符类型段
class StringField(Field):
    # 这个函数会在对象初始化的时候调用，我们可以选择实现，也可以选择不实现，一般建议是实现的，不实现对象属性就不会被初始化。
    def __init__(self, name=None, primary_key=False, default=None, ddl="varchar(100)"):
        # StringField__init__为父类调用Field__init__；self.__class__.__name__为StringField
        super().__init__(name, ddl, primary_key, default)


# 布尔类型段
class BooleanField(Field):
    def __init__(self, name=None, default=False):
        super().__init__(name, "boolean", False, default)


# 整形类型段
class IntegerField(Field):
    def __init__(self, name=None, primary_key=False, default=0):
        super().__init__(name, "bigint", primary_key, default)


# 浮点数类型段
class FloatField(Field):
    def __init__(self, name=None, primary_key=False, default=0.0):
        super().__init__(name, "real", primary_key, default)


# 文本类型段
class TextField(Field):
    def __init__(self, name=None, default=None):
        super().__init__(name, "text", False, default)


# 映射信息读取
class ModelMetaclass(type):
    # __new__() 是一种负责创建类实例的静态方法，它无需使用 staticmethod 装饰器修饰，且该方法会优先 __init__() 初始化方法被调用。
    def __new__(cls, name, bases, attrs):
        if name == "Model":
            return type.__new__(cls, name, bases, attrs)
        tableName = attrs.get("__table__", None) or name
        logging.info("找到模型: %s (表格： %s" % (name, tableName))
        # 映射数据定义为字典
        mappings = dict()
        fields = []
        # 关键字
        primaryKey = None
        # 获取字典键值和值
        for k, v in attrs.items():
            # print("k = %s******v=%s" % (k, v))
            # isinstance() 函数来判断一个对象是否是一个已知的类型，类似 type()。
            if isinstance(v, Field):
                # print("找到映射： %s ==> %s" % (k, v))
                logging.info("找到映射： %s ==> %s" % (k, v))
                mappings[k] = v
                # 如果键值不为空
                if v.primary_key:
                    # print("v.primary_key = %s" % v.primary_key)
                    # 找到主键值。如果primaryKey不为空则执行错误
                    if primaryKey:
                        raise StandardError("复制字段的主键: %s" % k)
                    # 这里赋值成了V导致getattr方法错误
                    primaryKey = k
                # 如果键值为空则将值添加到fields中
                else:
                    fields.append(k)
        if not primaryKey:
            raise StandardError("主键未找到.")
        # 获取映射数据中的键值移除
        for k in mappings.keys():
            # pop() 函数用于移除列表中的一个元素（默认最后一个元素），并且返回该元素的值。
            # 移除attrs中对应映射数据中的键值
            attrs.pop(k)
        # lambda f: '`%s`' % f相当于def(f) return '`%s`' % f
        # ap(lambda f: '`%s`' % f, fields)相当于把fields中的数据变成'x','x'...
        escaped_fields = list(map(lambda f: "`%s`" % f, fields))
        # print(escaped_fields)
        # print("mappings = %s" % mappings)
        # print("tableName = %s" % tableName)
        # print("primaryKey = %s" % primaryKey)
        # print("fields = %s" % fields)
        attrs["__mappings__"] = mappings  # 保存属性和列的映射关系
        attrs["__table__"] = tableName
        attrs["__primary_key__"] = primaryKey  # 主键属性名
        attrs["__fields__"] = fields  # 除主键外的属性名

        # 构造默认的SELECT, INSERT, UPDATE和DELETE语句:
        attrs["__select__"] = "select `%s`, %s from `%s`" % (
            primaryKey,
            ", ".join(escaped_fields),
            tableName,
        )
        attrs["__insert__"] = "insert into %s (%s, %s) values (%s)" % (
            tableName,
            ", ".join(escaped_fields),
            primaryKey,
            create_args_string(len(escaped_fields) + 1),
        )
        attrs["__update__"] = "update `%s` set %s where `%s`=?" % (
            tableName,
            ", ".join(map(lambda f: "`%s`=?" % (mappings.get(f).name or f), fields)),
            primaryKey,
        )
        attrs["__delete__"] = "delete from `%s` where `%s`=?" % (tableName, primaryKey)
        return type.__new__(cls, name, bases, attrs)


# 定义模板类metaclass元素为ModelMetaclass
class Model(dict, metaclass=ModelMetaclass):
    def __init__(self, **kw):
        super(Model, self).__init__(**kw)

    def __getattr__(self, key):
        # 获取不存在的属性将会抛出下面的异常
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Model' 对象没有属性。 '%s'" % key)

    # 在类实例的每个属性进行赋值时，都会首先调用__setattr__()方法，并在__setattr__()方法中将属性名和属性值添加到类实例的__dict__属性中
    def __setattr__(self, key, value):
        self[key] = value

    def getValue(self, key):
        return getattr(self, key, None)

    def getValueOrDefault(self, key):
        print("key = %s " % key)
        value = getattr(self, key, None)
        # print(key)
        print("value = %s" % value)
        # 如果值为空
        if value is None:
            field = self.__mappings__[key]
            if field.default is not None:
                # callable() 函数用于检查一个对象是否是可调用的。如果返回 True，object 仍然可能调用失败；但如果返回 False，调用对象 object 绝对不会成功
                value = field.default() if callable(field.default) else field.default
                logging.debug("使用的默认值 %s: %s" % (key, str(value)))
                setattr(self, key, value)
        return value

    # 查找所有
    @classmethod
    async def findAll(cls, where=None, args=None, **kw):
        #' 通过where子句查找对象. '
        sql = [cls.__select__]
        if where:
            sql.append("where")
            sql.append(where)
        if args is None:
            args = []
        orderBy = kw.get("orderBy", None)
        if orderBy:
            sql.append("order by")
            sql.append(orderBy)
        limit = kw.get("limit", None)
        print("orderBy = %s, limit = %s" % (orderBy, limit))
        if limit is not None:
            sql.append("limit")
            if isinstance(limit, int):
                sql.append("?")
                args.append(limit)
            elif isinstance(limit, tuple) and len(limit) == 2:
                sql.append("?, ?")
                # extend() 函数用于在列表末尾一次性追加另一个序列中的多个值（用新列表扩展原来的列表）。
                args.extend(limit)
            else:
                raise ValueError("无效的极限值: %s" % str(limit))
        rs = await select(" ".join(sql), args)
        # print(" ".join(sql))
        # print(rs)
        return [cls(**r) for r in rs]

    # 查找对应的数据
    @classmethod
    async def findNumber(cls, selectField, where=None, args=None):
        #' 通过select和where查找数字. '
        sql = ["select %s _num_ from `%s`" % (selectField, cls.__table__)]
        if where:
            sql.append("where")
            sql.append(where)
        rs = await select(" ".join(sql), args, 1)
        if len(rs) == 0:
            return None
        return rs[0]["_num_"]

    @classmethod
    async def find(cls, pk):
        #' 通过主键查找对象. '
        rs = await select(
            "%s where `%s`=?" % (cls.__select__, cls.__primary_key__), [pk], 1
        )
        if len(rs) == 0:
            return None
        return cls(**rs[0])

    async def save(self):
        print(self.__fields__)
        args = list(map(self.getValueOrDefault, self.__fields__))
        print("298行 args =%s" % args)

        args.append(self.getValueOrDefault(self.__primary_key__))
        print("301行 args =%s" % args)
        rows = await execute(self.__insert__, args)
        if rows != 1:
            logging.warn("插入记录失败: affected rows: %s" % rows)

    async def update(self):
        args = list(map(self.getValue, self.__fields__))
        args.append(self.getValue(self.__primary_key__))
        rows = await execute(self.__update__, args)
        if rows != 1:
            logging.warn("通过主键更新失败: 受影响的行: %s" % rows)

    async def remove(self):
        args = [self.getValue(self.__primary_key__)]
        rows = await execute(self.__delete__, args)
        if rows != 1:
            logging.warn("按主键删除失败: 受影响的行: %s" % rows)


# a = StringField()
# print(a)
# print(type(a))
# a = BooleanField()
# print(a)
# print(type(a))
