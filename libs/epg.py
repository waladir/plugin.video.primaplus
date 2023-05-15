# -*- coding: utf-8 -*-
import xbmcgui

from datetime import timedelta, datetime
import time
from libs.api import call_api, get_token

def get_epg_channel(channel, day_offset):
    start_date = datetime.today() + timedelta(days = int(day_offset))
    start_date_ts = int(time.mktime(datetime(start_date.year, start_date.month, start_date.day).timetuple()))
    post = {'query' : '{epg(day: ' + str(start_date_ts) + ', fromTime: ' + str(start_date_ts) + ') { ' + channel + ' { video { playId nid episodeTitle image {tileM_465x270 tileM_233x135} } title timeStart timeEnd channel annotation year genres countries program { flag image { tileM_465x270 tileM_233x135 } } hasHiddenSubtitles hasAudioDescription } } }'}
    data = call_api(url = 'https://api.iprima.cz/graphql', data = post, token = get_token())
    if 'data' not in data or 'epg' not in data['data']:
        xbmcgui.Dialog().notification('Prima+', 'Chyba načtení EPG', xbmcgui.NOTIFICATION_ERROR, 5000)
    else:
        return data['data']['epg'][channel]

def get_epg_day(channels, day_offstet = 0):
    start_date = datetime.today() + timedelta(days = int(day_offstet))
    start_date_ts = int(time.mktime(datetime(start_date.year, start_date.month, start_date.day).timetuple()))
    channel_query = ''
    epg = {}
    for channel in channels:
        channel_query += channel + ' { __typename ...EpgItem } '
    post = {'query' : '{ epg(day: ' + str(start_date_ts) + ', fromTime: ' + str(start_date_ts) + ') { ' + channel_query + ' } }  fragment EpgItem on EPG { serialNumber title timeStart timeEnd channel countries genres year hasAudioDescription hasHiddenSubtitles program { nid title image { landscape_580x326 } } video { nid playId category teaser episodeTitle } }'}
    data = call_api(url = 'https://api.iprima.cz/graphql', data = post, token = get_token())
    if 'data' not in data or 'epg' not in data['data']:
        xbmcgui.Dialog().notification('Prima+', 'Chyba načtení EPG', xbmcgui.NOTIFICATION_ERROR, 5000)
    else:
        for channel in data['data']['epg']:
            channel_epg = []
            for item in data['data']['epg'][channel]:
                channel_epg.append(item)
            epg.update({channel : channel_epg})
    return epg

def get_epg_live(channels):
    currenttime = time.localtime()
    epg_current = {}
    epg = []
    epg.append(get_epg_day(channels, -1))
    epg.append(get_epg_day(channels))
    for epg_day in epg:
        for channel in channels:
            if channel in epg_day:
                for item in epg_day[channel]:
                    timeStart = time.strptime(item['timeStart'][:-6], '%Y-%m-%dT%H:%M:%S')
                    if timeStart <= currenttime:
                        epg_current.update({channel : item})
    return epg_current