# alert.py
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

from gi.repository import GObject
from datetime import datetime
import uuid


class Alert(GObject.Object):
    """
    Data model to represent a price alert.
    """
    __gtype_name__ = 'Alert'

    def __init__(
        self,
        alert_id: str = None,
        symbol: str = '',
        alert_type: str = 'above',  # 'above' or 'below'
        target_price: float = 0.0,
        enabled: bool = True,
        created_at: str = None,
        triggered_at: str = None,
        last_price: float = 0.0,
    ):
        """
        Initialize an Alert.

        Args:
            alert_id: Unique alert ID
            symbol: Ticker symbol (e.g. 'AAPL')
            alert_type: Alert type ('above' for maximum, 'below' for minimum)
            target_price: Target price
            enabled: Whether the alert is active
            created_at: Creation date (ISO format)
            triggered_at: Date when triggered (ISO format or None)
            last_price: Last checked price
        """
        super().__init__()
        self._alert_id = alert_id or str(uuid.uuid4())
        self._symbol = symbol
        self._alert_type = alert_type
        self._target_price = target_price
        self._enabled = enabled
        self._created_at = created_at or datetime.now().isoformat()
        self._triggered_at = triggered_at
        self._last_price = last_price

    @GObject.Property(type=str)
    def alert_id(self) -> str:
        """Unique alert ID."""
        return self._alert_id

    @alert_id.setter
    def alert_id(self, value: str):
        self._alert_id = value

    @GObject.Property(type=str)
    def symbol(self) -> str:
        """Ticker symbol."""
        return self._symbol

    @symbol.setter
    def symbol(self, value: str):
        self._symbol = value

    @GObject.Property(type=str)
    def alert_type(self) -> str:
        """Alert type (above/below)."""
        return self._alert_type

    @alert_type.setter
    def alert_type(self, value: str):
        self._alert_type = value

    @GObject.Property(type=float)
    def target_price(self) -> float:
        """Target price."""
        return self._target_price

    @target_price.setter
    def target_price(self, value: float):
        self._target_price = value

    @GObject.Property(type=bool, default=True)
    def enabled(self) -> bool:
        """Whether the alert is active."""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        self._enabled = value

    @GObject.Property(type=str)
    def created_at(self) -> str:
        """Creation date."""
        return self._created_at

    @created_at.setter
    def created_at(self, value: str):
        self._created_at = value

    @GObject.Property(type=str)
    def triggered_at(self) -> str:
        """Date when triggered."""
        return self._triggered_at or ''

    @triggered_at.setter
    def triggered_at(self, value: str):
        self._triggered_at = value

    @GObject.Property(type=float)
    def last_price(self) -> float:
        """Last checked price."""
        return self._last_price

    @last_price.setter
    def last_price(self, value: float):
        self._last_price = value

    # ============== Helper methods ==============

    def is_triggered(self) -> bool:
        """
        Check if the alert has been triggered.

        Returns:
            True if triggered_at is not None
        """
        return self._triggered_at is not None and self._triggered_at != ''

    def check_condition(self, current_price: float) -> bool:
        """
        Check if the alert condition has been met.

        Args:
            current_price: Current stock price

        Returns:
            True if the condition has been met
        """
        if not self._enabled:
            return False

        if self.is_triggered():
            return False

        if self._alert_type == 'above':
            return current_price >= self._target_price
        elif self._alert_type == 'below':
            return current_price <= self._target_price

        return False

    def trigger(self):
        """Mark the alert as triggered."""
        self._triggered_at = datetime.now().isoformat()
        self.notify('triggered-at')

    def reset(self):
        """Reset the alert (clear triggered_at)."""
        self._triggered_at = None
        self.notify('triggered-at')

    def get_display_type(self) -> str:
        """
        Return readable type for display.

        Returns:
            'Above' or 'Below'
        """
        return 'Above' if self._alert_type == 'above' else 'Below'

    def get_status_display(self) -> str:
        """
        Return alert status for display.

        Returns:
            'Active', 'Triggered', or 'Disabled'
        """
        if not self._enabled:
            return 'Disabled'
        elif self.is_triggered():
            return 'Triggered'
        else:
            return 'Active'

    def to_dict(self) -> dict:
        """
        Convert the Alert to a dictionary.

        Returns:
            Dictionary with all alert data
        """
        return {
            'alert_id': self._alert_id,
            'symbol': self._symbol,
            'alert_type': self._alert_type,
            'target_price': self._target_price,
            'enabled': self._enabled,
            'created_at': self._created_at,
            'triggered_at': self._triggered_at,
            'last_price': self._last_price,
        }

    @classmethod
    def from_dict(cls, data: dict):
        """
        Create an Alert from a dictionary.

        Args:
            data: Dictionary with alert data

        Returns:
            Alert instance
        """
        return cls(
            alert_id=data.get('alert_id'),
            symbol=data.get('symbol', ''),
            alert_type=data.get('alert_type', 'above'),
            target_price=data.get('target_price', 0.0),
            enabled=data.get('enabled', True),
            created_at=data.get('created_at'),
            triggered_at=data.get('triggered_at'),
            last_price=data.get('last_price', 0.0),
        )

    def __str__(self) -> str:
        """String representation of the Alert."""
        return f"{self.symbol}: {self.get_display_type()} {self.target_price}"

    def __repr__(self) -> str:
        """Technical representation of the Alert."""
        return (
            f"Alert(symbol='{self.symbol}', "
            f"type='{self.alert_type}', "
            f"target={self.target_price}, "
            f"status='{self.get_status_display()}')"
        )
