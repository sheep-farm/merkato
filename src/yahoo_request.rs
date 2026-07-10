// yahoo_request.rs
//
// Copyright 2025 Flávio de Vasconcellos Corrêa
//
// SPDX-License-Identifier: GPL-3.0-or-later

use std::collections::HashMap;
use std::time::Duration;

use reqwest::Client;
use serde::Deserialize;
use tracing::{debug, error, warn};

use crate::data_cache::DataCache;
use crate::stock::Stock;

const REQUEST_TIMEOUT: Duration = Duration::from_secs(15);
const MAX_RETRIES: u32 = 3;
const RETRY_BASE_DELAY_MS: u64 = 500;

// ─── Yahoo Finance chart API response ────────────────────────────────────────

#[derive(Debug, Deserialize)]
struct ChartResponse {
    chart: ChartBody,
}

#[derive(Debug, Deserialize)]
struct ChartBody {
    result: Option<Vec<ChartResult>>,
}

#[derive(Debug, Deserialize, Default)]
struct ChartResult {
    meta: ChartMeta,
}

#[derive(Debug, Deserialize, Default)]
#[serde(rename_all = "camelCase")]
struct ChartMeta {
    symbol: Option<String>,
    long_name: Option<String>,
    short_name: Option<String>,
    regular_market_price: Option<f64>,
    chart_previous_close: Option<f64>,
    currency: Option<String>,
    instrument_type: Option<String>, // EQUITY, ETF, CRYPTOCURRENCY, etc.
    #[allow(dead_code)]
    exchange_name: Option<String>,
    market_state: Option<String>,
}

// ─── quoteSummary asset profile ───────────────────────────────────────────────

#[derive(Debug, Deserialize)]
struct QuoteSummaryResponse {
    #[serde(rename = "quoteSummary")]
    quote_summary: QuoteSummaryBody,
}

#[derive(Debug, Deserialize)]
struct QuoteSummaryBody {
    result: Option<Vec<QuoteSummaryResult>>,
}

#[derive(Debug, Deserialize, Default)]
#[serde(rename_all = "camelCase")]
struct QuoteSummaryResult {
    asset_profile: Option<AssetProfile>,
    quote_type: Option<QuoteTypeData>,
}

#[derive(Debug, Deserialize, Default)]
#[serde(rename_all = "camelCase")]
struct AssetProfile {
    sector: Option<String>,
    industry: Option<String>,
}

#[derive(Debug, Deserialize, Default)]
#[serde(rename_all = "camelCase")]
struct QuoteTypeData {
    quote_type: Option<String>,
}

// ─── Currency symbol mapping ──────────────────────────────────────────────────

fn currency_symbol(code: &str) -> String {
    match code {
        "USD" => "$",
        "EUR" => "€",
        "GBP" => "£",
        "JPY" => "¥",
        "CNY" | "CNH" => "¥",
        "BRL" => "R$",
        "CAD" => "C$",
        "AUD" => "A$",
        "CHF" => "Fr",
        "HKD" => "HK$",
        "INR" => "₹",
        "KRW" => "₩",
        "MXN" => "MX$",
        "RUB" => "₽",
        "SEK" | "DKK" | "NOK" => "kr",
        _ => code,
    }
    .to_string()
}

fn sanitize_f64(v: f64) -> f64 {
    if v.is_nan() || v.is_infinite() { 0.0 } else { v }
}

// ─── YahooRequest ────────────────────────────────────────────────────────────

/// Fetches stock data from Yahoo Finance chart API (no auth required).
pub struct YahooRequest {
    client: Client,
    cache: DataCache,
}

impl YahooRequest {
    pub fn new() -> Self {
        let client = Client::builder()
            .user_agent(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 \
                 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            )
            .timeout(REQUEST_TIMEOUT)
            .build()
            .expect("Failed to create HTTP client");

        Self {
            client,
            cache: DataCache::new("merkato"),
        }
    }

    async fn request_with_retry(&self, url: &str) -> Option<reqwest::Response> {
        for attempt in 0..MAX_RETRIES {
            match self.client.get(url).send().await {
                Ok(resp) if resp.status().is_success() => return Some(resp),
                Ok(resp) => {
                    warn!(url, status = %resp.status(), attempt, "unexpected HTTP status");
                }
                Err(e) => {
                    error!(url, error = %e, attempt, "request failed");
                }
            }
            if attempt + 1 < MAX_RETRIES {
                let delay = RETRY_BASE_DELAY_MS * 2_u64.pow(attempt);
                tokio::time::sleep(Duration::from_millis(delay)).await;
            }
        }
        None
    }

