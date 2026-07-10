// category_model.rs
//
// Copyright 2025 Flávio de Vasconcellos Corrêa
//
// SPDX-License-Identifier: GPL-3.0-or-later

use std::collections::HashMap;

use crate::stock::Stock;

#[derive(Debug, Clone)]
pub enum CategoryFilter {
    All,
    QuoteType(String),
    Sector(String),
    Others,
}

#[derive(Debug, Clone)]
pub struct CategoryInfo {
    pub key: &'static str,
    pub label: &'static str,
    pub icon: &'static str,
    pub filter: CategoryFilter,
}

/// All predefined categories (14 total, matching the Python implementation).
pub fn all_categories() -> Vec<CategoryInfo> {
    vec![
        CategoryInfo { key: "All",               label: "All Stocks",            icon: "view-list-symbolic",         filter: CategoryFilter::All },
        CategoryInfo { key: "Cryptocurrency",    label: "Cryptocurrency",         icon: "coin-symbolic",              filter: CategoryFilter::QuoteType("CRYPTOCURRENCY".into()) },
        CategoryInfo { key: "Technology",        label: "Technology",             icon: "computer-symbolic",          filter: CategoryFilter::Sector("Technology".into()) },
        CategoryInfo { key: "Healthcare",        label: "Healthcare",             icon: "hospital-symbolic",          filter: CategoryFilter::Sector("Healthcare".into()) },
        CategoryInfo { key: "Energy",            label: "Energy",                 icon: "lightning-symbolic",         filter: CategoryFilter::Sector("Energy".into()) },
        CategoryInfo { key: "Financial",         label: "Financial Services",     icon: "bank-symbolic",              filter: CategoryFilter::Sector("Financial Services".into()) },
        CategoryInfo { key: "Consumer Cyclical", label: "Consumer Cyclical",      icon: "shopping-cart-symbolic",     filter: CategoryFilter::Sector("Consumer Cyclical".into()) },
        CategoryInfo { key: "Consumer Defensive",label: "Consumer Defensive",     icon: "food-apple-symbolic",        filter: CategoryFilter::Sector("Consumer Defensive".into()) },
        CategoryInfo { key: "Industrial",        label: "Industrial",             icon: "emblem-system-symbolic",     filter: CategoryFilter::Sector("Industrials".into()) },
        CategoryInfo { key: "Real Estate",       label: "Real Estate",            icon: "home-symbolic",              filter: CategoryFilter::Sector("Real Estate".into()) },
        CategoryInfo { key: "Basic Materials",   label: "Basic Materials",        icon: "applications-science-symbolic", filter: CategoryFilter::Sector("Basic Materials".into()) },
        CategoryInfo { key: "Communication",     label: "Communication Services", icon: "network-wireless-symbolic",  filter: CategoryFilter::Sector("Communication Services".into()) },
        CategoryInfo { key: "Utilities",         label: "Utilities",              icon: "utilities-terminal-symbolic",filter: CategoryFilter::Sector("Utilities".into()) },
        CategoryInfo { key: "Others",            label: "Others",                 icon: "folder-symbolic",            filter: CategoryFilter::Others },
    ]
}

/// Stock categorization model.
#[derive(Debug, Default)]
pub struct CategoryModel {
    stocks: HashMap<String, Stock>,
    current_category: String,
}

impl CategoryModel {
    pub fn new() -> Self {
        Self {
            stocks: HashMap::new(),
            current_category: "All".to_string(),
        }
    }

    pub fn current_category(&self) -> &str {
        &self.current_category
    }

    pub fn set_current_category(&mut self, category: &str) {
        self.current_category = category.to_string();
    }

    pub fn add_stock(&mut self, stock: Stock) {
        self.stocks.insert(stock.symbol.clone(), stock);
    }

    pub fn update_stock(&mut self, stock: Stock) {
        self.stocks.insert(stock.symbol.clone(), stock);
    }

    pub fn remove_stock(&mut self, symbol: &str) {
        self.stocks.remove(symbol);
    }

    pub fn clear_all(&mut self) {
        self.stocks.clear();
    }

    pub fn get_stocks_by_category(&self, category: &str) -> Vec<&Stock> {
        let cats = all_categories();
        match cats.iter().find(|c| c.key == category) {
            None => vec![],
            Some(info) => match &info.filter {
                CategoryFilter::All => self.stocks.values().collect(),
                CategoryFilter::Others => self.get_uncategorized(),
                CategoryFilter::QuoteType(qt) => self.stocks.values().filter(|s| &s.quote_type == qt).collect(),
                CategoryFilter::Sector(sec) => self.stocks.values().filter(|s| &s.sector == sec).collect(),
            },
        }
    }

    fn get_uncategorized(&self) -> Vec<&Stock> {
        let cats = all_categories();
        self.stocks.values().filter(|stock| {
            !cats.iter().any(|cat| match &cat.filter {
                CategoryFilter::All | CategoryFilter::Others => false,
                CategoryFilter::QuoteType(qt) => &stock.quote_type == qt,
                CategoryFilter::Sector(sec) => &stock.sector == sec,
            })
        }).collect()
    }

    pub fn category_count(&self, category: &str) -> usize {
        self.get_stocks_by_category(category).len()
    }

    pub fn all_category_counts(&self) -> HashMap<&'static str, usize> {
        all_categories().iter().map(|c| (c.key, self.category_count(c.key))).collect()
    }

    pub fn current_stocks(&self) -> Vec<&Stock> {
        let cat = self.current_category.clone();
        self.get_stocks_by_category(&cat)
    }

    pub fn has_stocks(&self) -> bool {
        !self.stocks.is_empty()
    }

    pub fn stock_count(&self) -> usize {
        self.stocks.len()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn sample_stock(symbol: &str, sector: &str, quote_type: &str) -> Stock {
        let mut stock = Stock::new(symbol);
        stock.sector = sector.to_string();
        stock.quote_type = quote_type.to_string();
        stock
    }

    #[test]
    fn all_category_returns_everything() {
        let mut model = CategoryModel::new();
        model.add_stock(sample_stock("AAPL", "Technology", "EQUITY"));
        model.add_stock(sample_stock("MSFT", "Technology", "EQUITY"));
        assert_eq!(model.get_stocks_by_category("All").len(), 2);
    }

    #[test]
    fn filter_by_sector() {
        let mut model = CategoryModel::new();
        model.add_stock(sample_stock("AAPL", "Technology", "EQUITY"));
        model.add_stock(sample_stock("PFE", "Healthcare", "EQUITY"));
        assert_eq!(model.get_stocks_by_category("Technology").len(), 1);
        assert_eq!(model.get_stocks_by_category("Healthcare").len(), 1);
    }

    #[test]
    fn cryptocurrency_filter_overrides_sector() {
        let mut model = CategoryModel::new();
        model.add_stock(sample_stock("BTC-USD", "", "CRYPTOCURRENCY"));
        assert_eq!(model.get_stocks_by_category("Cryptocurrency").len(), 1);
    }

    #[test]
    fn counts_match_stocks() {
        let mut model = CategoryModel::new();
        model.add_stock(sample_stock("AAPL", "Technology", "EQUITY"));
        model.add_stock(sample_stock("PFE", "Healthcare", "EQUITY"));
        let counts = model.all_category_counts();
        assert_eq!(counts["All"], 2);
        assert_eq!(counts["Technology"], 1);
        assert_eq!(counts["Healthcare"], 1);
    }
}
