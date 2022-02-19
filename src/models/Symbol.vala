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
public class Mkt.Symbol : Object {
	public double ask {get; set; default = 0.00;}
	public int    askSize {get; set; default = 0;}
	public int    averageDailyVolume10Day {get; set; default = 0;}
	public int    averageDailyVolume3Month {get; set; default = 0;}
	public double bid {get; set; default = 0.00;}
	public int    bidSize {get; set; default = 0;}
	public double bookValue {get; set; default = 0.00;}
	public string currency {get; set; default = "";}
	public string displayName {get; set; default = "";}
	public int    dividendDate {get; set; default = 0;}
	public int    earningsTimestamp {get; set; default = 0;}
	public int    earningsTimestampEnd {get; set; default = 0;}
	public int    earningsTimestampStart {get; set; default = 0;}
	public double epsCurrentYear {get; set; default = 0.00;}
	public double epsForward {get; set; default = 0.00;}
	public double epsTrailingTwelveMonths {get; set; default = 0.00;}
	public bool   esgPopulated {get; set; default = false;}
	public string exchange {get; set; default = "";}
	public int    exchangeDataDelayedBy {get; set; default = 0;}
	public string exchangeTimezoneName {get; set; default = "";}
	public string exchangeTimezoneShortName {get; set; default = "";}
	public double fiftyDayAverage {get; set; default = 0.00;}
	public double fiftyDayAverageChange {get; set; default = 0.00;}
	public double fiftyDayAverageChangePercent {get; set; default = 0.00;}
	public double fiftyTwoWeekHigh {get; set; default = 0.00;}
	public double fiftyTwoWeekHighChange {get; set; default = 0.00;}
	public double fiftyTwoWeekHighChangePercent {get; set; default = 0.00;}
	public double fiftyTwoWeekLow {get; set; default = 0.00;}
	public double fiftyTwoWeekLowChange {get; set; default = 0.00;}
	public double fiftyTwoWeekLowChangePercent {get; set; default = 0.00;}
	public string fiftyTwoWeekRange {get; set; default = "";}
	public string financialCurrency {get; set; default = "";}
	public int    firstTradeDateMilliseconds {get; set; default = 0;}
	public double forwardPE {get; set; default = 0.00;}
	public string fullExchangeName {get; set; default = "";}
	public int    gmtOffSetMilliseconds {get; set; default = 0;}
	public bool   isMarketClosed {get {return this.marketState.down () != "regular";}}
	public string language {get; set; default = "";}
	public string longName {get; set; default = "";}
	public string market {get; set; default = "";}
	public int    marketCap {get; set; default = 0;}
	public string marketState {get; set; default = "";}
	public string messageBoardId {get; set; default = "";}
	public double postMarketChange {get; set; default = 0.00;}
	public double postMarketChangePercent {get; set; default = 0.00;}
	public double postMarketPrice {get; set; default = 0.00;}
	public int    postMarketTime {get; set; default = 0;}
	public double priceEpsCurrentYear {get; set; default = 0.00;}
	public int    priceHint {get; set; default = 0;}
	public double priceToBook {get; set; default = 0.00;}
	public string quoteSourceName {get; set; default = "";}
	public string quoteType {get; set; default = "";}
	public string region {get; set; default = "";}
	public double regularMarketChange {get; set; default = 0.00;}
	public double regularMarketChangePercent {get; set; default = 0.00;}
	public double regularMarketDayHigh {get; set; default = 0.00;}
	public double regularMarketDayLow {get; set; default = 0.00;}
	public string regularMarketDayRange {get; set; default = "";}
	public double regularMarketOpen {get; set; default = 0.00;}
	public double regularMarketPreviousClose {get; set; default = 0.00;}
	public double regularMarketPrice {get; set; default = 0.00;}
	public DateTime ? regularMarketTime {get; set; default = null;}
	public int    regularMarketVolume {get; set; default = 0;}
	public int    sharesOutstanding {get; set; default = 0;}
	public string shortName {get; set; default = "";}
	public int    sourceInterval {get; set; default = 0;}
	public string symbol {get; set; default = "";}
	public bool   tradeable {get; set; default = false;}
	public double trailingAnnualDividendRate {get; set; default = 0.00;}
	public double trailingAnnualDividendYield {get; set; default = 0.00;}
	public double trailingPE {get; set; default = 0.00;}
	public bool   triggerable {get; set; default = false;}
	public double twoHundredDayAverage {get; set; default = 0.00;}
	public double twoHundredDayAverageChange {get; set; default = 0.00;}
	public double twoHundredDayAverageChangePercent {get; set; default = 0.00;}

