// alert_manager.rs
//
// Copyright 2025 Flávio de Vasconcellos Corrêa
//
// SPDX-License-Identifier: GPL-3.0-or-later

use std::collections::HashMap;
use std::fs;
use std::path::PathBuf;

use serde::{Deserialize, Serialize};

use crate::alert::{Alert, AlertType};

#[derive(Serialize, Deserialize, Default)]
struct AlertFile {
    alerts: Vec<Alert>,
}

/// Manages price alerts: CRUD operations and persistence.
pub struct AlertManager {
    alerts: HashMap<String, Alert>,
    file_path: PathBuf,
}

impl std::fmt::Debug for AlertManager {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("AlertManager")
            .field("alerts", &self.alerts)
            .field("file_path", &self.file_path)
            .finish()
    }
}


impl AlertManager {
    pub fn new(app_name: &str) -> Self {
        let config_dir = glib::user_config_dir().join(app_name);
        fs::create_dir_all(&config_dir).ok();

        let file_path = config_dir.join("alerts.json");
        let mut mgr = Self { alerts: HashMap::new(), file_path };
        mgr.load();
        mgr
    }

    // ─── Persistence ────────────────────────────────────────────────────────────

    pub fn load(&mut self) {
        if !self.file_path.exists() {
            return;
        }
        match fs::read_to_string(&self.file_path) {
            Ok(content) => match serde_json::from_str::<AlertFile>(&content) {
                Ok(data) => {
                    self.alerts = data
                        .alerts
                        .into_iter()
                        .map(|a| (a.alert_id.clone(), a))
                        .collect();
                    eprintln!("Loaded {} alerts", self.alerts.len());
                }
                Err(e) => eprintln!("ERROR: Failed to parse alerts: {e}"),
            },
            Err(e) => eprintln!("ERROR: Failed to read alerts: {e}"),
        }
    }

    pub fn save(&self) -> bool {
        let data = AlertFile {
            alerts: self.alerts.values().cloned().collect(),
        };
        match serde_json::to_string_pretty(&data) {
            Ok(json) => fs::write(&self.file_path, json).is_ok(),
            Err(_) => false,
        }
    }

    // ─── CRUD ────────────────────────────────────────────────────────────────────

    pub fn add_alert(
        &mut self,
        symbol: &str,
        alert_type: AlertType,
        target_price: f64,
    ) -> &Alert {
        let alert = Alert::new(symbol, alert_type, target_price);
        let id = alert.alert_id.clone();
        self.alerts.insert(id.clone(), alert);
        self.save();
        self.alerts.get(&id).unwrap()
    }

    pub fn remove_alert(&mut self, alert_id: &str) -> bool {
        if self.alerts.remove(alert_id).is_some() {
            self.save();
            true
        } else {
            false
        }
    }

    pub fn get_alert(&self, alert_id: &str) -> Option<&Alert> {
        self.alerts.get(alert_id)
    }

    pub fn get_alert_mut(&mut self, alert_id: &str) -> Option<&mut Alert> {
        self.alerts.get_mut(alert_id)
    }

    pub fn all_alerts(&self) -> Vec<&Alert> {
        let mut alerts: Vec<&Alert> = self.alerts.values().collect();
        alerts.sort_by(|a, b| a.created_at.cmp(&b.created_at));
        alerts
    }

    pub fn active_alerts(&self) -> Vec<&Alert> {
        self.all_alerts()
            .into_iter()
            .filter(|a| a.enabled && !a.is_triggered())
            .collect()
    }

    pub fn triggered_alerts(&self) -> Vec<&Alert> {
        self.all_alerts()
            .into_iter()
            .filter(|a| a.is_triggered())
            .collect()
    }

    pub fn disabled_alerts(&self) -> Vec<&Alert> {
        self.all_alerts()
            .into_iter()
            .filter(|a| !a.enabled && !a.is_triggered())
            .collect()
    }

    // ─── Alert Checking ──────────────────────────────────────────────────────────

    /// Check all alerts against new prices. Returns triggered alert IDs with symbols.
    pub fn check_all_alerts(&mut self, prices: &HashMap<String, f64>) -> Vec<(String, String)> {
        let mut triggered = Vec::new();

        for alert in self.alerts.values_mut() {
            if let Some(&price) = prices.get(&alert.symbol) {
                alert.last_price = price;
                if alert.check_condition(price) {
                    alert.trigger();
                    triggered.push((alert.alert_id.clone(), alert.symbol.clone()));
                }
            }
        }

        if !triggered.is_empty() {
            self.save();
        }

        triggered
    }

    /// Set alert enabled/disabled state.
    pub fn set_enabled(&mut self, alert_id: &str, enabled: bool) {
        if let Some(alert) = self.alerts.get_mut(alert_id) {
            alert.enabled = enabled;
        }
        self.save();
    }

    /// Reset a triggered alert.
    pub fn reset_alert(&mut self, alert_id: &str) {
        if let Some(alert) = self.alerts.get_mut(alert_id) {
            alert.reset();
        }
        self.save();
    }

    /// Remove all triggered alerts.
    pub fn clear_triggered(&mut self) {
        self.alerts.retain(|_, a| !a.is_triggered());
        self.save();
    }

    /// Remove all alerts.
    pub fn clear_all(&mut self) {
        self.alerts.clear();
        self.save();
    }

    pub fn count(&self) -> usize {
        self.alerts.len()
    }

    pub fn active_count(&self) -> usize {
        self.active_alerts().len()
    }

    pub fn triggered_count(&self) -> usize {
        self.triggered_alerts().len()
    }
}
