// alert.rs
//
// Copyright 2025 Flávio de Vasconcellos Corrêa
//
// SPDX-License-Identifier: GPL-3.0-or-later

use chrono::Local;
use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum AlertType {
    Above,
    Below,
}

impl AlertType {
    pub fn display(&self) -> &'static str {
        match self {
            AlertType::Above => "Above",
            AlertType::Below => "Below",
        }
    }

    pub fn from_str(s: &str) -> Self {
        match s {
            "below" => AlertType::Below,
            _ => AlertType::Above,
        }
    }

    pub fn as_str(&self) -> &'static str {
        match self {
            AlertType::Above => "above",
            AlertType::Below => "below",
        }
    }
}

/// A price alert for a financial instrument.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Alert {
    pub alert_id: String,
    pub symbol: String,
    pub alert_type: AlertType,
    pub target_price: f64,
    pub enabled: bool,
    pub created_at: String,
    pub triggered_at: Option<String>,
    pub last_price: f64,
}

impl Alert {
    pub fn new(symbol: impl Into<String>, alert_type: AlertType, target_price: f64) -> Self {
        Self {
            alert_id: Uuid::new_v4().to_string(),
            symbol: symbol.into(),
            alert_type,
            target_price,
            enabled: true,
            created_at: Local::now().to_rfc3339(),
            triggered_at: None,
            last_price: 0.0,
        }
    }

    pub fn is_triggered(&self) -> bool {
        self.triggered_at.is_some()
    }

    /// Returns true if the current price satisfies the alert condition.
    pub fn check_condition(&self, current_price: f64) -> bool {
        if !self.enabled || self.is_triggered() {
            return false;
        }
        match self.alert_type {
            AlertType::Above => current_price >= self.target_price,
            AlertType::Below => current_price <= self.target_price,
        }
    }

    pub fn trigger(&mut self) {
        self.triggered_at = Some(Local::now().to_rfc3339());
    }

    pub fn reset(&mut self) {
        self.triggered_at = None;
    }

    pub fn status_display(&self) -> &'static str {
        if !self.enabled {
            "Disabled"
        } else if self.is_triggered() {
            "Triggered"
        } else {
            "Active"
        }
    }
}

impl std::fmt::Display for Alert {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(
            f,
            "{}: {} {}",
            self.symbol,
            self.alert_type.display(),
            self.target_price
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn above_alert_triggers_when_price_reaches_target() {
        let alert = Alert::new("AAPL", AlertType::Above, 150.0);
        assert!(alert.check_condition(150.0));
        assert!(alert.check_condition(155.0));
        assert!(!alert.check_condition(149.99));
    }

    #[test]
    fn below_alert_triggers_when_price_drops_to_target() {
        let alert = Alert::new("AAPL", AlertType::Below, 150.0);
        assert!(alert.check_condition(150.0));
        assert!(alert.check_condition(145.0));
        assert!(!alert.check_condition(150.01));
    }

    #[test]
    fn triggered_alert_does_not_trigger_again() {
        let mut alert = Alert::new("AAPL", AlertType::Above, 150.0);
        assert!(alert.check_condition(155.0));
        alert.trigger();
        assert!(!alert.check_condition(160.0));
    }

    #[test]
    fn disabled_alert_never_triggers() {
        let mut alert = Alert::new("AAPL", AlertType::Above, 150.0);
        alert.enabled = false;
        assert!(!alert.check_condition(200.0));
    }
}
