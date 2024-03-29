/* Application.vala
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
using Mkt;

public class Mkt.Application : Gtk.Application {
    private Controller controller;

    private const ActionEntry[] app_entries = {
        {"about"      , on_about_action},
        {"preferences", on_preferences_action},
        {"quit"       , on_quit_action},
    };

    public Application () {
        Object (
            application_id: Constants.APP_ID,
            flags : ApplicationFlags.FLAGS_NONE
        );
    }

    public override void activate () {
        Gtk.IconTheme.get_default ().add_resource_path ("/icons");
        if (active_window != null) {
            return;
        }
        var provider = new Gtk.CssProvider ();
        provider.load_from_resource ("/ui/Application.css");
        Gtk.StyleContext.add_provider_for_screen (Gdk.Screen.get_default (), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION);

        add_action_entries (app_entries, this);
        set_accels_for_action ("app.quit", {"<control>Q"});
        set_accels_for_action ("app.about", {"<control>A"});
        set_accels_for_action ("app.preferences", {"<control>P"});

        if (controller == null) {
            controller = new Controller (this);
        }
        controller.activate ();
    }

    private void on_quit_action () {
        controller.close_main_window ();
    }

    private void on_about_action () {
        controller.show_about_dialog ();
    }

    private void on_preferences_action () {
        controller.show_preferences_dialog ();
    }

    public static int main (string[] args) {
        // Init internationalization support
        Intl.setlocale (LocaleCategory.ALL, "");

        Intl.bindtextdomain (Constants.APP_ID, Path.build_filename (Constants.APP_INSTALL_PREFIX, "share", "locale"));
        Intl.bind_textdomain_codeset (Constants.APP_ID, "UTF-8");
        Intl.textdomain (Constants.APP_ID);

        var app = new Application ();
        app.startup.connect (() => { Hdy.init (); });
        return app.run (args);
    }
}

