# -*- coding: utf-8 -*-
import sys
import os
import xbmcgui
import xbmcaddon
try:
    from xbmcvfs import translatePath
except ImportError:
    from xbmc import translatePath

try:
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError
    from urllib.parse import parse_qs, urlparse
except ImportError:
    from urllib2 import urlopen, Request, HTTPError # type: ignore
    from urlparse import parse_qs, urlparse # type: ignore

import json
import codecs
import time
import uuid
import requests
from bs4 import BeautifulSoup # type: ignore

from libs.utils import ua

def call_api(url, data, token = None, method = None, skip_profile = False):
    from libs.profiles import get_profile_id
    addon = xbmcaddon.Addon()
    if token is not None:
        if not addon.getSetting('device') or len(addon.getSetting('device')) == 0:
            register_device(token)
        if skip_profile == True:
            headers = {'Authorization' : 'Bearer ' + str(token), 'X-OTT-Access-Token' : str(token), 'X-OTT-CDN-Url-Type' : 'WEB', 'X-OTT-Device' : addon.getSetting('device'), 'User-Agent' : ua, 'Accept': 'application/json; charset=utf-8', 'Content-type' : 'application/json;charset=UTF-8'}
        else:
            headers = {'Authorization' : 'Bearer ' + str(token), 'X-OTT-Access-Token' : str(token), 'X-OTT-CDN-Url-Type' : 'WEB', 'X-OTT-Device' : addon.getSetting('device'), 'X-OTT-User-SubProfile' : get_profile_id(), 'User-Agent' : ua, 'Accept': 'application/json; charset=utf-8', 'Content-type' : 'application/json;charset=UTF-8'}
    else:
        headers = {'User-Agent': ua, 'Accept-language' : 'cs', 'Accept-Encoding' : 'gzip', 'Accept': 'application/json; charset=utf-8', 'Content-type' : 'application/json;charset=UTF-8'}
    if data != None:
        data = json.dumps(data).encode("utf-8")
    if addon.getSetting('log_requests') == 'true':
        print(url)
        print(data)
    if method is not None:
        request = Request(url = url, data = data, method = method, headers = headers)
    else:
        request = Request(url = url, data = data, headers = headers)
    try:
        response = urlopen(request)
        html = response.read()
        if addon.getSetting('log_requests') == 'true':
            print(html)
        if html and len(html) > 0:
            data = json.loads(html)
            return data
        else:
            return []
    except HTTPError as e:
        print(e.reason)
        return { 'err' : e.reason }      

def get_token(reset = False):
    addon = xbmcaddon.Addon()
    if not addon.getSetting('email') or len(addon.getSetting('email')) == 0 and not addon.getSetting('password') and len(addon.getSetting('password')) == 0:
        xbmcgui.Dialog().notification('Prima+', 'Zadejte v nastavení přihlašovací údaje', xbmcgui.NOTIFICATION_ERROR, 5000)
        sys.exit()
    if not addon.getSetting('deviceid') or len(addon.getSetting('deviceid')) == 0:
        addon.setSetting('deviceid', 'd-' + str(uuid.uuid4()))

    data = None
    addon_userdata_dir = translatePath(addon.getAddonInfo('profile'))
    filename = os.path.join(addon_userdata_dir, 'session.txt')
    try:
        with codecs.open(filename, 'r', encoding='utf-8') as file:
            for row in file:
                data = row[:-1]
    except IOError as error:
        if error.errno != 2:
            xbmcgui.Dialog().notification('Prima+', 'Chyba při načtení session', xbmcgui.NOTIFICATION_ERROR, 5000)
    if data is not None and reset == False:
        data = json.loads(data)
        if 'token' in data and 'valid_to' in data and data['valid_to'] > int(time.time()):
            token = data['token']
            return token

    headers = {'User-Agent': ua}
    response = requests.post(url = 'https://ucet.iprima.cz/api/session/create', json = {'email' : addon.getSetting('email'), 'password' : addon.getSetting('password'), 'deviceName' : 'Windows Firefox'}, headers = headers)
    data = json.loads(response.content)
    if 'accessToken' in data:
        token = data['accessToken']['value']
        data = json.dumps({'token' : token, 'valid_to' : int(time.time()) + 7*60*60})
        try:
            with codecs.open(filename, 'w', encoding='utf-8') as file:
                file.write('%s\n' % data)
        except IOError:
            xbmcgui.Dialog().notification('Prima+', 'Chyba uložení session', xbmcgui.NOTIFICATION_ERROR, 5000)
        return token
    else:
        xbmcgui.Dialog().notification('Prima+', 'Chyba při přihlášení', xbmcgui.NOTIFICATION_ERROR, 5000)
        sys.exit()

def register_device(token):
    addon = xbmcaddon.Addon()
    headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/112.0', 'Accept': 'application/json; charset=utf-8', 'Content-type' : 'application/json;charset=UTF-8'}
    post = {'id' : '1', 'jsonrpc' : '2.0', 'method' : 'user.device.slot.add', 'params':{'_accessToken' : token, 'deviceSlotType' : 'WEB', 'deviceSlotName' : 'Windows Firefox', 'deviceUid' : addon.getSetting('deviceid')}}
    request = Request(url = 'https://gateway-api.prod.iprima.cz/json-rpc/', data = json.dumps(post).encode("utf-8"), headers = headers)
    response = urlopen(request)
    html = response.read()
    if html and len(html) > 0:
        data = json.loads(html)
        if 'result' and data or 'data' in data['result'] and 'slotId' in data['result']['data']:
            addon.setSetting('device', data['result']['data']['slotId'])
