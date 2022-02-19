/* SearchSpinner.vala
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

class Mkt.SymbolListBox : Gtk.ListBox, Consumer {
    private GLib.ListStore symbol_store = new GLib.ListStore ();
    private CompareDataFunc<Symbol> compare_symbols_name_asc;
    private CompareDataFunc<Symbol> compare_symbols_name_desc;
    private CompareDataFunc<Symbol> compare_symbols_market_change_up;
    private CompareDataFunc<Symbol> compare_symbols_market_change_down;
    private SettingChannel.OrderView order_view {get; set;}

    public SymbolListBox () {
        compare_symbols_name_asc           = (a, b)  => { return (a.shortName.up () < b.shortName.up () ? -1 : 1); };
        compare_symbols_name_desc          = (a, b)  => { return (a.shortName.up () > b.shortName.up () ? -1 : 1); };
        compare_symbols_market_change_down = (a, b)  => { return (a.regularMarketChangePercent < b.regularMarketChangePercent ? -1 : 1); };
        compare_symbols_market_change_up   = (a, b)  => { return (a.regularMarketChangePercent > b.regularMarketChangePercent ? -1 : 1); };
    }

    public void receive (Channel sender, Broadcast.ChannelEvent event, string? tag, Value? new_value, Value? old_value) {
        if (sender.uuid == SymbolQuestDaemon.UUID) {
            receive_symbol_quest_channel (event, tag, new_value, old_value);
        } else
        if (sender.uuid = SettingChannel.UUID) {
            receive_setting_channel (event, tag, new_value, old_value);
        }
    }

    private void receive_symbol_quest_channel (Broadcast.ChannelEvent event, string? tag, Value? new_value, Value? old_value) {
        if (event == Broadcast.ChannelEvent.ON || event == Broadcast.ChannelEvent.CHANGE) {
            var symbol_list = (List<Symbol>) new_value;
            symbol_store.remove_all ();
            foreach (Symbol s in symbol_list) {
                symbol_store.append (s);
            }
            on_sort_symbols ();
        }
    }

    private void receive_setting_channel (Broadcast.ChannelEvent event, string? tag, Value? new_value, Value? old_value) {
        if (tag == "order-view-ref") {
            var new_order_view = SettingChannel.OrderView.from_value ((int) new_value);
            if (order_view != new_order_view) {
                order_view = new_order_view;
                on_sort_symbols ();
            }
        }
    }

    private void on_sort_symbols () {
        if (symbol_store != null && symbol_store.get_n_items () > 1) {
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
}
