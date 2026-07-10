// data_cache.rs
//
// Copyright 2025 Flávio de Vasconcellos Corrêa
//
// SPDX-License-Identifier: GPL-3.0-or-later

use std::collections::HashMap;
use std::fs;
use std::path::PathBuf;
use std::time::{SystemTime, UNIX_EPOCH};

use serde::{Deserialize, Serialize};
use tracing::{debug, error, warn};

use crate::stock::Stock;

const DEFAULT_TTL_SECONDS: u64 = 300; // 5 minutes

#[derive(Serialize, Deserialize, Debug)]
struct CacheEntry {
    fetched_at: u64,
    stock: Stock,
}

#[derive(Serialize, Deserialize, Debug, Default)]
struct CacheFile {
    entries: HashMap<String, CacheEntry>,
}

/// Local disk cache for Yahoo Finance data with TTL support.
pub struct DataCache {
    file_path: PathBuf,
    ttl_seconds: u64,
}

impl DataCache {
    pub fn new(app_name: &str) -> Self {
        let cache_dir = glib::user_cache_dir().join(app_name);
        fs::create_dir_all(&cache_dir).ok();
        let file_path = cache_dir.join("quotes.json");
        debug!(cache_file = %file_path.display(), "data cache path");
        Self {
            file_path,
            ttl_seconds: DEFAULT_TTL_SECONDS,
        }
    }

    /// Load cache file from disk.
    fn load(&self) -> CacheFile {
        if !self.file_path.exists() {
            return CacheFile::default();
        }
        match fs::read_to_string(&self.file_path) {
            Ok(content) => serde_json::from_str(&content).unwrap_or_else(|e| {
                error!(error = %e, "failed to parse cache file");
                CacheFile::default()
            }),
            Err(e) => {
                error!(error = %e, "failed to read cache file");
                CacheFile::default()
            }
        }
    }

    fn save(&self, cache: &CacheFile) {
        match serde_json::to_string_pretty(cache) {
            Ok(json) => {
                if let Err(e) = fs::write(&self.file_path, json) {
                    error!(error = %e, "failed to write cache file");
                }
            }
            Err(e) => error!(error = %e, "failed to serialize cache"),
        }
    }

    fn now() -> u64 {
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs()
    }

    /// Return cached stocks that are still fresh for the given symbols.
    pub fn get_fresh(&self, symbols: &[String]) -> HashMap<String, Stock> {
        let cache = self.load();
        let now = Self::now();
        let mut fresh = HashMap::new();

        for symbol in symbols {
            if let Some(entry) = cache.entries.get(symbol) {
                let age = now.saturating_sub(entry.fetched_at);
                if age <= self.ttl_seconds {
                    debug!(symbol, age, "cache hit");
                    fresh.insert(symbol.clone(), entry.stock.clone());
                } else {
                    debug!(symbol, age, "cache expired");
                }
            }
        }

        fresh
    }

    /// Store stocks in the cache.
    pub fn put(&self, stocks: &HashMap<String, Stock>) {
        let mut cache = self.load();
        let now = Self::now();
        for (symbol, stock) in stocks {
            cache.entries.insert(
                symbol.clone(),
                CacheEntry {
                    fetched_at: now,
                    stock: stock.clone(),
                },
            );
        }
        self.save(&cache);
        debug!(count = stocks.len(), "wrote stocks to cache");
    }

    /// Clear all cached entries.
    #[allow(dead_code)]
    pub fn clear(&self) {
        if let Err(e) = fs::remove_file(&self.file_path) {
            warn!(error = %e, "failed to remove cache file");
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::env;

    fn temp_cache() -> DataCache {
        let dir = env::temp_dir().join(format!("merkato-test-{:?}", std::thread::current().id()));
        fs::create_dir_all(&dir).unwrap();
        DataCache {
            file_path: dir.join("quotes.json"),
            ttl_seconds: DEFAULT_TTL_SECONDS,
        }
    }

    fn dummy_stock(symbol: &str) -> Stock {
        let mut stock = Stock::new(symbol);
        stock.price = 123.45;
        stock
    }

    #[test]
    fn cache_roundtrip() {
        let cache = temp_cache();
        let mut stocks = HashMap::new();
        stocks.insert("AAPL".to_string(), dummy_stock("AAPL"));
        cache.put(&stocks);

        let fresh = cache.get_fresh(&["AAPL".to_string()]);
        assert_eq!(fresh.len(), 1);
        assert_eq!(fresh["AAPL"].symbol, "AAPL");
        assert!((fresh["AAPL"].price - 123.45).abs() < f64::EPSILON);
    }

    #[test]
    fn cache_expires_after_ttl() {
        let cache = temp_cache();
        let mut stocks = HashMap::new();
        stocks.insert("AAPL".to_string(), dummy_stock("AAPL"));
        cache.put(&stocks);

        // Simulate expired cache by backdating entry
        let mut expired = cache.load();
        expired
            .entries
            .get_mut("AAPL")
            .unwrap()
            .fetched_at = DataCache::now().saturating_sub(DEFAULT_TTL_SECONDS + 1);
        cache.save(&expired);

        let fresh = cache.get_fresh(&["AAPL".to_string()]);
        assert!(fresh.is_empty());
    }
}
