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

    private ApplicationSet app_set;

    public PreferencesWindow (Gtk.Application app, Window parent) {
        Object (transient_for: parent, application: app);
        app_set = (ApplicationSet) Lookup.singleton ().find (ApplicationSet.ID);
        dark_theme.active        = app_set.dark_theme;
        pull_interval.active_id = app_set.pull_interval.to_string ();
        order_custom.active = (app_set.order_view == ApplicationSet.OrderView.CUSTOM);
        order_title_asc.active = (app_set.order_view == ApplicationSet.OrderView.TITLE_ASC);
        order_title_desc.active = (app_set.order_view == ApplicationSet.OrderView.TITLE_DESC);
        order_change_up.active = (app_set.order_view == ApplicationSet.OrderView.CHANGE_UP);
        order_change_down.active = (app_set.order_view == ApplicationSet.OrderView.CHANGE_DOWN);
    }

    [GtkCallback]
    private bool on_dark_theme_state_set (Switch sender, bool enabled) {
        app_set.dark_theme = enabled;
        return false;
    }

    [GtkCallback]
    private void on_order_button_toggle (ToggleButton sender) {
        if (sender == order_custom) {
            app_set.order_view = ApplicationSet.OrderView.CUSTOM;
        } else
        if (sender == order_title_asc) {
            app_set.order_view = ApplicationSet.OrderView.TITLE_ASC;
        } else
        if (sender == order_title_desc) {
            app_set.order_view = ApplicationSet.OrderView.TITLE_DESC;
        } else
        if (sender == order_change_up) {
            app_set.order_view = ApplicationSet.OrderView.CHANGE_UP;
        } else
        if (sender == order_change_down) {
            app_set.order_view = ApplicationSet.OrderView.CHANGE_DOWN;
        }
    }

    [GtkCallback]
    private void on_pull_interval_changed () {
        app_set.pull_interval = int.parse (pull_interval.active_id);
    }

    [GtkCallback]
    private bool on_delete_event () {
        int width;
        int height;
        get_size (out width, out height);
        app_set.pref_window_width = width;
        app_set.pref_window_height = height;
        return false;
    }
}
