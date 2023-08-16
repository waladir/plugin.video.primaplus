# -*- coding: utf-8 -*-
import sys
import os
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
try:
    from xbmcvfs import translatePath
except ImportError:
    from xbmc import translatePath

import codecs
import json

from libs.api import call_api, get_token
from libs.utils import get_url


_url = sys.argv[0]
if len(sys.argv) > 1:
    _handle = int(sys.argv[1])

def list_profiles(label):
    xbmcplugin.setPluginCategory(_handle, label)
    profiles = get_profiles()
    for profile in profiles:
        if profile['active'] == True:
            list_item = xbmcgui.ListItem(label = '[B]' + profile['name'] + '[/B]')
        else:
            list_item = xbmcgui.ListItem(label = profile['name'])
        list_item.setArt({'thumb' : profile['image'], 'icon' : profile['image']})
        url = get_url(action='set_active_profile', id = profile['id'])  
        xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
    list_item = xbmcgui.ListItem(label = 'Načtení profilů')
    url = get_url(action='reset_profiles')  
    xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
    xbmcplugin.endOfDirectory(_handle)        

def set_active_profile(id):
    addon = xbmcaddon.Addon()
    addon_userdata_dir = translatePath(addon.getAddonInfo('profile'))
    filename = os.path.join(addon_userdata_dir, 'profiles.txt')
    profiles = get_profiles()
    for profile in profiles:
        if profile['id'] ==  id:
            profile['active'] = True
        else:
            profile['active'] = False
    try:
        with codecs.open(filename, 'w', encoding='utf-8') as file:
            file.write('%s\n' % json.dumps(profiles))        
    except IOError as error:
        xbmcgui.Dialog().notification('Prima+', 'Chyba při uložení profilů', xbmcgui.NOTIFICATION_ERROR, 5000)            
    xbmc.executebuiltin('Container.Refresh')

def get_profiles(active = False):
    addon = xbmcaddon.Addon()
    addon_userdata_dir = translatePath(addon.getAddonInfo('profile'))
    filename = os.path.join(addon_userdata_dir, 'profiles.txt')
    profiles = []
    data = None
    try:
        with codecs.open(filename, 'r', encoding='utf-8') as file:
            for row in file:
                data = row[:-1]
    except IOError as error:
        if error.errno != 2:
            xbmcgui.Dialog().notification('Prima+', 'Chyba při načtení profilů', xbmcgui.NOTIFICATION_ERROR, 5000)
            sys.exit()
    if data is not None:
        profiles = json.loads(data)
    else:
        data = call_api(url = 'https://auth.iprima.cz/userapi/1/user-profile', data = None, token = get_token(), skip_profile = True)
        if 'err' in data:
            xbmcgui.Dialog().notification('Prima+', 'Chyba při načtení profilů', xbmcgui.NOTIFICATION_ERROR, 5000)
            sys.exit()
        active = True
        for profile in data:
            profiles.append({'id' : profile['ulid'], 'name' : profile['name'], 'image' : profile['avatarUrl'], 'active' : active})
            active = False
        try:
            with codecs.open(filename, 'w', encoding='utf-8') as file:
                file.write('%s\n' % json.dumps(profiles))        
        except IOError as error:
            xbmcgui.Dialog().notification('Prima+', 'Chyba při uložení profilů', xbmcgui.NOTIFICATION_ERROR, 5000)        
            sys.exit()
    if active == True:
        for profile in profiles:
            if profile['active'] == True:
                return profile
        return None
    else:
        return profiles

def get_profile_id():
    profile = get_profiles(active = True)
    return profile['id']

def reset_profiles():
    addon = xbmcaddon.Addon()
    addon_userdata_dir = translatePath(addon.getAddonInfo('profile'))
    filename = os.path.join(addon_userdata_dir, 'profiles.txt')
    if os.path.exists(filename):
        try:
            os.remove(filename) 
        except IOError:
            xbmcgui.Dialog().notification('Prima+', 'Chyba při znovunačtení profilů', xbmcgui.NOTIFICATION_ERROR, 5000)
    get_profiles()
    xbmcgui.Dialog().notification('Prima+', 'Profily byly znovu načtené', xbmcgui.NOTIFICATION_INFO, 5000)    
    xbmc.executebuiltin('Container.Refresh')

def get_subscription():
    data = call_api(url = 'https://api.play-backend.iprima.cz/api/v1/user/sub/active', data = None, token = get_token(), skip_profile = True)
    if 'err' in data:
        xbmcgui.Dialog().notification('Prima+', 'Chyba při načtení profilů', xbmcgui.NOTIFICATION_ERROR, 5000)
        sys.exit()
    subscription = 'free'
    for sub in data:
        if sub['subPackage'] == 'HVOD':
            subscription = 'light'
        elif sub ['subPackage'] == 'SVOD':
            subscription = 'premium'
    return subscription