# -*- coding: utf-8 -*-
# Pitivi video editor
# Copyright (c) 2017, Suhas Nayak <suhas2go@gmail.com>
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
from unittest import mock

from gi.repository import Gdk
from gi.repository import GES
from gi.repository import Gtk

from pitivi.effects import EffectsPropertiesManager
from pitivi.effects import PROPS_TO_IGNORE
from pitivi.utils.widgets import DynamicWidget
from pitivi.utils.widgets import GstElementSettingsWidget
from pitivi.utils.widgets import NumericWidget
from tests import common


class TestCustomEffectUI(common.TestCase):

    def create_alpha_widget(self, widgets):
        self.builder = Gtk.Builder()
        # self.builder.add_from_file(os.path.join(os.path.dirname(__file__), "plugins", "test_alpha.ui"))
        self.builder.add_objects_from_file(os.path.join(os.path.dirname(__file__), "plugins", "test_alpha.ui"), widgets)
        self.element_settings_widget.mapBuilder(self.builder)
        return self.builder.get_object("GstAlpha::black-sensitivity")

    def register_alpha_widget(self, widgets):
        self.alpha_effect = GES.Effect.new("alpha")
        self.prop_name = "black-sensitivity"
        _, _, self.prop = self.alpha_effect.lookup_child(self.prop_name)

        self.effects_prop_manager = EffectsPropertiesManager(self.app)
        self.element_settings_widget = GstElementSettingsWidget()
        self.element_settings_widget.setElement(self.alpha_effect, PROPS_TO_IGNORE)

        with mock.patch("pitivi.utils.custom_effect_widgets.create_alpha_widget") as MockClass:
            MockClass.return_value = self.create_alpha_widget(widgets)
            self.effects_prop_manager.emit('create-widget', self.element_settings_widget, self.alpha_effect)
        self.effects_prop_manager._connectAllWidgetCallbacks(self.element_settings_widget, self.alpha_effect)
        self.effects_prop_manager._postConfiguration(self.alpha_effect, self.element_settings_widget)

    def test_wrapping(self):
        self.app = common.create_pitivi_mock()
        self.register_alpha_widget(("black_sens_adjustment","GstAlpha::black-sensitivity"))

        # Check if the widget is wrapped correctly
        wrapped_spin_button = self.element_settings_widget.properties[self.prop]
        self.assertTrue(isinstance(wrapped_spin_button, DynamicWidget))
        self.assertTrue(isinstance(wrapped_spin_button, NumericWidget))

        # Check if the wrapper has the correct default value
        self.assertEqual(self.prop.default_value, wrapped_spin_button.getWidgetDefault())

        # Check if the callbacks are functioning
        wrapped_spin_button.setWidgetValue(80)
        _, prop_value = self.alpha_effect.get_child_property(self.prop_name)
        self.assertEqual(prop_value, wrapped_spin_button.getWidgetValue())

    def test_prop_keyframe(self):
        uri = common.get_sample_uri("tears_of_steel.webm")
        asset = GES.UriClipAsset.request_sync(uri)
        ges_clip = asset.extract()

        # Add the clip to a timeline so it gets tracks.
        timeline = common.create_timeline_container()
        self.app = timeline.app
        ges_timeline = timeline.ges_timeline
        ges_timeline.append_layer()
        ges_layer, = ges_timeline.get_layers()
        ges_layer.add_clip(ges_clip)

        self.register_alpha_widget(
            ("black_sens_adjustment", "GstAlpha::black-sensitivity", "GstAlpha::black-sensitivity::keyframe"))
        ges_clip.add(self.alpha_effect)
        track_element = self.element_settings_widget._GstElementSettingsWidget__get_track_element_of_same_type(
            self.alpha_effect)
        prop_keyframe_button = \
        list(self.element_settings_widget._GstElementSettingsWidget__widgets_by_keyframe_button.keys())[0]

        # Control the self.prop property on the timeline
        prop_keyframe_button.set_active(True)
        self.assertEqual(track_element.ui_element._TimelineElement__controlledProperty, self.prop)
        # Revert to controlling the default property
        prop_keyframe_button.set_active(False)
        self.assertNotEqual(track_element.ui_element._TimelineElement__controlledProperty, self.prop)

    def test_prop_reset(self):
        self.app = common.create_pitivi_mock()
        self.register_alpha_widget(
            ("black_sens_adjustment", "GstAlpha::black-sensitivity", "GstAlpha::black-sensitivity::reset", "image1"))
        wrapped_spin_button = self.element_settings_widget.properties[self.prop]
        wrapped_spin_button.setWidgetValue(80)
        _, prop_value = self.alpha_effect.get_child_property(self.prop_name)
        self.assertEqual(prop_value, wrapped_spin_button.getWidgetValue())
        # Reset the value of the property to default
        prop_reset_button = \
        list(self.element_settings_widget._GstElementSettingsWidget__widgets_by_reset_button.keys())[0]
        prop_reset_button.clicked()
        _, prop_value = self.alpha_effect.get_child_property(self.prop_name)
        self.assertEqual(self.prop.default_value, prop_value)
