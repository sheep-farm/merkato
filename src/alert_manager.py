# alert_manager.py
#
# Copyright 2025 Flávio de Vasconcellos Corrêa
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

import json
import os
from gi.repository import GLib, GObject
from datetime import datetime
from typing import List, Optional, Dict

from .alert import Alert


class AlertManager(GObject.Object):
    """
    Price alert manager.
    Responsible for CRUD, persistence and alert verification.
    """
    __gtype_name__ = 'AlertManager'

    __gsignals__ = {
        'alert-triggered': (GObject.SignalFlags.RUN_FIRST, None, (Alert,)),
        'alerts-changed': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def __init__(self, app_name='merkato'):
        super().__init__()
        config_dir = os.path.join(GLib.get_user_config_dir(), app_name)
        os.makedirs(config_dir, exist_ok=True)

        self.alerts_file = os.path.join(config_dir, 'alerts.json')
        print(f"Alerts file: {self.alerts_file}")

        self._alerts: List[Alert] = []

    # ============== CRUD Operations ==============

    def add_alert(self, alert: Alert) -> bool:
        """
        Add a new alert.

        Args:
            alert: Alert object to add

        Returns:
            True if successfully added
        """
        try:
            self._alerts.append(alert)
            self.save()
            self.emit('alerts-changed')
            print(f"Alert added: {alert}")
            return True
        except Exception as e:
            print(f"ERROR: Failed to add alert: {e}")
            return False

    def remove_alert(self, alert_id: str) -> bool:
        """
        Remove an alert by ID.

        Args:
            alert_id: ID of the alert to remove

        Returns:
            True if successfully removed
        """
        try:
            self._alerts = [a for a in self._alerts if a.alert_id != alert_id]
            self.save()
            self.emit('alerts-changed')
            print(f"Alert removed: {alert_id}")
            return True
        except Exception as e:
            print(f"ERROR: Failed to remove alert: {e}")
            return False

    def update_alert(self, alert: Alert) -> bool:
        """
        Update an existing alert.

        Args:
            alert: Updated Alert object

        Returns:
            True if successfully updated
        """
        try:
            for i, a in enumerate(self._alerts):
                if a.alert_id == alert.alert_id:
                    self._alerts[i] = alert
                    self.save()
                    self.emit('alerts-changed')
                    print(f"Alert updated: {alert}")
                    return True
            return False
        except Exception as e:
            print(f"ERROR: Failed to update alert: {e}")
            return False

    def get_alert(self, alert_id: str) -> Optional[Alert]:
        """
        Find an alert by ID.

        Args:
            alert_id: Alert ID

        Returns:
            Alert object or None if not found
        """
        for alert in self._alerts:
            if alert.alert_id == alert_id:
                return alert
        return None

    def get_all_alerts(self) -> List[Alert]:
        """
        Return all alerts.

        Returns:
            List of Alert objects
        """
        return self._alerts.copy()

    def get_alerts_for_symbol(self, symbol: str) -> List[Alert]:
        """
        Return all alerts for a specific symbol.

        Args:
            symbol: Ticker symbol

        Returns:
            List of Alert objects
        """
        return [a for a in self._alerts if a.symbol == symbol]

    def get_active_alerts(self) -> List[Alert]:
        """
        Return only active alerts (enabled=True and not triggered).

        Returns:
            List of active Alert objects
        """
        return [a for a in self._alerts if a.enabled and not a.is_triggered()]

    def get_triggered_alerts(self) -> List[Alert]:
        """
        Return only triggered alerts.

        Returns:
            List of triggered Alert objects
        """
        return [a for a in self._alerts if a.is_triggered()]

    # ============== Alert Verification ==============

    def check_alerts(self, symbol: str, current_price: float) -> List[Alert]:
        """
        Check if any alert should be triggered for a symbol.

        Args:
            symbol: Ticker symbol
            current_price: Current price

        Returns:
            List of alerts that were triggered
        """
        triggered = []

        for alert in self._alerts:
            if alert.symbol != symbol:
                continue

            # Update last price
            alert.last_price = current_price

            # Check condition
            if alert.check_condition(current_price):
                alert.trigger()
                triggered.append(alert)
                print(f"ALERT TRIGGERED: {alert}")
                self.emit('alert-triggered', alert)

        if triggered:
            self.save()
            self.emit('alerts-changed')

        return triggered

    def check_all_alerts(self, prices: Dict[str, float]) -> List[Alert]:
        """
        Check alerts for multiple symbols.

        Args:
            prices: Dictionary {symbol: price}

        Returns:
            List of all triggered alerts
        """
        all_triggered = []
        for symbol, price in prices.items():
            triggered = self.check_alerts(symbol, price)
            all_triggered.extend(triggered)
        return all_triggered

    # ============== Persistence ==============

    def load(self) -> bool:
        """
        Load alerts from file.

        Returns:
            True if successfully loaded
        """
        if not os.path.exists(self.alerts_file):
            print("No saved alerts found")
            return True

        try:
            with open(self.alerts_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            alerts_data = data.get('alerts', [])
            self._alerts = [Alert.from_dict(a) for a in alerts_data]

            print(f"Loaded {len(self._alerts)} alerts")
            self.emit('alerts-changed')
            return True

        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON in alerts file: {e}")
            return False
        except Exception as e:
            print(f"ERROR: Failed to load alerts: {e}")
            return False

    def save(self) -> bool:
        """
        Save alerts to file.

        Returns:
            True if successfully saved
        """
        try:
            alerts_data = [a.to_dict() for a in self._alerts]

            data = {
                'alerts': alerts_data,
                'last_updated': datetime.now().isoformat(),
                'version': '0.2.1'
            }

            with open(self.alerts_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"Saved {len(self._alerts)} alerts")
            return True

        except Exception as e:
            print(f"ERROR: Failed to save alerts: {e}")
            return False

    def clear(self) -> bool:
        """
        Remove all alerts.

        Returns:
            True if successfully removed
        """
        self._alerts = []
        result = self.save()
        self.emit('alerts-changed')
        return result

    # ============== Statistics ==============

    def get_count(self) -> int:
        """Return total number of alerts."""
        return len(self._alerts)

    def get_active_count(self) -> int:
        """Return number of active alerts."""
        return len(self.get_active_alerts())

    def get_triggered_count(self) -> int:
        """Return number of triggered alerts."""
        return len(self.get_triggered_alerts())

    def get_stats(self) -> dict:
        """
        Return alert statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            'total': self.get_count(),
            'active': self.get_active_count(),
            'triggered': self.get_triggered_count(),
            'disabled': len([a for a in self._alerts if not a.enabled]),
        }
