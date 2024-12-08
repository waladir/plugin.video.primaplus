# -*- coding: utf-8 -*-
import sys
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

import json 

try:
    from urllib.parse import quote
except ImportError:
    from urllib import quote

from libs.api import get_token, call_api
from libs.profiles import get_profile_id
from libs.utils import get_url, plugin_id, encode, view_modes

if len(sys.argv) > 1:
    _handle = int(sys.argv[1])

def get_list_item(item, favourite = False):
    list_item = None
    if item['type'] in ['movie', 'episode'] and item['distribution']['showLock'] == False:
        date = ''
        if item['additionals']['broadcastDateTime'] is not None:
            split_date = item['additionals']['broadcastDateTime'][:10].split('-')
            date = ' | ' + split_date[2] + '.' + split_date[1] + '.' + split_date[0]
        elif item['additionals']['premiereDateTime'] is not None:
            split_date = item['additionals']['premiereDateTime'][:10].split('-')
            date = ' | ' + split_date[2] + '.' + split_date[1] + '.' + split_date[0]
        if item['type'] == 'episode' and '(' + str(item['additionals']['episodeNumber']) + ')' not in item['title']:
            list_item = xbmcgui.ListItem(label = item['title'] + ' (' + str(item['additionals']['episodeNumber']) + ')' + date)
        else:
            list_item = xbmcgui.ListItem(label = item['title'] + date)
        list_item.setContentLookup(False)          
        url = get_url(action='play_stream', playId = item['playId'])  
        list_item.setProperty('IsPlayable', 'true')       
        list_item.setInfo('video', {'mediatype':'video', 'title': item['title']})                  
        list_item.setArt({'poster' : item['images']['3x5'], 'thumb' : item['images']['16x9']})
        list_item.setInfo('video', {'plot': item['perex']})
        list_item.setInfo('video', {'year': int(item['additionals']['year'])})
        list_item.setInfo('video', {'country': item['additionals']['originCountries']})
        list_item.setInfo('video', {'genre' : item['additionals']['genres']})    
        if favourite == True:
            list_item.addContextMenuItems([('Odstranit z oblíbených Prima+', 'RunPlugin(plugin://' + plugin_id + '?action=remove_favourite&item=' + quote(json.dumps(item)) + ')',)], replaceItems = True)        
        else:
            list_item.addContextMenuItems([('Přidat do oblíbených Prima+', 'RunPlugin(plugin://' + plugin_id + '?action=add_favourite&item=' + quote(json.dumps(item)) + ')',)], replaceItems = True)        
        if item['type'] == 'episode':
            url = get_url(action='play_stream', playId = item['playId'])  
            list_item.setInfo('video', {'mediatype': 'episode', 'episode' : int(item['additionals']['episodeNumber'])}) 
            list_item.setInfo('video', {'title' : item['title']})  
            list_item.setInfo('video', {'tvshowtitle' : item['additionals']['seasonTitle']})  
            list_item.setInfo('video', {'season' : int(item['additionals']['seasonNumber'])}) 
        xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
    elif item['type'] == 'series':
        list_item = xbmcgui.ListItem(label = item['title'])
        list_item.setArt({'poster' : item['images']['3x5'], 'thumb' : item['images']['16x9']})
        url = get_url(action='list_series', label = encode(item['title']), slug = item['slug'])  
        if favourite == True:
            list_item.addContextMenuItems([('Odstranit z oblíbených Prima+', 'RunPlugin(plugin://' + plugin_id + '?action=remove_favourite&item=' + quote(json.dumps(item)) + ')',)], replaceItems = True)        
        else:
            list_item.addContextMenuItems([('Přidat do oblíbených Prima+', 'RunPlugin(plugin://' + plugin_id + '?action=add_favourite&item=' + quote(json.dumps(item)) + ')',)], replaceItems = True)        
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    return list_item

