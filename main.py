# -*- coding: utf-8 -*-
import os
import sys
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
try:
    from xbmcvfs import translatePath
except ImportError:
    from xbmc import translatePath

try:
    from urlparse import parse_qsl
except ImportError:
    from urllib.parse import parse_qsl

from libs.api import get_token, call_api, register_device
from libs.lists import list_layout, list_strip, list_series, list_season, list_genres
from libs.live import list_channels, play_channel
from libs.archive import list_archive, list_archive_days, list_program
from libs.profiles import list_profiles, set_active_profile, reset_profiles, get_subscription
from libs.search import list_search, delete_search, program_search
from libs.favourites import list_favourites, add_favourite, remove_favourite
from libs.devices import list_devices, remove_device
from libs.utils import get_url, ua, PY2

subscription = get_subscription()
LAYOUTS = {'Filmy' : 'categoryMovie__' + subscription, 'Seriály' : 'categorySeries__' + subscription, 'Novinky' : 'categoryNewReleases__' + subscription}

if len(sys.argv) > 1:
    _handle = int(sys.argv[1])

def play_stream(playId):
    addon = xbmcaddon.Addon()
    data = call_api(url = 'https://api.play-backend.iprima.cz/api/v1/products/id-' + playId + '/play', data = None, token = get_token())
    if 'streamInfos' not in data or len(data['streamInfos']) < 1:
        xbmcgui.Dialog().notification('Prima+', 'Chyba při přehrání pořadu', xbmcgui.NOTIFICATION_ERROR, 5000)
    else:
        url = None
        drm = False
        for stream in data['streamInfos']:
            if 'type' in stream and stream['type'] == addon.getSetting('stream_type') and 'url' in stream:
                if '/cze-' in stream['url'] or url is None:
                    url = stream['url']
                if 'drmInfo' in stream:
                    drm = True
                    for drminfo in stream['drmInfo']['modularDrmInfos']:
                        if drminfo['keySystem'] == 'com.widevine.alpha':
                            drm_license_url = drminfo['licenseServerUrl']
                            drm_token = drminfo['token']
                            headers = {'User-Agent': ua, 'X-AxDRM-Message' : drm_token}
        if url is not None:
            list_item = xbmcgui.ListItem()
            if addon.getSetting('stream_type') == 'DASH':
                if PY2:
                    list_item.setProperty('inputstreamaddon', 'inputstream.adaptive')
                else:
                    list_item.setProperty('inputstream', 'inputstream.adaptive')
                list_item.setProperty('inputstream.adaptive.manifest_type', 'mpd')
                if drm == True and drm_license_url and headers:
                    list_item.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
                    try:
                        from urllib import urlencode
                    except ImportError:
                        from urllib.parse import urlencode
                    list_item.setProperty('inputstream.adaptive.license_key', drm_license_url + '|' + urlencode(headers) + '|R{SSM}|')                
                list_item.setMimeType('application/dash+xml')    
            list_item.setPath(url)
            xbmcplugin.setResolvedUrl(_handle, True, list_item)
        else:
            xbmcgui.Dialog().notification('Prima+', 'Chyba při přehrání pořadu', xbmcgui.NOTIFICATION_ERROR, 5000)

def reset_session():
    addon = xbmcaddon.Addon()
    addon_userdata_dir = translatePath(addon.getAddonInfo('profile'))
    filename = os.path.join(addon_userdata_dir, 'session.txt')
    if os.path.exists(filename):
        try:
            os.remove(filename) 
        except IOError:
            xbmcgui.Dialog().notification('Prima+', 'Chyba při resetu session', xbmcgui.NOTIFICATION_ERROR, 5000)
    get_token(reset = True)
    xbmcgui.Dialog().notification('Prima+', 'Byla vytvořená nová session', xbmcgui.NOTIFICATION_INFO, 5000)    

def reset_device():
    addon = xbmcaddon.Addon()
    addon.setSetting('device', '')
    register_device(get_token())
    xbmcgui.Dialog().notification('Prima+', 'Zařízení bylo resetováno', xbmcgui.NOTIFICATION_INFO, 5000)  
    xbmc.executebuiltin('Container.Refresh')
  


def list_settings(label):
    _handle = int(sys.argv[1])
    xbmcplugin.setPluginCategory(_handle, label)

    list_item = xbmcgui.ListItem(label = 'Profily')
    url = get_url(action='list_profiles', label = 'Profily')  
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    list_item = xbmcgui.ListItem(label = 'Zařízení')
    url = get_url(action='list_devices', label = 'Zařízení')  
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    list_item = xbmcgui.ListItem(label = 'Nastavení doplňku')
    url = get_url(action='addon_settings', label = 'Nastavení doplňku')  
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    xbmcplugin.endOfDirectory(_handle)

