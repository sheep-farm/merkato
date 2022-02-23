/* Preferences.vala
 *
 * Copyright 2021 - 2022 Flávio Vasconcellos Corrêa
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
public class Mkt.Preferences : GLib.Object {
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
    public bool dark_theme {get; set;}
    public int pull_interval {get; set;}
    public int window_width {get; set;}
    public int window_height {get; set;}
    public int pref_window_width {get; set;}
    public int pref_window_height {get; set;}
    public int order_view {get; set;}

    private Settings settings;

    public Preferences () {
        settings = new Settings ("com.ekonomikas.merkato");
        attach_listeners ();
    }

    private void attach_listeners () {
        bind_setting ("dark-theme", "dark_theme");
        bind_setting ("pull-interval", "pull_interval");
        bind_setting ("order-view", "order_view");
        bind_setting ("window-width", "window_width");
        bind_setting ("window-height", "window_height");
        bind_setting ("pref-window-width", "pref_window_width");
        bind_setting ("pref-window-height", "pref_window_height");
    }

    private void bind_setting (string setting_prop, string state_prop) {
        settings.bind (setting_prop, this, state_prop, SettingsBindFlags.DEFAULT);
    }
}