    public bool mark_persist {get; set; default=false;}

	public Symbol.from_json (Json.Object json) {
	    update_from_json (json);
	}

	public void update_from_json (Json.Object json) {
	    if (json == null) {
	        return;
        }

	    if (json.has_member ("ask")) {
	        this.ask = json.get_double_member ("ask");
	    }
	    if (json.has_member ("askSize")) {
	        this.askSize = (int) json.get_int_member ("askSize");
	    }
	    if (json.has_member ("averageDailyVolume10Day")) {
	        this.averageDailyVolume10Day = (int) json.get_int_member ("averageDailyVolume10Day");
	    }
	    if (json.has_member ("averageDailyVolume3Month")) {
	        this.averageDailyVolume3Month = (int) json.get_int_member ("averageDailyVolume3Month");
	    }
	    if (json.has_member ("bid")) {
	        this.bid = json.get_double_member ("bid");
	    }
	    if (json.has_member ("bidSize")) {
	        this.bidSize = (int) json.get_int_member ("bidSize");
	    }
	    if (json.has_member ("bookValue")) {
	        this.bookValue = json.get_double_member ("bookValue");
	    }
	    if (json.has_member ("currency")) {
	        this.currency = json.get_string_member ("currency");
	    }
	    if (json.has_member ("displayName")) {
	        this.displayName = json.get_string_member ("displayName");
	    }
	    if (json.has_member ("dividendDate")) {
	        this.dividendDate = (int) json.get_int_member ("dividendDate");
	    }
	    if (json.has_member ("earningsTimestamp")) {
	        this.earningsTimestamp = (int) json.get_int_member ("earningsTimestamp");
	    }
	    if (json.has_member ("earningsTimestampEnd")) {
	        this.earningsTimestampEnd = (int) json.get_int_member ("earningsTimestampEnd");
	    }
	    if (json.has_member ("earningsTimestampStart")) {
	        this.earningsTimestampStart = (int) json.get_int_member ("earningsTimestampStart");
	    }
	    if (json.has_member ("epsCurrentYear")) {
	        this.epsCurrentYear = json.get_double_member ("epsCurrentYear");
	    }
	    if (json.has_member ("epsForward")) {
	        this.epsForward = json.get_double_member ("epsForward");
	    }
	    if (json.has_member ("epsTrailingTwelveMonths")) {
	        this.epsTrailingTwelveMonths = json.get_double_member ("epsTrailingTwelveMonths");
	    }
	    if (json.has_member ("esgPopulated")) {
	        this.esgPopulated = json.get_boolean_member ("esgPopulated");
	    }
	    if (json.has_member ("exchange")) {
	        this.exchange = json.get_string_member ("exchange");
	    }
	    if (json.has_member ("exchangeDataDelayedBy")) {
	        this.exchangeDataDelayedBy = (int) json.get_int_member ("exchangeDataDelayedBy");
	    }
	    if (json.has_member ("exchangeTimezoneName")) {
	        this.exchangeTimezoneName = json.get_string_member ("exchangeTimezoneName");
	    }
	    if (json.has_member ("exchangeTimezoneShortName")) {
	        this.exchangeTimezoneShortName = json.get_string_member ("exchangeTimezoneShortName");
	    }
	    if (json.has_member ("fiftyDayAverage")) {
	        this.fiftyDayAverage = json.get_double_member ("fiftyDayAverage");
	    }
	    if (json.has_member ("fiftyDayAverageChange")) {
	        this.fiftyDayAverageChange = json.get_double_member ("fiftyDayAverageChange");
	    }
	    if (json.has_member ("fiftyDayAverageChangePercent")) {
	        this.fiftyDayAverageChangePercent = json.get_double_member ("fiftyDayAverageChangePercent");
	    }
	    if (json.has_member ("fiftyTwoWeekHigh")) {
	        this.fiftyTwoWeekHigh = json.get_double_member ("fiftyTwoWeekHigh");
	    }
	    if (json.has_member ("fiftyTwoWeekHighChange")) {
	        this.fiftyTwoWeekHighChange = json.get_double_member ("fiftyTwoWeekHighChange");
	    }
	    if (json.has_member ("fiftyTwoWeekHighChangePercent")) {
	        this.fiftyTwoWeekHighChangePercent = json.get_double_member ("fiftyTwoWeekHighChangePercent");
	    }
	    if (json.has_member ("fiftyTwoWeekLow")) {
	        this.fiftyTwoWeekLow = json.get_double_member ("fiftyTwoWeekLow");
	    }
	    if (json.has_member ("fiftyTwoWeekLowChange")) {
	        this.fiftyTwoWeekLowChange = json.get_double_member ("fiftyTwoWeekLowChange");
	    }
	    if (json.has_member ("fiftyTwoWeekLowChangePercent")) {
	        this.fiftyTwoWeekLowChangePercent = json.get_double_member ("fiftyTwoWeekLowChangePercent");
	    }
	    if (json.has_member ("fiftyTwoWeekRange")) {
	        this.fiftyTwoWeekRange = json.get_string_member ("fiftyTwoWeekRange");
	    }
	    if (json.has_member ("financialCurrency")) {
	        this.financialCurrency = json.get_string_member ("financialCurrency");
	    }
	    if (json.has_member ("firstTradeDateMilliseconds")) {
	        this.firstTradeDateMilliseconds = (int) json.get_int_member ("firstTradeDateMilliseconds");
	    }
	    if (json.has_member ("forwardPE")) {
	        this.forwardPE = json.get_double_member ("forwardPE");
	    }
	    if (json.has_member ("fullExchangeName")) {
	        this.fullExchangeName = json.get_string_member ("fullExchangeName");
	    }
	    if (json.has_member ("gmtOffSetMilliseconds")) {
	        this.gmtOffSetMilliseconds = (int) json.get_int_member ("gmtOffSetMilliseconds");
	    }
	    if (json.has_member ("language")) {
	        this.language = json.get_string_member ("language");
	    }
	    if (json.has_member ("longName")) {
	        this.longName = json.get_string_member ("longName");
	    }
	    if (json.has_member ("market")) {
	        this.market = json.get_string_member ("market");
	    }
	    if (json.has_member ("marketCap")) {
	        this.marketCap = (int) json.get_int_member ("marketCap");
	    }
	    if (json.has_member ("marketState")) {
	        this.marketState = json.get_string_member ("marketState");
	    }
	    if (json.has_member ("messageBoardId")) {
	        this.messageBoardId = json.get_string_member ("messageBoardId");
	    }
	    if (json.has_member ("postMarketChange")) {
	        this.postMarketChange = json.get_double_member ("postMarketChange");
	    }
	    if (json.has_member ("postMarketChangePercent")) {
	        this.postMarketChangePercent = json.get_double_member ("postMarketChangePercent");
	    }
	    if (json.has_member ("postMarketPrice")) {
	        this.postMarketPrice = json.get_double_member ("postMarketPrice");
	    }
	    if (json.has_member ("postMarketTime")) {
	        this.postMarketTime = (int) json.get_int_member ("postMarketTime");
	    }
	    if (json.has_member ("priceEpsCurrentYear")) {
	        this.priceEpsCurrentYear = json.get_double_member ("priceEpsCurrentYear");
	    }
	    if (json.has_member ("priceHint")) {
	        this.priceHint = (int) json.get_int_member ("priceHint");
	    }
	    if (json.has_member ("priceToBook")) {
	        this.priceToBook = json.get_double_member ("priceToBook");
	    }
	    if (json.has_member ("quoteSourceName")) {
	        this.quoteSourceName = json.get_string_member ("quoteSourceName");
	    }
	    if (json.has_member ("quoteType")) {
	        this.quoteType = json.get_string_member ("quoteType");
	    }
	    if (json.has_member ("region")) {
	        this.region = json.get_string_member ("region");
	    }
	    if (json.has_member ("regularMarketChange")) {
	        this.regularMarketChange = json.get_double_member ("regularMarketChange");
	    }
	    if (json.has_member ("regularMarketChangePercent")) {
	        this.regularMarketChangePercent = json.get_double_member ("regularMarketChangePercent");
	    }
	    if (json.has_member ("regularMarketDayHigh")) {
	        this.regularMarketDayHigh = json.get_double_member ("regularMarketDayHigh");
	    }
	    if (json.has_member ("regularMarketDayLow")) {
	        this.regularMarketDayLow = json.get_double_member ("regularMarketDayLow");
	    }
	    if (json.has_member ("regularMarketDayRange")) {
	        this.regularMarketDayRange = json.get_string_member ("regularMarketDayRange");
	    }
	    if (json.has_member ("regularMarketOpen")) {
	        this.regularMarketOpen = json.get_double_member ("regularMarketOpen");
	    }
	    if (json.has_member ("regularMarketPreviousClose")) {
	        this.regularMarketPreviousClose = json.get_double_member ("regularMarketPreviousClose");
	    }
	    if (json.has_member ("regularMarketPrice")) {
	        this.regularMarketPrice = json.get_double_member ("regularMarketPrice");
	    }
	    if (json.has_member ("regularMarketTime")) {
	        this.regularMarketTime = new DateTime.from_unix_utc (
                json.get_int_member ("regularMarketTime")
            );
	    }
	    if (json.has_member ("regularMarketVolume")) {
	        this.regularMarketVolume = (int) json.get_int_member ("regularMarketVolume");
	    }
	    if (json.has_member ("sharesOutstanding")) {
	        this.sharesOutstanding = (int) json.get_int_member ("sharesOutstanding");
	    }
	    if (json.has_member ("shortName")) {
	        this.shortName = json.get_string_member ("shortName");
	    }
	    if (json.has_member ("sourceInterval")) {
	        this.sourceInterval = (int) json.get_int_member ("sourceInterval");
	    }
	    if (json.has_member ("symbol")) {
	        this.symbol = json.get_string_member ("symbol");
	    }
	    if (json.has_member ("tradeable")) {
	        this.tradeable = json.get_boolean_member ("tradeable");
	    }
	    if (json.has_member ("trailingAnnualDividendRate")) {
	        this.trailingAnnualDividendRate = json.get_double_member ("trailingAnnualDividendRate");
	    }
	    if (json.has_member ("trailingAnnualDividendYield")) {
	        this.trailingAnnualDividendYield = json.get_double_member ("trailingAnnualDividendYield");
	    }
	    if (json.has_member ("trailingPE")) {
	        this.trailingPE = json.get_double_member ("trailingPE");
	    }
	    if (json.has_member ("triggerable")) {
	        this.triggerable = json.get_boolean_member ("triggerable");
	    }
	    if (json.has_member ("twoHundredDayAverage")) {
	        this.twoHundredDayAverage = json.get_double_member ("twoHundredDayAverage");
	    }
	    if (json.has_member ("twoHundredDayAverageChange")) {
	        this.twoHundredDayAverageChange = json.get_double_member ("twoHundredDayAverageChange");
	    }
	    if (json.has_member ("twoHundredDayAverageChangePercent")) {
	        this.twoHundredDayAverageChangePercent = json.get_double_member ("twoHundredDayAverageChangePercent");
	    }
	}

