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
from copy import copy

from gi.repository import Gtk, Gdk, GObject

from . import settings
from .pithosconfig import get_ui_file
from .plugins.scrobble import LastFmAuth
from .pandora.data import *

class PreferencesPithosDialog(Gtk.Dialog):
    __gtype_name__ = "PreferencesPithosDialog"

    def __init__(self):
        """__init__ - This function is typically not called directly.
        Creation of a PreferencesPithosDialog requires reading the associated ui
        file and parsing the ui definition extrenally,
        and then calling PreferencesPithosDialog.finish_initializing().

        Use the convenience function NewPreferencesPithosDialog to create
        NewAboutPithosDialog objects.
        """

        pass

    def finish_initializing(self, builder, is_startup):
        """finish_initalizing should be called after parsing the ui definition
        and creating a AboutPithosDialog object with it in order to finish
        initializing the start of the new AboutPithosDialog instance.
        """

        # get a reference to the builder and set up the signals
        self.builder = builder
        self.builder.connect_signals(self)

        # initialize the "Audio Quality" combobox backing list
        audio_quality_combo = self.builder.get_object('prefs_audio_quality')
        fmt_store = Gtk.ListStore(GObject.TYPE_STRING, GObject.TYPE_STRING)
        for audio_quality in valid_audio_formats:
            fmt_store.append(audio_quality)
        audio_quality_combo.set_model(fmt_store)
        render_text = Gtk.CellRendererText()
        audio_quality_combo.pack_start(render_text, True)
        audio_quality_combo.add_attribute(render_text, "text", 1)
        
        if is_startup:
            self.set_type_hint(Gdk.WindowTypeHint.NORMAL) 
            cancel_button = self.builder.get_object('button_cancel')
            cancel_button.set_sensitive(False)

        self.__preferences = copy(settings.preferences)
        self.setup_fields()

    def setup_fields(self):
        self.builder.get_object('prefs_username').set_text(self.__preferences["username"])
        self.builder.get_object('prefs_password').set_text(self.__preferences["password"])
        self.builder.get_object('checkbutton_pandora_one').set_active(self.__preferences["pandora_one"])
        self.builder.get_object('prefs_proxy').set_text(self.__preferences["proxy"])
        self.builder.get_object('prefs_control_proxy').set_text(self.__preferences["control_proxy"])
        self.builder.get_object('prefs_control_proxy_pac').set_text(self.__preferences["control_proxy_pac"])
        if not settings.pacparser_imported:
            self.builder.get_object('prefs_control_proxy_pac').set_sensitive(False)
            self.builder.get_object('prefs_control_proxy_pac').set_tooltip_text("Please install python-pacparser")

        audio_quality_combo = self.builder.get_object('prefs_audio_quality')
        for row in audio_quality_combo.get_model():
            if row[0] == self.__preferences["audio_quality"]:
                audio_quality_combo.set_active_iter(row.iter)
                break

        self.builder.get_object('checkbutton_notify').set_active(self.__preferences["notify"])
        self.builder.get_object('checkbutton_screensaverpause').set_active(self.__preferences["enable_screensaverpause"])
        self.builder.get_object('checkbutton_icon').set_active(self.__preferences["show_icon"])

        self.lastfm_auth = LastFmAuth(self.__preferences, "lastfm_key", self.builder.get_object('lastfm_btn'))

    def response_cb(self, dialog, response):
        if response == Gtk.ResponseType.OK:
            self.__preferences["username"] = self.builder.get_object('prefs_username').get_text()
            self.__preferences["password"] = self.builder.get_object('prefs_password').get_text()
            self.__preferences["pandora_one"] = self.builder.get_object('checkbutton_pandora_one').get_active()
            self.__preferences["proxy"] = self.builder.get_object('prefs_proxy').get_text()
            self.__preferences["control_proxy"] = self.builder.get_object('prefs_control_proxy').get_text()
            self.__preferences["control_proxy_pac"] = self.builder.get_object('prefs_control_proxy_pac').get_text()
            self.__preferences["notify"] = self.builder.get_object('checkbutton_notify').get_active()
            self.__preferences["enable_screensaverpause"] = self.builder.get_object('checkbutton_screensaverpause').get_active()
            self.__preferences["show_icon"] = self.builder.get_object('checkbutton_icon').get_active()

            audio_quality = self.builder.get_object('prefs_audio_quality')
            active_idx = audio_quality.get_active()
            if active_idx != -1: # ignore unknown format
                self.__preferences["audio_quality"] = audio_quality.get_model()[active_idx][0]

            settings.save(self.__preferences)
