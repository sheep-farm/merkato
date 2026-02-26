// list_stock.rs
//
// Copyright 2025 Flávio de Vasconcellos Corrêa
//
// SPDX-License-Identifier: GPL-3.0-or-later

use std::cell::RefCell;

use gtk4::prelude::*;
use gtk4::subclass::prelude::*;
use gtk4::{glib, gio, CompositeTemplate};
use libadwaita::prelude::{ActionRowExt, PreferencesRowExt};

use crate::stock::Stock;

// ─── Sort mode ────────────────────────────────────────────────────────────────

#[derive(Debug, Clone, PartialEq)]
pub enum SortMode {
    Alphabetical,
    TopGains,
    TopLosses,
}

impl SortMode {
    pub fn from_str(s: &str) -> Self {
        match s {
            "gains"  => SortMode::TopGains,
            "losses" => SortMode::TopLosses,
            _        => SortMode::Alphabetical,
        }
    }
    #[allow(dead_code)]
    pub fn as_str(&self) -> &'static str {
        match self {
            SortMode::Alphabetical => "alphabetical",
            SortMode::TopGains     => "gains",
            SortMode::TopLosses    => "losses",
        }
    }
}

// ─── GObject subclass ─────────────────────────────────────────────────────────

mod imp {
    use super::*;
    use gtk4::TemplateChild;

    #[derive(CompositeTemplate)]
    #[template(resource = "/com/github/sheepfarm/merkato/list_stock.ui")]
    pub struct ListStock {
        #[template_child(id = "_list_scroll")]
        pub list_scroll: TemplateChild<gtk4::ScrolledWindow>,
        #[template_child(id = "_list_stock")]
        pub list_box: TemplateChild<gtk4::ListBox>,
        #[template_child(id = "_empty_watchlist_state")]
        pub empty_state: TemplateChild<libadwaita::StatusPage>,

        pub stocks: RefCell<Vec<Stock>>,
        pub sort_mode: RefCell<SortMode>,
        pub remove_mode: RefCell<bool>,
        pub remove_callback:    RefCell<Option<Box<dyn Fn(String)>>>,
        pub add_alert_callback: RefCell<Option<Box<dyn Fn(String)>>>,
    }

    impl Default for ListStock {
        fn default() -> Self {
            Self {
                list_scroll:         Default::default(),
                list_box:            Default::default(),
                empty_state:         Default::default(),
                stocks:              RefCell::new(Vec::new()),
                sort_mode:           RefCell::new(SortMode::Alphabetical),
                remove_mode:         RefCell::new(false),
                remove_callback:     RefCell::new(None),
                add_alert_callback:  RefCell::new(None),
            }
        }
    }

    impl std::fmt::Debug for ListStock {
        fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
            f.debug_struct("ListStock").finish()
        }
    }

    #[glib::object_subclass]
    impl ObjectSubclass for ListStock {
        const NAME: &'static str = "MerkatoListStock";
        type Type = super::ListStock;
        type ParentType = gtk4::Box;

        fn class_init(klass: &mut Self::Class) {
            klass.bind_template();
        }
        fn instance_init(obj: &glib::subclass::InitializingObject<Self>) {
            obj.init_template();
        }
    }

    impl ObjectImpl for ListStock {
        fn constructed(&self) {
            self.parent_constructed();
        }
    }

    impl WidgetImpl for ListStock {}
    impl BoxImpl  for ListStock {}
}

// ─── Public wrapper ───────────────────────────────────────────────────────────

glib::wrapper! {
    pub struct ListStock(ObjectSubclass<imp::ListStock>)
        @extends gtk4::Box, gtk4::Widget,
        @implements gtk4::Accessible, gtk4::Buildable, gtk4::ConstraintTarget,
                    gtk4::Orientable;
}

impl ListStock {
    pub fn new() -> Self {
        glib::Object::new()
    }

    // ── Data ─────────────────────────────────────────────────────────────────

    pub fn set_stocks(&self, stocks: Vec<Stock>) {
        *self.imp().stocks.borrow_mut() = stocks;
        self.refresh_list();
    }