    public void build_json (Json.Builder builder) {
        if (builder == null) {
            return;
        }
        builder.begin_object ();

        builder.set_member_name ("ask");
        builder.add_double_value (this.ask);

        builder.set_member_name ("askSize");
        builder.add_int_value (this.askSize);

        builder.set_member_name ("averageDailyVolume10Day");
        builder.add_int_value (this.averageDailyVolume10Day);

        builder.set_member_name ("averageDailyVolume3Month");
        builder.add_int_value (this.averageDailyVolume3Month);

        builder.set_member_name ("bid");
        builder.add_double_value (this.bid);

        builder.set_member_name ("bidSize");
        builder.add_int_value (this.bidSize);

        builder.set_member_name ("bookValue");
        builder.add_double_value (this.bookValue);

        builder.set_member_name ("currency");
        builder.add_string_value (this.currency);

        builder.set_member_name ("displayName");
        builder.add_string_value (this.displayName);

        builder.set_member_name ("dividendDate");
        builder.add_int_value (this.dividendDate);

        builder.set_member_name ("earningsTimestamp");
        builder.add_int_value (this.earningsTimestamp);

        builder.set_member_name ("earningsTimestampEnd");
        builder.add_int_value (this.earningsTimestampEnd);

        builder.set_member_name ("earningsTimestampStart");
        builder.add_int_value (this.earningsTimestampStart);

        builder.set_member_name ("epsCurrentYear");
        builder.add_double_value (this.epsCurrentYear);

        builder.set_member_name ("epsForward");
        builder.add_double_value (this.epsForward);

        builder.set_member_name ("epsTrailingTwelveMonths");
        builder.add_double_value (this.epsTrailingTwelveMonths);

        builder.set_member_name ("esgPopulated");
        builder.add_boolean_value (this.esgPopulated);

        builder.set_member_name ("exchange");
        builder.add_string_value (this.exchange);

        builder.set_member_name ("exchangeDataDelayedBy");
        builder.add_int_value (this.exchangeDataDelayedBy);

        builder.set_member_name ("exchangeTimezoneName");
        builder.add_string_value (this.exchangeTimezoneName);

        builder.set_member_name ("exchangeTimezoneShortName");
        builder.add_string_value (this.exchangeTimezoneShortName);

        builder.set_member_name ("fiftyDayAverage");
        builder.add_double_value (this.fiftyDayAverage);

        builder.set_member_name ("fiftyDayAverageChange");
        builder.add_double_value (this.fiftyDayAverageChange);

        builder.set_member_name ("fiftyDayAverageChangePercent");
        builder.add_double_value (this.fiftyDayAverageChangePercent);

        builder.set_member_name ("fiftyTwoWeekHigh");
        builder.add_double_value (this.fiftyTwoWeekHigh);

        builder.set_member_name ("fiftyTwoWeekHighChange");
        builder.add_double_value (this.fiftyTwoWeekHighChange);

        builder.set_member_name ("fiftyTwoWeekHighChangePercent");
        builder.add_double_value (this.fiftyTwoWeekHighChangePercent);

        builder.set_member_name ("fiftyTwoWeekLow");
        builder.add_double_value (this.fiftyTwoWeekLow);

        builder.set_member_name ("fiftyTwoWeekLowChange");
        builder.add_double_value (this.fiftyTwoWeekLowChange);

        builder.set_member_name ("fiftyTwoWeekLowChangePercent");
        builder.add_double_value (this.fiftyTwoWeekLowChangePercent);

        builder.set_member_name ("fiftyTwoWeekRange");
        builder.add_string_value (this.fiftyTwoWeekRange);

        builder.set_member_name ("financialCurrency");
        builder.add_string_value (this.financialCurrency);

        builder.set_member_name ("firstTradeDateMilliseconds");
        builder.add_int_value (this.firstTradeDateMilliseconds);

        builder.set_member_name ("forwardPE");
        builder.add_double_value (this.forwardPE);

        builder.set_member_name ("fullExchangeName");
        builder.add_string_value (this.fullExchangeName);

        builder.set_member_name ("gmtOffSetMilliseconds");
        builder.add_int_value (this.gmtOffSetMilliseconds);

        builder.set_member_name ("language");
        builder.add_string_value (this.language);

        builder.set_member_name ("longName");
        builder.add_string_value (this.longName);

        builder.set_member_name ("market");
        builder.add_string_value (this.market);

        builder.set_member_name ("marketCap");
        builder.add_int_value (this.marketCap);

        builder.set_member_name ("marketState");
        builder.add_string_value (this.marketState);

        builder.set_member_name ("messageBoardId");
        builder.add_string_value (this.messageBoardId);

        builder.set_member_name ("postMarketChange");
        builder.add_double_value (this.postMarketChange);

        builder.set_member_name ("postMarketChangePercent");
        builder.add_double_value (this.postMarketChangePercent);

        builder.set_member_name ("postMarketPrice");
        builder.add_double_value (this.postMarketPrice);

        builder.set_member_name ("askSize");
        builder.add_int_value (this.askSize);

        builder.set_member_name ("priceEpsCurrentYear");
        builder.add_double_value (this.priceEpsCurrentYear);

        builder.set_member_name ("priceHint");
        builder.add_int_value (this.priceHint);

        builder.set_member_name ("priceToBook");
        builder.add_double_value (this.priceToBook);

        builder.set_member_name ("quoteSourceName");
        builder.add_string_value (this.quoteSourceName);

        builder.set_member_name ("quoteType");
        builder.add_string_value (this.quoteType);

        builder.set_member_name ("currency");
        builder.add_string_value (this.currency);

        builder.set_member_name ("regularMarketChange");
        builder.add_double_value (this.regularMarketChange);

        builder.set_member_name ("regularMarketChangePercent");
        builder.add_double_value (this.regularMarketChangePercent);

        builder.set_member_name ("regularMarketDayHigh");
        builder.add_double_value (this.regularMarketDayHigh);

        builder.set_member_name ("regularMarketDayLow");
        builder.add_double_value (this.regularMarketDayLow);

        builder.set_member_name ("regularMarketDayRange");
        builder.add_string_value (this.regularMarketDayRange);

        builder.set_member_name ("regularMarketOpen");
        builder.add_double_value (this.regularMarketOpen);

        builder.set_member_name ("regularMarketPreviousClose");
        builder.add_double_value (this.regularMarketPreviousClose);

        builder.set_member_name ("regularMarketPrice");
        builder.add_double_value (this.regularMarketPrice);

        builder.set_member_name ("regularMarketTime");
        builder.add_int_value ((int) this.regularMarketTime.to_unix ());

        builder.set_member_name ("regularMarketVolume");
        builder.add_int_value (this.regularMarketVolume);

        builder.set_member_name ("sharesOutstanding");
        builder.add_int_value (this.sharesOutstanding);

        builder.set_member_name ("shortName");
        builder.add_string_value (this.shortName);

        builder.set_member_name ("sourceInterval");
        builder.add_int_value (this.sourceInterval);

        builder.set_member_name ("symbol");
        builder.add_string_value (this.symbol);

        builder.set_member_name ("tradeable");
        builder.add_boolean_value (this.tradeable);

        builder.set_member_name ("trailingAnnualDividendRate");
        builder.add_double_value (this.trailingAnnualDividendRate);

        builder.set_member_name ("trailingAnnualDividendYield");
        builder.add_double_value (this.trailingAnnualDividendYield);

        builder.set_member_name ("trailingPE");
        builder.add_double_value (this.trailingPE);

        builder.set_member_name ("triggerable");
        builder.add_boolean_value (this.triggerable);

        builder.set_member_name ("twoHundredDayAverage");
        builder.add_double_value (this.twoHundredDayAverage);

        builder.set_member_name ("twoHundredDayAverageChange");
        builder.add_double_value (this.twoHundredDayAverageChange);

        builder.set_member_name ("twoHundredDayAverageChangePercent");
        builder.add_double_value (this.twoHundredDayAverageChangePercent);

        builder.end_object ();
    }

