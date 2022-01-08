/* RestClient.vala
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

const string BASE_URL = "https://query1.finance.yahoo.com";

class Mkt.YahooFinanceClient : Object {
    public const string ID = "Mkt.YahooFinanceClient";

    public async Gee.List <Ticker> search_tickers (string query) {
        var ticker_list = new Gee.ArrayList <Ticker> ();
        if (query != null && query != "") {
            var rest_client = new RestClient ();
            var url = @"$BASE_URL/v1/finance/search" +
                      @"?q=$query" +
                       "&lang=en-US" +
                       "&region=US" +
                       "&quotesCount=10" +
                       "&newsCount=0" +
                       "&enableFuzzyQuery=false" +
                       "&quotesQueryId=tss_match_phrase_query" +
                       "&enableEnhancedTrivialQuery=true";
            var json = yield rest_client.fetch (url);
            if (json != null) {
                if (json.get_object ().has_member ("quotes")) {
                    var json_response = json.get_object ().get_array_member ("quotes");
                    if (json_response != null) {
                        for (var i = 0; i < json_response.get_length (); i++) {
                            var object = json_response.get_object_element (i);
                            if (object != null) {
                                ticker_list.add (new Ticker.from_json (object));
                            }
                        }
                    }
                }
            }
        }
        return ticker_list;
    }

    public async Gee.List<Symbol> search_symbols (string tickers) {
        var symbol_list = new Gee.ArrayList <Symbol> ();
        if (tickers != null && tickers != "") {
            var rest_client = new RestClient ();
            var url = @"$BASE_URL/v7/finance/quote?"+
                      "lang=en-US"+
                      "&region=US"+
                      "&corsDomain=finance.yahoo.com"+
                      @"&symbols=$tickers";
            var json = yield rest_client.fetch (url);
            if (json != null) {
                if (json.get_object ().has_member ("quoteResponse")) {
                    var quoteResponse = json.get_object ().get_object_member ("quoteResponse");
                    if (quoteResponse.has_member ("result")) {
                        var json_response = quoteResponse.get_array_member ("result");
                        for (var i = 0; i < json_response.get_length (); i++) {
                            var object = json_response.get_object_element (i);
                            if (object != null) {
                                var symbol = new Symbol.from_json (object);
                                symbol_list.add (symbol);
                            }
                        }
                    }
                }
            }
        }
        return symbol_list;
   }
}
