# -*- coding: utf-8 -*-
# Pitivi video editor
# Copyright (c) 2013, Thibault Saunier <thibault.saunier@collabora.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program; if not, write to the
# Free Software Foundation, Inc., 51 Franklin St, Fifth Floor,
# Boston, MA 02110-1301, USA.
import os
from types import MethodType

from gi.repository import Gdk
from gi.repository import Gtk

from pitivi import configure

CUSTOM_WIDGETS_DIR = os.path.join(configure.get_ui_dir(), "customwidgets")


def setup_custom_effect_widgets(effect_prop_manager):
    effect_prop_manager.connect('create_widget', create_custom_widget_cb)


def setup_from_ui_file(element_setting_widget, path):
    # Load the ui file using builder
    builder = Gtk.Builder()
    builder.add_from_file(path)
    # Link ui widgets to the corresponding properties of the effect
    element_setting_widget.mapBuilder(builder)
    return builder


def create_custom_widget_cb(effect_prop_manager, effect_widget, effect):
    """Write custom widget callbacks here."""
    effect_name = effect.get_property("bin-description")
    default_path = os.path.join(CUSTOM_WIDGETS_DIR, effect_name + '.ui')

    # Check if there is a UI file available as a glade file
    try:
        # Assuming a GtkGrid called base_table exists
        builder = setup_from_ui_file(effect_widget, default_path)
        widget = builder.get_object("base_table")
        return widget
    except:
        return None


def create_alpha_widget(element_setting_widget, element):
    """Not implemented yet."""
    return None
