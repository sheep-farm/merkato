/* SearchTickerChannel.vala
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

class SearchTickerChannel : GLib.Object, Channel {
    public const string UUID = "9fd96c63-34ac-48fc-9a55-526439196b13";
    public string uuid {get; protected set;}
    public Broadcast.ChannelState state {get; protected set;}
    public string query_parameters {get; set;}

    private Gee.List<Ticker> ticker_list = new Gee.ArrayList<Ticker> ();

    public SearchTickerChannel () {
        uuid = UUID;
        notify["query_parameters"].connect (execute_query);
    }

    private void execute_query () {
        if (state == Broadcast.ChannelState.ON) {
            YahooFinanceClient yahoo_client = new YahooFinanceClient ();
            yahoo_client.search_tickers.begin (query_parameters, (obj, res) => {
                connector (Broadcast.ChannelEvent.CHANGE, "start-query", null, null);
                ticker_list = yahoo_client.search_tickers.end (res);
                connector (Broadcast.ChannelEvent.CHANGE, "stop-query", null, null);
                connector (Broadcast.ChannelEvent.CHANGE, "update", ticker_list, null);
            });
            yahoo_client = null;
        }
    }

    public void channel_on () {
        state = Broadcast.ChannelState.ON;
        connector (Broadcast.ChannelEvent.ON, "on", null, null);
    }

    public void channel_off () {
        state = Broadcast.ChannelState.OFF;
        connector (Broadcast.ChannelEvent.OFF, "off", null, null);
    }
}
