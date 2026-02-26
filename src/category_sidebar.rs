// category_sidebar.rs
//
// Copyright 2025 Flávio de Vasconcellos Corrêa
//
// SPDX-License-Identifier: GPL-3.0-or-later

use std::collections::HashMap;

use gtk4::prelude::*;

use crate::category_model::all_categories;

/// Populate a GTK4 ListBox with category rows.
/// Returns a map of category key → ListBoxRow.
pub fn populate_category_list(
    list_box: &gtk4::ListBox,
    on_selected: impl Fn(&str) + Clone + 'static,
) {
    let categories = all_categories();

    for cat in &categories {
        let row = build_category_row(cat.key, &cat.label, cat.icon);
        list_box.append(&row);
    }

    let cat_keys: Vec<&'static str> = categories.iter().map(|c| c.key).collect();
    list_box.connect_row_selected(move |_, row| {
        if let Some(row) = row {
            let index = row.index() as usize;
            if let Some(key) = cat_keys.get(index) {
                on_selected(key);
            }
        }
    });

    // Select first row (All)
    if let Some(row) = list_box.row_at_index(0) {
        list_box.select_row(Some(&row));
    }
}

/// Update category badge counts.
pub fn update_category_counts(list_box: &gtk4::ListBox, counts: &HashMap<&'static str, usize>) {
    let categories = all_categories();

    for (i, cat) in categories.iter().enumerate() {
        if let Some(row) = list_box.row_at_index(i as i32) {
            let count = counts.get(cat.key).copied().unwrap_or(0);
            update_row_count(&row, count);
        }
    }
}

fn build_category_row(key: &'static str, label: &str, icon: &str) -> gtk4::ListBoxRow {
    let row = gtk4::ListBoxRow::new();
    row.set_activatable(true);

    let hbox = gtk4::Box::new(gtk4::Orientation::Horizontal, 8);
    hbox.set_margin_top(6);
    hbox.set_margin_bottom(6);
    hbox.set_margin_start(8);
    hbox.set_margin_end(8);

    let image = gtk4::Image::new();
    // Use a fallback icon if the specific one isn't available
    image.set_icon_name(Some(icon));
    image.set_icon_size(gtk4::IconSize::Normal);
    image.add_css_class("dim-label");

    let label_widget = gtk4::Label::new(Some(label));
    label_widget.set_halign(gtk4::Align::Start);
    label_widget.set_hexpand(true);

    // Badge for count
    let badge = gtk4::Label::new(Some("0"));
    badge.add_css_class("dim-label");
    badge.add_css_class("caption");
    badge.add_css_class("numeric");
    badge.set_widget_name(&format!("badge_{key}"));

    hbox.append(&image);
    hbox.append(&label_widget);
    hbox.append(&badge);

    row.set_child(Some(&hbox));
    row
}

fn update_row_count(row: &gtk4::ListBoxRow, count: usize) {
    if let Some(hbox) = row.child().and_downcast::<gtk4::Box>() {
        // The badge is the last child
        if let Some(badge) = hbox.last_child().and_downcast::<gtk4::Label>() {
            badge.set_label(&count.to_string());
            badge.set_visible(count > 0);
        }
    }
}
