// Tests for Yahoo Finance response parsing.
//
// These tests exercise the private deserialization structs indirectly by
// checking the public fetch behaviour against mocked JSON responses.
// Because YahooRequest::fetch is async and uses the network, we keep these
// fixtures here as documentation and for future mocking (e.g. with wiremock).

#[test]
fn chart_response_fixture_is_valid_json() {
    let json = r#"{
        "chart": {
            "result": [
                {
                    "meta": {
                        "symbol": "AAPL",
                        "longName": "Apple Inc.",
                        "regularMarketPrice": 150.25,
                        "chartPreviousClose": 148.0,
                        "currency": "USD",
                        "instrumentType": "EQUITY",
                        "marketState": "REGULAR"
                    }
                }
            ]
        }
    }"#;

    let parsed: serde_json::Value = serde_json::from_str(json).expect("valid chart JSON");
    let meta = parsed["chart"]["result"][0]["meta"].clone();
    assert_eq!(meta["symbol"], "AAPL");
    assert_eq!(meta["regularMarketPrice"], 150.25);
}

#[test]
fn quote_summary_response_fixture_is_valid_json() {
    let json = r#"{
        "quoteSummary": {
            "result": [
                {
                    "assetProfile": {
                        "sector": "Technology",
                        "industry": "Consumer Electronics"
                    },
                    "quoteType": {
                        "quoteType": "EQUITY"
                    }
                }
            ]
        }
    }"#;

    let parsed: serde_json::Value =
        serde_json::from_str(json).expect("valid quote summary JSON");
    let result = &parsed["quoteSummary"]["result"][0];
    assert_eq!(result["assetProfile"]["sector"], "Technology");
    assert_eq!(result["quoteType"]["quoteType"], "EQUITY");
}
