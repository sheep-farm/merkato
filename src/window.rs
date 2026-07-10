// window.rs
//
// Copyright 2025 Flávio de Vasconcellos Corrêa
//
// SPDX-License-Identifier: GPL-3.0-or-later

use std::cell::RefCell;
use std::collections::HashMap;

use gtk4::prelude::*;
use gtk4::subclass::prelude::*;
use gtk4::{glib, CompositeTemplate};

use crate::alert_dialog::AlertDialog;
use crate::alert_manager::AlertManager;
use crate::alerts_view::AlertsView;
use crate::category_model::CategoryModel;
use crate::category_sidebar::{populate_category_list, update_category_counts};
use crate::heatmap_view::HeatmapView;
use crate::list_stock::{ListStock, SortMode};
use crate::search_stock::SearchStock;
use crate::stock::Stock;
use crate::stock_controller::StockController;

mod imp {
    use super::*;
    use gtk4::TemplateChild;

    #[derive(Debug, CompositeTemplate)]
    #[template(resource = "/com/github/sheepfarm/merkato/window.ui")]
    pub struct MerkatoWindow {
        #[template_child]
        pub split_view: TemplateChild<libadwaita::OverlaySplitView>,
        #[template_child]
        pub category_list: TemplateChild<gtk4::ListBox>,
        #[template_child]
        pub sidebar_toggle: TemplateChild<gtk4::ToggleButton>,
        #[template_child]
        pub view_stack: TemplateChild<libadwaita::ViewStack>,
        #[template_child]
        pub trash_view_mode: TemplateChild<gtk4::ToggleButton>,
        #[template_child]
        pub spinner: TemplateChild<gtk4::Spinner>,
        #[template_child]
        pub toast_overlay: TemplateChild<libadwaita::ToastOverlay>,
        #[template_child]
        pub search_stock_entry: TemplateChild<SearchStock>,
        #[template_child]
        pub list_stock: TemplateChild<ListStock>,
        #[template_child]
        pub heatmap_view: TemplateChild<HeatmapView>,
        #[template_child]
        pub alerts_view: TemplateChild<AlertsView>,
        #[template_child]
        pub last_updated_label: TemplateChild<gtk4::Label>,

        pub stocks: RefCell<Vec<Stock>>,
        pub category_model: RefCell<CategoryModel>,
        pub alert_manager: RefCell<AlertManager>,
        pub controller: RefCell<StockController>,
    }

    impl Default for MerkatoWindow {
        fn default() -> Self {
            Self {
                split_view: Default::default(),
                category_list: Default::default(),
                sidebar_toggle: Default::default(),
                view_stack: Default::default(),
                trash_view_mode: Default::default(),
                spinner: Default::default(),
                toast_overlay: Default::default(),
                search_stock_entry: Default::default(),
                list_stock: Default::default(),
                heatmap_view: Default::default(),
                alerts_view: Default::default(),
                last_updated_label: Default::default(),

                stocks: RefCell::new(Vec::new()),
                category_model: RefCell::new(CategoryModel::new()),
                alert_manager: RefCell::new(AlertManager::new("merkato")),
                controller: RefCell::new(StockController::new()),
            }
        }
    }

    #[glib::object_subclass]
    impl ObjectSubclass for MerkatoWindow {
        const NAME: &'static str = "MerkatoWindow";
        type Type = super::MerkatoWindow;
        type ParentType = libadwaita::ApplicationWindow;

        fn class_init(klass: &mut Self::Class) {
            // Register custom types before the template is loaded
            SearchStock::ensure_type();
            ListStock::ensure_type();
            HeatmapView::ensure_type();
            AlertsView::ensure_type();

            klass.bind_template();
            klass.install_action("win.refresh", None, |win, _, _| win.on_manual_refresh());
            klass.install_action("win.sort", Some(gtk4::glib::VariantTy::STRING), |win, _, param| {
                if let Some(s) = param.and_then(|p| p.get::<String>()) {
                    win.on_sort(&s);
                }
            });
        }

        fn instance_init(obj: &glib::subclass::InitializingObject<Self>) {
            obj.init_template();
        }
    }

    impl ObjectImpl for MerkatoWindow {
        fn constructed(&self) {
            self.parent_constructed();
            self.obj().setup();
        }
    }

    impl WidgetImpl for MerkatoWindow {}
    impl WindowImpl for MerkatoWindow {}
    impl ApplicationWindowImpl for MerkatoWindow {}
    impl libadwaita::subclass::application_window::AdwApplicationWindowImpl for MerkatoWindow {}
}

glib::wrapper! {
    pub struct MerkatoWindow(ObjectSubclass<imp::MerkatoWindow>)
        @extends libadwaita::ApplicationWindow, gtk4::ApplicationWindow,
                 gtk4::Window, gtk4::Widget,
        @implements gtk4::Buildable, gtk4::ConstraintTarget,
                    gtk4::Native, gtk4::Root, gtk4::ShortcutManager,
                    gio::ActionGroup, gio::ActionMap;
}

