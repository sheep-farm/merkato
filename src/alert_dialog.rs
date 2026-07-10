// alert_dialog.rs
//
// Copyright 2025 Flávio de Vasconcellos Corrêa
//
// SPDX-License-Identifier: GPL-3.0-or-later

use std::cell::RefCell;

use gtk4::prelude::*;
use gtk4::subclass::prelude::*;
use gtk4::{glib, CompositeTemplate};

use crate::alert::AlertType;

#[derive(Debug, Clone)]
pub struct AlertCreatedData {
    pub symbol: String,
    pub alert_type: AlertType,
    pub target_price: f64,
}

mod imp {
    use super::*;
    use libadwaita::prelude::*;
    use gtk4::TemplateChild;

    #[derive(CompositeTemplate)]
    #[template(resource = "/com/github/sheepfarm/merkato/alert_dialog.ui")]
    pub struct AlertDialog {
        #[template_child]
        pub cancel_button: TemplateChild<gtk4::Button>,
        #[template_child]
        pub create_button: TemplateChild<gtk4::Button>,
        #[template_child]
        pub symbol_entry: TemplateChild<libadwaita::EntryRow>,
        #[template_child]
        pub stock_name_row: TemplateChild<libadwaita::ActionRow>,
        #[template_child]
        pub alert_type_row: TemplateChild<libadwaita::ComboRow>,
        #[template_child]
        pub target_price_entry: TemplateChild<libadwaita::EntryRow>,
        #[template_child]
        pub currency_label: TemplateChild<gtk4::Label>,
        #[template_child]
        pub current_price_row: TemplateChild<libadwaita::ActionRow>,

        pub on_created: RefCell<Option<Box<dyn Fn(AlertCreatedData)>>>,
    }

    impl std::fmt::Debug for AlertDialog {
        fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
            f.debug_struct("AlertDialog")
                .field("cancel_button", &self.cancel_button)
                .field("create_button", &self.create_button)
                .field("symbol_entry", &self.symbol_entry)
                .field("stock_name_row", &self.stock_name_row)
                .field("alert_type_row", &self.alert_type_row)
                .field("target_price_entry", &self.target_price_entry)
                .field("currency_label", &self.currency_label)
                .field("current_price_row", &self.current_price_row)
                .field("on_created", &"<callback>")
                .finish()
        }
    }

    impl Default for AlertDialog {
        fn default() -> Self {
            Self {
                cancel_button: Default::default(),
                create_button: Default::default(),
                symbol_entry: Default::default(),
                stock_name_row: Default::default(),
                alert_type_row: Default::default(),
                target_price_entry: Default::default(),
                currency_label: Default::default(),
                current_price_row: Default::default(),
                on_created: RefCell::new(None),
            }
        }
    }

    #[glib::object_subclass]
    impl ObjectSubclass for AlertDialog {
        const NAME: &'static str = "AlertDialog";
        type Type = super::AlertDialog;
        type ParentType = libadwaita::Dialog;

        fn class_init(klass: &mut Self::Class) {
            klass.bind_template();
        }

        fn instance_init(obj: &glib::subclass::InitializingObject<Self>) {
            obj.init_template();
        }
    }

    impl ObjectImpl for AlertDialog {
        fn constructed(&self) {
            self.parent_constructed();

            let obj = self.obj();

            // Validate form on changes
            self.symbol_entry.connect_changed(glib::clone!(
                #[weak]
                obj,
                move |_| obj.update_create_button()
            ));
            self.target_price_entry.connect_changed(glib::clone!(
                #[weak]
                obj,
                move |_| obj.update_create_button()
            ));

            self.create_button.set_sensitive(false);

            // Cancel button
            self.cancel_button.connect_clicked(glib::clone!(
                #[weak]
                obj,
                move |_| obj.force_close()
            ));

            // Create button
            self.create_button.connect_clicked(glib::clone!(
                #[weak]
                obj,
                move |_| obj.on_create_clicked()
            ));
        }
    }

    impl WidgetImpl for AlertDialog {}
    impl libadwaita::subclass::dialog::AdwDialogImpl for AlertDialog {}
}

glib::wrapper! {
    pub struct AlertDialog(ObjectSubclass<imp::AlertDialog>)
        @extends libadwaita::Dialog, gtk4::Widget,
        @implements gtk4::Buildable, gtk4::ConstraintTarget;
}

impl AlertDialog {
    pub fn new() -> Self {
        glib::Object::new()
    }

    pub fn set_symbol(&self, symbol: &str) {
        self.imp().symbol_entry.set_text(symbol);
    }

    pub fn set_current_price(&self, price: f64, currency_symbol: &str, name: &str) {
        use libadwaita::prelude::ActionRowExt;
        self.imp()
            .current_price_row
            .set_subtitle(&format!("{}{:.2}", currency_symbol, price));
        self.imp().stock_name_row.set_subtitle(name);
        self.imp().currency_label.set_label(currency_symbol);
    }

    fn update_create_button(&self) {
        let imp = self.imp();
        let has_symbol = !imp.symbol_entry.text().is_empty();
        let has_price = imp
            .target_price_entry
            .text()
            .parse::<f64>()
            .map(|v| v > 0.0)
            .unwrap_or(false);
        imp.create_button.set_sensitive(has_symbol && has_price);
    }

    fn on_create_clicked(&self) {
        use libadwaita::prelude::AdwDialogExt;
        use libadwaita::prelude::ComboRowExt;
        let imp = self.imp();
        let symbol = imp.symbol_entry.text().to_uppercase();
        let target_price: f64 = imp
            .target_price_entry
            .text()
            .parse()
            .unwrap_or(0.0);
        let alert_type = if imp.alert_type_row.selected() == 0 {
            AlertType::Above
        } else {
            AlertType::Below
        };

        let data = AlertCreatedData { symbol, alert_type, target_price };

        if let Some(cb) = imp.on_created.borrow().as_ref() {
            cb(data);
        }

        self.force_close();
    }

    pub fn connect_alert_created<F: Fn(AlertCreatedData) + 'static>(&self, f: F) {
        *self.imp().on_created.borrow_mut() = Some(Box::new(f));
    }
}

impl Default for AlertDialog {
    fn default() -> Self {
        Self::new()
    }
}