def list_series(label, slug):
    addon = xbmcaddon.Addon()
    xbmcplugin.setPluginCategory(_handle, label)
    xbmcplugin.setContent(_handle, 'movies')
    post = {'id' : '1', 'jsonrpc' : '2.0', 'method' : 'vdm.frontend.title', 'params' : {'deviceType' : 'WEB', 'slug' : slug, 'limit' : 200, 'profileId' : get_profile_id(), '_accessToken' : get_token(), 'deviceId' : addon.getSetting('deviceid')}}        
    data = call_api(url = 'https://gateway-api.prod.iprima.cz/json-rpc/', data = post, token = get_token())
    if 'result' not in data or 'data' not in data['result'] or 'title' not in data['result']['data'] or 'seasons' not in data['result']['data']['title']:
        xbmcgui.Dialog().notification('Prima+', 'Chyba načtení pořadů', xbmcgui.NOTIFICATION_ERROR, 5000)
    else:
        seasons = data['result']['data']['title']['seasons']
        if len(seasons) > 1:
            for season in seasons:
                list_item = xbmcgui.ListItem(label = season['title'])
                url = get_url(action='list_season', label = label + ' / ' + encode(season['title']), slug = slug, season = season['id'])  
                xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
        else:
            for season in seasons:
                episodes = list(season['episodes'])
                episodes.reverse() 
                for item in episodes:
                    get_list_item(item)
    xbmcplugin.endOfDirectory(_handle, cacheToDisc = True)    
    xbmc.executebuiltin('Container.SetViewMode(' + view_modes[addon.getSetting('viewmode')] + ')')


def list_season(label, slug, season):
    addon = xbmcaddon.Addon()
    xbmcplugin.setPluginCategory(_handle, label)
    xbmcplugin.setContent(_handle, 'movies')
    current_season = season
    post = {'id' : '1', 'jsonrpc' : '2.0', 'method' : 'vdm.frontend.title', 'params' : {'deviceType' : 'WEB', 'slug' : slug, 'limit' : 200, 'profileId' : get_profile_id(), '_accessToken' : get_token(), 'deviceId' : addon.getSetting('deviceid')}}        
    data = call_api(url = 'https://gateway-api.prod.iprima.cz/json-rpc/', data = post, token = get_token())
    if 'result' not in data or 'data' not in data['result'] or 'title' not in data['result']['data'] or 'seasons' not in data['result']['data']['title']:
        xbmcgui.Dialog().notification('Prima+', 'Chyba načtení pořadů', xbmcgui.NOTIFICATION_ERROR, 5000)
    else:
        seasons = data['result']['data']['title']['seasons']
        for season in seasons:
            if season['id'] == current_season:
                episodes = list(season['episodes'])
                episodes.reverse() 
                for item in episodes:
                    get_list_item(item)
                xbmcplugin.endOfDirectory(_handle, cacheToDisc = True)    
        xbmc.executebuiltin('Container.SetViewMode(' + view_modes[addon.getSetting('viewmode')] + ')')

