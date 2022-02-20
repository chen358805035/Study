# d = {"Michael": 95, "Bod": 75, "Tracy": 85}
# b = [d.get("Michael"), d.get("Bod"), d.get("Tracy")]
# a = dict()
# # # a = d.get("Michael")
# # for k, v in d.items():
# #     print("key = %s,value = %s" % (k, v))
# # # with d.get() as a:
# # print(a)

# # print(b)
# # print(list(map(lambda f: "`%s`" % f, b)))

import orm, asyncio
from models import User, Blog, Comment


async def test(loop):
    await orm.create_pool(loop=loop, user="cb", password="cb", db="cb")

    u = User(
        name="Test", email="test@example.com", passwd="1234567890", image="about:blank"
    )

    await u.save()


loop = asyncio.get_event_loop()
loop.run_until_complete(test(loop))
loop.close()
