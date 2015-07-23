#! /usr/bin/env python
# -*- coding: utf-8 -*-
import urllib.request
import urllib.parse
import base64
import time
from urllib.error import HTTPError

key = "api:key-c43ee09bf8aac9a783c1a2d6557322d9"
mobile = ["18601250262", "18601152810", "18604711912", "15822853996"]

try:
    urllib.request.urlopen("https://api.kachebang.com/v1.7/trucks")
except HTTPError as err:
    num = err.code
    if num == 403:
        exit(0)
try:
    for m in mobile:
        data = urllib.parse.urlencode({'mobile': m, 'message': "OpenAPI 服務無法連接 "+time.strftime("%F %H:%M:%S")+"【卡车帮】"})
        data = data.encode('utf-8')
        request = urllib.request.Request("https://sms-api.luosimao.com/v1/send.json")
        request.add_header("Content-Type","application/x-www-form-urlencoded;charset=utf-8")
        request.add_header("Authorization","Basic "+(base64.b64encode(key.encode("ascii"))).decode("ascii"))
        f = urllib.request.urlopen(request, data)
except HTTPError as err:
    print(err)
