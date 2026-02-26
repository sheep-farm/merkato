// alerts_view.rs
//
// Copyright 2025 Flávio de Vasconcellos Corrêa
//
// SPDX-License-Identifier: GPL-3.0-or-later

use gtk4::prelude::*;
use gtk4::subclass::prelude::*;
use gtk4::{glib, CompositeTemplate};

use crate::alert::Alert;

mod imp {
    use super::*;
    use gtk4::TemplateChild;

    #[derive(Debug, Default, CompositeTemplate)]
    #[template(resource = "/com/github/sheepfarm/merkato/alerts_view.ui")]
    pub struct AlertsView {
        #[template_child]
        pub title_widget: TemplateChild<libadwaita::WindowTitle>,
        #[template_child]
        pub main_box: TemplateChild<gtk4::Box>,
        #[template_child]
        pub empty_state: TemplateChild<libadwaita::StatusPage>,
        #[template_child]
        pub alerts_container: TemplateChild<gtk4::Box>,
        #[template_child]
        pub active_group: TemplateChild<libadwaita::PreferencesGroup>,
        #[template_child]
        pub active_alerts_list: TemplateChild<gtk4::ListBox>,
        #[template_child]
        pub triggered_group: TemplateChild<libadwaita::PreferencesGroup>,
        #[template_child]
        pub triggered_alerts_list: TemplateChild<gtk4::ListBox>,
        #[template_child]
        pub disabled_group: TemplateChild<libadwaita::PreferencesGroup>,
        #[template_child]
        pub disabled_alerts_list: TemplateChild<gtk4::ListBox>,
    }

    #[glib::object_subclass]
    impl ObjectSubclass for AlertsView {
        const NAME: &'static str = "AlertsView";
        type Type = super::AlertsView;
        type ParentType = gtk4::Box;

        fn class_init(klass: &mut Self::Class) {
            klass.bind_template();
        }

        fn instance_init(obj: &glib::subclass::InitializingObject<Self>) {
            obj.init_template();
        }
    }

    impl ObjectImpl for AlertsView {
        fn constructed(&self) {
            self.parent_constructed();
        }
    }

    impl WidgetImpl for AlertsView {}
    impl BoxImpl for AlertsView {}
}

glib::wrapper! {
    pub struct AlertsView(ObjectSubclass<imp::AlertsView>)
        @extends gtk4::Box, gtk4::Widget,
        @implements gtk4::Accessible, gtk4::Buildable, gtk4::ConstraintTarget, gtk4::Orientable;
}

impl AlertsView {
    pub fn new() -> Self {
        glib::Object::new()
    }

    pub fn refresh(
        &self,
        active: &[Alert],
        triggered: &[Alert],
        disabled: &[Alert],
        on_toggle: impl Fn(&str, bool) + Clone + 'static,
        on_reset: impl Fn(&str) + Clone + 'static,
        on_delete: impl Fn(&str) + Clone + 'static,
    ) {
        let imp = self.imp();
        let total = active.len() + triggered.len() + disabled.len();

        imp.empty_state.set_visible(total == 0);
        imp.alerts_container.set_visible(total > 0);

        // Clear all lists
        self.clear_list(&imp.active_alerts_list);
        self.clear_list(&imp.triggered_alerts_list);
        self.clear_list(&imp.disabled_alerts_list);

        imp.active_group.set_visible(!active.is_empty());
        imp.triggered_group.set_visible(!triggered.is_empty());
        imp.disabled_group.set_visible(!disabled.is_empty());

        for alert in active {
            let row = self.build_alert_row(
                alert,
                on_toggle.clone(),
                on_reset.clone(),
                on_delete.clone(),
            );
            imp.active_alerts_list.append(&row);
        }

        for alert in triggered {
            let row = self.build_alert_row(
                alert,
                on_toggle.clone(),
                on_reset.clone(),
                on_delete.clone(),
            );
            imp.triggered_alerts_list.append(&row);
        }

        for alert in disabled {
            let row = self.build_alert_row(
                alert,
                on_toggle.clone(),
                on_reset.clone(),
                on_delete.clone(),
            );
            imp.disabled_alerts_list.append(&row);
        }
    }

