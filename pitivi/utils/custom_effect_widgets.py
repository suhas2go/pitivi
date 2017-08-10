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
import math
import os
from colorsys import rgb_to_hsv
from types import MethodType

from gi.repository import Gdk
from gi.repository import GObject
from gi.repository import Gtk

from pitivi import configure
from pitivi.utils.loggable import Loggable
from pitivi.utils.widgets import ColorPickerButton

CUSTOM_WIDGETS_DIR = os.path.join(configure.get_ui_dir(), "customwidgets")


def setup_custom_effect_widgets(effect_prop_manager):
    effect_prop_manager.connect("create_widget", create_custom_widget_cb)
    effect_prop_manager.connect("create_property_widget", create_custom_prop_widget_cb)


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
    default_path = os.path.join(CUSTOM_WIDGETS_DIR, effect_name + ".ui")

    # Write individual effect callbacks here
    if effect_name == "alpha":
        widget = create_alpha_widget(effect_widget, effect)
        return widget
    elif effect_name == "frei0r-filter-3-point-color-balance":
        widget = create_3point_color_balance_widget(effect_widget, effect)
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
    builder = setup_from_ui_file(element_setting_widget, os.path.join(CUSTOM_WIDGETS_DIR, "alpha.ui"))

    # Additional Setup

    # Color button has to be connected manually!

    r_NumericWidget = element_setting_widget.get_widget_of_prop("target-r")
    g_NumericWidget = element_setting_widget.get_widget_of_prop("target-g")
    b_NumericWidget = element_setting_widget.get_widget_of_prop("target-b")

    color_button = builder.get_object("colorbutton")

    def color_set_cb(color_button):
        # TODO: use Gdk.rgba_to_string instead
        color = color_button.get_color()

        r_NumericWidget.setWidgetValue(int((color.red / 65535) * 255))
        g_NumericWidget.setWidgetValue(int((color.green / 65535) * 255))
        b_NumericWidget.setWidgetValue(int((color.blue / 65535) * 255))

    color_button.connect("color-set", color_set_cb)

    # All modes other than custom RGB chroma keying are useless to us.
    # "ALPHA_METHOD_CUSTOM" corresponds to "3"
    Loggable().debug("Setting alpha's method to 3 (custom RGB chroma keying)")
    element.set_child_property("method", 3)
    return builder.get_object("base_table")


def create_custom_alpha_prop_widget(element_setting_widget, element, prop, prop_value):
    """Not implemented yet."""
    # In the auto-generated UI, replace a property widget with a custom one
    return None


class CustomGtkHSV(Gtk.HSV):
    """Hackish version of the GtkHSV widget which allows to keep track of color."""

    def __init__(self, default_r=0, default_g=0, default_b=0):
        Gtk.HSV.__init__(self)
        self.r_adjustment = Gtk.Adjustment(default_r, 0, 255, 1, 1, 0)
        self.g_adjustment = Gtk.Adjustment(default_g, 0, 255, 1, 1, 0)
        self.b_adjustment = Gtk.Adjustment(default_b, 0, 255, 1, 1, 0)
        self.r_handler_id = self.r_adjustment.connect("value-changed", self.value_changed_cb)
        self.g_handler_id = self.g_adjustment.connect("value-changed", self.value_changed_cb)
        self.b_handler_id = self.b_adjustment.connect("value-changed", self.value_changed_cb)
        self.wheel_handler_id = self.connect("changed", self.changed_cb)

    def value_changed_cb(self, unused_arg):
        """Handles color adjustment changes updating the wheel."""
        self.handler_block(self.wheel_handler_id)
        try:
            hsv_color = self.get_color()
            rgb_color = self.to_rgb(hsv_color.h, hsv_color.s, hsv_color.v)
            old_r = math.ceil(rgb_color.r * 255)
            old_g = math.ceil(rgb_color.g * 255)
            old_b = math.ceil(rgb_color.b * 255)
            new_r = self.r_adjustment.get_value()
            new_g = self.g_adjustment.get_value()
            new_b = self.b_adjustment.get_value()
            if (new_r, new_g, new_b) != (old_r, old_g, old_b):
                new_h, new_s, new_v = rgb_to_hsv(new_r / 255, new_g / 255, new_b / 255)
                self.set_color(new_h, new_s, new_v)
        finally:
            self.handler_unblock(self.wheel_handler_id)

    def changed_cb(self, unused_arg):
        """Handles changes updating the color adjustments."""
        self.r_adjustment.handler_block(self.r_handler_id)
        self.g_adjustment.handler_block(self.g_handler_id)
        self.b_adjustment.handler_block(self.b_handler_id)
        try:
            hsv_color = self.get_color()
            rgb_color = self.to_rgb(hsv_color.h, hsv_color.s, hsv_color.v)
            new_r = math.ceil(rgb_color.r * 255)
            new_g = math.ceil(rgb_color.g * 255)
            new_b = math.ceil(rgb_color.b * 255)
            old_r = self.r_adjustment.get_value()
            old_g = self.g_adjustment.get_value()
            old_b = self.b_adjustment.get_value()
            if (new_r, new_g, new_b) != (old_r, old_g, old_b):
                self.r_adjustment.set_value(new_r)
                self.g_adjustment.set_value(new_g)
                self.b_adjustment.set_value(new_b)
        finally:
            self.r_adjustment.handler_unblock(self.r_handler_id)
            self.g_adjustment.handler_unblock(self.g_handler_id)
            self.b_adjustment.handler_unblock(self.b_handler_id)


