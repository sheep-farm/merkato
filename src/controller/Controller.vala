/* Controller.vala
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

public class Mkt.Controller : GLib.Object {
    private Application application;
    private MainWindow main_window;

    private TickerViewBox   ticker_view_box;
    private TickerView      ticker_view;
    private Gtk.Stack       ticker_stack;
    private Gtk.Button      go_back_button;
    private Gtk.SearchEntry search_entry;
    private Gtk.ListBox     ticker_list_box;
    private Gtk.Spinner     ticker_view_spinner;

    private SymbolViewBox    symbol_view_box;
    private SymbolView       symbol_view;
    private Gtk.Stack        symbol_stack;
    private Gtk.Button       add_symbol_view_button;
    private Gtk.ToggleButton remove_symbol_view_button;
    private Gtk.ListBox      symbol_list_box;
    private Gtk.Spinner      symbol_view_spinner;

    private Gtk.Stack     main_stack;

    private Gee.List<Symbol> symbol_list;
    private Gee.List<Ticker> ticker_list;

    private YahooFinanceClient yahoo_finance_client;
    private uint? timeout_id = null;
    private int? pull_interval = 30;

    private CompareDataFunc<Symbol> compare_symbols_name_asc;
    private CompareDataFunc<Symbol> compare_symbols_name_desc;
    private CompareDataFunc<Symbol> compare_symbols_market_change_up;
    private CompareDataFunc<Symbol> compare_symbols_market_change_down;
    private SymbolPersistence persistence;

    private Preferences preferences;

    private const string SYMBOL_VIEW_BOX  = "symbol_view_box";
    private const string SYMBOL_VIEW      = "symbol_view";
    private const string NO_SYMBOL_VIEW   = "no_symbol_view";
    private const string TICKER_VIEW_BOX  = "ticker_view_box";
    private const string TICKER_VIEW      = "ticker_view";
    private const string NO_TICKER_VIEW   = "no_ticker_view";

    public Controller (Application application) {
        preferences = new Preferences ();
        Gtk.Settings.get_default ().gtk_application_prefer_dark_theme = preferences.dark_theme;
        preferences.notify["order-view"].connect (() => {
            order_symbol_list ();
            update_symbol_view_box ();
        });
        preferences.notify["pull-interval"].connect (() => {
            pull_interval = preferences.pull_interval;
            stop_update_symbol_list_loop ();
            begin_update_symbol_list_loop ();
        });
        preferences.notify["dark-theme"].connect (() => {
            Gtk.Settings.get_default ().gtk_application_prefer_dark_theme = preferences.dark_theme;
        });

        pull_interval = preferences.pull_interval;

        this.application = application;
        main_window = new MainWindow (application);
        main_window.default_width = preferences.window_width;
        main_window.default_height = preferences.window_height;
        main_window.delete_event.connect (() => {
            on_quit ();
            return false;
        });
        main_stack = main_window.stack;

        symbol_view_box = new SymbolViewBox (main_window);
        symbol_view_spinner = symbol_view_box.spinner;

        add_symbol_view_button = symbol_view_box.add_symbol_view_button;
        add_symbol_view_button.clicked.connect (() => {
            update_ticker_view_box ();
            stop_update_symbol_list_loop ();
        });

        remove_symbol_view_button = symbol_view_box.remove_symbol_view_button;
        remove_symbol_view_button.toggled.connect (() => {
            update_symbol_view_box ();
            if (remove_symbol_view_button.active) {
                stop_update_symbol_list_loop ();
            } else {
                begin_update_symbol_list_loop ();
            }
        });

        symbol_view = new SymbolView ();
        symbol_list_box = symbol_view.symbol_list_box;
        symbol_list_box.row_activated.connect ( (row) => {
            ((SymbolRow) row).on_row_clicked ();
        });

        symbol_stack = symbol_view_box.stack;
        symbol_stack.add_named (symbol_view, SYMBOL_VIEW);
        symbol_stack.add_named (new NoSymbolView (), NO_SYMBOL_VIEW);

        ticker_view_box = new TickerViewBox (main_window);
        ticker_view_spinner = ticker_view_box.spinner;
        ticker_stack = ticker_view_box.stack;
        go_back_button = ticker_view_box.go_back_button;
        go_back_button.clicked.connect (() => {
            search_entry.text = "";
            update_symbol_view_box ();
            begin_update_symbol_list_loop ();
        });
        search_entry = ticker_view_box.search_entry;
        search_entry.activate.connect (() => {
            update_ticker_list ();
        });
        search_entry.search_changed.connect (() => {
            if (search_entry.text.length == 0) {
                update_ticker_list ();
            }
        });
        search_entry.stop_search.connect (() => {
            if (search_entry.text.length > 0) {
                search_entry.text = "";
            }
        });

        ticker_view = new TickerView ();
        ticker_list_box = ticker_view.ticker_list_box;
        ticker_stack.add_named (ticker_view, TICKER_VIEW);
        ticker_stack.add_named (new NoTickerView (), NO_TICKER_VIEW);

        main_stack.add_named (symbol_view_box, SYMBOL_VIEW_BOX);
        main_stack.add_named (ticker_view_box, TICKER_VIEW_BOX);

        persistence = new SymbolPersistence ();
        yahoo_finance_client = new YahooFinanceClient ();
        symbol_list = new Gee.ArrayList<Symbol> ();
        ticker_list = new Gee.ArrayList<Ticker> ();

        compare_symbols_name_asc           = (a, b)  => { return (a.shortName.up () < b.shortName.up () ? -1 : 1); };
        compare_symbols_name_desc          = (a, b)  => { return (a.shortName.up () > b.shortName.up () ? -1 : 1); };
        compare_symbols_market_change_down = (a, b)  => { return (a.regularMarketChangePercent < b.regularMarketChangePercent ? -1 : 1); };
        compare_symbols_market_change_up   = (a, b)  => { return (a.regularMarketChangePercent > b.regularMarketChangePercent ? -1 : 1); };

        init_symbol_list ();
        update_symbol_view_box ();
        update_symbol_list ();
        begin_update_symbol_list_loop ();
    }

    public void activate () {
        main_window.present ();
    }

    public void show_preferences_dialog () {
        var prefs = new PreferencesWindow (application, main_window, preferences);
        prefs.default_height = preferences.pref_window_height;
        prefs.default_width  = preferences.pref_window_width;
        prefs.present ();
    }

    public void show_about_dialog () {
        var dialog = new AboutDialog (main_window);
        dialog.run ();
        dialog.destroy ();
    }

    public void close_main_window () {
        main_window.close ();
    }

    public void on_quit () {
        int width;
        int height;
        main_window.get_size (out width, out height);
        preferences.window_width = width;
        preferences.window_height = height;
        persistence.persist_symbols (symbol_list);
    }

    private void stack_visible (string new_stack) {
        switch (new_stack) {
            case SYMBOL_VIEW_BOX :
                main_stack.set_visible_child_name (SYMBOL_VIEW_BOX);
                break;
            case SYMBOL_VIEW :
                symbol_stack.set_visible_child_name (SYMBOL_VIEW);
                break;
            case NO_SYMBOL_VIEW :
                symbol_stack.set_visible_child_name (NO_SYMBOL_VIEW);
                break;
            case TICKER_VIEW_BOX :
                main_stack.set_visible_child_name (TICKER_VIEW_BOX);
                break;
            case TICKER_VIEW :
                ticker_stack.set_visible_child_name (TICKER_VIEW);
                break;
            case NO_TICKER_VIEW :
                ticker_stack.set_visible_child_name (NO_TICKER_VIEW);
                break;
        }
    }

    private void init_symbol_list () {
        symbol_list.add_all (persistence.load_symbols ());
    }

    private void begin_update_symbol_list_loop () {
        timeout_id = Timeout.add_seconds (pull_interval, () => {
            update_symbol_list ();
            return true;
        });
    }

    private void stop_update_symbol_list_loop () {
        if (timeout_id != null) {
            Source.remove (timeout_id);
            timeout_id = null;
        }
    }

    private void update_symbol_view_box () {
        var children = symbol_list_box.get_children ();
        foreach (Gtk.Widget widget in children) symbol_list_box.remove (widget);
        foreach (Symbol s in symbol_list){
            SymbolRow symbol_row = new SymbolRow (s, remove_symbol_view_button.active);
            symbol_list_box.add (symbol_row);
            symbol_row.remove_symbol_button.clicked.connect (() => {
                symbol_list.remove_at (symbol_list.index_of (s));
                update_symbol_view_box ();
            });
            symbol_row.drag_data_received.connect ((context, x, y, selection_data, target_type) => {
                var row = ((Gtk.Widget[]) selection_data.get_data ())[0];
                Symbol src = ((SymbolRow) row).symbol;
                Symbol dst = s;
                var src_pos = symbol_list.index_of (src);
                var dst_pos = symbol_list.index_of (dst);
                symbol_list.remove_at (src_pos);
                symbol_list.insert (dst_pos, src);
                preferences.order_view = Preferences.OrderView.CUSTOM;
                update_symbol_view_box ();
            });

        }
        remove_symbol_view_button.visible = !symbol_list.is_empty;
        stack_visible (SYMBOL_VIEW_BOX);
        stack_visible (symbol_list.is_empty ? NO_SYMBOL_VIEW : SYMBOL_VIEW);
    }

    private void update_symbol_list () {
        if (!symbol_list.is_empty) {
            var tickers = "";
            foreach (Symbol s in symbol_list) {
                tickers += s.symbol + ",";
            }
            symbol_view_spinner.start ();
            yahoo_finance_client.search_symbols.begin (tickers, (obj, res) => {
                var result = yahoo_finance_client.search_symbols.end (res);
                if (!result.is_empty) {
                    symbol_list.clear ();
                    symbol_list.add_all (result);
                    order_symbol_list ();
                    update_symbol_view_box ();
                    persistence.persist_symbols (symbol_list);
                }
                symbol_view_spinner.stop ();
            });
        }
    }

    private void order_symbol_list () {
        if ((symbol_list != null && !symbol_list.is_empty) && !(preferences.order_view == Preferences.OrderView.CUSTOM.to_value())) {
            if (preferences.order_view == Preferences.OrderView.TITLE_ASC.to_value()) {
                symbol_list.sort (compare_symbols_name_asc);
            } else
            if (preferences.order_view == Preferences.OrderView.TITLE_DESC.to_value()) {
                symbol_list.sort (compare_symbols_name_desc);
            } else
            if (preferences.order_view == Preferences.OrderView.CHANGE_UP.to_value()) {
                symbol_list.sort (compare_symbols_market_change_up);
            } else
            if (preferences.order_view == Preferences.OrderView.CHANGE_DOWN.to_value()) {
                symbol_list.sort (compare_symbols_market_change_down);
            }
        }
    }

    private void update_ticker_view_box () {
        var size = ticker_list.size;
        var children = ticker_list_box.get_children ();
        foreach (Gtk.Widget widget in children) ticker_list_box.remove (widget);
        foreach (Ticker t in ticker_list) {
            TickerRow ticker_row = new TickerRow (t);
            ticker_row.add_button.clicked.connect (() => {
                ticker_list_box.remove (ticker_row);
                yahoo_finance_client.search_symbols.begin (t.symbol, (obj, res) => {
                    var result_list = yahoo_finance_client.search_symbols.end (res);
                    var symbol = result_list.@get(0);
                    if (symbol != null) {
                        symbol_list.add (symbol);
                        order_symbol_list ();
                        persistence.persist_symbols (symbol_list);
                    }
                });
            });
            ticker_list_box.add (ticker_row);
        }
        stack_visible (TICKER_VIEW_BOX);
        stack_visible (ticker_list.is_empty ? NO_TICKER_VIEW : TICKER_VIEW);
    }

    private void update_ticker_list () {
        ticker_list.clear ();
        if (search_entry.text != "") {
            ticker_view_spinner.start ();
            yahoo_finance_client.search_tickers.begin (search_entry.text, (obj, res) => {
                ticker_list.add_all (yahoo_finance_client.search_tickers.end (res));
                ticker_view_spinner.stop ();
                update_ticker_view_box ();
            });
        } else {
            update_ticker_view_box ();
        }
    }
}
