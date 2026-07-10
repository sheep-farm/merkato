// stock_object.rs
//
// Copyright 2025 Flávio de Vasconcellos Corrêa
//
// SPDX-License-Identifier: GPL-3.0-or-later

use gtk4::glib;
use gtk4::subclass::prelude::*;

use crate::stock::Stock;

mod imp {
    use super::*;

    #[derive(Default)]
    pub struct StockObject {
        pub inner: std::cell::RefCell<Stock>,
    }

    #[glib::object_subclass]
    impl ObjectSubclass for StockObject {
        const NAME: &'static str = "MerkatoStockObject";
        type Type = super::StockObject;
        type ParentType = glib::Object;
    }

    impl ObjectImpl for StockObject {}
}

glib::wrapper! {
    pub struct StockObject(ObjectSubclass<imp::StockObject>);
}

impl StockObject {
    pub fn new(stock: Stock) -> Self {
        let obj: Self = glib::Object::new();
        *obj.imp().inner.borrow_mut() = stock;
        obj
    }

    pub fn stock(&self) -> Stock {
        self.imp().inner.borrow().clone()
    }
}