def create_3point_color_balance_widget(element_setting_widget, element):
    builder = setup_from_ui_file(element_setting_widget, os.path.join(CUSTOM_WIDGETS_DIR, "frei0r.ui"))
    element_setting_widget.mapBuilder(builder)
    color_balance_grid = builder.get_object("base_table")

    shadows_wheel = CustomGtkHSV(0, 0, 0)
    midtones_wheel = CustomGtkHSV(128, 128, 128)
    highlights_wheel = CustomGtkHSV(255, 255, 255)

    color_balance_grid.attach(shadows_wheel, 1, 0, 1, 1)
    color_balance_grid.attach(midtones_wheel, 2, 0, 1, 1)
    color_balance_grid.attach(highlights_wheel, 3, 0, 1, 1)

    shadows_color_picker_button = ColorPickerButton(0, 0, 0)
    midtones_color_picker_button = ColorPickerButton(128, 128, 128)
    highlights_color_picker_button = ColorPickerButton(255, 255, 255)

    color_balance_grid.attach(shadows_color_picker_button, 1, 1, 1, 1)
    color_balance_grid.attach(midtones_color_picker_button, 2, 1, 1, 1)
    color_balance_grid.attach(highlights_color_picker_button, 3, 1, 1, 1)

    # Manually handle the custom part of the UI.
    # 1) Connecting the color wheel widgets
    # 2) Scale values between to be shown on the UI vs
    #    the actual property values (RGB values here).

    black_r = element_setting_widget.get_widget_of_prop("black-color-r")
    black_g = element_setting_widget.get_widget_of_prop("black-color-g")
    black_b = element_setting_widget.get_widget_of_prop("black-color-b")

    gray_r = element_setting_widget.get_widget_of_prop("gray-color-r")
    gray_g = element_setting_widget.get_widget_of_prop("gray-color-g")
    gray_b = element_setting_widget.get_widget_of_prop("gray-color-b")

    white_r = element_setting_widget.get_widget_of_prop("white-color-r")
    white_g = element_setting_widget.get_widget_of_prop("white-color-g")
    white_b = element_setting_widget.get_widget_of_prop("white-color-b")

    # The UI widget values need to scaled back to the property.
    # Since for RGB vlaues 0-255 format is used in the UI
    # where as the property values are actually between 0-1.

    def getWidgetScaledValue(self):
        return self.adjustment.get_value() / 255

    black_r.getWidgetValue = MethodType(getWidgetScaledValue, black_r)
    black_g.getWidgetValue = MethodType(getWidgetScaledValue, black_g)
    black_b.getWidgetValue = MethodType(getWidgetScaledValue, black_b)

    gray_r.getWidgetValue = MethodType(getWidgetScaledValue, gray_r)
    gray_g.getWidgetValue = MethodType(getWidgetScaledValue, gray_g)
    gray_b.getWidgetValue = MethodType(getWidgetScaledValue, gray_b)

    white_r.getWidgetValue = MethodType(getWidgetScaledValue, white_r)
    white_b.getWidgetValue = MethodType(getWidgetScaledValue, white_b)
    white_g.getWidgetValue = MethodType(getWidgetScaledValue, white_g)

    # Bind all the widget color properties to synchronize them

    def bind_color_widgets(spinbutton_r, spinbutton_g, spinbutton_b, color_wheel, color_picker_button):
        color_wheel.r_adjustment.bind_property("value", spinbutton_r.adjustment, "value", GObject.BindingFlags.BIDIRECTIONAL)
        color_wheel.g_adjustment.bind_property("value", spinbutton_g.adjustment, "value", GObject.BindingFlags.BIDIRECTIONAL)
        color_wheel.b_adjustment.bind_property("value", spinbutton_b.adjustment, "value", GObject.BindingFlags.BIDIRECTIONAL)
        color_wheel.r_adjustment.bind_property("value", color_picker_button, "color_r", GObject.BindingFlags.BIDIRECTIONAL)
        color_wheel.g_adjustment.bind_property("value", color_picker_button, "color_g", GObject.BindingFlags.BIDIRECTIONAL)
        color_wheel.b_adjustment.bind_property("value", color_picker_button, "color_b", GObject.BindingFlags.BIDIRECTIONAL)

    bind_color_widgets(black_r, black_g, black_b, shadows_wheel, shadows_color_picker_button)
    bind_color_widgets(gray_r, gray_g, gray_b, midtones_wheel, midtones_color_picker_button)
    bind_color_widgets(white_r, white_g, white_b, highlights_wheel, highlights_color_picker_button)

    # Initialize the wheels with the correct values

    shadows_wheel.set_color(0, 0, 0)
    midtones_wheel.set_color(0, 0, 0.5)
    highlights_wheel.set_color(0, 0, 1)

    return color_balance_grid
