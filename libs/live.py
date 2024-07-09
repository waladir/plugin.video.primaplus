# -*- coding: utf-8 -*-
import sys
import xbmcgui
import xbmcplugin

from libs.api import call_api, get_token
from libs.epg import get_epg_live, epg_listitem
from libs.profiles import get_profile_id
from libs.utils import get_url

if len(sys.argv) > 1:
    _handle = int(sys.argv[1])

def list_channels(label):
    xbmcplugin.setPluginCategory(_handle, label)
    post = {'id' : '1', 'jsonrpc' : '2.0', 'method' : 'strip.strip.items.vdm', 'params' : {'deviceType' : 'WEB', 'stripId' : '4e0d6d10-4183-4424-8795-2edc47281e9e', 'profileId' : get_profile_id()}}
    data = call_api(url = 'https://gateway-api.prod.iprima.cz/json-rpc/', data = post, token = get_token())
    if 'result' not in data or 'data' not in data['result']:
        xbmcgui.Dialog().notification('Prima+', 'Chyba načtení kanálů', xbmcgui.NOTIFICATION_ERROR, 5000)
    else:
        channels = []
        for item in data['result']['data']['items']:
            channels.append(item['id'])
        epg = get_epg_live(channels)
        for item in data['result']['data']['items']:
            channel = item['id']
            if channel in epg:
                list_item = xbmcgui.ListItem(label = item['title'] + ' | ' + epg[channel]['title'])
                url = get_url(action='play_channel', playId = item['playId'])  
                list_item = epg_listitem(list_item, epg[channel], item['additionals']['logoColorPng'])
            else:
                list_item = xbmcgui.ListItem(label = item['title'])
                url = get_url(action='play_channel', playId = item['playId'])  
                list_item.setInfo('video', {'mediatype':'movie', 'title': item['title']})                  
                list_item.setArt({'thumb' : item['additionals']['logoColorPng'], 'icon' : item['additionals']['logoColorPng']})
            list_item.setProperty('IsPlayable', 'true')       
            list_item.setContentLookup(False)          
            xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
        xbmcplugin.endOfDirectory(_handle, cacheToDisc = False)  

def play_channel(playId):
    data = call_api(url = 'https://api.play-backend.iprima.cz/api/v1/products/id-' + playId + '/play', data = None, token = get_token())
    if 'streamInfos' not in data or len(data['streamInfos']) < 1:
        xbmcgui.Dialog().notification('Prima+', 'Chyba při přehrání pořadu', xbmcgui.NOTIFICATION_ERROR, 5000)
    else:
        url = None
        for stream in data['streamInfos']:
            if 'type' in stream and stream['type'] == 'HLS' and 'url' in stream:
                url = stream['url']
        if url is not None:
            list_item = xbmcgui.ListItem()
            list_item.setPath(url)
            xbmcplugin.setResolvedUrl(_handle, True, list_item)
        else:
            xbmcgui.Dialog().notification('Prima+', 'Chyba při přehrání pořadu', xbmcgui.NOTIFICATION_ERROR, 5000)

