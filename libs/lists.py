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
from libs.profiles import get_profile_id, get_subscription
from libs.utils import get_url, plugin_id, encode, view_modes, get_recombee_url

if len(sys.argv) > 1:
    _handle = int(sys.argv[1])

def get_lock(distributions, subscription):
    for dist in distributions:
        if dist['userLevel'] == subscription:
            return dist['showLock']
    return False
    
def get_list_item(item, subscription, favourite = False):
    list_item = None
    if item['type'] in ['movie', 'episode'] and get_lock(item['distributions'], subscription) == False:
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

def episodes_dict(episodes):
    episodes_dict = {}
    cnt = 1
    for item in episodes:
        key = str(item['additionals']['seasonNumber']).zfill(3) + str(item['additionals']['episodeNumber']).zfill(5) + str(cnt).zfill(4)
        episodes_dict.update({key : item})
        cnt += 1
    return episodes_dict


def get_episodes(id):
    addon = xbmcaddon.Addon()
    post = {'id' : '1', 'jsonrpc' : '2.0', 'method' : 'vdm.frontend.episodes.list.hbbtv', 'params' : {'id' : id, 'deviceType' : 'WEB', 'pager' : {'limit' : 500, 'offset' : 0}, 'profileId' : get_profile_id(), '_accessToken' : get_token(), 'deviceId' : addon.getSetting('deviceid')}}        
    data = call_api(url = 'https://gateway-api.prod.iprima.cz/json-rpc/', data = post, token = get_token())
    if 'result' not in data or 'data' not in data['result'] or 'episodes' not in data['result']['data']:
        xbmcgui.Dialog().notification('Prima+', 'Chyba načtení pořadů', xbmcgui.NOTIFICATION_ERROR, 5000)
        return []
    else:
        return data['result']['data']['episodes']

def list_series(label, slug):
    addon = xbmcaddon.Addon()
    xbmcplugin.setPluginCategory(_handle, label)
    xbmcplugin.setContent(_handle, 'movies')
    subscription = get_subscription()
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
            if addon.getSetting('episodes_order') == 'od nejstarších':
                reversed = False
            else:
                reversed = True
            for season in seasons:
                episodes = episodes_dict(list(get_episodes(season['id'])))
                for id in sorted(episodes.keys(), reverse = reversed):
                    get_list_item(episodes[id], subscription)
    xbmcplugin.endOfDirectory(_handle, cacheToDisc = True)    
    xbmc.executebuiltin('Container.SetViewMode(' + view_modes[addon.getSetting('viewmode')] + ')')

def list_season(label, slug, season):
    addon = xbmcaddon.Addon()
    xbmcplugin.setPluginCategory(_handle, label)
    xbmcplugin.setContent(_handle, 'movies')
    current_season = season
    subscription = get_subscription()
    post = {'id' : '1', 'jsonrpc' : '2.0', 'method' : 'vdm.frontend.title', 'params' : {'deviceType' : 'WEB', 'slug' : slug, 'limit' : 200, 'profileId' : get_profile_id(), '_accessToken' : get_token(), 'deviceId' : addon.getSetting('deviceid')}}        
    data = call_api(url = 'https://gateway-api.prod.iprima.cz/json-rpc/', data = post, token = get_token())
    if 'result' not in data or 'data' not in data['result'] or 'title' not in data['result']['data'] or 'seasons' not in data['result']['data']['title']:
        xbmcgui.Dialog().notification('Prima+', 'Chyba načtení pořadů', xbmcgui.NOTIFICATION_ERROR, 5000)
    else:
        if addon.getSetting('episodes_order') == 'od nejstarších':
            reversed = False
        else:
            reversed = True
        seasons = data['result']['data']['title']['seasons']
        for season in seasons:
            if season['id'] == current_season:
                episodes = episodes_dict(list(get_episodes(season['id'])))
                for id in sorted(episodes.keys(), reverse = reversed):
                    get_list_item(episodes[id], subscription)
                xbmcplugin.endOfDirectory(_handle, cacheToDisc = True)    
        xbmc.executebuiltin('Container.SetViewMode(' + view_modes[addon.getSetting('viewmode')] + ')')

