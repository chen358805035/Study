import config_default


class Dict(dict):
    """
    简单的字典，但支持访问为x.y风格。
    """

    def __init__(self, names=(), values=(), **kw):
        super(Dict, self).__init__(**kw)
        for k, v in zip(names, values):
            self[k] = v

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Dict' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value


def merge(default, overrise):
    r = {}
    # 获取默认文件中的数据
    # print("default =%s, overrise= %s" % (default, overrise))
    for k, v in default.items():
        # print("k =%s, v= %s" % (k, v))
        # 如果获取的键值存在与重写文件中
        if k in overrise:
            # 判断该键值对应的值是否是字典类型，如果是将再次调用该函数进行判断
            if isinstance(v, dict):
                r[k] = merge(v, overrise[k])
            # 否则将重写文件中的数据赋值给r
            else:
                r[k] = overrise[k]
        # 如果重写的文件中不存在和默认文件相同的键值数据，将默认文件的数据赋值给r
        else:
            r[k] = v
    # 返回一个字典，该字典相当于是将重写文件中的数据替换到默认文件中的数据中
    # print("r= %s" % r)
    return r


def toDict(d):
    D = Dict()
    for k, v in d.items():
        print("k =%s, v= %s" % (k, v))
        D[k] = toDict(v) if isinstance(v, dict) else v

    return D


configs = config_default.configs
# print(configs)
try:
    import config_override

    configs = merge(configs, config_override.configs)
    # print(configs)
except ImportError:
    pass
configs = toDict(configs)
print(configs)
