/* TickerViewBox.vala
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

[GtkTemplate (ui = "/com/ekonomikas/merkato/MktTickerViewBox.ui")]
public class Mkt.TickerViewBox : Box  {
    public const string ID = "Mkt.TickerViewBox";

    private MainWindow window;

    [GtkChild]
    private unowned MenuButton menu_button;

    [GtkChild]
    private unowned SearchEntry search_entry;

    [GtkChild]
    private unowned Stack stack;

    [GtkChild]
    private unowned Spinner spinner;

    private TickerView ticker_view;
    private ApplicationSet  app_set;
    public  Gee.List<Ticker> ticker_list {get; set;}

    public TickerViewBox (MainWindow window) {
        Lookup.singleton ().put (ID, this);
        this.window = window;
        menu_button.add_accelerator (
            "clicked",
            window.accel_group,
            Gdk.Key.F10,
            0,
            Gtk.AccelFlags.VISIBLE
        );
        window.notify["stack-view"].connect (on_window_stack_view_slot);
        app_set = (ApplicationSet) Lookup.singleton(). find (ApplicationSet.ID);
        app_set.notify["network-status"].connect (on_network_status_slot);

        ticker_view = new TickerView (this);
        ticker_view.notify["ticker-list"].connect (on_update_view);
        stack.add_named(new NoTickerView (), NoTickerView.ID);
        stack.add_named(new ErrorView (), ErrorView.ID);

        stack.add_named(ticker_view, TickerView.ID);
        on_window_stack_view_slot ();
        on_update_view ();
    }

    private void on_network_status_slot () {
        if (app_set.network_status == ApplicationSet.NetworkStatus.IDLE) {
            spinner.stop ();
        } else if (app_set.network_status == ApplicationSet.NetworkStatus.IN_PROGRESS) {
            spinner.start ();
        }
    }

    private void on_update_view () {
        if (ticker_view.ticker_list.size == 0) {
            stack.set_visible_child_name (NoTickerView.ID);
        } else {
            stack.set_visible_child_name (TickerView.ID);
        }
    }

    public void on_window_stack_view_slot () {
        if (window.stack_view == ID) {
            search_entry.grab_focus ();
            ticker_list = new Gee.ArrayList<Ticker> ();
            search_entry.text = "";
            ticker_view.reset ();
        }
    }

    [GtkCallback]
    private void on_search_active_slot () {
        var client = (YahooFinanceClient) Lookup.singleton ().find (YahooFinanceClient.ID);
         client.search_tickers.begin (search_entry.text, (obj, res) => {
            ticker_view.ticker_list = client.search_tickers.end (res);
        });
        on_update_view ();
    }

    [GtkCallback]
    private void on_stop_search_slot () {
        if (search_entry.text.length > 0) {
            search_entry.text = "";
        }
        on_search_active_slot ();
    }

    [GtkCallback]
    private void on_search_changed_slot () {
    }

    [GtkCallback]
    private void on_go_back_slot () {
        window.stack_view = SymbolViewBox.ID;
    }
}
