/* SymbolView.vala
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

[GtkTemplate (ui = "/com/ekonomikas/merkato/MktSymbolView.ui")]
public class Mkt.SymbolView : Box {
    public const string ID = "Mkt.SymbolView";

    [GtkChild]
    public unowned Gtk.ListBox symbol_list_box;

    private ApplicationSet app_set = (ApplicationSet) Lookup.singleton (). find (ApplicationSet.ID);

    public SymbolView () {
        Lookup.singleton ().put (ID, this);
        symbol_list_box.bind_model (app_set.symbol_store, create_row_widget);
    }

    private Widget create_row_widget (Object item) {
        return new SymbolRow.from_object ((Symbol) item);
    }

    [GtkCallback]
    private void on_symbol_list_box_row_activated (Gtk.ListBox box, Gtk.ListBoxRow row) {
        ((SymbolRow) row).on_row_clicked ();
    }
}
