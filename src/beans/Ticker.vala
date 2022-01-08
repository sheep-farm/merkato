/* Quote.vala
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
public class Mkt.Ticker : Object {

    public string exchange {get; set; default="";}
    public string shortname {get; set; default="";}
    public string quoteType {get; set; default="";}
    public string symbol {get; set; default="";}
    public string index {get; set; default="";}
    public int score {get; set;}
    public string typeDisp {get; set; default="";}
    public string exchDisp {get; set; default="";}
    public bool isYahooFinance {get; set; default=false;}

    public Ticker.from_json (Json.Object json) {
        if (json == null) return;

	    if (json.has_member ("exchange")) {
	        this.exchange = json.get_string_member ("exchange");
	    }
	    if (json.has_member ("shortname")) {
	        this.shortname = json.get_string_member ("shortname");
	    }
	    if (json.has_member ("quoteType")) {
	        this.quoteType = json.get_string_member ("quoteType");
	    }
	    if (json.has_member ("symbol")) {
	        this.symbol = json.get_string_member ("symbol");
	    }
	    if (json.has_member ("index")) {
	        this.index = json.get_string_member ("index");
	    }
	    if (json.has_member ("score")) {
	        this.score = (int) json.get_int_member ("score");
	    }
	    if (json.has_member ("typeDisp")) {
	        this.typeDisp = json.get_string_member ("typeDisp");
	    }
	    if (json.has_member ("exchDisp")) {
	        this.exchDisp = json.get_string_member ("exchDisp");
	    }
	    if (json.has_member ("isYahooFinance")) {
	        this.isYahooFinance = json.get_boolean_member ("isYahooFinance");
	    }
    }

    public void clone (Ticker other) {
        exchange = other.exchange;
        shortname = other.shortname;
        quoteType = other.quoteType;
        symbol = other.symbol;
        index = other.index;
        score = other.score;
        typeDisp = other.typeDisp;
        exchDisp = other.exchDisp;
        isYahooFinance = other.isYahooFinance;
    }

    public string to_string () {
        return @"Ticker [symbol = $symbol, shortname = $shortname]";
    }

/*
    private string decode_entities (string value) {
        return value.replace ("&amp;", "&").strip ();
    }
*/
}
