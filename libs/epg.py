# -*- coding: utf-8 -*-
import xbmcgui
import xbmc 

from datetime import timedelta, datetime
import time
from libs.api import call_api, get_token
from libs.utils import get_kodi_version

def get_epg_channel(channel, day_offset):
    start_date = datetime.today() + timedelta(days = int(day_offset))
    post = {'id' : 'web-1', 'jsonrpc' : '2.0', 'method' : 'epg.program.bulk.list', 'params' : {'date' : {'date' : start_date.strftime('%Y-%m-%d')}, 'channelIds' : [channel]}}
    data = call_api(url = 'https://gateway-api.prod.iprima.cz/json-rpc/', data = post, token = get_token())
    if 'result' not in data or 'data' not in data['result'] and len(data['result']['data']) < 1:
        xbmcgui.Dialog().notification('Prima+', 'Chyba načtení EPG', xbmcgui.NOTIFICATION_ERROR, 5000)
    else:
        for epg in data['result']['data']:
            return epg['items']

def get_epg_live(channels):
    post = {'id' : 'web-1', 'jsonrpc' : '2.0', 'method' : 'epg.program.bulk.current', 'params' : {'channelIds' : channels}}
    data = call_api(url = 'https://gateway-api.prod.iprima.cz/json-rpc/', data = post, token = get_token())
    if 'result' not in data or 'data' not in data['result'] and len(data['result']['data']) < 1:
        xbmcgui.Dialog().notification('Prima+', 'Chyba načtení EPG', xbmcgui.NOTIFICATION_ERROR, 5000)
    else:
        epg = {}
        for channel in data['result']['data']:
            epg.update({channel['channelVdmId'] : channel['items'][0]})
        return epg
    
def epg_listitem(list_item, epg, logo):
    genres = []
    kodi_version = get_kodi_version()
    if kodi_version >= 20:
        infotag = list_item.getVideoInfoTag()
        infotag.setMediaType('movie')
    else:
        list_item.setInfo('video', {'mediatype' : 'movie'})
    if 'images' in epg and epg['images'] is not None and '16x9' in epg['images'] and epg['images']['16x9'] is not None and len(epg['images']['16x9']) > 0:
        if logo is not None:
            list_item.setArt({'thumb': logo, 'poster' : epg['images']['16x9']})
        else:
            list_item.setArt({'thumb': epg['images']['16x9'], 'poster' : epg['images']['16x9']})
    else:
        if logo is not None:
            list_item.setArt({'thumb': logo, 'icon': logo})    
    if 'description' in epg and len(epg['description']) > 0:
        if kodi_version >= 20:
            infotag.setPlot(epg['description'])
        else:
            list_item.setInfo('video', {'plot': epg['description']})
    if 'year' in epg and len(str(epg['year'])) > 0:
        if kodi_version >= 20:
            infotag.setYear(int(epg['year']))
        else:
            list_item.setInfo('video', {'year': int(epg['year'])})
    if 'countries' in epg and len(epg['countries']) > 0:
        if kodi_version >= 20:
            infotag.setCountries([epg['countries'][0]])
        else:
            list_item.setInfo('video', {'countries': epg['countries'][0]})
    if 'genres' in epg and len(epg['genres']) > 0:
        for genre in epg['genres']:      
          genres.append(genre)
        if kodi_version >= 20:
            infotag.setGenres(genres)
        else:
            list_item.setInfo('video', {'genre' : genres})    
    if 'episodeNumber' in epg and epg['episodeNumber'] != None and int(epg['episodeNumber']) > 0:
        if kodi_version >= 20:
            infotag.setEpisode(int(epg['episodeNumber']))
        else:
            list_item.setInfo('video', {'mediatype': 'episode', 'episode' : int(epg['episodeNumber'])}) 
    if 'seasonNumber' in epg and epg['seasonNumber'] != None and int(epg['seasonNumber']) > 0:
        if kodi_version >= 20:
            infotag.setSeason(int(epg['seasonNumber']))
        else:
            list_item.setInfo('video', {'season' : int(epg['seasonNumber'])})  
    return list_item


