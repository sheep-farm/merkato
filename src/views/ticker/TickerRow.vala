/* SymbolRow.vala
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

[GtkTemplate (ui = "/com/ekonomikas/merkato/MktTickerRow.ui")]
public class Mkt.TickerRow : ListBoxRow {
    public const string ID = "Mkt.TickerRow";

    [GtkChild]
    private unowned Label symbol {get;}

    [GtkChild]
    private unowned Label shortname {get;}

    private Ticker ticker;

    private TickerView ticker_view;

    public TickerRow (Ticker ticker, TickerView ticker_view) {
        this.ticker = ticker;
        this.ticker_view = ticker_view;
        symbol.label = ticker.symbol;
        shortname.label = ticker.shortname;
    }

    [GtkCallback]
    private void on_add_slot () {
        ticker_view.on_add_ticker (ticker);
    }

}
