// stock.rs
//
// Copyright 2025 Flávio de Vasconcellos Corrêa
//
// SPDX-License-Identifier: GPL-3.0-or-later

use serde::{Deserialize, Serialize};

/// Data model representing a financial instrument (stock, crypto, ETF, etc.)
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct Stock {
    pub symbol: String,
    pub long_name: String,
    pub price: f64,
    pub change: f64,
    /// Percentage change as a fraction (e.g., 0.05 = 5%)
    pub change_pct: f64,
    pub market_state: String,
    pub currency: String,
    pub currency_symbol: String,
    /// Asset type: EQUITY, CRYPTOCURRENCY, ETF, MUTUAL_FUND, CURRENCY, INDEX
    pub quote_type: String,
    pub sector: String,
    pub industry: String,
}

impl Stock {
    pub fn new(symbol: impl Into<String>) -> Self {
        Self {
            symbol: symbol.into(),
            ..Default::default()
        }
    }

    pub fn is_gaining(&self) -> bool {
        self.change > 0.0
    }

    pub fn is_losing(&self) -> bool {
        self.change < 0.0
    }

    pub fn is_market_open(&self) -> bool {
        self.market_state == "REGULAR"
    }

    pub fn is_cryptocurrency(&self) -> bool {
        self.quote_type == "CRYPTOCURRENCY"
    }

    /// Returns formatted percentage change string, e.g. "+5.23%" or "-2.45%"
    pub fn formatted_change_pct(&self) -> String {
        let pct = self.change_pct * 100.0;
        let sign = if pct >= 0.0 { "+" } else { "" };
        format!("{sign}{pct:.2}%")
    }

    /// Returns formatted price with currency symbol
    pub fn formatted_price(&self) -> String {
        format!("{}{:.2}", self.currency_symbol, self.price)
    }
}

impl std::fmt::Display for Stock {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{} ({}): {} {}", self.symbol, self.long_name, self.price, self.currency)
    }
}
