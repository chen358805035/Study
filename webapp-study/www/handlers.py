#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "Chen Bo"

" url handlers "
import re, time, json, logging, hashlib, base64, asyncio

from web import get, post

from models import User, Comment, Blog, next_id


@get("/")
async def index(request):
    users = await User.findAll()
    return {"__template__": "test.html", "users": users}


# print(User.findAll())
