/* Application.vala
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

public class Mkt.Application : Gtk.Application {
    public const string ID = "Mkt.Application";

    public const string APP_TITLE = "Merkato";

    private MainWindow window;

    private const ActionEntry[] app_entries =
    {
        {"about"      , on_about_action_slot},
        {"preferences", on_preferences_action_slot},
        {"quit"       , on_quit_slot        },
    };

    public Application () {
        Object (
            application_id: Constants.APP_ID,
            flags : ApplicationFlags.FLAGS_NONE
        );
    }

    public override void activate () {
        Lookup.singleton ().put (ID, this);
        Lookup.singleton ().put (YahooFinanceClient.ID, new YahooFinanceClient ());
        Lookup.singleton ().put (SymbolPersistence.ID , new SymbolPersistence ());
        Lookup.singleton ().put (ApplicationSet.ID    , new ApplicationSet ());

        if (active_window != null) {
            return;
        }
        var provider = new Gtk.CssProvider ();
        provider.load_from_resource ("/com/ekonomikas/merkato/Application.css");
        Gtk.StyleContext.add_provider_for_screen (
            Gdk.Screen.get_default (),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        );

        add_action_entries (app_entries, this);
        set_accels_for_action ("app.quit", {"<control>Q"});
        set_accels_for_action ("app.about", {"<control>A"});
        set_accels_for_action ("app.preferences", {"<control>P"});

        window = new MainWindow (this);
        window.present ();
    }

    private void on_quit_slot () {
        this.window.close ();
    }

    private void on_about_action_slot () {
        window.show_about_dialog ();
    }

    private void on_preferences_action_slot () {
        window.show_preferences_dialog ();
    }

    public static int main (string[] args) {
        // Init internationalization support
        Intl.setlocale (LocaleCategory.ALL, "");
        string langpack_dir = Path.build_filename (Constants.APP_INSTALL_PREFIX, "share", "locale");

        Intl.bindtextdomain (Constants.APP_ID, langpack_dir);
        Intl.bind_textdomain_codeset (Constants.APP_ID, "UTF-8");
        Intl.textdomain (Constants.APP_ID);

        var app = new Application ();
        app.startup.connect (() => { Hdy.init (); });
        return app.run (args);
    }
}