    public void clone (Symbol other) {
        if (other == null) {
            return;
        }
	    ask = other.ask;
	    askSize = other.askSize;
	    averageDailyVolume10Day = other.averageDailyVolume10Day;
	    averageDailyVolume3Month = other.averageDailyVolume3Month;
	    bid = other.bid;
	    bidSize = other.bidSize;
	    bookValue = other.bookValue;
	    currency = other.currency;
	    displayName = other.displayName;
	    dividendDate = other.dividendDate;
	    earningsTimestamp = other.earningsTimestamp;
	    earningsTimestampEnd = other.earningsTimestampEnd;
	    earningsTimestampStart = other.earningsTimestampStart;
	    epsCurrentYear = other.epsCurrentYear;
	    epsForward = other.epsForward;
	    epsTrailingTwelveMonths = other.epsTrailingTwelveMonths;
	    esgPopulated = other.esgPopulated;
	    exchange = other.exchange;
	    exchangeDataDelayedBy = other.exchangeDataDelayedBy;
	    exchangeTimezoneName = other.exchangeTimezoneName;
	    exchangeTimezoneShortName = other.exchangeTimezoneShortName;
	    fiftyDayAverage = other.fiftyDayAverage;
	    fiftyDayAverageChange = other.fiftyDayAverageChange;
	    fiftyDayAverageChangePercent = other.fiftyDayAverageChangePercent;
	    fiftyTwoWeekHigh = other.fiftyTwoWeekHigh;
	    fiftyTwoWeekHighChange = other.fiftyTwoWeekHighChange;
	    fiftyTwoWeekHighChangePercent = other.fiftyTwoWeekHighChangePercent;
	    fiftyTwoWeekLow = other.fiftyTwoWeekLow;
	    fiftyTwoWeekLowChange = other.fiftyTwoWeekLowChange;
	    fiftyTwoWeekLowChangePercent = other.fiftyTwoWeekLowChangePercent;
	    fiftyTwoWeekRange = other.fiftyTwoWeekRange;
	    financialCurrency = other.financialCurrency;
	    firstTradeDateMilliseconds = other.firstTradeDateMilliseconds;
	    forwardPE = other.forwardPE;
	    fullExchangeName = other.fullExchangeName;
	    gmtOffSetMilliseconds = other.gmtOffSetMilliseconds;
	    language = other.language;
	    longName = other.longName;
	    market = other.market;
	    marketCap = other.marketCap;
	    marketState = other.marketState;
	    messageBoardId = other.messageBoardId;
	    postMarketChange = other.postMarketChange;
	    postMarketChangePercent = other.postMarketChangePercent;
	    postMarketPrice = other.postMarketPrice;
	    postMarketTime = other.postMarketTime;
	    priceEpsCurrentYear = other.priceEpsCurrentYear;
	    priceHint = other.priceHint;
	    priceToBook = other.priceToBook;
	    quoteSourceName = other.quoteSourceName;
	    quoteType = other.quoteType;
	    region = other.region;
	    regularMarketChange = other.regularMarketChange;
	    regularMarketChangePercent = other.regularMarketChangePercent;
	    regularMarketDayHigh = other.regularMarketDayHigh;
	    regularMarketDayLow = other.regularMarketDayLow;
	    regularMarketDayRange = other.regularMarketDayRange;
	    regularMarketOpen = other.regularMarketOpen;
	    regularMarketPreviousClose = other.regularMarketPreviousClose;
	    regularMarketPrice = other.regularMarketPrice;
	    regularMarketTime = other.regularMarketTime;
	    regularMarketVolume = other.regularMarketVolume;
	    sharesOutstanding = other.sharesOutstanding;
	    shortName = other.shortName;
	    sourceInterval = other.sourceInterval;
	    symbol = other.symbol;
	    tradeable = other.tradeable;
	    trailingAnnualDividendRate = other.trailingAnnualDividendRate;
	    trailingAnnualDividendYield = other.trailingAnnualDividendYield;
	    trailingPE = other.trailingPE;
	    triggerable = other.triggerable;
	    twoHundredDayAverage = other.twoHundredDayAverage;
	    twoHundredDayAverageChange = other.twoHundredDayAverageChange;
	    twoHundredDayAverageChangePercent = other.twoHundredDayAverageChangePercent;
    }

	public string to_string () {
	    return @"Symbol [symbol: $symbol, shortName: $shortName]";
	}

	public uint hash () {
	    var result = 31 * symbol.hash ();
	    return result;
	}
}