def list_strip(label, stripId, strip_filter = None):
    addon = xbmcaddon.Addon()
    xbmcplugin.setPluginCategory(_handle, label)
    xbmcplugin.setContent(_handle, 'movies')
    limit = 100
    page = 1
    last = False
    items = []
    while last == False:
        if page == 1:
            if strip_filter is not None:
                post = {'id' : '1', 'jsonrpc' : '2.0', 'method' : 'strip.strip.items.vdm', 'params' : {'filter' : json.loads(strip_filter), 'deviceType' : 'WEB', 'stripId' : stripId, 'limit' : limit, 'profileId' : get_profile_id(), '_accessToken' : get_token(), 'deviceId' : addon.getSetting('deviceid')}}
            else:
                post = {'id' : '1', 'jsonrpc' : '2.0', 'method' : 'strip.strip.items.vdm', 'params' : {'deviceType' : 'WEB', 'stripId' : stripId, 'limit' : limit, 'profileId' : get_profile_id(), '_accessToken' : get_token(), 'deviceId' : addon.getSetting('deviceid')}}
        else:
            if strip_filter is not None:
                post = {'id' : '1', 'jsonrpc' : '2.0', 'method' : 'strip.strip.nextItems.vdm', 'params' : {'filter' : json.loads(strip_filter), 'deviceType' : 'WEB', 'stripId' : stripId, 'limit' : limit, 'offset' : int(page) * limit, 'recommId' : recommId, 'profileId' : get_profile_id(), '_accessToken' : get_token(), 'deviceId' : addon.getSetting('deviceid')}}
            else:
                post = {'id' : '1', 'jsonrpc' : '2.0', 'method' : 'strip.strip.nextItems.vdm', 'params' : {'deviceType' : 'WEB', 'stripId' : stripId, 'limit' : limit, 'offset' : int(page) * limit, 'recommId' : recommId, 'profileId' : get_profile_id(), '_accessToken' : get_token(), 'deviceId' : addon.getSetting('deviceid')}}
        data = call_api(url = 'https://gateway-api.prod.iprima.cz/json-rpc/', data = post, token = get_token())
        if 'result' not in data or 'data' not in data['result'] or 'items' not in data['result']['data']:
            if page < 11:
                xbmcgui.Dialog().notification('Prima+', 'Chyba načtení pořadů', xbmcgui.NOTIFICATION_ERROR, 5000)
            last = True
        else:
            items += data['result']['data']['items']
            page += 1
            recommId = data['result']['data']['recommId']
            if data['result']['data']['isNextItems'] == False:
                last = True
    if addon.getSetting('order') == 'podle abecedy':                
        items = sorted(items, key=lambda d: d['title']) 
    for item in items:
        if item['type'] == 'static':
            list_item = xbmcgui.ListItem(label = item['title'])
            url = get_url(action='list_strip', label = label + ' / ' + encode(item['title']), stripId = stripId, strip_filter = json.dumps([{'type' : 'genre', 'value' : item['title']}]))  
            xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
        elif item['type'] in ['movie', 'series']:
            get_list_item(item)
    xbmcplugin.endOfDirectory(_handle, cacheToDisc = True)    
    xbmc.executebuiltin('Container.SetViewMode(' + view_modes[addon.getSetting('viewmode')] + ')')

def list_layout(label, layout):
    xbmcplugin.setPluginCategory(_handle, label)
    post = {'id' : '1', 'jsonrpc' : '2.0', 'method' : 'strip.layout.serve.vdm', 'params' : {'deviceType' : 'WEB', 'layout' : layout, 'profileId' : get_profile_id()}}
    data = call_api(url = 'https://gateway-api.prod.iprima.cz/json-rpc/', data = post, token = get_token())
    if 'result' not in data or 'data' not in data['result']:
        xbmcgui.Dialog().notification('Prima+', 'Chyba načtení pořadů', xbmcgui.NOTIFICATION_ERROR, 5000)
    else:
        for strip in data['result']['data']:
            if strip['type'] == 'strip' and strip['stripData']['layoutType'] in ['portraitStrip', 'landscapeStrip']:
                list_item = xbmcgui.ListItem(label = strip['stripData']['title'])
                url = get_url(action='list_strip', label = label + ' / ' + encode(strip['stripData']['title']), stripId = strip['stripData']['id'])  
                xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
        xbmcplugin.endOfDirectory(_handle, cacheToDisc = True)    

def list_genres(label):
    xbmcplugin.setPluginCategory(_handle, label)
    post = {'id' : '1', 'jsonrpc' : '2.0', 'method' : 'vdm.frontend.genre.list', 'params' : {}}
    data = call_api(url = 'https://gateway-api.prod.iprima.cz/json-rpc/', data = post, token = get_token())
    if 'result' not in data or 'data' not in data['result']:
        xbmcgui.Dialog().notification('Prima+', 'Chyba načtení žánrů', xbmcgui.NOTIFICATION_ERROR, 5000)
    else:
        for genre in data['result']['data']:
            list_item = xbmcgui.ListItem(label = genre['title'])
            url = get_url(action='list_strip', label = label + ' / ' + encode(genre['title']), stripId = '8138baa8-c933-4015-b7ea-17ac7a679da4', strip_filter = json.dumps([{'type' : 'genre', 'value' : genre['title']}]))  
            xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
        xbmcplugin.endOfDirectory(_handle, cacheToDisc = True)    


