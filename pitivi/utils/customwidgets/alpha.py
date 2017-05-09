# PiTiVi , Non-linear video editor
#
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


def getWidgetIntegerValue(container):
    self = container[0]
    DEFAULT_VALUE = container[1]
    if self.matches:
        return self.last_valid
    if self.text.get_text():
        val = int(float(self.text.get_text()))
        if val > 255:
            val = 255
            self.text.set_text(str(val))
        return val
    else:
        # Don't set text now, wait to focus out
        val = DEFAULT_VALUE
    return val


def create_widget(element_setting_widget, element):
    # 1) Load the ui file using builder
    builder = Gtk.Builder()
    builder.add_from_file(os.path.join(configure.get_ui_dir(),"customwidgets","alpha.ui"))

    # 2) Link ui widgets to the corresponding properties of the effect
    element_setting_widget.mapBuilder(builder)

    # 3) Other connects, if required
    ctr = 0
    for prop in element_setting_widget.properties:
        if prop.name == 'target-r':
            r_TextWidget = element_setting_widget.properties[prop]
            ctr += 1
        elif prop.name == 'target-g':
            g_TextWidget = element_setting_widget.properties[prop]
            ctr += 1
        elif prop.name == 'target-b':
            b_TextWidget = element_setting_widget.properties[prop]
            ctr += 1
        if ctr == 3:
            break

    # Parsing the string from the text-widget to get the corresponding value
    r_TextWidget.getWidgetValue = MethodType(getWidgetIntegerValue, (r_TextWidget, 0))
    g_TextWidget.getWidgetValue = MethodType(getWidgetIntegerValue, (g_TextWidget, 255))
    b_TextWidget.getWidgetValue = MethodType(getWidgetIntegerValue, (b_TextWidget, 0))

    def check_empty_entry(self, event, default_value):
        print (default_value)
        if not self.get_text():
            self.set_text(default_value)

    r_TextWidget.text.connect("focus-out-event", check_empty_entry,"0")
    g_TextWidget.text.connect("focus-out-event", check_empty_entry, "255")
    b_TextWidget.text.connect("focus-out-event", check_empty_entry, "0")

    color_button = builder.get_object("colorbutton")

    def update_color(color_button_):
        # TODO: use Gdk.rgba_to_string instead
        color = color_button_.get_color()

        r_TextWidget.text.set_text(str((color.red/65535)*255))
        g_TextWidget.text.set_text(str((color.green/65535)*255))
        b_TextWidget.text.set_text(str((color.blue/65535)*255))

    color_button.connect("color-set", update_color)
    # TODO: update the color picker when the entry changes
    return builder.get_object("base_table")