    pub fn set_sort_mode(&self, mode: SortMode) {
        *self.imp().sort_mode.borrow_mut() = mode;
        self.refresh_list();
    }

    pub fn set_remove_mode(&self, enabled: bool) {
        *self.imp().remove_mode.borrow_mut() = enabled;
        self.refresh_list();
    }

    pub fn sort_mode(&self) -> SortMode {
        self.imp().sort_mode.borrow().clone()
    }

    // ── Callbacks ─────────────────────────────────────────────────────────────

    /// Called when the remove button is clicked for a stock.
    pub fn connect_remove_requested<F: Fn(String) + 'static>(&self, f: F) {
        *self.imp().remove_callback.borrow_mut() = Some(Box::new(f));
    }

    /// Called when "Add Price Alert" is selected in the context menu.
    pub fn connect_add_alert<F: Fn(String) + 'static>(&self, f: F) {
        *self.imp().add_alert_callback.borrow_mut() = Some(Box::new(f));
    }

    // ── List management ───────────────────────────────────────────────────────

    fn sorted_stocks(&self) -> Vec<Stock> {
        let mut stocks = self.imp().stocks.borrow().clone();
        match *self.imp().sort_mode.borrow() {
            SortMode::Alphabetical => {
                stocks.sort_by(|a, b| {
                    a.long_name.to_lowercase().cmp(&b.long_name.to_lowercase())
                });
            }
            SortMode::TopGains => {
                stocks.sort_by(|a, b| {
                    b.change_pct
                        .partial_cmp(&a.change_pct)
                        .unwrap_or(std::cmp::Ordering::Equal)
                });
            }
            SortMode::TopLosses => {
                stocks.sort_by(|a, b| {
                    a.change_pct
                        .partial_cmp(&b.change_pct)
                        .unwrap_or(std::cmp::Ordering::Equal)
                });
            }
        }
        stocks
    }

    fn refresh_list(&self) {
        let imp = self.imp();
        let list_box   = &*imp.list_box;
        let remove_mode = *imp.remove_mode.borrow();

        // Clear
        while let Some(child) = list_box.first_child() {
            list_box.remove(&child);
        }

        let stocks   = self.sorted_stocks();
        let is_empty = stocks.is_empty();

        imp.list_scroll.set_visible(!is_empty);
        imp.empty_state.set_visible(is_empty);

        for stock in &stocks {
            let row = self.build_row(stock, remove_mode);
            list_box.append(&row);
        }
    }

    // ── Row construction ─────────────────────────────────────────────────────

    fn build_row(&self, stock: &Stock, remove_mode: bool) -> libadwaita::ActionRow {
        let row = libadwaita::ActionRow::new();

        // Title = company name, Subtitle = symbol  (Yahoo Finance style)
        row.set_title(&glib::markup_escape_text(&stock.long_name));
        row.set_subtitle(&stock.symbol);
        row.set_activatable(true);
        row.set_cursor_from_name(Some("pointer"));

        // Market state CSS
        if stock.is_market_open() {
            row.add_css_class("market-opened");
        } else {
            row.add_css_class("market-closed");
        }

        // Suffix: price + change box
        let price_box = self.build_price_box(stock);
        row.add_suffix(&price_box);

        // Suffix: remove button (always present, visibility toggled)
        let remove_btn = self.build_remove_button(&stock.symbol, remove_mode);
        row.add_suffix(&remove_btn);

        // Primary activation → open Yahoo Finance
        let symbol = stock.symbol.clone();
        row.connect_activated(move |_| {
            let url = format!("https://finance.yahoo.com/quote/{}/", symbol);
            let _ = gio::AppInfo::launch_default_for_uri(&url, gio::AppLaunchContext::NONE);
        });

        // Context menu (right click)
        self.attach_context_menu(&row, stock);

        row
    }

    fn build_price_box(&self, stock: &Stock) -> gtk4::Box {
        let vbox = gtk4::Box::new(gtk4::Orientation::Vertical, 2);
        vbox.set_halign(gtk4::Align::End);
        vbox.set_valign(gtk4::Align::Center);

        // Price — omit currency symbol for indices (^GSPC, ^DJI, etc.)
        let price_str = if stock.symbol.starts_with('^') {
            format!("{:.2}", stock.price)
        } else {
            format!("{:.2} {}", stock.price, stock.currency_symbol)
        };
        let price_label = gtk4::Label::new(Some(&price_str));
        price_label.set_halign(gtk4::Align::End);
        price_label.add_css_class("numeric");

        // Change: "+1.23 (0.45%)" or "-1.23 (-0.45%)"
        let sign = if stock.change >= 0.0 { "+" } else { "" };
        let change_str = format!(
            "{}{:.2} ({:.2}%)",
            sign,
            stock.change,
            stock.change_pct * 100.0
        );
        let change_label = gtk4::Label::new(Some(&change_str));
        change_label.set_halign(gtk4::Align::End);
        change_label.add_css_class("caption");
        change_label.add_css_class("numeric");

        if stock.change_pct > 0.0 {
            change_label.add_css_class("success");
        } else if stock.change_pct < 0.0 {
            change_label.add_css_class("error");
        }

        vbox.append(&price_label);
        vbox.append(&change_label);
        vbox
    }

    fn build_remove_button(&self, symbol: &str, visible: bool) -> gtk4::Button {
        let btn = gtk4::Button::new();
        btn.set_icon_name("user-trash-symbolic");
        btn.add_css_class("destructive-action");
        btn.add_css_class("circular");
        btn.add_css_class("flat");
        btn.set_valign(gtk4::Align::Center);
        btn.set_tooltip_text(Some("Remove from watchlist"));
        btn.set_visible(visible);

        let sym = symbol.to_string();
        btn.connect_clicked(glib::clone!(
            #[weak(rename_to = list_widget)]
            self,
            move |_| {
                if let Some(cb) = list_widget.imp().remove_callback.borrow().as_ref() {
                    cb(sym.clone());
                }
            }
        ));
        btn
    }

    fn attach_context_menu(&self, row: &libadwaita::ActionRow, stock: &Stock) {
        let menu = gio::Menu::new();
        menu.append(Some("Add Price Alert"),      Some("row.add-alert"));
        menu.append(Some("Open in Yahoo Finance"), Some("row.open-yahoo"));

        let popover = gtk4::PopoverMenu::from_model(Some(&menu));
        popover.set_parent(row);
        popover.set_has_arrow(false);

        let action_group = gio::SimpleActionGroup::new();

        // add-alert
        let add_alert = gio::SimpleAction::new("add-alert", None);
        let sym = stock.symbol.clone();
        add_alert.connect_activate(glib::clone!(
            #[weak(rename_to = list_widget)]
            self,
            move |_, _| {
                if let Some(cb) = list_widget.imp().add_alert_callback.borrow().as_ref() {
                    cb(sym.clone());
                }
            }
        ));
        action_group.add_action(&add_alert);

        // open-yahoo
        let open_yahoo = gio::SimpleAction::new("open-yahoo", None);
        let url = format!("https://finance.yahoo.com/quote/{}/", stock.symbol);
        open_yahoo.connect_activate(move |_, _| {
            let _ = gio::AppInfo::launch_default_for_uri(&url, gio::AppLaunchContext::NONE);
        });
        action_group.add_action(&open_yahoo);

        row.insert_action_group("row", Some(&action_group));

        // Right-click gesture
        let gesture = gtk4::GestureClick::new();
        gesture.set_button(3);
        let popover_ref = popover.clone();
        gesture.connect_pressed(move |gesture, _, x, y| {
            let rect = gdk4::Rectangle::new(x as i32, y as i32, 1, 1);
            popover_ref.set_pointing_to(Some(&rect));
            popover_ref.popup();
            gesture.set_state(gtk4::EventSequenceState::Claimed);
        });
        row.add_controller(gesture);
    }
}

impl Default for ListStock {
    fn default() -> Self {
        Self::new()
    }
}