impl MerkatoWindow {
    pub fn new(app: &libadwaita::Application) -> Self {
        glib::Object::builder().property("application", app).build()
    }

    fn setup(&self) {
        self.setup_sidebar_toggle();
        self.setup_trash_mode();
        self.setup_search();
        self.setup_category_sidebar();
        self.load_saved_watchlist();
        self.start_auto_refresh();
    }

    // ─── Stock management ─────────────────────────────────────────────────────

    fn add_stock(&self, stock: Stock) {
        let mut stocks = self.imp().stocks.borrow_mut();
        if stocks.iter().any(|s| s.symbol == stock.symbol) {
            return;
        }
        self.imp().category_model.borrow_mut().add_stock(stock.clone());
        stocks.push(stock);
        drop(stocks);
        self.update_views();
    }

    fn apply_refresh(&self, updated: HashMap<String, Stock>) {
        let mut prices = HashMap::new();
        {
            let mut stocks = self.imp().stocks.borrow_mut();
            for stock in stocks.iter_mut() {
                if let Some(new) = updated.get(&stock.symbol) {
                    prices.insert(stock.symbol.clone(), new.price);
                    stock.price = new.price;
                    stock.change = new.change;
                    stock.change_pct = new.change_pct;
                    stock.market_state = new.market_state.clone();
                    self.imp().category_model.borrow_mut().update_stock(stock.clone());
                }
            }
        }
        self.update_views();
        self.check_alerts_with_prices(&prices);
    }

    fn check_alerts_with_prices(&self, prices: &HashMap<String, f64>) {
        let triggered = self.imp().alert_manager.borrow_mut().check_all_alerts(prices);
        if !triggered.is_empty() {
            for (_, symbol) in &triggered {
                self.show_toast(&format!("Price alert triggered for {symbol}!"));
            }
            self.refresh_alerts_view();
        }
    }

    fn remove_stock(&self, symbol: &str) {
        self.imp().stocks.borrow_mut().retain(|s| s.symbol != symbol);
        self.imp().category_model.borrow_mut().remove_stock(symbol);
        self.update_views();
        self.save_watchlist();
    }

    fn update_views(&self) {
        let imp = self.imp();
        let category = imp.category_model.borrow().current_category().to_string();
        let stocks: Vec<Stock> = imp
            .category_model
            .borrow()
            .get_stocks_by_category(&category)
            .into_iter()
            .cloned()
            .collect();

        imp.list_stock.set_stocks(stocks.clone());
        imp.heatmap_view.set_stocks(stocks);

        let counts = imp.category_model.borrow().all_category_counts();
        update_category_counts(&imp.category_list, &counts);
        self.refresh_alerts_view();
    }

    fn refresh_alerts_view(&self) {
        let imp = self.imp();
        let am = imp.alert_manager.borrow();
        let active: Vec<_> = am.active_alerts().into_iter().cloned().collect();
        let triggered: Vec<_> = am.triggered_alerts().into_iter().cloned().collect();
        let disabled: Vec<_> = am.disabled_alerts().into_iter().cloned().collect();
        drop(am);

        imp.alerts_view.refresh(
            &active,
            &triggered,
            &disabled,
            glib::clone!(
                #[weak(rename_to = win)]
                self,
                move |id, enabled| {
                    win.imp().alert_manager.borrow_mut().set_enabled(id, enabled);
                    win.refresh_alerts_view();
                }
            ),
            glib::clone!(
                #[weak(rename_to = win)]
                self,
                move |id| {
                    win.imp().alert_manager.borrow_mut().reset_alert(id);
                    win.refresh_alerts_view();
                }
            ),
            glib::clone!(
                #[weak(rename_to = win)]
                self,
                move |id| {
                    win.imp().alert_manager.borrow_mut().remove_alert(id);
                    win.refresh_alerts_view();
                }
            ),
        );
    }

    // ─── Persistence ──────────────────────────────────────────────────────────

    fn load_saved_watchlist(&self) {
        let saved = self.imp().controller.borrow().load_watchlist();
        if saved.is_empty() {
            return;
        }
        let symbols: Vec<String> = saved.iter().map(|s| s.symbol.clone()).collect();
        for stock in saved {
            self.add_stock(stock);
        }
        // Refresh prices for saved stocks
        self.begin_refresh(symbols);
    }

    fn save_watchlist(&self) {
        let stocks = self.imp().stocks.borrow().clone();
        self.imp().controller.borrow().save_watchlist(&stocks);
    }

    // ─── Background operations ────────────────────────────────────────────────

