# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: nil; -*-
### BEGIN LICENSE
# Copyright (C) 2010 Kevin Mehall <km@kevinmehall.net>
#This program is free software: you can redistribute it and/or modify it
#under the terms of the GNU General Public License version 3, as published
#by the Free Software Foundation.
#
#This program is distributed in the hope that it will be useful, but
#WITHOUT ANY WARRANTY; without even the implied warranties of
#MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR
#PURPOSE.  See the GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License along
#with this program.  If not, see <http://www.gnu.org/licenses/>.
### END LICENSE

import sys
import os
import stat
import logging

from gi.repository import GLib
from .pandora.data import *

pacparser_imported = False
try:
    import pacparser
    pacparser_imported = True
except ImportError:
    logging.info("Could not import python-pacparser.")

config_home = GLib.get_user_config_dir()
configfilename = os.path.join(config_home, 'pithos.ini')

preferences = {}

def load_preferences():
    global preferences

    #default preferences that will be overwritten if some are saved
    preferences = {
        "username":'',
        "password":'',
        "notify":True,
        "last_station_id":None,
        "proxy":'',
        "control_proxy":'',
        "control_proxy_pac":'',
        "show_icon": False,
        "lastfm_key": False,
        "enable_mediakeys":True,
        "enable_screensaverpause":False,
        "volume": 1.0,
        # If set, allow insecure permissions. Implements CVE-2011-1500
        "unsafe_permissions": False,
        "audio_quality": default_audio_quality,
        "pandora_one": False,
        "force_client": None,
    }

    try:
        f = open(configfilename)
    except IOError:
        f = []

    for line in f:
        sep = line.find('=')
        key = line[:sep]
        val = line[sep+1:].strip()
        if val == 'None': val=None
        elif val == 'False': val=False
        elif val == 'True': val=True
        preferences[key]=val

    if 'audio_format' in preferences:
        # Pithos <= 0.3.17, replaced by audio_quality
        del preferences['audio_format']

    if not pacparser_imported and preferences['control_proxy_pac'] != '':
        preferences['control_proxy_pac'] = ''
    
    if fix_perms():
        # Changes were made, save new config variable
        save()
    
    return preferences

def fix_perms():
    """Apply new file permission rules, fixing CVE-2011-1500.
    If the file is 0644 and if "unsafe_permissions" is not True,
       chmod 0600
    If the file is world-readable (but not exactly 0644) and if
    "unsafe_permissions" is not True:
       chmod o-rw
    """
    def complain_unsafe():
        # Display this message iff permissions are unsafe, which is why
        #   we don't just check once and be done with it.
        logging.warning("Ignoring potentially unsafe permissions due to user override.")

    changed = False

    if os.path.exists(configfilename):
        # We've already written the file, get current permissions
        config_perms = stat.S_IMODE(os.stat(configfilename).st_mode)
        if config_perms == (stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH):
            if self.__preferences["unsafe_permissions"]:
                return complain_unsafe()
            # File is 0644, set to 0600
            logging.warning("Removing world- and group-readable permissions, to fix CVE-2011-1500 in older software versions. To force, set unsafe_permissions to True in pithos.ini.")
            os.chmod(configfilename, stat.S_IRUSR | stat.S_IWUSR)
            changed = True

        elif config_perms & stat.S_IROTH:
            if self.__preferences["unsafe_permissions"]:
                return complain_unsafe()
            # File is o+r,
            logging.warning("Removing world-readable permissions, configuration should not be globally readable. To force, set unsafe_permissions to True in pithos.ini.")
            config_perms ^= stat.S_IROTH
            os.chmod(configfilename, config_perms)
            changed = True

        if config_perms & stat.S_IWOTH:
            if self.__preferences["unsafe_permissions"]:
                return complain_unsafe()
            logging.warning("Removing world-writable permissions, configuration should not be globally writable. To force, set unsafe_permissions to True in pithos.ini.")
            config_perms ^= stat.S_IWOTH
            os.chmod(configfilename, config_perms)
            changed = True

    return changed

def save(new_preferences):
    global preferences
    
    existed = os.path.exists(configfilename)
    
    with open(configfilename, 'w') as f:
        if not existed:
            # make the file owner-readable and writable only
            os.fchmod(f.fileno(), (stat.S_IRUSR | stat.S_IWUSR))

        for key, value in new_preferences.items():
            f.write('%s=%s\n'%(key, value))
    
    preferences = new_preferences
