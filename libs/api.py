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
    from urllib2 import urlopen, Request, HTTPError
    from urlparse import parse_qs, urlparse

import json
import codecs
import time
import uuid
import requests
import gzip
from bs4 import BeautifulSoup

def call_api(url, data, token = None, method = None, skip_profile = False):
    from libs.profiles import get_profile_id
    if token is not None:
        addon = xbmcaddon.Addon()
        if skip_profile == True:
            headers = {'Authorization' : 'Bearer ' + str(token), 'X-OTT-Access-Token' : str(token), 'X-OTT-CDN-Url-Type' : 'WEB', 'X-OTT-Device' : addon.getSetting('deviceid'), 'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/112.0', 'Accept': 'application/json; charset=utf-8', 'Content-type' : 'application/json;charset=UTF-8'}
        else:
            headers = {'Authorization' : 'Bearer ' + str(token), 'X-OTT-Access-Token' : str(token), 'X-OTT-CDN-Url-Type' : 'WEB', 'X-OTT-Device' : addon.getSetting('deviceid'), 'X-OTT-User-SubProfile' : get_profile_id(), 'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/112.0', 'Accept': 'application/json; charset=utf-8', 'Content-type' : 'application/json;charset=UTF-8'}
    else:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/112.0', 'Accept-language' : 'cs', 'Accept-Encoding' : 'gzip', 'Accept': 'application/json; charset=utf-8', 'Content-type' : 'application/json;charset=UTF-8'}
    if data != None:
        data = json.dumps(data).encode("utf-8")
    if method is not None:
        request = Request(url = url, data = data, method = method, headers = headers)
    else:
        request = Request(url = url, data = data, headers = headers)
    try:
        response = urlopen(request)
        html = response.read()        
        if html and len(html) > 0:
            data = json.loads(html)
            return data
        else:
            return []
    except HTTPError as e:
        return { 'err' : e.reason }      

def get_token():
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
    if data is not None:
        data = json.loads(data)
        if 'token' in data and 'valid_to' in data and data['valid_to'] > int(time.time()):
            token = data['token']
            return token

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/112.0'}
    session = requests.Session()
    response = session.get(url = 'https://auth.iprima.cz/oauth2/login' , headers = headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    input = soup.find('input', {'name' : '_csrf_token'})
    if input is None:
        xbmcgui.Dialog().notification('Prima+', 'Chyba při přihlášení', xbmcgui.NOTIFICATION_ERROR, 5000)
        sys.exit()
    else:
        csrf_token = input.get('value')

    response = session.post(url = 'https://auth.iprima.cz/oauth2/login', json = {'_email' : addon.getSetting('email'), '_password' : addon.getSetting('password'), '_csrf_token' : csrf_token}, headers = headers)
    response = session.get(url = 'https://auth.iprima.cz/oauth2/authorize?auth_init_url=https%3A%2F%2Fwww.iprima.cz%2F&auth_return_url=https%3A%2F%2Fwww.iprima.cz%2F%3Fauthentication%3Dcancelled&client_id=prima_sso&redirect_uri=https%3A%2F%2Fauth.iprima.cz%2Fsso%2Fauth-check&response_type=code&scope=openid%20email%20profile%20phone%20address%20offline_access&state=prima_sso', headers = headers)
    auth_url = parse_qs(urlparse(response.url).query)
    if 'code' not in auth_url:
        xbmcgui.Dialog().notification('Prima+', 'Chyba při přihlášení', xbmcgui.NOTIFICATION_ERROR, 5000)
        sys.exit()
    auth_code = auth_url['code'][0]

    data = {'scope' : 'openid+email+profile+phone+address+offline_access', 'client_id' : 'prima_sso', 'grant_type' : 'authorization_code', 'code' : auth_code, 'redirect_uri' : 'https://auth.iprima.cz/sso/auth-check'}
    response = session.post(url = 'https://auth.iprima.cz/oauth2/token', json = data, headers = headers)
    token_data = json.loads(response.content)
    if 'access_token' in token_data:
        token = token_data['access_token']
        data = json.dumps({'token' : token, 'valid_to' : int(time.time()) + 60*60})
        try:
            with codecs.open(filename, 'w', encoding='utf-8') as file:
                file.write('%s\n' % data)
        except IOError:
            xbmcgui.Dialog().notification('Prima+', 'Chyba uložení session', xbmcgui.NOTIFICATION_ERROR, 5000)
        return token
    else:
        xbmcgui.Dialog().notification('Prima+', 'Chyba při přihlášení', xbmcgui.NOTIFICATION_ERROR, 5000)
        sys.exit()
