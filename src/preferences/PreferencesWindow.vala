/* PreferencesWindow.vala
 *
 * Copyright 2021 Flávio Vasconcellos Corrêa
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */
using Mkt, Gtk;

[GtkTemplate (ui = "/com/ekonomikas/merkato/MktPreferencesWindow.ui")]
public class Mkt.PreferencesWindow : Hdy.PreferencesWindow {
    [GtkChild]
    private unowned ComboBoxText pull_interval;
    [GtkChild]
    private unowned RadioButton order_custom;
    [GtkChild]
    private unowned RadioButton order_title_asc;
    [GtkChild]
    private unowned RadioButton order_title_desc;
    [GtkChild]
    private unowned RadioButton order_change_up;
    [GtkChild]
    private unowned RadioButton order_change_down;
    [GtkChild]
    private unowned Switch dark_theme;

    private Preferences preferences;

    public PreferencesWindow (Gtk.Application app, Window parent, Preferences preferences) {
        Object (transient_for: parent, application: app);
        this.preferences = preferences;
        dark_theme.active        = this.preferences.dark_theme;
        pull_interval.active_id  = this.preferences.pull_interval.to_string ();
        order_custom.active      = (this.preferences.order_view == Preferences.OrderView.CUSTOM.to_value ());
        order_title_asc.active   = (this.preferences.order_view == Preferences.OrderView.TITLE_ASC.to_value ());
        order_title_desc.active  = (this.preferences.order_view == Preferences.OrderView.TITLE_DESC.to_value ());
        order_change_up.active   = (this.preferences.order_view == Preferences.OrderView.CHANGE_UP.to_value ());
        order_change_down.active = (this.preferences.order_view == Preferences.OrderView.CHANGE_DOWN.to_value ());
    }

    [GtkCallback]
    private bool on_dark_theme_state_set (Switch sender, bool enabled) {
        this.preferences.dark_theme = enabled;
        return false;
    }

    [GtkCallback]
    private void on_order_button_toggle (ToggleButton sender) {
        if (sender == order_custom) {
            this.preferences.order_view = Preferences.OrderView.CUSTOM.to_value ();
        } else if (sender == order_title_asc) {
            this.preferences.order_view = Preferences.OrderView.TITLE_ASC.to_value ();
        } else if (sender == order_title_desc) {
            this.preferences.order_view = Preferences.OrderView.TITLE_DESC.to_value ();
        } else if (sender == order_change_up) {
            this.preferences.order_view = Preferences.OrderView.CHANGE_UP.to_value ();
        } else if (sender == order_change_down) {
            this.preferences.order_view = Preferences.OrderView.CHANGE_DOWN.to_value ();
        }
    }

    [GtkCallback]
    private void on_pull_interval_changed () {
        this.preferences.pull_interval = int.parse (pull_interval.active_id);
    }

    [GtkCallback]
    private bool on_delete_event () {
        int width;
        int height;
        get_size (out width, out height);
        this.preferences.pref_window_width = width;
        this.preferences.pref_window_height = height;
        return false;
    }
}
