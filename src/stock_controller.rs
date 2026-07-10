// stock_controller.rs
//
// Copyright 2025 Flávio de Vasconcellos Corrêa
//
// SPDX-License-Identifier: GPL-3.0-or-later

use std::collections::HashMap;
use std::sync::Arc;

use async_channel::Receiver;
use tokio::runtime::Runtime;

use crate::alert_manager::AlertManager;
use crate::stock::Stock;
use crate::watchlist_manager::WatchlistManager;
use crate::yahoo_request::YahooRequest;

pub type SearchResult = (HashMap<String, Stock>, Vec<String>);
pub type RefreshResult = (HashMap<String, Stock>, Vec<String>);

/// Central controller managing stock data and auto-updates.
pub struct StockController {
    yahoo: Arc<YahooRequest>,
    watchlist: WatchlistManager,
    runtime: Arc<Runtime>,
    refresh_source: Option<glib::SourceId>,
}

impl std::fmt::Debug for StockController {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("StockController")
            .field("watchlist", &"<WatchlistManager>")
            .field("refresh_source", &"<SourceId>")
            .finish()
    }
}

impl StockController {
    pub fn new() -> Self {
        let runtime = Arc::new(
            tokio::runtime::Builder::new_multi_thread()
                .enable_all()
                .build()
                .expect("Failed to create Tokio runtime"),
        );

        Self {
            yahoo: Arc::new(YahooRequest::new()),
            watchlist: WatchlistManager::new("merkato"),
            runtime,
            refresh_source: None,
        }
    }

    // ─── Persistence ──────────────────────────────────────────────────────────

    pub fn load_watchlist(&self) -> Vec<Stock> {
        self.watchlist.load()
    }

    pub fn save_watchlist(&self, stocks: &[Stock]) {
        self.watchlist.save(stocks);
    }

    pub fn load_sort_order(&self) -> String {
        self.watchlist.load_sort_order()
    }

    pub fn save_sort_order(&self, order: &str) {
        self.watchlist.save_sort_order(order);
    }

    // ─── Search ───────────────────────────────────────────────────────────────

    /// Search for stocks. Returns an async channel receiver for the result.
    pub fn search_stocks(
        &self,
        input: &str,
        existing_symbols: &[String],
    ) -> Receiver<SearchResult> {
        let (tx, rx) = async_channel::bounded(1);

        let symbols: Vec<String> = input
            .split(',')
            .map(|s| s.trim().to_uppercase())
            .filter(|s| !s.is_empty())
            .filter(|s| !existing_symbols.contains(s))
            .collect();

        if symbols.is_empty() {
            let _ = tx.try_send((HashMap::new(), vec![]));
            return rx;
        }

        let yahoo = Arc::clone(&self.yahoo);
        let rt = Arc::clone(&self.runtime);

        std::thread::spawn(move || {
            let result = rt.block_on(yahoo.fetch(&symbols));
            let _ = tx.try_send(result);
        });

        rx
    }

    // ─── Refresh ──────────────────────────────────────────────────────────────

    /// Refresh prices for existing stocks. Returns an async channel receiver.
    pub fn refresh_stocks(&self, symbols: Vec<String>) -> Option<Receiver<RefreshResult>> {
        if symbols.is_empty() {
            return None;
        }

        let (tx, rx) = async_channel::bounded(1);
        let yahoo = Arc::clone(&self.yahoo);
        let rt = Arc::clone(&self.runtime);

        std::thread::spawn(move || {
            let result = rt.block_on(yahoo.refresh(&symbols));
            let _ = tx.try_send(result);
        });

        Some(rx)
    }

    // ─── Alert checking ───────────────────────────────────────────────────────

    pub fn check_alerts(
        &self,
        alert_manager: &mut AlertManager,
        prices: &HashMap<String, f64>,
    ) -> Vec<(String, String)> {
        alert_manager.check_all_alerts(prices)
    }

    // ─── Auto-refresh ───────────────────────────────────────────────────────────

    pub fn start_auto_refresh<F>(&mut self, callback: F)
    where
        F: Fn() + 'static,
    {
        self.stop_auto_refresh();
        let source = glib::timeout_add_seconds_local(60, move || {
            callback();
            glib::ControlFlow::Continue
        });
        self.refresh_source = Some(source);
    }

    pub fn stop_auto_refresh(&mut self) {
        if let Some(source) = self.refresh_source.take() {
            source.remove();
        }
    }
}

impl Default for StockController {
    fn default() -> Self {
        Self::new()
    }
}
