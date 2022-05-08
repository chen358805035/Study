#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "Chen Bo"

" url handlers "
import re, time, json, logging, hashlib, base64, asyncio
import markdown2
from web import get, post
from models import User, Comment, Blog, next_id
from apis import APIValueError, APIResourceNotFoundError

# @get("/")
# async def index(request):
#     users = await User.findAll()
#     return {"__template__": "test.html", "users": users}
_RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
_RE_SHA1 = re.compile(r'^[0-9a-f]{40}$')


# print(User.findAll())
@get("/")
def index(request):
    summary = "Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."
    blogs = [
        Blog(id='1', name='Test Blog', summary=summary, created_at=time.time() - 120),
        Blog(id='2', name='Something New', summary=summary, created_at=time.time() - 3600),
        Blog(id='3', name='Learn Swift', summary=summary, created_at=time.time() - 7200)
    ]
    return {"__template__": "blogs.html", "blogs": blogs}


@post('/api/users')
async def api_get_users(*, email, name, passwd):
    if not name or not name.strip():
        raise APIValueError('name')
    if not email or not _RE_EMAIL.match(email):
        raise APIValueError('email')
    if not passwd or not _RE_SHA1.match(passwd):
        raise APIValueError('passwd')
    users = await User.findAll('email=?', [email])


    page_index = get_page_index(page)
    num = await User.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, users=())
    users = await User.findAll(orderBy='created_at desc')
    for u in users:
        u.passwd = '*****'
    return dict(users=1)
