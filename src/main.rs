// main.rs
//
// Copyright 2025 Flávio de Vasconcellos Corrêa
//
// SPDX-License-Identifier: GPL-3.0-or-later

mod alert;
mod alert_dialog;
mod alert_manager;
mod alerts_view;
mod application;
mod category_model;
mod category_sidebar;
mod data_cache;
mod heatmap_view;
mod list_stock;
mod search_stock;
mod stock;
mod stock_controller;
mod stock_object;
mod watchlist_manager;
mod window;
mod yahoo_request;

use gtk4::prelude::*;

use application::MerkatoApplication;

fn main() {
    tracing_subscriber::fmt::init();

    // Register GLib resources (compiled by build.rs / pre-compiled)
    let resources_bytes =
        include_bytes!(concat!(env!("CARGO_MANIFEST_DIR"), "/src/merkato.gresource"));

    let resource = gio::Resource::from_data(&glib::Bytes::from_static(resources_bytes))
        .expect(
            "Could not load GLib resources.\n\
             Run: blueprint-compiler compile for each .blp file, then\n\
             glib-compile-resources src/merkato.gresource.xml --target=src/merkato.gresource",
        );
    gio::resources_register(&resource);

    // Run application
    let app = MerkatoApplication::new();

    app.run();
    // std::process::exit(app.run());
}