def list_menu():
    addon = xbmcaddon.Addon()
    icons_dir = os.path.join(addon.getAddonInfo('path'), 'resources','images')

    for layout in LAYOUTS:
        list_item = xbmcgui.ListItem(label = layout)
        url = get_url(action='list_layout', label = layout, layout = LAYOUTS[layout])  
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    list_item = xbmcgui.ListItem(label = 'Žánry')
    url = get_url(action='list_genres', label = 'Žánry')  
    list_item.setArt({ 'thumb' : os.path.join(icons_dir , 'categories.png'), 'icon' : os.path.join(icons_dir , 'categories.png') })
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    list_item = xbmcgui.ListItem(label = 'Živě')
    url = get_url(action='list_channels', label = 'Živě')  
    list_item.setArt({ 'thumb' : os.path.join(icons_dir , 'livetv.png'), 'icon' : os.path.join(icons_dir , 'livetv.png') })
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    list_item = xbmcgui.ListItem(label = 'Archiv')
    url = get_url(action='list_archive', label = 'Archiv')  
    list_item.setArt({ 'thumb' : os.path.join(icons_dir , 'archive.png'), 'icon' : os.path.join(icons_dir , 'archive.png') })
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    list_item = xbmcgui.ListItem(label = 'Vyhledávání')
    url = get_url(action='list_search', label = 'Vyhledávání')  
    list_item.setArt({ 'thumb' : os.path.join(icons_dir , 'search.png'), 'icon' : os.path.join(icons_dir , 'search.png') })
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    list_item = xbmcgui.ListItem(label = 'Oblíbené')
    url = get_url(action='list_favourites', label = 'Oblíbené')  
    list_item.setArt({ 'thumb' : os.path.join(icons_dir , 'favourites.png'), 'icon' : os.path.join(icons_dir , 'favourites.png') })
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    list_item = xbmcgui.ListItem(label = 'Nastavení')
    url = get_url(action='list_settings', label = 'Nastavení')  
    list_item.setArt({ 'thumb' : os.path.join(icons_dir , 'settings.png'), 'icon' : os.path.join(icons_dir , 'settings.png') })
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    xbmcplugin.endOfDirectory(_handle, cacheToDisc = True)    

def router(paramstring):
    params = dict(parse_qsl(paramstring))
    if params:
        if params['action'] == 'list_layout':
            list_layout(params['label'], params['layout'])
        elif params['action'] == 'list_strip':
            if 'strip_filter' in params:
                list_strip(params['label'], params['stripId'], params['strip_filter'])
            else:
                list_strip(params['label'], params['stripId'])
        elif params['action'] == 'list_series':
            list_series(params['label'], params['slug'])
        elif params['action'] == 'list_season':
            list_season(params['label'], params['season'])
        elif params['action'] == 'list_genres':
            list_genres(params['label'])

        elif params['action'] == 'play_stream':
            play_stream(params['playId'])

        elif params['action'] == 'list_channels':
            list_channels(params['label'])
        elif params['action'] == 'play_channel':
            play_channel(params['label'], params['channel'])

        elif params['action'] == 'list_archive':
            list_archive(params['label'])
        elif params['action'] == 'list_archive_days':
            list_archive_days(params['label'], params['channel'])
        elif params['action'] == 'list_program':
            list_program(params['label'], params['channel'], params['day_min'])

        elif params['action'] == 'list_search':
            list_search(params['label'])
        elif params['action'] == 'program_search':
            program_search(params['query'], params['label'])
        elif params['action'] == 'delete_search':
            delete_search(params['query'])

        elif params['action'] == 'list_favourites':
            list_favourites(params['label'])
        elif params['action'] == 'add_favourite':
            add_favourite(params['item'])
        elif params['action'] == 'remove_favourite':
            remove_favourite(params['item'])

        elif params['action'] == 'list_settings':
            list_settings(params['label'])
        elif params['action'] == 'addon_settings':
            xbmcaddon.Addon().openSettings()
        elif params['action'] == 'reset_session':
            reset_session()         
        elif params['action'] == 'list_profiles':
            list_profiles(params['label'])                      
        elif params['action'] == 'set_active_profile':
            set_active_profile(params['id'])                      
        elif params['action'] == 'reset_profiles':
            reset_profiles()         
        elif params['action'] == 'list_devices':
            list_devices(params['label'])                      
        elif params['action'] == 'reset_device':
            reset_device()         
        elif params['action'] == 'remove_device':
            remove_device(params['device'])                      
        else:
            raise ValueError('Neznámý parametr: {0}!'.format(paramstring))
    else:
         list_menu()

if __name__ == '__main__':
    router(sys.argv[2][1:])
