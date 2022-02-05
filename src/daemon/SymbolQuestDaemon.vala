/* SymbolQuestDaemon.vala
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
/**
 * Services:
 * -- start       - launch when this daemon started
 * -- stop        - launch when this daemon stoped
 * -- on          - launch when this daemon is on
 * -- off         - launch when this daemon is off
 * -- start-query - launch when this daemon begins query in yahoofinance api
 * -- stop-query  - launch when this daemon ends query in yahoofinance api
 * -- update      - launch when this daemon complete push data and update the current query
 */
public class SymbolQuestDaemon : GLib.Object, Daemon, Channel {
    public const string UUID = "6158dd13-7d18-49fb-8435-4ec5405c0a7f";
    public string uuid {get; protected set;}
    public Broadcast.ChannelState state {get; protected set;}

    private Gee.List<Symbol> symbol_buffer = new Gee.ArrayList<Symbol> ();
    private uint ? timeout_id = null;
    public int pull_interval {get; set;}

    public SymbolQuestDaemon () {
        uuid = UUID;
        notify["pull-interval"].connect (on_pull_interval_updated);
        pull_interval = 30;
        channel_on ();
    }

    public void start () {
        if (!is_running ()) {
            execute_service ();
            timeout_id = Timeout.add_seconds (pull_interval, execute_service);
            connector (Broadcast.ChannelEvent.CHANGE, "start", symbol_buffer, null);
        }
    }

    public void stop () {
        if (is_running ()) {
            Source.remove (timeout_id);
            timeout_id = null;
            connector (Broadcast.ChannelEvent.CHANGE, "stop", symbol_buffer, null);
        }
    }

    public void restart () {
        stop (); start ();
    }

    public bool is_running () {
        return (timeout_id != null);
    }

    public void channel_on () {
        state = Broadcast.ChannelState.ON;
        connector (Broadcast.ChannelEvent.ON, "on", symbol_buffer, null);
        start ();
    }

    public void channel_off () {
        state = Broadcast.ChannelState.OFF;
        connector (Broadcast.ChannelEvent.OFF, "off", symbol_buffer, null);
        stop ();
    }

    private bool execute_service () {
        MerkatoIO mio = MerkatoIOFactory.make_default ();
        Gee.List<Symbol> symbol_persist = mio.load_all_symbols ();
        var tickers = "";
        foreach (Symbol s in symbol_persist) {
            tickers += s.symbol + ",";
        }
        YahooFinanceClient yahoo_client = new YahooFinanceClient ();

        yahoo_client.search_symbols.begin (tickers, (obj, res) => {
            connector (Broadcast.ChannelEvent.CHANGE, "start-query", null, null);
            var symbol_list = yahoo_client.search_symbols.end (res);
            if (symbol_list.size > 0) {
                for (var j = 0; j < symbol_list.size; j++) {
                    var symbol_found = symbol_list.@get (j);
                    var symbol = (Symbol) symbol_persist.@get(j);
                    symbol.clone (symbol_found);
                }
                mio.save (symbol_list);
                connector (Broadcast.ChannelEvent.CHANGE, "update", symbol_list, symbol_buffer);
                symbol_buffer = symbol_list;
                connector (Broadcast.ChannelEvent.CHANGE, "stop-query", null, null);
            }
        });
        return false;
    }

    private void on_pull_interval_updated () {
        if (is_running ()) {
            restart ();
        }
    }

}
