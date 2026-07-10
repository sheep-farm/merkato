// application.rs
//
// Copyright 2025 Flávio de Vasconcellos Corrêa
//
// SPDX-License-Identifier: GPL-3.0-or-later

use gtk4::prelude::*;
use gtk4::subclass::prelude::*;
use gtk4::{glib, gio};
use libadwaita::prelude::AdwDialogExt;

use crate::window::MerkatoWindow;

const APP_ID: &str = "com.ekonomikas.merkato";
const VERSION: &str = env!("CARGO_PKG_VERSION");

mod imp {
    use super::*;

    #[derive(Default)]
    pub struct MerkatoApplication {}

    #[glib::object_subclass]
    impl ObjectSubclass for MerkatoApplication {
        const NAME: &'static str = "MerkatoApplication";
        type Type = super::MerkatoApplication;
        type ParentType = libadwaita::Application;
    }

    impl ObjectImpl for MerkatoApplication {}

    impl ApplicationImpl for MerkatoApplication {
        fn activate(&self) {
            self.parent_activate();
            let app = self.obj();

            // Load CSS
            let provider = gtk4::CssProvider::new();
            provider.load_from_resource("/com/github/sheepfarm/merkato/style.css");
            gtk4::style_context_add_provider_for_display(
                &gdk4::Display::default().expect("Could not connect to display"),
                &provider,
                gtk4::STYLE_PROVIDER_PRIORITY_APPLICATION,
            );

            // Create or raise window
            if let Some(win) = app.active_window() {
                gtk4::prelude::GtkWindowExt::present(&win);
            } else {
                let win = MerkatoWindow::new(app.upcast_ref::<libadwaita::Application>());
                gtk4::prelude::GtkWindowExt::present(&win);
            }
        }

        fn startup(&self) {
            self.parent_startup();
            let app = self.obj();
            app.setup_actions();
        }
    }

    impl GtkApplicationImpl for MerkatoApplication {}
    impl libadwaita::subclass::application::AdwApplicationImpl for MerkatoApplication {}
}

glib::wrapper! {
    pub struct MerkatoApplication(ObjectSubclass<imp::MerkatoApplication>)
        @extends libadwaita::Application, gtk4::Application, gio::Application,
        @implements gio::ActionGroup, gio::ActionMap;
}

impl MerkatoApplication {
    pub fn new() -> Self {
        glib::Object::builder()
            .property("application-id", APP_ID)
            .property("flags", gio::ApplicationFlags::empty())
            .build()
    }

    fn setup_actions(&self) {
        // About action
        let about_action = gio::SimpleAction::new("about", None);
        about_action.connect_activate(glib::clone!(
            #[weak(rename_to = app)]
            self,
            move |_, _| app.show_about_dialog()
        ));
        self.add_action(&about_action);

        // Quit action
        let quit_action = gio::SimpleAction::new("quit", None);
        quit_action.connect_activate(glib::clone!(
            #[weak(rename_to = app)]
            self,
            move |_, _| app.quit()
        ));
        self.add_action(&quit_action);
        self.set_accels_for_action("app.quit", &["<primary>q"]);

        // Show alerts action
        let show_alerts = gio::SimpleAction::new("show-alerts", None);
        show_alerts.connect_activate(glib::clone!(
            #[weak(rename_to = app)]
            self,
            move |_, _| {
                if let Some(win) = app.active_window() {
                    // Switch to alerts tab
                    if let Ok(merkato_win) = win.downcast::<MerkatoWindow>() {
                        merkato_win
                            .imp()
                            .view_stack
                            .set_visible_child_name("alerts");
                    }
                }
            }
        ));
        self.add_action(&show_alerts);
    }

    fn show_about_dialog(&self) {
        let dialog = libadwaita::AboutDialog::new();
        dialog.set_application_name("Merkato");
        dialog.set_application_icon(APP_ID);
        dialog.set_version(VERSION);
        dialog.set_developer_name("Flávio de Vasconcellos Corrêa");
        dialog.set_license_type(gtk4::License::Gpl30);
        dialog.set_website("https://github.com/sheep-farm/merkato");
        dialog.set_issue_url("https://github.com/sheep-farm/merkato/issues");
        dialog.set_copyright("© 2025 Flávio de Vasconcellos Corrêa");
        dialog.set_comments(
            "A modern financial market tracker for GNOME.\n\
             Data provided by Yahoo Finance.",
        );

        if let Some(win) = self.active_window() {
            dialog.present(Some(&win));
        }
    }
}

impl Default for MerkatoApplication {
    fn default() -> Self {
        Self::new()
    }
}