def list_recombee_strip(label, recombeeScenarioId, recombee_filter):
    if recombee_filter == 'none':
        recombee_filter = ''
    addon = xbmcaddon.Addon()
    xbmcplugin.setPluginCategory(_handle, label)
    xbmcplugin.setContent(_handle, 'movies')
    items = []
    subscription = get_subscription()
    post = {"cascadeCreate":True,"returnProperties":True,"includedProperties":["xFrontendMetadata"],"expertSettings":{"returnedInteractionTypes":["viewPortion","purchase"]},"scenario":recombeeScenarioId,"count":70,"filter":"'type' in {\"movie\", \"series\", \"episode\"}" + recombee_filter}
    data = call_api(url = get_recombee_url(), data = post, token = get_token())
    if 'recomms' not in data:    
        xbmcgui.Dialog().notification('Prima+', 'Chyba načtení pořadů', xbmcgui.NOTIFICATION_ERROR, 5000)
    else:
        for item in data['recomms']:
            if 'values' in item and 'xFrontendMetadata' in item['values'] and item['values']['xFrontendMetadata'] is not None:
                items.append(json.loads(item['values']['xFrontendMetadata']))

    if addon.getSetting('order') == 'podle abecedy':                
        items = sorted(items, key=lambda d: d['title']) 
    for item in items:
        if item['type'] in ['movie', 'series', 'episode'] and get_lock(item['distributions'], subscription) == False:
            get_list_item(item, subscription)
    xbmcplugin.endOfDirectory(_handle, cacheToDisc = True)    
    xbmc.executebuiltin('Container.SetViewMode(' + view_modes[addon.getSetting('viewmode')] + ')')

def list_layout(label, layout, recombee_filter = 'none'):
    xbmcplugin.setPluginCategory(_handle, label)
    layout = layout.split('__')
    pageSlug = layout[0]
    userLevel = layout[1]
    post = {'id' : '1', 'jsonrpc' : '2.0', 'method' : 'layout.layout.serve', 'params' : {'deviceType' : 'WEB', 'pageSlug' : pageSlug, 'userLevel' : userLevel}}
    data = call_api(url = 'https://gateway-api.prod.iprima.cz/json-rpc/', data = post, token = get_token())
    if 'result' not in data or 'data' not in data['result']:
        xbmcgui.Dialog().notification('Prima+', 'Chyba načtení pořadůx', xbmcgui.NOTIFICATION_ERROR, 5000)
    else:
        for strip in data['result']['data']['layoutBlocks']:
            if strip['stripData']['stripType'] in ['defaultStrip', 'bannerStrip'] and strip['stripData']['recombeeDataSource'] is not None:
                recombeeScenarioId = strip['stripData']['recombeeDataSource']['scenario']
                list_item = xbmcgui.ListItem(label = strip['stripData']['title'])
                url = get_url(action='list_recombee_strip', label = label + ' / ' + encode(strip['stripData']['title']), recombeeScenarioId = recombeeScenarioId, recombee_filter = recombee_filter)  
                xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
        xbmcplugin.endOfDirectory(_handle, cacheToDisc = True)    

def list_genres(label):
    subscription = get_subscription()
    xbmcplugin.setPluginCategory(_handle, label)
    post = {'id' : '1', 'jsonrpc' : '2.0', 'method' : 'vdm.frontend.genre.list', 'params' : {}}
    data = call_api(url = 'https://gateway-api.prod.iprima.cz/json-rpc/', data = post, token = get_token())
    if 'result' not in data or 'data' not in data['result']:
        xbmcgui.Dialog().notification('Prima+', 'Chyba načtení žánrů', xbmcgui.NOTIFICATION_ERROR, 5000)
    else:
        for genre in data['result']['data']:
            list_item = xbmcgui.ListItem(label = genre['title'])
            url = get_url(action='list_layout', label = label + ' / ' + encode(genre['title']), layout = 'genres__' + subscription, recombee_filter = " AND \"" + encode(genre['title']) + "\" in 'xGenres'")  
            xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
        xbmcplugin.endOfDirectory(_handle, cacheToDisc = True)    


