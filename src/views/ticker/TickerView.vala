/* TickerView.vala
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

[GtkTemplate (ui = "/com/ekonomikas/merkato/MktTickerView.ui")]
public class Mkt.TickerView : Box {
    public const string ID = "Mkt.TickerView";

    [GtkChild]
    private unowned ListBox ticker_list_box;

    private TickerViewBox owner;

    private ApplicationSet app_set;

    public Gee.Collection<Ticker> ticker_list {get; set;}

    public GLib.ListStore ticker_store;

    public TickerView (TickerViewBox owner) {
        this.owner = owner;
        app_set = (ApplicationSet) Lookup.singleton ().find (ApplicationSet.ID);
        ticker_store = new GLib.ListStore (typeof (Ticker));
        ticker_list = new Gee.ArrayList<Ticker> ();
        ticker_list_box.bind_model (ticker_store, create_ticker_row_widget);
        notify["ticker-list"].connect (on_ticker_list_change_slot);

    }

    public void reset () {
        ticker_list = new Gee.ArrayList<Ticker> ();
    }

    private Widget create_ticker_row_widget (Object item) {
        return new TickerRow ((Ticker) item, this);
    }

    private void on_ticker_list_change_slot () {
        ticker_store.remove_all ();
        foreach (var t in ticker_list) {
            ticker_store.append (t);
        }
    }

    public void on_add_ticker (Ticker ticker) {
        var yahoo_finance = (YahooFinanceClient) Lookup.singleton ().find (YahooFinanceClient.ID);

        yahoo_finance.search_symbols.begin (ticker.symbol, (obj, res) => {
            var result_list = yahoo_finance.search_symbols.end (res);
            var symbol = result_list.@get(0);
            if (symbol != null) {
                uint pos;
                EqualFunc<Symbol> equal_func = (a, b) => { return a.symbol == b.symbol;};
                if (!app_set.symbol_store.find_with_equal_func (symbol, equal_func, out pos)) {
                    app_set.symbol_store.append (symbol);
                    app_set.on_sort_symbols ();
                }
            }
        });
        Gee.Collection<Ticker> tmp_list = new Gee.ArrayList<Ticker> ();
        foreach (var t in ticker_list) {
            if (t.symbol != ticker.symbol) {
                tmp_list.add (t);
            }
        }
        ticker_list = tmp_list;
    }
}
