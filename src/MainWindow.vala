/* Main.vala
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

[GtkTemplate (ui = "/com/ekonomikas/merkato/MktMainWindow.ui")]
public class Mkt.MainWindow : Hdy.ApplicationWindow {
    public const string ID = "Mkt.Application";

    [GtkChild]
    public unowned Gtk.AccelGroup accel_group {get;}

    [GtkChild]
    public unowned Gtk.Stack stack;

    public string stack_view {get; set;}

    private ApplicationSet app_set;
    private SymbolViewBox symbol_view_box;
    private TickerViewBox ticker_view_box;

    public MainWindow (Application app) {
        Object (application: app);
        app_set = (ApplicationSet) Lookup.singleton ().find (ApplicationSet.ID);

        default_width  = app_set.window_width;
        default_height = app_set.window_height;

        app_set.load_symbols ();
        app_set.on_tick ();

        symbol_view_box = new SymbolViewBox (this);
        ticker_view_box = new TickerViewBox (this);

        Lookup.singleton ().put (SymbolViewBox.ID, symbol_view_box);
        Lookup.singleton ().put (TickerViewBox.ID, ticker_view_box);

        stack.add_named (symbol_view_box, SymbolViewBox.ID);
        stack.add_named (ticker_view_box, TickerViewBox.ID);

        notify["stack-view"].connect (on_stack_view_slot);

        stack_view = SymbolViewBox.ID;
    }

    private void on_stack_view_slot () {
        stack.set_visible_child_name (stack_view);
    }

    [GtkCallback]
    private bool on_delete_event_listener () {
        int width;
        int height;
        get_size (out width, out height);
        app_set.window_width = width;
        app_set.window_height = height;

        app_set.persist_symbols ();
        return false;
    }

    public void show_about_dialog () {
        var dialog = new AboutDialog (this);
        dialog.run ();
        dialog.destroy ();
    }

    public void show_preferences_dialog () {
        var prefs = new PreferencesWindow (get_application (), this);
        prefs.default_height = app_set.pref_window_height;
        prefs.default_width  = app_set.pref_window_width;
        prefs.present ();
    }
}
