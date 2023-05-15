# -*- coding: utf-8 -*-
import sys
import xbmcgui
import xbmcplugin

from libs.api import call_api, get_token
from libs.epg import get_epg_live
from libs.profiles import get_profile_id
from libs.utils import get_url, encode

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
            channels.append(item['id'].replace('prima_', ''))
        epg = get_epg_live(channels)
        for item in data['result']['data']['items']:
            channel = item['id'].replace('prima_', '')
            if channel in epg:
                list_item = xbmcgui.ListItem(label = item['title'] + ' | ' + epg[channel]['title'])
                url = get_url(action='play_channel', label = label + ' / ' + encode(item['title']), channel = channel)  
                list_item.setInfo('video', {'mediatype':'movie', 'title': item['title'] + ' | ' + epg[channel]['title']})                  
                if epg[channel]['video'] is not None and 'teaser' in epg[channel]['video']:
                    list_item.setInfo('video', {'plot': epg[channel]['video']['teaser']})
                if 'year' in epg[channel] and epg[channel]['year'] is not None:
                    list_item.setInfo('video', {'year': int(epg[channel]['year'])})
                list_item.setInfo('video', {'country': epg[channel]['countries']})
                list_item.setInfo('video', {'genre' : epg[channel]['genres']})    
            else:
                list_item = xbmcgui.ListItem(label = item['title'])
                url = get_url(action='play_channel', label = label + ' / ' + encode(item['title']), channel = channel)  
                list_item.setInfo('video', {'mediatype':'movie', 'title': item['title']})                  
            list_item.setArt({'thumb' : item['additionals']['logoColorPng'], 'icon' : item['additionals']['logoColorPng']})
            list_item.setProperty('IsPlayable', 'true')       
            list_item.setContentLookup(False)          
            xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
        xbmcplugin.endOfDirectory(_handle, cacheToDisc = False)  

def play_channel(label, channel):
    xbmcplugin.setPluginCategory(_handle, label)
    post = {'query' : '{ channelList { id, playId } }'}
    data = call_api(url = 'https://api.iprima.cz/graphql', data = post, token = get_token())
    if 'data' not in data or 'channelList' not in data['data']:
        xbmcgui.Dialog().notification('Prima+', 'Chyba načtení pořadů', xbmcgui.NOTIFICATION_ERROR, 5000)
    for item in data['data']['channelList']:
        if item['id'] == channel:
            data = call_api(url = 'https://api.play-backend.iprima.cz/api/v1/products/id-' + item['playId'] + '/play', data = None, token = get_token())
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

