# -*- coding: utf-8 -*-
import sys
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

from datetime import datetime
from libs.api import call_api, get_token, register_device
from libs.utils import get_url

if len(sys.argv) > 1:
    _handle = int(sys.argv[1])

def list_devices(label):
    xbmcplugin.setPluginCategory(_handle, label)
    addon = xbmcaddon.Addon()
    post = {'id' : 'auth-fe-1', 'jsonrpc' : '2.0', 'method' : 'user.device.slot.list', 'params' : {'_accessToken' : get_token()}}        
    data = call_api(url = 'https://gateway-api.prod.iprima.cz/json-rpc/', data = post, token = get_token())
    if 'result' not in data or 'data' not in data['result']:
        xbmcgui.Dialog().notification('Prima+', 'Chyba načtení zařízení', xbmcgui.NOTIFICATION_ERROR, 5000)
    else:
        for device in data['result']['data']:
            if device['slotId'] == addon.getSetting('device'):
                title = '[B]' + device['title'] + ' (' + device['slotId'] + ')[/B]'
            else:
                title = device['title'] + ' (' + device['slotId'] + ')'
            list_item = xbmcgui.ListItem(label = title + '\n[COLOR=gray]Poslední příhlášení: ' + datetime.fromisoformat(device['lastChanged']).strftime('%d.%m.%Y %H:%M') + '[/COLOR]')
            url = get_url(action='remove_device', device = device['slotId'])  
            xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
    list_item = xbmcgui.ListItem(label = 'Reset zařízení')
    url = get_url(action='reset_device')  
    xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
    xbmcplugin.endOfDirectory(_handle)        

def remove_device(device):
    response = xbmcgui.Dialog().yesno('Prima+', 'Opravdu odstranit zařízení?', nolabel = 'Ne', yeslabel = 'Ano')
    if response:
        addon = xbmcaddon.Addon()
        post = {'id' : 'auth-fe-1', 'jsonrpc' : '2.0', 'method' : 'user.device.slot.remove', 'params' : {'_accessToken' : get_token(), 'slotId' : device}}        
        call_api(url = 'https://gateway-api.prod.iprima.cz/json-rpc/', data = post, token = get_token())
        xbmcgui.Dialog().notification('Prima+', 'Zařízení bylo odstraněno', xbmcgui.NOTIFICATION_INFO, 5000)  
        if device == addon.getSetting('device'):
            addon.setSetting('device', '')
            register_device(get_token())
        xbmc.executebuiltin('Container.Refresh')
