// watchlist_manager.rs
//
// Copyright 2025 Flávio de Vasconcellos Corrêa
//
// SPDX-License-Identifier: GPL-3.0-or-later

use std::fs;
use std::path::PathBuf;

use chrono::Local;
use serde::{Deserialize, Serialize};

use crate::stock::Stock;

#[derive(Serialize, Deserialize)]
struct WatchlistFile {
    stocks: Vec<Stock>,
    last_updated: String,
    version: String,
}

pub struct WatchlistManager {
    watchlist_file: PathBuf,
    sort_file: PathBuf,
}

impl WatchlistManager {
    pub fn new(app_name: &str) -> Self {
        let config_dir = glib::user_config_dir().join(app_name);
        fs::create_dir_all(&config_dir).ok();

        let watchlist_file = config_dir.join("watchlist.json");
        let sort_file = config_dir.join("sort_order.txt");

        eprintln!("Watchlist file: {}", watchlist_file.display());

        Self { watchlist_file, sort_file }
    }

    pub fn load(&self) -> Vec<Stock> {
        if !self.watchlist_file.exists() {
            eprintln!("No saved watchlist found");
            return Vec::new();
        }

        match fs::read_to_string(&self.watchlist_file) {
            Ok(content) => match serde_json::from_str::<WatchlistFile>(&content) {
                Ok(data) => {
                    eprintln!(
                        "Loaded {} tickers from watchlist (last updated: {})",
                        data.stocks.len(),
                        data.last_updated
                    );
                    data.stocks
                }
                Err(e) => {
                    eprintln!("ERROR: Invalid JSON in watchlist file: {e}");
                    Vec::new()
                }
            },
            Err(e) => {
                eprintln!("ERROR: Failed to load watchlist: {e}");
                Vec::new()
            }
        }
    }

    pub fn save(&self, stocks: &[Stock]) -> bool {
        let data = WatchlistFile {
            stocks: stocks.to_vec(),
            last_updated: Local::now().to_rfc3339(),
            version: "0.2.0".to_string(),
        };

        match serde_json::to_string_pretty(&data) {
            Ok(json) => match fs::write(&self.watchlist_file, json.as_bytes()) {
                Ok(_) => {
                    eprintln!("Saved {} tickers to watchlist", stocks.len());
                    true
                }
                Err(e) => {
                    eprintln!("ERROR: Failed to write watchlist: {e}");
                    false
                }
            },
            Err(e) => {
                eprintln!("ERROR: Failed to serialize watchlist: {e}");
                false
            }
        }
    }

    pub fn save_sort_order(&self, sort_order: &str) -> bool {
        match fs::write(&self.sort_file, sort_order) {
            Ok(_) => true,
            Err(e) => {
                eprintln!("Error saving sort order: {e}");
                false
            }
        }
    }

    pub fn load_sort_order(&self) -> String {
        if self.sort_file.exists() {
            fs::read_to_string(&self.sort_file)
                .unwrap_or_else(|_| "alphabetical".to_string())
                .trim()
                .to_string()
        } else {
            "alphabetical".to_string()
        }
    }

    #[allow(dead_code)]
    pub fn clear(&self) -> bool {
        self.save(&[])
    }

    #[allow(dead_code)]
    pub fn exists(&self) -> bool {
        self.watchlist_file.exists()
    }

    #[allow(dead_code)]
    pub fn file_path(&self) -> &PathBuf {
        &self.watchlist_file
    }
}
