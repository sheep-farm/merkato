/* ApplicationSet.vala
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

public class Mkt.ApplicationSet : Object {
    public const string ID = "Mkt.ApplicationSet";

    public enum NetworkStatus {
        IDLE,
        IN_PROGRESS,
    }

    public enum QueryStatus {
        SUCCESS,
        FAILURE
    }

    public enum OrderView {
        CUSTOM,
        TITLE_ASC,
        TITLE_DESC,
        CHANGE_UP,
        CHANGE_DOWN;

        public string to_string () {
            switch (this) {
                case CUSTOM      : return "CUSTOM";
                case TITLE_ASC   : return "TITLE_ASC";
                case TITLE_DESC  : return "TITLE_DESC";
                case CHANGE_UP   : return "CHANGE_UP";
                case CHANGE_DOWN : return "CHANGE_DOWN";
                default          : assert_not_reached();
            }
        }

        public int to_value () {
            switch (this) {
                case CUSTOM      : return 0;
                case TITLE_ASC   : return 1;
                case TITLE_DESC  : return 2;
                case CHANGE_UP   : return 3;
                case CHANGE_DOWN : return 4;
                default          : assert_not_reached();
            }
        }

        public static OrderView from_value (int n) {
            switch (n) {
                case 0 : return CUSTOM;
                case 1 : return TITLE_ASC;
                case 2 : return TITLE_DESC;
                case 3 : return CHANGE_UP;
                case 4 : return CHANGE_DOWN;
                default: assert_not_reached();
            }
        }
    }

    private SymbolPersistence persistence;
    private CompareDataFunc<Symbol> compare_symbols_name_asc;
    private CompareDataFunc<Symbol> compare_symbols_name_desc;
    private CompareDataFunc<Symbol> compare_symbols_market_change_up;
    private CompareDataFunc<Symbol> compare_symbols_market_change_down;
    private Settings settings;
    private uint ? timeout_id = null;

    public NetworkStatus network_status {get; set;}
    public QueryStatus query_status {get; set;}
    public OrderView order_view {get; set;}
    public int order_view_ref {get;set;}
    public int pull_interval {get; set;}
    public bool tick_enable {get; set;}
    public bool dark_theme {get; set;}
    public int window_width {get; set;}
    public int window_height {get; set;}
    public int pref_window_width {get; set;}
    public int pref_window_height {get; set;}

    public ListStore symbol_store {get; set;}

    public ApplicationSet () {
        settings = new Settings ("com.ekonomikas.merkato");
        persistence = (SymbolPersistence) Lookup.singleton ().find (SymbolPersistence.ID);
        symbol_store = new GLib.ListStore (typeof (Symbol));
        attach_listeners ();
        init_default_values ();
        on_dark_theme ();
    }

    private void init_default_values () {
        network_status = NetworkStatus.IDLE;
        order_view = OrderView.from_value (order_view_ref);
        tick_enable = true;
        compare_symbols_name_asc = (a, b)  => { return (a.shortName.up () < b.shortName.up () ? -1 : 1); };
        compare_symbols_name_desc = (a, b)  => { return (a.shortName.up () > b.shortName.up () ? -1 : 1); };
        compare_symbols_market_change_down = (a, b)  => { return (a.regularMarketChangePercent < b.regularMarketChangePercent ? -1 : 1); };
        compare_symbols_market_change_up = (a, b)  => { return (a.regularMarketChangePercent > b.regularMarketChangePercent ? -1 : 1); };
    }

    private void attach_listeners () {
        notify["pull-interval"].connect (on_pull_interval_updated);
        notify["dark-theme"].connect (on_dark_theme);
        notify["order-view"].connect (on_sort_symbols);
        notify["order-view"].connect (on_order_view);

        bind_setting ("dark-theme", "dark_theme");
        bind_setting ("pull-interval", "pull_interval");
        bind_setting ("window-width", "window_width");
        bind_setting ("window-height", "window_height");
        bind_setting ("pref-window-width", "pref_window_width");
        bind_setting ("pref-window-height", "pref_window_height");
        bind_setting ("order-view-ref", "order_view_ref");
    }

    private void on_order_view () {
        order_view_ref = order_view.to_value ();
    }

    private void on_dark_theme () {
        Gtk.Settings.get_default ().gtk_application_prefer_dark_theme = dark_theme;
    }

    public void on_sort_symbols () {
        if (symbol_store != null) {
            if (order_view == OrderView.TITLE_ASC) {
                symbol_store.sort (compare_symbols_name_asc);
            } else
            if (order_view == OrderView.TITLE_DESC) {
                symbol_store.sort (compare_symbols_name_desc);
            } else
            if (order_view == OrderView.CHANGE_UP) {
                symbol_store.sort (compare_symbols_market_change_up);
            } else
            if (order_view == OrderView.CHANGE_DOWN) {
                symbol_store.sort (compare_symbols_market_change_down);
            }
        }
    }

    private void on_pull_interval_updated () {
        if (timeout_id != null) {
            Source.remove (timeout_id);
        }
        this.timeout_id = Timeout.add_seconds (pull_interval, on_tick);
    }

    public bool on_tick () {
        network_status = NetworkStatus.IN_PROGRESS;
        if (tick_enable) {
            this.update_symbols.begin ((obj, res) => {
                this.update_symbols.end (res);
            });
        }
        network_status = NetworkStatus.IDLE;
        return true;
    }

    public void load_symbols () {
        var symbol_list = persistence.load_symbols ();
        symbol_store.remove_all();
        foreach (var s in symbol_list) {
            symbol_store.append (s);
        }
        symbol_store.items_changed.connect (persist_symbols);
        on_sort_symbols ();
    }

    public async void update_symbols () {
        var yahoo_client = (YahooFinanceClient) Lookup.singleton (). find (YahooFinanceClient.ID);
        uint n = symbol_store.get_n_items ();
        for (var i=0; i < n; i++) {
            var symbol = (Symbol) symbol_store.get_object (i);
            yahoo_client.search_symbols.begin (symbol.symbol, (obj, res) => {
                var symbol_list = yahoo_client.search_symbols.end (res);
                if (symbol_list.size > 0) {
                    var symbol_found = symbol_list.@get (0);
                    if (symbol_found != null && symbol.symbol == symbol_found.symbol) {
                        symbol.clone (symbol_found);
                    }
                }
            });
        }
        on_sort_symbols ();
        persist_symbols ();
    }

    public void persist_symbols () {
        var list_symbols = new Gee.ArrayList<Symbol> ();
        uint n = symbol_store.get_n_items ();
        for (var i=0; i < n; i++) {
            var o = (Symbol) symbol_store.get_object (i);
            list_symbols.add (o);
        }
        persistence.persist_symbols (list_symbols);
    }

    private void bind_setting (string setting_prop, string state_prop) {
        this.settings.bind (setting_prop, this, state_prop, SettingsBindFlags.DEFAULT);
    }
}