    /// Fetch price data for a single symbol via the chart API.
    async fn fetch_chart(&self, symbol: &str) -> Option<Stock> {
        let url = format!(
            "https://query1.finance.yahoo.com/v8/finance/chart/{}?interval=1d&range=1d",
            symbol
        );

        let resp = self.request_with_retry(&url).await?;
        let data: ChartResponse = match resp.json().await {
            Ok(d) => d,
            Err(e) => {
                error!(symbol, error = %e, "failed to parse chart JSON");
                return None;
            }
        };
        let meta = data.chart.result?.into_iter().next()?.meta;

        let price = sanitize_f64(meta.regular_market_price?);
        if price <= 0.0 {
            warn!(symbol, "invalid price received");
            return None;
        }
        let prev_close = sanitize_f64(meta.chart_previous_close.unwrap_or(price));
        let change = sanitize_f64(price - prev_close);
        let change_pct = if prev_close != 0.0 {
            sanitize_f64(change / prev_close)
        } else {
            0.0
        };
        let currency = meta.currency.clone().unwrap_or_default();
        let sym = meta.symbol.unwrap_or_else(|| symbol.to_string());

        let mut stock = Stock::new(sym.clone());
        stock.long_name = meta.long_name.or(meta.short_name).unwrap_or_default();
        stock.price = price;
        stock.change = change;
        stock.change_pct = change_pct;
        stock.currency_symbol = currency_symbol(&currency);
        stock.currency = currency;
        stock.market_state = meta.market_state.unwrap_or_else(|| "REGULAR".to_string());
        stock.quote_type = meta.instrument_type.unwrap_or_default();

        debug!(symbol = %sym, price, "fetched chart data");
        Some(stock)
    }

    /// Fetch sector, industry and canonical quoteType for a single symbol.
    async fn fetch_asset_profile(
        &self,
        symbol: &str,
    ) -> (Option<String>, Option<String>, Option<String>) {
        let url = format!(
            "https://query1.finance.yahoo.com/v11/finance/quoteSummary/{}\
             ?modules=assetProfile%2CquoteType",
            symbol
        );

        let resp = match self.request_with_retry(&url).await {
            Some(r) => r,
            None => return (None, None, None),
        };

        match resp.json::<QuoteSummaryResponse>().await {
            Ok(data) => {
                let result = data
                    .quote_summary
                    .result
                    .and_then(|mut r| r.pop())
                    .unwrap_or_default();
                let profile = result.asset_profile.unwrap_or_default();
                let qtype = result.quote_type.and_then(|q| q.quote_type);
                (profile.sector, profile.industry, qtype)
            }
            Err(e) => {
                error!(symbol, error = %e, "failed to parse asset profile JSON");
                (None, None, None)
            }
        }
    }

    /// Full fetch: price + sector/industry for new stocks.
    pub async fn fetch(
        &self,
        symbols: &[String],
    ) -> (HashMap<String, Stock>, Vec<String>) {
        if symbols.is_empty() {
            return (HashMap::new(), Vec::new());
        }

        let mut results = self.cache.get_fresh(symbols);
        let mut errors: Vec<String> = Vec::new();
        let missing: Vec<String> = symbols
            .iter()
            .filter(|s| !results.contains_key(*s))
            .cloned()
            .collect();

        if !missing.is_empty() {
            debug!(missing = ?missing, "fetching missing symbols from network");
            // Fetch all symbols concurrently
            let futures: Vec<_> = missing.iter().map(|s| self.fetch_chart(s)).collect();
            let chart_results = futures::future::join_all(futures).await;

            for (sym, maybe_stock) in missing.iter().zip(chart_results.into_iter()) {
                match maybe_stock {
                    Some(stock) => {
                        results.insert(sym.clone(), stock);
                    }
                    None => errors.push(sym.clone()),
                }
            }
            self.cache.put(&results);
        }

        // Fetch sector/industry for equity-like symbols concurrently
        let equity_symbols: Vec<String> = results.keys().cloned().collect();
        let profile_futures: Vec<_> = equity_symbols
            .iter()
            .map(|s| self.fetch_asset_profile(s))
            .collect();
        let profile_results = futures::future::join_all(profile_futures).await;

        for (sym, (sector, industry, qtype)) in
            equity_symbols.iter().zip(profile_results.into_iter())
        {
            if let Some(stock) = results.get_mut(sym) {
                if let Some(s) = sector {
                    stock.sector = s;
                }
                if let Some(i) = industry {
                    stock.industry = i;
                }
                if let Some(q) = qtype {
                    stock.quote_type = q;
                }
            }
        }

        // Update cache with enriched data
        self.cache.put(&results);

        (results, errors)
    }

    /// Refresh existing stocks – only fetch price data.
    pub async fn refresh(
        &self,
        symbols: &[String],
    ) -> (HashMap<String, Stock>, Vec<String>) {
        if symbols.is_empty() {
            return (HashMap::new(), Vec::new());
        }

        // Refresh always goes to network to get latest prices
        let futures: Vec<_> = symbols.iter().map(|s| self.fetch_chart(s)).collect();
        let results = futures::future::join_all(futures).await;

        let mut map: HashMap<String, Stock> = HashMap::new();
        let mut errors: Vec<String> = Vec::new();

        for (sym, maybe_stock) in symbols.iter().zip(results.into_iter()) {
            match maybe_stock {
                Some(stock) => {
                    map.insert(sym.clone(), stock);
                }
                None => errors.push(sym.clone()),
            }
        }

        self.cache.put(&map);
        (map, errors)
    }
}

impl Default for YahooRequest {
    fn default() -> Self {
        Self::new()
    }
}
