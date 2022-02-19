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
[GtkTemplate (ui = "/com/ekonomikas/merkato/MktSymbolViewBox.ui")]
public class Mkt.SymbolViewBox : Gtk.Box {
    [GtkChild]
    public unowned Gtk.ModelButton option_preferences_button {get;}

    [GtkChild]
    public unowned Gtk.Button add_symbol_view_button {get;}

    [GtkChild]
    public unowned Gtk.ToggleButton remove_symbol_view_button {get;}

    [GtkChild]
    public unowned Gtk.MenuButton menu_button {get;}

    [GtkChild]
    public unowned Gtk.Stack stack {get;}

    [GtkChild]
    public unowned Gtk.Spinner spinner {get;}

    public SymbolViewBox (Mkt.MainWindow window) {
        menu_button.add_accelerator (
            "clicked",
            window.accel_group,
            Gdk.Key.F10,
            0,
            Gtk.AccelFlags.VISIBLE
        );
    }
}