    fn clear_list(&self, list: &gtk4::ListBox) {
        while let Some(child) = list.first_child() {
            list.remove(&child);
        }
    }

    fn build_alert_row(
        &self,
        alert: &Alert,
        on_toggle: impl Fn(&str, bool) + 'static,
        on_reset: impl Fn(&str) + 'static,
        on_delete: impl Fn(&str) + 'static,
    ) -> gtk4::ListBoxRow {
        let row = gtk4::ListBoxRow::new();
        row.set_activatable(false);

        let hbox = gtk4::Box::new(gtk4::Orientation::Horizontal, 8);
        hbox.set_margin_top(8);
        hbox.set_margin_bottom(8);
        hbox.set_margin_start(12);
        hbox.set_margin_end(12);

        // Direction icon
        let icon = gtk4::Image::new();
        icon.set_icon_name(Some(if alert.alert_type == crate::alert::AlertType::Above {
            "go-up-symbolic"
        } else {
            "go-down-symbolic"
        }));

        // Info
        let vbox = gtk4::Box::new(gtk4::Orientation::Vertical, 2);
        vbox.set_hexpand(true);

        let title = gtk4::Label::new(Some(&format!(
            "{} {} {:.2}",
            alert.symbol,
            alert.alert_type.display(),
            alert.target_price
        )));
        title.set_halign(gtk4::Align::Start);
        title.add_css_class("title-4");

        let subtitle_text = if let Some(t) = &alert.triggered_at {
            format!("Triggered: {} | Last: {:.2}", &t[..10], alert.last_price)
        } else if alert.last_price > 0.0 {
            format!("Last price: {:.2}", alert.last_price)
        } else {
            format!("Status: {}", alert.status_display())
        };
        let subtitle = gtk4::Label::new(Some(&subtitle_text));
        subtitle.set_halign(gtk4::Align::Start);
        subtitle.add_css_class("caption");
        subtitle.add_css_class("dim-label");

        vbox.append(&title);
        vbox.append(&subtitle);

        // Buttons
        let btn_box = gtk4::Box::new(gtk4::Orientation::Horizontal, 4);

        let alert_id = alert.alert_id.clone();
        let enabled = alert.enabled;
        let is_triggered = alert.is_triggered();

        // Toggle enable/disable button
        let toggle_btn = gtk4::Button::new();
        toggle_btn.set_icon_name(if enabled {
            "media-playback-pause-symbolic"
        } else {
            "media-playback-start-symbolic"
        });
        toggle_btn.add_css_class("flat");
        toggle_btn.add_css_class("circular");
        toggle_btn.set_tooltip_text(Some(if enabled { "Disable" } else { "Enable" }));
        let id2 = alert_id.clone();
        toggle_btn.connect_clicked(move |_| on_toggle(&id2, !enabled));

        // Reset button (only for triggered)
        if is_triggered {
            let reset_btn = gtk4::Button::new();
            reset_btn.set_icon_name("view-refresh-symbolic");
            reset_btn.add_css_class("flat");
            reset_btn.add_css_class("circular");
            reset_btn.set_tooltip_text(Some("Reset"));
            let id3 = alert_id.clone();
            reset_btn.connect_clicked(move |_| on_reset(&id3));
            btn_box.append(&reset_btn);
        }

        // Delete button
        let delete_btn = gtk4::Button::new();
        delete_btn.set_icon_name("user-trash-symbolic");
        delete_btn.add_css_class("flat");
        delete_btn.add_css_class("circular");
        delete_btn.add_css_class("destructive-action");
        delete_btn.set_tooltip_text(Some("Delete"));
        let id4 = alert_id.clone();
        delete_btn.connect_clicked(move |_| on_delete(&id4));

        btn_box.append(&toggle_btn);
        btn_box.append(&delete_btn);

        hbox.append(&icon);
        hbox.append(&vbox);
        hbox.append(&btn_box);

        row.set_child(Some(&hbox));
        row
    }
}

impl Default for AlertsView {
    fn default() -> Self {
        Self::new()
    }
}
