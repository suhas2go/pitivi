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
from pitivi.utils.loggable import Loggable

CUSTOM_WIDGETS_DIR = os.path.join(configure.get_ui_dir(), "customwidgets")


def setup_custom_effect_widgets(effect_prop_manager):
    effect_prop_manager.connect('create_widget', create_custom_widget_cb)
    effect_prop_manager.connect('create_property_widget', create_custom_prop_widget_cb)


def setup_from_ui_file(element_setting_widget, path):
    # Load the ui file using builder
    builder = Gtk.Builder()
    builder.add_from_file(path)
    # Link ui widgets to the corresponding properties of the effect
    element_setting_widget.mapBuilder(builder)
    return builder


def create_custom_prop_widget_cb(effect_prop_manager, effect_widget, effect, prop, prop_value):
    effect_name = effect.get_property("bin-description")
    if effect_name == "alpha":
        return create_custom_alpha_prop_widget(effect_widget, effect, prop, prop_value)


def create_custom_widget_cb(effect_prop_manager, effect_widget, effect):
    """Write custom widget callbacks here."""
    effect_name = effect.get_property("bin-description")
    default_path = os.path.join(CUSTOM_WIDGETS_DIR, effect_name + '.ui')

    # Write individual effect callbacks here
    if effect_name == 'alpha':
        widget = create_alpha_widget(effect_widget, effect)
        return widget

    # Check if there is a UI file available as a glade file
    try:
        # Assuming a GtkGrid called base_table exists
        builder = setup_from_ui_file(effect_widget, default_path)
        widget = builder.get_object("base_table")
        return widget
    except:
        return None


def create_alpha_widget(element_setting_widget, element):
    builder = setup_from_ui_file(element_setting_widget, os.path.join(CUSTOM_WIDGETS_DIR, 'alpha.ui'))

    # Additional Setup

    # Color button has to be connected manually!
    ctr = 0
    for prop in element_setting_widget.properties:
        if prop.name == 'target-r':
            r_NumericWidget = element_setting_widget.properties[prop]
            ctr += 1
        elif prop.name == 'target-g':
            g_NumericWidget = element_setting_widget.properties[prop]
            ctr += 1
        elif prop.name == 'target-b':
            b_NumericWidget = element_setting_widget.properties[prop]
            ctr += 1
        if ctr == 3:
            break

    color_button = builder.get_object("colorbutton")

    def update_color(color_button_):
        # TODO: use Gdk.rgba_to_string instead
        color = color_button_.get_color()

        r_NumericWidget.setWidgetValue(int((color.red/65535)*255))
        g_NumericWidget.setWidgetValue(int((color.green/65535)*255))
        b_NumericWidget.setWidgetValue(int((color.blue/65535)*255))

    color_button.connect("color-set", update_color)

    # All modes other than custom RGB chroma keying are useless to us.
    # "ALPHA_METHOD_CUSTOM" corresponds to "3"
    Loggable().debug("Setting alpha's method to 3 (custom RGB chroma keying)")
    element.set_child_property("method", 3)
    return builder.get_object("base_table")

def create_custom_alpha_prop_widget(element_setting_widget, element, prop, prop_value):
    """Not implemented yet."""
    # In the auto-generated UI, replace a property widget with a custom one
    return None
