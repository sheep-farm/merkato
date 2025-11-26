# window.py
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

from datetime import datetime
from gi.repository import Adw, Gtk, Gio, GLib

from .search_stock import MerkatoSearchStock
from .list_stock import MerkatoListStock
from .stock_controller import StockController
from .stock import Stock
from .category_model import CategoryModel
from .heatmap_view import HeatmapView
from .alerts_view import AlertsView
from .alert_dialog import AlertDialog


@Gtk.Template(resource_path='/com/github/sheepfarm/merkato/window.ui')
class MerkatoWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'MerkatoWindow'

    # Template children
    split_view = Gtk.Template.Child()
    sidebar_toggle = Gtk.Template.Child()
    category_list = Gtk.Template.Child()
    view_stack = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()
    search_stock_entry = Gtk.Template.Child()
    list_stock = Gtk.Template.Child()
    heatmap_view = Gtk.Template.Child()
    alerts_view = Gtk.Template.Child()
    spinner = Gtk.Template.Child()
    last_updated_label = Gtk.Template.Child()
    trash_view_mode = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.settings = Gio.Settings.new('com.ekonomikas.merkato')

        # Restore window size
        width = self.settings.get_int('window-width')
        height = self.settings.get_int('window-height')
        is_maximized = self.settings.get_boolean('window-maximized')
        
        if width > 0 and height > 0:
            self.set_default_size(width, height)
        if is_maximized:
            self.maximize()

        # Initialize controller
        self.controller = StockController(update_interval=60)

        # Initialize category model
        self.category_model = CategoryModel()

        # Populate category sidebar
        self._populate_category_sidebar()

        # Connect controller signals
        self._connect_controller_signals()

        # Create actions
        self._create_actions()

        # Connect UI signals
        self._connect_ui_signals()

        # Connect category signals
        self._connect_category_signals()

        # Connect heatmap signals
        self._connect_heatmap_signals()

        # Connect alert signals
        self._connect_alerts_signals()

        # Load watchlist and initialize
        self._initialize()

    def _populate_category_sidebar(self):
        """Populates the sidebar with categories."""
        self.category_rows = {}
        
        for category_key, info in self.category_model.CATEGORIES.items():
            row = Adw.ActionRow()
            row.set_title(info.get('label', category_key))
            row.set_activatable(True)
            row.category_key = category_key
            
            # Ícone
            icon = Gtk.Image.new_from_icon_name(info.get('icon', 'folder-symbolic'))
            icon.set_pixel_size(16)
            row.add_prefix(icon)
            
            # Badge contador
            count_label = Gtk.Label(label="0")
            count_label.add_css_class("dim-label")
            count_label.add_css_class("caption")
            row.add_suffix(count_label)
            row.count_label = count_label
            
            self.category_list.append(row)
            self.category_rows[category_key] = row
        
        # Select "All" by default
        if "All" in self.category_rows:
            self.category_list.select_row(self.category_rows["All"])

    def _update_category_counts(self):
        """Updates the counters in categories."""
        for category_key, row in self.category_rows.items():
            count = self.category_model.get_category_count(category_key)
            row.count_label.set_label(str(count))

    def _create_actions(self):
        """Creates window actions."""
        self.refresh_action = self._create_action('refresh', self.on_refresh_action)

        sort_action = Gio.SimpleAction.new_stateful(
            "sort",
            GLib.VariantType.new("s"),
            GLib.Variant("s", "alphabetical")
        )
        sort_action.connect("activate", self.on_sort_action)
        self.add_action(sort_action)
        self.sort_action = sort_action

    def _create_action(self, name, callback):
        """Helper to create actions."""
        action = Gio.SimpleAction.new(name, None)
        action.connect('activate', callback)
        self.add_action(action)
        return action

    def _connect_controller_signals(self):
        """Connects controller signals."""
        self.controller.connect('search-started', self.on_search_started)
        self.controller.connect('search-completed', self.on_search_completed)
        self.controller.connect('search-error', self.on_search_error)

        self.controller.connect('refresh-started', self.on_refresh_started)
        self.controller.connect('refresh-completed', self.on_refresh_completed)
        self.controller.connect('refresh-error', self.on_refresh_error)

        self.controller.connect('watchlist-loaded', self.on_watchlist_loaded)
        self.controller.connect('stock-added', self.on_stock_added)

    def _connect_ui_signals(self):
        """Connects UI widget signals."""
        self.search_stock_entry.connect('activate', self.on_search_clicked)
        self.search_stock_entry.connect('changed', self.on_search_changed)
        self.connect('close-request', self.on_close_request)

        self.list_stock.connect('empty-state-changed', self.on_empty_state_changed)
        self.list_stock.connect('stock-remove-requested', self.on_stock_remove_requested)
        self.list_stock.connect('add-alert-requested', self.on_add_alert_from_list)

        self.trash_view_mode.connect('toggled', self.on_trash_mode_toggled)
        self.sidebar_toggle.connect('toggled', self.on_sidebar_toggle)

        self.view_stack.connect('notify::visible-child-name', self.on_view_changed)
    
    def _connect_category_signals(self):
        """Connects category signals."""
        self.category_list.connect('row-activated', self.on_category_selected)
        self.category_model.connect('counts-updated', self.on_category_counts_updated)
    
    def _connect_heatmap_signals(self):
        """Connects heatmap signals."""
        self.heatmap_view.connect('stock-selected', self.on_heatmap_stock_selected)

    def _connect_alerts_signals(self):
        """Connect alert signals."""
        # Connect AlertsView to AlertManager
        self.alerts_view.set_alert_manager(self.controller.alert_manager)

        # Connect add alert signal
        self.alerts_view.connect('add-alert-clicked', self.on_add_alert_clicked)

        # Connect triggered alerts signal from controller
        self.controller.connect('alerts-triggered', self.on_alerts_triggered)

    def _initialize(self):
        """Initializes the application."""
        self.load_watchlist()
        self.load_alerts()
        self.on_refresh_action()
        self.controller.start_auto_update()
        self.trash_view_mode.set_visible(not self.list_stock.is_empty())

    # ============== Category Callbacks ==============

    def on_category_selected(self, listbox, row):
        """Callback when a category is selected."""
        if row and hasattr(row, 'category_key'):
            category_key = row.category_key
            self._filter_stocks_by_category(category_key)
    
    def on_category_counts_updated(self, model):
        """Callback when counts are updated."""
        self._update_category_counts()
    
    def on_view_changed(self, stack, param):
        """Callback when the view changes between List and Heatmap."""
        visible_child = stack.get_visible_child_name()

        # Show trash only in List view
        is_list_view = (visible_child == "list")
        self.trash_view_mode.set_visible(is_list_view and not self.list_stock.is_empty())

        # If it was active and switched to heatmap, deactivate
        if not is_list_view and self.trash_view_mode.get_active():
            self.trash_view_mode.set_active(False)

    def on_sidebar_toggle(self, toggle_button):
        """Callback for sidebar toggle."""
        self.split_view.set_show_sidebar(toggle_button.get_active())
    
    def _filter_stocks_by_category(self, category_key):
        """Filters the stock list by category."""
        filtered_stocks = self.category_model.get_stocks_by_category(category_key)

        # Update list
        self.list_stock.clear_all()
        for stock in filtered_stocks:
            self.list_stock.append(stock)
        self.list_stock._apply_sort()

        # Update heatmap WITH THE LIST ORDER
        sorted_stocks = self.list_stock.get_all_stocks()
        self.heatmap_view.set_stocks(sorted_stocks)
    
    # ============== Heatmap Callbacks ==============

    def on_heatmap_stock_selected(self, heatmap, stock):
        """Callback when a stock is selected in the heatmap."""
        url = f"https://finance.yahoo.com/quote/{stock.symbol}/"
        Gio.AppInfo.launch_default_for_uri(url, None)

    # ============== Controller Callbacks ==============

    def on_refresh_started(self, controller):
        """Callback when refresh starts."""
        self.refresh_action.set_enabled(False)
        self.sort_action.set_enabled(False)
        self.spinner.set_spinning(True)
        self.search_stock_entry.freeze(True)
        self.trash_view_mode.set_sensitive(False)

    def on_search_started(self, controller):
        """Callback when search starts."""
        print("DEBUG: on_search_started chamado")
        self.spinner.set_spinning(True)
        self.search_stock_entry.freeze(True)

    def on_search_completed(self, controller, results, errors):
        """Callback when search is completed."""
        print(f"DEBUG: on_search_completed - {len(results)} results, {len(errors)} errors")

        # Show results
        for symbol in results.keys():
            print(f"DEBUG: Result received: {symbol}")

        # Show errors
        if errors:
            print(f"DEBUG: Errors: {errors}")

        self.spinner.set_spinning(False)
        self.search_stock_entry.freeze(False)
        self.search_stock_entry.clear_entry()
        self.update_timestamp()

        # IMPORTANT: Save watchlist after adding stocks
        print("DEBUG: Saving watchlist after search")
        self.save_watchlist()

    def on_search_error(self, controller, error_msg):
        """Callback when a search error occurs."""
        print(f"ERROR: Search Error: {error_msg}")
        self.spinner.set_spinning(False)
        self.search_stock_entry.freeze(False)

    def on_refresh_completed(self, controller, results, errors):
        """Callback when refresh is completed."""
        for symbol, stock in results.items():
            self.category_model.update_stock(stock)
            self.list_stock.update(stock)

        # Update heatmap with list order
        sorted_stocks = self.list_stock.get_all_stocks()
        self.heatmap_view.set_stocks(sorted_stocks)

        self.spinner.set_spinning(False)
        self.search_stock_entry.freeze(False)
        self.trash_view_mode.set_sensitive(True)
        self.refresh_action.set_enabled(True)
        self.sort_action.set_enabled(True)
        self.update_timestamp()

    def on_refresh_error(self, controller, error_msg):
        """Callback when a refresh error occurs."""
        print(f"Refresh Error: {error_msg}")
        self.spinner.set_spinning(False)
        self.search_stock_entry.freeze(False)
        self.trash_view_mode.set_sensitive(True)
        self.refresh_action.set_enabled(True)
        self.sort_action.set_enabled(True)

    def on_watchlist_loaded(self, controller, stocks_data):
        """Callback when watchlist is loaded."""
        if stocks_data:
            self.last_updated_label.set_label(_('cached'))

    def on_stock_added(self, controller, stock):
        """Callback when a stock is added."""
        print(f"DEBUG: on_stock_added called for {stock.symbol} - {stock.long_name}")

        # Add to category model
        self.category_model.add_stock(stock)
        print(f"DEBUG: Stock added to category_model")

        # Update views if stock belongs to current category
        selected_row = self.category_list.get_selected_row()
        if selected_row and hasattr(selected_row, 'category_key'):
            current_category = selected_row.category_key
            print(f"DEBUG: Current category: {current_category}")

            filtered = self.category_model.get_stocks_by_category(current_category)
            print(f"DEBUG: {len(filtered)} stocks in category {current_category}")

            if stock in filtered:
                print(f"DEBUG: Stock {stock.symbol} belongs to category, adding to list")
                self.list_stock.append(stock)

                # Update heatmap with list order
                sorted_stocks = self.list_stock.get_all_stocks()
                self.heatmap_view.set_stocks(sorted_stocks)
                print(f"DEBUG: Stock added to visualization")
            else:
                print(f"DEBUG: Stock {stock.symbol} does NOT belong to current category")
        else:
            print(f"DEBUG: No category selected or invalid row")

    # ============== UI Callbacks ==============

    def on_sort_action(self, action, parameter):
        """Callback for sort action."""
        sort_type = parameter.get_string()
        action.set_state(parameter)

        if sort_type == "alphabetical":
            self.list_stock.sort_alphabetical()
        elif sort_type == "gains":
            self.list_stock.sort_by_gains()
        elif sort_type == "losses":
            self.list_stock.sort_by_losses()

        self.controller.save_sort_order(sort_type)

        # Update heatmap with new order
        sorted_stocks = self.list_stock.get_all_stocks()
        self.heatmap_view.set_stocks(sorted_stocks)

    def on_empty_state_changed(self, widget, is_empty):
        """Callback when the list empty state changes."""
        visible_child = self.view_stack.get_visible_child_name()
        is_list_view = (visible_child == "list")
        self.trash_view_mode.set_visible(is_list_view and not is_empty)

        if is_empty and self.trash_view_mode.get_active():
            self.trash_view_mode.set_active(False)

    def on_close_request(self, window):
        """Save window state before closing"""
        self.settings.set_int('window-width', self.get_width())
        self.settings.set_int('window-height', self.get_height())
        self.settings.set_boolean('window-maximized', self.is_maximized())
        self.save_watchlist()
        self.controller.stop_auto_update()

    def on_search_changed(self, widget, text: str):
        """Callback when search text changes."""
        if text:
            self.controller.pause_auto_update()
        else:
            self.controller.restart_auto_update()

    def on_trash_mode_toggled(self, toggle_button):
        """Callback when remove mode is toggled."""
        is_active = toggle_button.get_active()
        self.list_stock.set_remove_enabled(is_active)
        self.search_stock_entry.set_visible(not is_active)
        self.refresh_action.set_enabled(not is_active)
        self.sort_action.set_enabled(not is_active)

        if is_active:
            self.controller.pause_auto_update()
        else:
            self.controller.restart_auto_update()

    def on_stock_remove_requested(self, widget, stock_item):
        """Callback when a stock is requested for removal."""
        print(f"Removing stock: {stock_item.symbol} - {stock_item.long_name}")

        success = self.list_stock.remove_stock_by_symbol(stock_item.symbol)

        if success:
            self.controller.remove_stock(stock_item.symbol)
            self.category_model.remove_stock(stock_item.symbol)

            # Update heatmap
            sorted_stocks = self.list_stock.get_all_stocks()
            self.heatmap_view.set_stocks(sorted_stocks)
            
            print(f"Successfully removed {stock_item.symbol}")
        else:
            print(f"Failed to remove {stock_item.symbol}")

    def on_refresh_action(self, action=None, param=None):
        """Callback for refresh action."""
        self.controller.refresh_stocks()
        return True

    def on_search_clicked(self, widget, symbol_input=None):
        """Callback when search is triggered."""
        if symbol_input is None:
            symbol_input = self.search_stock_entry.get_text()

        if symbol_input.strip():
            self.controller.search_stocks(symbol_input)

    # ============== Helper Methods ==============

    def update_timestamp(self):
        """Updates the last update label."""
        self.last_updated_label.set_label(_(f"{datetime.now().strftime('%H:%M:%S')}"))

    def load_watchlist(self):
        """Loads the watchlist from the controller."""
        stocks_data, sort_order = self.controller.load_watchlist()

        if stocks_data:
            for stock_data in stocks_data:
                stock_item = Stock.from_dict(stock_data)
                self.category_model.add_stock(stock_item)
                self.list_stock.append(stock_item)

        if sort_order:
            self.sort_action.set_state(GLib.Variant("s", sort_order))
            self.list_stock.current_sort = sort_order
            self.list_stock._apply_sort()

        # Update counters and initial heatmap
        self._update_category_counts()
        sorted_stocks = self.list_stock.get_all_stocks()
        self.heatmap_view.set_stocks(sorted_stocks)

    def save_watchlist(self) -> bool:
        """Saves the watchlist through the controller."""
        all_stocks = self.category_model.get_stocks_by_category("All")
        is_success = self.controller.save_watchlist(all_stocks)

        if not is_success:
            print(_("WARNING: Failed to save watchlist"))

        return is_success

    # ============== Alert Methods ==============

    def load_alerts(self):
        """Load saved alerts."""
        self.controller.alert_manager.load()

    def on_add_alert_clicked(self, alerts_view):
        """Callback when add alert button is clicked (from Alerts tab)."""
        # Create and show dialog without pre-selected stock
        dialog = AlertDialog()
        dialog.connect('alert-created', self.on_alert_created)
        dialog.present(self)

    def on_add_alert_from_list(self, list_stock, stock):
        """Callback when 'Add Alert' is clicked in stock context menu."""
        # Create and show dialog WITH pre-filled stock
        dialog = AlertDialog(stock=stock)
        dialog.connect('alert-created', self.on_alert_created)
        dialog.present(self)

    def on_alert_created(self, dialog, alert):
        """Callback when an alert is created in the dialog."""
        # Add alert to manager
        self.controller.alert_manager.add_alert(alert)
        print(f"Alert created and added: {alert}")

        # Show confirmation toast
        toast = Adw.Toast.new(f"Alert created for {alert.symbol}")
        toast.set_timeout(3)
        self.toast_overlay.add_toast(toast)

    def on_alerts_triggered(self, controller, triggered_alerts):
        """Callback when alerts are triggered."""
        if not triggered_alerts:
            return

        print(f"Processing {len(triggered_alerts)} triggered alerts")

        # Show toast AND system notification for each triggered alert
        for alert in triggered_alerts:
            message = f"🔔 {alert.symbol} reached ${alert.target_price:.2f}!"

            # Toast notification (in-app)
            toast = Adw.Toast.new(message)
            toast.set_timeout(5)
            toast.set_priority(Adw.ToastPriority.HIGH)
            self.toast_overlay.add_toast(toast)

            # System notification (works in background)
            self._send_system_notification(alert)

            print(f"Toast and system notification shown for alert: {message}")

    def _send_system_notification(self, alert):
        """
        Send system notification when an alert triggers.

        Args:
            alert: Alert object that was triggered
        """
        # Notification title
        title = _("Price Alert Triggered")

        # Notification body with details
        if alert.alert_type == 'above':
            body = _("{symbol} reached ${price:.2f} (above target)").format(
                symbol=alert.symbol,
                price=alert.target_price
            )
        else:
            body = _("{symbol} reached ${price:.2f} (below target)").format(
                symbol=alert.symbol,
                price=alert.target_price
            )

        # Create notification
        notification = Gio.Notification.new(title)
        notification.set_body(body)

        # Set icon (use app icon)
        icon = Gio.ThemedIcon.new("com.ekonomikas.merkato")
        notification.set_icon(icon)

        # Set priority to HIGH to appear even in do not disturb mode
        notification.set_priority(Gio.NotificationPriority.HIGH)

        # Add action to open app when clicking notification
        notification.set_default_action("app.show-alerts")

        # Send notification
        # Unique ID allows replacing old notifications from same alert
        notification_id = f"alert-{alert.alert_id}"
        self.get_application().send_notification(notification_id, notification)

        print(f"System notification sent: {title} - {body}")
