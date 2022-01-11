/* WatchSymbolViewBox.vala
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

[GtkTemplate (ui = "/com/ekonomikas/merkato/MktSymbolViewBox.ui")]
public class Mkt.SymbolViewBox : Box {
    public const string ID = "Mkt.SymbolViewBox";

    private MainWindow window;

    [GtkChild]
    private unowned ModelButton option_preferences_button;

    [GtkChild]
    private unowned Button add_symbol_view_button;

    [GtkChild]
    private unowned ToggleButton remove_symbol_view_button;

    [GtkChild]
    private unowned MenuButton menu_button;

    [GtkChild]
    private unowned Stack stack;

    [GtkChild]
    private unowned Spinner spinner;

    private SymbolView symbol_view;
    private ApplicationSet app_set;

    public SymbolViewBox (MainWindow window) {
        this.window = window;

        menu_button.add_accelerator (
            "clicked",
            this.window.accel_group,
            Gdk.Key.F10,
            0,
            Gtk.AccelFlags.VISIBLE
        );

        Lookup.singleton ().put (ID, this);

        app_set = (ApplicationSet) Lookup.singleton (). find (ApplicationSet.ID);
        app_set.notify["network-status"].connect (on_network_status);
        app_set.notify["query-status"].connect (on_update_view);
        app_set.symbol_store.items_changed.connect (on_update_view);

        symbol_view = new SymbolView ();

        stack.add_named (new NoSymbolView (), NoSymbolView.ID);
        stack.add_named (new ErrorView (), ErrorView.ID);
        stack.add_named (symbol_view   , SymbolView.ID);

        on_update_view ();
    }

    private void on_network_status () {
        if (app_set.network_status == ApplicationSet.NetworkStatus.IDLE) {
            spinner.stop ();
        } else if (app_set.network_status == ApplicationSet.NetworkStatus.IN_PROGRESS) {
            spinner.start ();
        }
    }

    private void on_update_view () {
        if (app_set.query_status == ApplicationSet.QueryStatus.SUCCESS) {
            var symbol_store_is_empty = app_set.symbol_store.get_n_items () == 0;
            //var symbol_store_only_one = app_set.symbol_store.get_n_items () == 1;
            if (symbol_store_is_empty) {
                stack.set_visible_child_name (NoSymbolView.ID);
                remove_symbol_view_button.active = false;
            } else {
                stack.set_visible_child_name (SymbolView.ID);
            }
            remove_symbol_view_button.visible = !symbol_store_is_empty;
        } else {
            stack.set_visible_child_name (ErrorView.ID);
        }
    }

    [GtkCallback]
    private void on_remove_symbol_view_button_toggled () {
        var children = symbol_view.symbol_list_box.get_children ();
        foreach (Gtk.Widget widget in children) {
            var symbol_row = (SymbolRow) widget;
            symbol_row.remove_symbol_button.visible = remove_symbol_view_button.active;
        }
        app_set.tick_enable = !remove_symbol_view_button.active;
        add_symbol_view_button.set_sensitive (!remove_symbol_view_button.active);
        option_preferences_button.set_sensitive (!remove_symbol_view_button.active);

    }

    [GtkCallback]
    private void on_add_view () {
        remove_symbol_view_button.active = false;
        window.stack_view = TickerViewBox.ID;
    }
}
