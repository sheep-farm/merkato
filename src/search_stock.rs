// search_stock.rs
//
// Copyright 2025 Flávio de Vasconcellos Corrêa
//
// SPDX-License-Identifier: GPL-3.0-or-later

use gtk4::prelude::*;
use gtk4::subclass::prelude::*;
use gtk4::{glib, CompositeTemplate};

mod imp {
    use super::*;
    use gtk4::TemplateChild;

    #[derive(Debug, Default, CompositeTemplate)]
    #[template(resource = "/com/github/sheepfarm/merkato/search_stock.ui")]
    pub struct SearchStock {
        #[template_child(id = "_entry")]
        pub entry: TemplateChild<gtk4::SearchEntry>,
        #[template_child(id = "_button")]
        pub button: TemplateChild<gtk4::Button>,
    }

    #[glib::object_subclass]
    impl ObjectSubclass for SearchStock {
        const NAME: &'static str = "MerkatoSearchStock";
        type Type = super::SearchStock;
        type ParentType = gtk4::Box;

        fn class_init(klass: &mut Self::Class) {
            klass.bind_template();
        }

        fn instance_init(obj: &glib::subclass::InitializingObject<Self>) {
            obj.init_template();
        }
    }

    impl ObjectImpl for SearchStock {
        fn constructed(&self) {
            self.parent_constructed();
            let entry = self.entry.clone();
            let button = self.button.clone();

            // Enable/disable button based on entry content
            entry.connect_changed(glib::clone!(
                #[weak]
                button,
                move |e| {
                    button.set_sensitive(!e.text().is_empty());
                }
            ));
            button.set_sensitive(false);
        }
    }

    impl WidgetImpl for SearchStock {}
    impl BoxImpl for SearchStock {}
}

glib::wrapper! {
    pub struct SearchStock(ObjectSubclass<imp::SearchStock>)
        @extends gtk4::Box, gtk4::Widget,
        @implements gtk4::Buildable, gtk4::ConstraintTarget, gtk4::Orientable;
}

impl SearchStock {
    pub fn new() -> Self {
        glib::Object::new()
    }

    pub fn text(&self) -> String {
        self.imp().entry.text().to_string()
    }

    pub fn set_text(&self, text: &str) {
        self.imp().entry.set_text(text);
    }

    pub fn set_frozen(&self, frozen: bool) {
        self.imp().entry.set_sensitive(!frozen);
        self.imp().button.set_sensitive(!frozen && !self.imp().entry.text().is_empty());
    }

    pub fn connect_search<F: Fn(String) + 'static>(&self, f: F) {
        let entry = self.imp().entry.clone();
        let button = self.imp().button.clone();

        let f = std::rc::Rc::new(f);
        let f2 = f.clone();

        button.connect_clicked(glib::clone!(
            #[weak]
            entry,
            move |_| {
                let text = entry.text().to_string();
                if !text.is_empty() {
                    f(text);
                }
            }
        ));

        self.imp().entry.connect_activate(move |e| {
            let text = e.text().to_string();
            if !text.is_empty() {
                f2(text);
            }
        });
    }
}

impl Default for SearchStock {
    fn default() -> Self {
        Self::new()
    }
}
