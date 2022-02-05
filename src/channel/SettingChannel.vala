/* SettingChannel.vala
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
using Mkt;

public class SettingChannel : GLib.Object, Channel {
    public const string UUID = "b9b29c10-a258-4d63-ad2b-61a5c3363766";
    public string uuid {get; protected set;}
    public Broadcast.ChannelState state {get; protected set;}

    public enum OrderView {
        CUSTOM,
        TITLE_ASC,
        TITLE_DESC,
        CHANGE_UP,
        CHANGE_DOWN;

        public string to_string () {
            switch (this) {
                case CUSTOM      : return "CUSTOM";
                case TITLE_ASC   : return "TITLE_ASC";
                case TITLE_DESC  : return "TITLE_DESC";
                case CHANGE_UP   : return "CHANGE_UP";
                case CHANGE_DOWN : return "CHANGE_DOWN";
                default          : assert_not_reached();
            }
        }

        public int to_value () {
            switch (this) {
                case CUSTOM      : return 0;
                case TITLE_ASC   : return 1;
                case TITLE_DESC  : return 2;
                case CHANGE_UP   : return 3;
                case CHANGE_DOWN : return 4;
                default          : assert_not_reached();
            }
        }

        public static OrderView from_value (int n) {
            switch (n) {
                case 0 : return CUSTOM;
                case 1 : return TITLE_ASC;
                case 2 : return TITLE_DESC;
                case 3 : return CHANGE_UP;
                case 4 : return CHANGE_DOWN;
                default: assert_not_reached();
            }
        }
    }

    public bool only_open_markets {get; set;}
    public bool dark_theme {get; set;}
    public int pull_interval {get; set;}
    public int window_width {get; set;}
    public int window_height {get; set;}
    public int pref_window_width {get; set;}
    public int pref_window_height {get; set;}
    public OrderView order_view {get; set;}
    public int order_view_ref {get; set;}

    private Settings settings;

    public SettingChannel () {
        uuid = UUID;
        settings = new Settings ("com.ekonomikas.merkato");
    }

    private void on_order_view () {
        order_view_ref = order_view.to_value ();
        connector (Broadcast.ChannelEvent.CHANGE, "order-view-ref", order_view_ref, null);
    }

    private void on_dark_theme () {
        Gtk.Settings.get_default ().gtk_application_prefer_dark_theme = dark_theme;
        connector (Broadcast.ChannelEvent.CHANGE, "dark-theme", dark_theme, null);
    }

    private void on_pull_interval () {
        connector (Broadcast.ChannelEvent.CHANGE, "pull-interval", pull_interval, null);
    }

    private void attach_listeners () {
        notify["pull-interval"].connect (on_pull_interval);
        notify["dark-theme"].connect (on_dark_theme);
        notify["order-view"].connect (on_order_view);

        bind_setting ("dark-theme", "dark_theme");
        bind_setting ("pull-interval", "pull_interval");
        bind_setting ("window-width", "window_width");
        bind_setting ("window-height", "window_height");
        bind_setting ("pref-window-width", "pref_window_width");
        bind_setting ("pref-window-height", "pref_window_height");
        bind_setting ("order-view-ref", "order_view_ref");
    }

    private void bind_setting (string setting_prop, string state_prop) {
        this.settings.bind (setting_prop, this, state_prop, SettingsBindFlags.DEFAULT);
    }

    public void channel_on () {
        state = Broadcast.ChannelState.ON;
        connector (Broadcast.ChannelEvent.ON, "on", null, null);
    }

    public void channel_off () {
        state = Broadcast.ChannelState.OFF;
        connector (Broadcast.ChannelEvent.OFF, "off", null, null);
    }
}
