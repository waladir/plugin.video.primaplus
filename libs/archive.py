# -*- coding: utf-8 -*-
import sys
import os
import xbmcgui
import xbmcplugin
import xbmcaddon

from datetime import date, datetime, timedelta
import time

from libs.api import call_api, get_token
from libs.profiles import get_profile_id
from libs.epg import get_epg_channel, epg_listitem
from libs.utils import get_url, day_translation, day_translation_short, encode

if len(sys.argv) > 1:
    _handle = int(sys.argv[1])

def list_archive(label):
    xbmcplugin.setPluginCategory(_handle, label)
    post = {'id' : '1', 'jsonrpc' : '2.0', 'method' : 'strip.strip.items.vdm', 'params' : {'deviceType' : 'WEB', 'stripId' : '4e0d6d10-4183-4424-8795-2edc47281e9e', 'profileId' : get_profile_id()}}
    data = call_api(url = 'https://gateway-api.prod.iprima.cz/json-rpc/', data = post, token = get_token())
    if 'result' not in data or 'data' not in data['result']:
        xbmcgui.Dialog().notification('Prima+', 'Chyba načtení kanálů', xbmcgui.NOTIFICATION_ERROR, 5000)
    else:
        for item in data['result']['data']['items']:
            list_item = xbmcgui.ListItem(label = item['title'])
            list_item.setArt({'thumb' : item['additionals']['logoColorPng'], 'icon' : item['additionals']['logoColorPng']})
            url = get_url(action='list_archive_days', channel = item['id'], label = label + ' / ' + encode(item['title']))  
            xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    xbmcplugin.endOfDirectory(_handle, cacheToDisc = True)

def list_archive_days(label, channel):
    xbmcplugin.setPluginCategory(_handle, label)
    for i in range (8):
        day = date.today() - timedelta(days = i)
        if i == 0:
            den_label = 'Dnes'
            den = 'Dnes'
        elif i == 1:
            den_label = 'Včera'
            den = 'Včera'
        else:
            den_label = day_translation_short[day.strftime('%w')] + ' ' + day.strftime('%d.%m')
            den = day_translation[day.strftime('%w')] + ' ' + day.strftime('%d.%m.%Y')
        list_item = xbmcgui.ListItem(label = den)
        url = get_url(action='list_program', channel = channel, day_min = i, label = label + ' / ' + den_label)  
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    xbmcplugin.endOfDirectory(_handle, cacheToDisc = False)

def list_program(label, channel, day_min):
    addon = xbmcaddon.Addon()
    icons_dir = os.path.join(addon.getAddonInfo('path'), 'resources','images')
    label = label.replace('Archiv /','')
    xbmcplugin.setPluginCategory(_handle, label)

    epg = get_epg_channel(channel, -1 * int(day_min))

    if int(day_min) < 7:
        list_item = xbmcgui.ListItem(label='Předchozí den')
        day = date.today() - timedelta(days = int(day_min) + 1)
        den_label = day_translation_short[day.strftime('%w')] + ' ' + day.strftime('%d.%m')
        url = get_url(action='list_program', channel = channel, day_min = int(day_min) + 1, label = label.rsplit(' / ')[0] + ' / ' + encode(den_label))
        list_item.setArt({ 'thumb' : os.path.join(icons_dir , 'previous_arrow.png'), 'icon' : os.path.join(icons_dir , 'previous_arrow.png') })
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    for item in epg:
        start_date = datetime.today() + timedelta(days = -1 * int(day_min))
        start_date_ts = int(time.mktime(datetime(start_date.year, start_date.month, start_date.day).timetuple()))
        startTime = time.mktime(time.strptime(item['programStartTime'][:-6], '%Y-%m-%dT%H:%M:%S')) + 7200
        endTime = time.mktime(time.strptime(item['programEndTime'][:-6], '%Y-%m-%dT%H:%M:%S')) + 7200
        if int(endTime) >= start_date_ts and int(endTime) < start_date_ts + 60*60*24:
            if 'playId' in item and item['playId'] is not None and 'playId' and 'isPlayable' in item and item['isPlayable'] == True:
                list_item = xbmcgui.ListItem(label = day_translation_short[datetime.fromtimestamp(startTime).strftime('%w')] + ' ' + datetime.fromtimestamp(startTime).strftime('%d.%m %H:%M') + ' - ' + datetime.fromtimestamp(endTime).strftime('%H:%M') + ' | ' + encode(item['title']))
                list_item = epg_listitem(list_item, item, None)
                list_item.setProperty('IsPlayable', 'true')
                list_item.setContentLookup(False)   
                url = get_url(action='play_stream', playId = item['playId'])  
            else:
                list_item = xbmcgui.ListItem(label = '[COLOR = grey]' + day_translation_short[datetime.fromtimestamp(startTime).strftime('%w')] + ' ' + datetime.fromtimestamp(startTime).strftime('%d.%m %H:%M') + ' - ' + datetime.fromtimestamp(endTime).strftime('%H:%M') + ' | ' + encode(item['title']) + '[/COLOR]')
                url = get_url(action='play_stream', playId = 'N/A') 
            xbmcplugin.addDirectoryItem(_handle, url, list_item, False)

    if int(day_min) > 0:
        list_item = xbmcgui.ListItem(label='Následující den')
        day = date.today() - timedelta(days = int(day_min) - 1)
        den_label = day_translation_short[day.strftime('%w')] + ' ' + day.strftime('%d.%m')
        url = get_url(action='list_program', channel = channel, day_min = int(day_min) - 1, label = label.rsplit(' / ')[0] + ' / ' + den_label)  
        list_item.setArt({ 'thumb' : os.path.join(icons_dir , 'next_arrow.png'), 'icon' : os.path.join(icons_dir , 'next_arrow.png') })
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    xbmcplugin.endOfDirectory(_handle, updateListing = True, cacheToDisc = True)    