# alerts_view.py
#
# Copyright 2025 Flávio de Vasconcellos Corrêa
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gio, GObject
from datetime import datetime

from .alert import Alert
from .alert_manager import AlertManager


@Gtk.Template(resource_path='/com/github/sheepfarm/merkato/alerts_view.ui')
class AlertsView(Gtk.Box):
    __gtype_name__ = 'AlertsView'

    # Template children
    toolbar = Gtk.Template.Child()
    add_alert_button = Gtk.Template.Child()
    title_widget = Gtk.Template.Child()
    main_box = Gtk.Template.Child()
    empty_state = Gtk.Template.Child()
    alerts_container = Gtk.Template.Child()
    active_group = Gtk.Template.Child()
    active_alerts_list = Gtk.Template.Child()
    triggered_group = Gtk.Template.Child()
    triggered_alerts_list = Gtk.Template.Child()
    disabled_group = Gtk.Template.Child()
    disabled_alerts_list = Gtk.Template.Child()

    __gsignals__ = {
        'add-alert-clicked': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def __init__(self, alert_manager: AlertManager = None, **kwargs):
        super().__init__(**kwargs)

        self.alert_manager = alert_manager

        # Connect signals
        self.add_alert_button.connect('clicked', self.on_add_alert_clicked)

        # Create actions
        self._create_actions()

        # If there's an alert_manager, connect signals
        if self.alert_manager:
            self.alert_manager.connect('alerts-changed', self.on_alerts_changed)
            self.refresh()

    def _create_actions(self):
        """Create view actions."""
        action_group = Gio.SimpleActionGroup()

        clear_triggered_action = Gio.SimpleAction.new('clear-triggered', None)
        clear_triggered_action.connect('activate', self.on_clear_triggered)
        action_group.add_action(clear_triggered_action)

        clear_all_action = Gio.SimpleAction.new('clear-all', None)
        clear_all_action.connect('activate', self.on_clear_all)
        action_group.add_action(clear_all_action)

        self.insert_action_group('alerts', action_group)

    def set_alert_manager(self, alert_manager: AlertManager):
        """
        Set the AlertManager.

        Args:
            alert_manager: AlertManager instance
        """
        self.alert_manager = alert_manager
        self.alert_manager.connect('alerts-changed', self.on_alerts_changed)
        self.refresh()

    def on_add_alert_clicked(self, button):
        """Callback for 'Add Alert' button in toolbar."""
        self.emit('add-alert-clicked')

    def on_alerts_changed(self, alert_manager=None):
        """Callback when alerts change."""
        self.refresh()

    def refresh(self):
        """Update the alerts view."""
        if not self.alert_manager:
            return

        # Clear lists
        self._clear_list(self.active_alerts_list)
        self._clear_list(self.triggered_alerts_list)
        self._clear_list(self.disabled_alerts_list)

        # Get alerts
        active = []
        triggered = []
        disabled = []

        for alert in self.alert_manager.get_all_alerts():
            if not alert.enabled:
                disabled.append(alert)
            elif alert.is_triggered():
                triggered.append(alert)
            else:
                active.append(alert)

        # Update title
        total = len(active) + len(triggered) + len(disabled)
        if total == 0:
            self.title_widget.set_subtitle("No alerts")
        elif total == 1:
            self.title_widget.set_subtitle("1 alert")
        else:
            self.title_widget.set_subtitle(f"{total} alerts")

        # Show/hide empty state
        has_alerts = total > 0
        self.empty_state.set_visible(not has_alerts)
        self.alerts_container.set_visible(has_alerts)

        if not has_alerts:
            return

        # Populate lists
        if active:
            self.active_group.set_visible(True)
            for alert in active:
                row = self._create_alert_row(alert)
                self.active_alerts_list.append(row)
        else:
            self.active_group.set_visible(False)

        if triggered:
            self.triggered_group.set_visible(True)
            for alert in triggered:
                row = self._create_alert_row(alert)
                self.triggered_alerts_list.append(row)
        else:
            self.triggered_group.set_visible(False)

        if disabled:
            self.disabled_group.set_visible(True)
            for alert in disabled:
                row = self._create_alert_row(alert)
                self.disabled_alerts_list.append(row)
        else:
            self.disabled_group.set_visible(False)

    def _clear_list(self, listbox: Gtk.ListBox):
        """Clear a ListBox."""
        while True:
            row = listbox.get_row_at_index(0)
            if row is None:
                break
            listbox.remove(row)

    def _create_alert_row(self, alert: Alert) -> Adw.ActionRow:
        """
        Create an ActionRow for an alert.

        Args:
            alert: Alert object

        Returns:
            Configured ActionRow
        """
        row = Adw.ActionRow()
        row.alert = alert  # Store reference

        # Title: SYMBOL - Type
        title = f"{alert.symbol} - {alert.get_display_type()} ${alert.target_price:.2f}"
        row.set_title(title)

        # Subtitle with status
        subtitle_parts = []

        # Status
        status = alert.get_status_display()
        subtitle_parts.append(f"Status: {status}")

        # Current price if available
        if alert.last_price > 0:
            subtitle_parts.append(f"Last: ${alert.last_price:.2f}")

        # Trigger date if triggered
        if alert.is_triggered() and alert.triggered_at:
            try:
                dt = datetime.fromisoformat(alert.triggered_at)
                date_str = dt.strftime("%Y-%m-%d %H:%M")
                subtitle_parts.append(f"Triggered: {date_str}")
            except:
                pass

        row.set_subtitle(" • ".join(subtitle_parts))

        # Prefix icon based on type
        if alert.alert_type == 'above':
            icon_name = 'go-up-symbolic'
        else:
            icon_name = 'go-down-symbolic'

        icon = Gtk.Image.new_from_icon_name(icon_name)
        icon.set_pixel_size(16)
        row.add_prefix(icon)

        # Action buttons
        actions_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        # Toggle enabled/disabled button
        if alert.enabled:
            toggle_btn = Gtk.Button(icon_name='media-playback-pause-symbolic')
            toggle_btn.set_tooltip_text("Disable alert")
            toggle_btn.add_css_class('flat')
            toggle_btn.connect('clicked', self.on_toggle_alert, alert)
            actions_box.append(toggle_btn)
        else:
            toggle_btn = Gtk.Button(icon_name='media-playback-start-symbolic')
            toggle_btn.set_tooltip_text("Enable alert")
            toggle_btn.add_css_class('flat')
            toggle_btn.connect('clicked', self.on_toggle_alert, alert)
            actions_box.append(toggle_btn)

        # Reset button if triggered
        if alert.is_triggered():
            reset_btn = Gtk.Button(icon_name='view-refresh-symbolic')
            reset_btn.set_tooltip_text("Reset alert")
            reset_btn.add_css_class('flat')
            reset_btn.connect('clicked', self.on_reset_alert, alert)
            actions_box.append(reset_btn)

        # Delete button
        delete_btn = Gtk.Button(icon_name='user-trash-symbolic')
        delete_btn.set_tooltip_text("Delete alert")
        delete_btn.add_css_class('flat')
        delete_btn.add_css_class('destructive-action')
        delete_btn.connect('clicked', self.on_delete_alert, alert)
        actions_box.append(delete_btn)

        row.add_suffix(actions_box)
        row.set_activatable(False)

        return row

    def on_toggle_alert(self, button, alert: Alert):
        """Toggle enabled/disabled."""
        alert.enabled = not alert.enabled
        self.alert_manager.update_alert(alert)

    def on_reset_alert(self, button, alert: Alert):
        """Reset alert (clear triggered state)."""
        alert.reset()
        self.alert_manager.update_alert(alert)

    def on_delete_alert(self, button, alert: Alert):
        """Delete alert."""
        # TODO: Add confirmation
        self.alert_manager.remove_alert(alert.alert_id)

    def on_clear_triggered(self, action, param):
        """Remove all triggered alerts."""
        if not self.alert_manager:
            return

        triggered = self.alert_manager.get_triggered_alerts()
        for alert in triggered:
            self.alert_manager.remove_alert(alert.alert_id)

    def on_clear_all(self, action, param):
        """Remove all alerts."""
        if not self.alert_manager:
            return

        # TODO: Add confirmation
        self.alert_manager.clear()
