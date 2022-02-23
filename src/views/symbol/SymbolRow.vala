/* SymbolRow.vala
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
[GtkTemplate (ui = "/com/ekonomikas/merkato/MktSymbolRow.ui")]
public class Mkt.SymbolRow : Gtk.ListBoxRow {
    [GtkChild]
    private unowned Gtk.Label symbol_label;

    [GtkChild]
    private unowned Gtk.Label shortName_label;

    [GtkChild]
    private unowned Gtk.Label change;

    [GtkChild]
    private unowned Gtk.Label price;

    [GtkChild]
    private unowned Gtk.Label currency;

    [GtkChild]
    private unowned Gtk.Label market;

    [GtkChild]
    private unowned Gtk.Label time;

    [GtkChild]
    private unowned Gtk.EventBox drag_handle;

    [GtkChild]
    public unowned Gtk.Button remove_symbol_button {get;}

    public Mkt.Symbol symbol {get; protected set;}

    private const Gtk.TargetEntry[] TARGET_ENTRIES = {
        {"symbolROW", Gtk.TargetFlags.SAME_APP, 0}
    };

    public SymbolRow (Symbol symbol, bool remove_symbol) {
        this.symbol = symbol;
        this.symbol.notify.connect (on_update);

        Gtk.drag_source_set (
            this.drag_handle, Gdk.ModifierType.BUTTON1_MASK, TARGET_ENTRIES, Gdk.DragAction.MOVE
        );
        Gtk.drag_dest_set (
            this, Gtk.DestDefaults.ALL, TARGET_ENTRIES, Gdk.DragAction.MOVE
        );
        remove_symbol_button.visible = remove_symbol;
        on_update ();
    }

    private void on_update () {
        var s = symbol;
        symbol_label.label = s.symbol;
        shortName_label.label = s.shortName;
        price.label = @"%'.$(s.priceHint)F".printf (s.regularMarketPrice);
        currency.label = s.currency.up ();
        currency.visible = s.currency != ""; // Hide currency for market indices
        change.label = @"%'+.$(s.priceHint)F (%'+.2F%)".printf (s.regularMarketChange, s.regularMarketChangePercent);
        var change_style = change.get_style_context ();
        change_style.remove_class ("profit");
        change_style.remove_class ("loss");
        if (s.regularMarketChange >= 0) {
            change_style.add_class ("profit");
        } else {
            change_style.add_class ("loss");
        }
        var market_style = market.get_style_context ();
        market_style.remove_class ("open");
        market_style.remove_class ("dim-label");
        if (s.isMarketClosed) {
            market.label = (_("Market Closed"));
            market_style.add_class ("dim-label");
            market_style.add_class ("market_close");
        } else {
            market.label = (_("Market Open"));
            market_style.add_class ("market_open");
        }
        if (s.regularMarketTime != null) {
            time.label = s.regularMarketTime.to_local ().format ("%b %e, %X");
        }
    }

    public void on_row_clicked () {
        try {
            Gtk.show_uri_on_window (null,@"https://finance.yahoo.com/quote/$(symbol.symbol)", Gdk.CURRENT_TIME);
        } catch (Error e) {
            warning (@"An error occured when opening the link, message: $(e.message)");
        }
    }

    [GtkCallback]
    private void on_drag_begin (Gtk.Widget widget, Gdk.DragContext context) {
        var row = ((SymbolRow) widget);
        row.get_style_context ().add_class ("drag-begin");
    }

    [GtkCallback]
    private void on_drag_end (Gtk.Widget widget, Gdk.DragContext context) {
        var row = ((SymbolRow) widget);
        row.get_style_context ().remove_class ("drag-begin");
    }

    [GtkCallback]
    private void on_drag_data_get (
        Gdk.DragContext ctx, Gtk.SelectionData selection_data,
        uint info, uint time_
    ) {
        uchar[] data = new uchar[(sizeof (Gtk.Widget))];
        ((Gtk.Widget[]) data)[0] = this.parent;
        selection_data.set (Gdk.Atom.intern_static_string ("symbolROW"), 32, data);
	}

}