    /// Begin an async search and receive results via glib channel.
    fn begin_search(&self, input: String) {
        let existing: Vec<String> = self
            .imp()
            .stocks
            .borrow()
            .iter()
            .map(|s| s.symbol.clone())
            .collect();

        let rx = self
            .imp()
            .controller
            .borrow()
            .search_stocks(&input, &existing);

        self.imp().spinner.set_spinning(true);
        self.imp().search_stock_entry.set_frozen(true);

        glib::spawn_future_local(glib::clone!(
            #[weak(rename_to = win)]
            self,
            async move {
                if let Ok((stocks, errors)) = rx.recv().await {
                    win.imp().spinner.set_spinning(false);
                    win.imp().search_stock_entry.set_frozen(false);
                    win.imp().search_stock_entry.set_text("");

                    if !errors.is_empty() {
                        win.show_toast(&format!("Could not find: {}", errors.join(", ")));
                    }
                    for stock in stocks.into_values() {
                        win.add_stock(stock);
                    }
                    win.save_watchlist();
                    win.update_last_refreshed();
                }
            }
        ));
    }

    /// Begin an async refresh and receive results via async channel.
    fn begin_refresh(&self, symbols: Vec<String>) {
        let rx = match self.imp().controller.borrow().refresh_stocks(symbols) {
            Some(r) => r,
            None => return,
        };

        self.imp().spinner.set_spinning(true);
        glib::spawn_future_local(glib::clone!(
            #[weak(rename_to = win)]
            self,
            async move {
                if let Ok((stocks, _errors)) = rx.recv().await {
                    win.imp().spinner.set_spinning(false);
                    win.apply_refresh(stocks);
                    win.update_last_refreshed();
                }
            }
        ));
    }

    // ─── UI setup ─────────────────────────────────────────────────────────────

    fn setup_sidebar_toggle(&self) {
        let split_view = self.imp().split_view.clone();
        self.imp().sidebar_toggle.connect_active_notify(move |btn| {
            split_view.set_show_sidebar(btn.is_active());
        });
    }

    fn setup_trash_mode(&self) {
        self.imp().list_stock.connect_remove_requested(glib::clone!(
            #[weak(rename_to = win)]
            self,
            move |symbol| {
                win.remove_stock(&symbol);
            }
        ));
        self.imp().list_stock.connect_add_alert(glib::clone!(
            #[weak(rename_to = win)]
            self,
            move |symbol| {
                win.show_add_alert_dialog(&symbol);
            }
        ));
        self.imp().trash_view_mode.connect_active_notify(glib::clone!(
            #[weak(rename_to = win)]
            self,
            move |btn| {
                win.imp().list_stock.set_remove_mode(btn.is_active());
            }
        ));
    }

    fn setup_search(&self) {
        self.imp().search_stock_entry.connect_search(glib::clone!(
            #[weak(rename_to = win)]
            self,
            move |text| {
                win.begin_search(text);
            }
        ));
    }

    fn setup_category_sidebar(&self) {
        populate_category_list(
            &self.imp().category_list,
            glib::clone!(
                #[weak(rename_to = win)]
                self,
                move |key| {
                    win.imp().category_model.borrow_mut().set_current_category(key);
                    win.update_views();
                }
            ),
        );
    }

    fn start_auto_refresh(&self) {
        self.imp().controller.borrow_mut().start_auto_refresh(glib::clone!(
            #[weak(rename_to = win)]
            self,
            move || {
                let symbols: Vec<String> = win
                    .imp()
                    .stocks
                    .borrow()
                    .iter()
                    .map(|s| s.symbol.clone())
                    .collect();
                win.begin_refresh(symbols);
            }
        ));
    }

    // ─── Actions ──────────────────────────────────────────────────────────────

    fn on_manual_refresh(&self) {
        let symbols: Vec<String> = self
            .imp()
            .stocks
            .borrow()
            .iter()
            .map(|s| s.symbol.clone())
            .collect();
        self.begin_refresh(symbols);
    }

    fn on_sort(&self, mode: &str) {
        let sort = SortMode::from_str(mode);
        self.imp().list_stock.set_sort_mode(sort);
        self.imp().controller.borrow().save_sort_order(mode);
    }

    pub fn show_add_alert_dialog(&self, symbol: &str) {
        let dialog = AlertDialog::new();
        dialog.set_symbol(symbol);

        if let Some(stock) = self.imp().stocks.borrow().iter().find(|s| s.symbol == symbol) {
            dialog.set_current_price(stock.price, &stock.currency_symbol, &stock.long_name);
        }

        dialog.connect_alert_created(glib::clone!(
            #[weak(rename_to = win)]
            self,
            move |data| {
                win.imp().alert_manager.borrow_mut().add_alert(
                    &data.symbol,
                    data.alert_type,
                    data.target_price,
                );
                win.refresh_alerts_view();
                win.show_toast(&format!("Alert created for {}", data.symbol));
            }
        ));

        libadwaita::prelude::AdwDialogExt::present(&dialog, Some(self));
    }

    // ─── Helpers ──────────────────────────────────────────────────────────────

    fn show_toast(&self, message: &str) {
        let toast = libadwaita::Toast::new(message);
        toast.set_timeout(3);
        self.imp().toast_overlay.add_toast(toast);
    }

    fn update_last_refreshed(&self) {
        let now = chrono::Local::now();
        self.imp()
            .last_updated_label
            .set_label(&now.format("%H:%M:%S").to_string());
    }
}
