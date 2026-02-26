// heatmap_view.rs
//
// Copyright 2025 Flávio de Vasconcellos Corrêa
//
// SPDX-License-Identifier: GPL-3.0-or-later

use std::cell::{Cell, RefCell};

use cairo::Context;
use gtk4::graphene::Rect;
use gtk4::prelude::*;
use gtk4::subclass::prelude::*;
use gtk4::{glib, Snapshot};

use crate::stock::Stock;

// ─── Tile ─────────────────────────────────────────────────────────────────────

#[derive(Clone, Debug)]
pub struct Tile {
    stock: Stock,
    x: f64,
    y: f64,
    w: f64,
    h: f64,
}

// ─── Squarified treemap ───────────────────────────────────────────────────────
//
// Stocks are pre-sorted descending by change_pct so that the biggest gainers
// land top-left and biggest losers land bottom-right — the same convention
// used by Yahoo Finance and Finviz.  Every stock gets equal weight so tile
// sizes stay roughly uniform (no distortion from price magnitude).

fn squarify(stocks: &[Stock], x: f64, y: f64, w: f64, h: f64) -> Vec<Tile> {
    if stocks.is_empty() || w <= 0.0 || h <= 0.0 {
        return vec![];
    }

    // Sort: best gainer first → worst loser last
    let mut sorted = stocks.to_vec();
    sorted.sort_by(|a, b| {
        b.change_pct
            .partial_cmp(&a.change_pct)
            .unwrap_or(std::cmp::Ordering::Equal)
    });

    let n = sorted.len() as f64;
    let mut tiles = Vec::new();
    squarify_row(&sorted, x, y, w, h, w * h, n, &mut tiles);
    tiles
}

fn squarify_row(
    stocks: &[Stock],
    x: f64, y: f64, w: f64, h: f64,
    total_area: f64, total_n: f64,
    tiles: &mut Vec<Tile>,
) {
    if stocks.is_empty() { return; }

    let min_side = w.min(h);
    let mut best_end = 1;
    let mut best_ratio = f64::MAX;

    for end in 1..=stocks.len() {
        let row_n = end as f64;
        let row_area = total_area * row_n / total_n;
        let ratio = worst_ratio_equal(row_n, row_area, min_side);
        if ratio <= best_ratio {
            best_ratio = ratio;
            best_end = end;
        } else {
            break;
        }
    }

    let row = &stocks[..best_end];
    let rest = &stocks[best_end..];
    let row_n = best_end as f64;
    let row_area = total_area * row_n / total_n;

    if w >= h {
        // Horizontal strip
        let strip_w = row_area / h;
        let tile_h = h / row_n;
        for (k, stock) in row.iter().enumerate() {
            tiles.push(Tile {
                stock: stock.clone(),
                x,
                y: y + k as f64 * tile_h,
                w: strip_w,
                h: tile_h,
            });
        }
        squarify_row(rest, x + strip_w, y, w - strip_w, h,
                     total_area - row_area, total_n - row_n, tiles);
    } else {
        // Vertical strip
        let strip_h = row_area / w;
        let tile_w = w / row_n;
        for (k, stock) in row.iter().enumerate() {
            tiles.push(Tile {
                stock: stock.clone(),
                x: x + k as f64 * tile_w,
                y,
                w: tile_w,
                h: strip_h,
            });
        }
        squarify_row(rest, x, y + strip_h, w, h - strip_h,
                     total_area - row_area, total_n - row_n, tiles);
    }
}

/// Worst aspect ratio for a strip of `n` equal-area tiles fitted into
/// a row of `row_area` on the shorter side `s`.
fn worst_ratio_equal(n: f64, row_area: f64, s: f64) -> f64 {
    if n <= 0.0 || row_area <= 0.0 || s <= 0.0 { return f64::MAX; }
    let tile_area = row_area / n;
    let strip_w   = row_area / s;       // width of the strip
    let tile_h    = tile_area / strip_w; // height of each tile in strip
    (strip_w / tile_h).max(tile_h / strip_w)
}

// ─── Color ────────────────────────────────────────────────────────────────────

fn lerp(a: f64, b: f64, t: f64) -> f64 { a + (b - a) * t }

fn lerp_rgb(from: (f64, f64, f64), to: (f64, f64, f64), t: f64) -> (f64, f64, f64) {
    (lerp(from.0, to.0, t), lerp(from.1, to.1, t), lerp(from.2, to.2, t))
}

/// Professional palette: colours saturate as magnitude grows (0 → ±5 %).
fn tile_color(change_pct: f64, hover: bool) -> (f64, f64, f64) {
    let t = (change_pct.abs() / 5.0).min(1.0);

    let base = if change_pct > 0.0 {
        // #1e4d32 → #16a34a  (muted dark green → saturated green)
        lerp_rgb((0.118, 0.302, 0.196), (0.086, 0.639, 0.290), t)
    } else if change_pct < 0.0 {
        // #4d1e1e → #dc2626  (muted dark red → saturated red)
        lerp_rgb((0.302, 0.118, 0.118), (0.863, 0.149, 0.149), t)
    } else {
        (0.196, 0.196, 0.204) // neutral slate
    };

    if hover {
        ((base.0 + 0.12).min(1.0),
         (base.1 + 0.12).min(1.0),
         (base.2 + 0.12).min(1.0))
    } else {
        base
    }
}

// ─── Text helper ─────────────────────────────────────────────────────────────

/// Render `text` horizontally centred at `cx`, ink top at `ink_top`.
/// Returns the ink height so the caller can stack lines.
fn draw_hcentered(cr: &Context, text: &str, cx: f64, ink_top: f64) -> f64 {
    let e = cr.text_extents(text)
        .unwrap_or_else(|_| cairo::TextExtents::new(0., 0., 0., 0., 0., 0.));
    cr.move_to(cx - e.width() / 2.0 - e.x_bearing(), ink_top - e.y_bearing());
    let _ = cr.show_text(text);
    e.height()
}

// ─── GObject subclass ─────────────────────────────────────────────────────────

mod imp {
    use super::*;

    #[derive(Default)]
    pub struct HeatmapView {
        pub stocks: RefCell<Vec<Stock>>,
        pub tiles: RefCell<Vec<Tile>>,
        pub hovered_index: Cell<Option<usize>>,
    }

    #[glib::object_subclass]
    impl ObjectSubclass for HeatmapView {
        const NAME: &'static str = "HeatmapView";
        type Type = super::HeatmapView;
        type ParentType = gtk4::Widget;
    }

    impl ObjectImpl for HeatmapView {
        fn constructed(&self) {
            self.parent_constructed();
            let widget = self.obj();
            widget.set_vexpand(true);
            widget.set_hexpand(true);

            // Hover
            let motion = gtk4::EventControllerMotion::new();
            motion.connect_motion(glib::clone!(
                #[weak] widget,
                move |_, x, y| {
                    let imp = widget.imp();
                    let tiles = imp.tiles.borrow();
                    let found = tiles.iter().position(|t| {
                        x >= t.x && x < t.x + t.w && y >= t.y && y < t.y + t.h
                    });
                    if imp.hovered_index.get() != found {
                        imp.hovered_index.set(found);
                        widget.queue_draw();
                    }
                }
            ));
            motion.connect_leave(glib::clone!(
                #[weak] widget,
                move |_| {
                    widget.imp().hovered_index.set(None);
                    widget.queue_draw();
                }
            ));
            widget.add_controller(motion);

            // Click → open Yahoo Finance
            let click = gtk4::GestureClick::new();
            click.connect_released(glib::clone!(
                #[weak] widget,
                move |_, _, x, y| {
                    let tiles = widget.imp().tiles.borrow();
                    if let Some(tile) = tiles.iter().find(|t| {
                        x >= t.x && x < t.x + t.w && y >= t.y && y < t.y + t.h
                    }) {
                        let url = format!(
                            "https://finance.yahoo.com/quote/{}",
                            tile.stock.symbol
                        );
                        let _ = gtk4::gio::AppInfo::launch_default_for_uri(
                            &url,
                            gtk4::gio::AppLaunchContext::NONE,
                        );
                    }
                }
            ));
            widget.add_controller(click);
        }
    }

    impl WidgetImpl for HeatmapView {
        fn snapshot(&self, snapshot: &Snapshot) {
            let widget = self.obj();
            let width  = widget.width()  as f64;
            let height = widget.height() as f64;
            if width <= 0.0 || height <= 0.0 { return; }

            let stocks = self.stocks.borrow().clone();
            let tiles  = squarify(&stocks, 0.0, 0.0, width, height);
            *self.tiles.borrow_mut() = tiles.clone();

            let cr = snapshot.append_cairo(
                &Rect::new(0.0, 0.0, width as f32, height as f32),
            );
            self.draw_tiles(&cr, &tiles);
        }
    }

    impl HeatmapView {
        fn draw_tiles(&self, cr: &Context, tiles: &[Tile]) {
            let hovered = self.hovered_index.get();
            let gap     = 2.0_f64;

            for (i, tile) in tiles.iter().enumerate() {
                let is_hover = hovered == Some(i);
                let (r, g, b) = tile_color(tile.stock.change_pct, is_hover);

                let x = tile.x + gap / 2.0;
                let y = tile.y + gap / 2.0;
                let w = (tile.w - gap).max(1.0);
                let h = (tile.h - gap).max(1.0);

                // ── Fill ─────────────────────────────────────────────────────
                cr.rectangle(x, y, w, h);
                cr.set_source_rgb(r, g, b);
                let _ = cr.fill();

                // ── Hover: top edge accent line ───────────────────────────────
                if is_hover {
                    cr.rectangle(x, y, w, 2.5);
                    cr.set_source_rgba(1.0, 1.0, 1.0, 0.55);
                    let _ = cr.fill();
                }

                // ── Text ─────────────────────────────────────────────────────
                if w < 36.0 || h < 24.0 { continue; }

                let symbol = &tile.stock.symbol;
                let pct    = tile.stock.formatted_change_pct();
                let price  = tile.stock.formatted_price();

                let show_pct   = h > 44.0;
                let show_price = h > 70.0;

                // Sizes
                let sym_sz = (w / symbol.len() as f64 * 1.7)
                    .min(h / if show_pct { 2.9 } else { 1.8 })
                    .min(26.0)
                    .max(9.0);
                let pct_sz   = (sym_sz * 0.72).max(7.0);
                let price_sz = (pct_sz  * 0.80).max(7.0);

                let cx = x + w / 2.0;

                // Measure symbol to compute group vertical centre
                cr.select_font_face(
                    "Sans", cairo::FontSlant::Normal, cairo::FontWeight::Bold,
                );
                cr.set_font_size(sym_sz);
                let sym_h = cr.text_extents(symbol)
                    .map(|e| e.height()).unwrap_or(sym_sz);

                let gap_lines = sym_sz * 0.28;

                cr.select_font_face(
                    "Sans", cairo::FontSlant::Normal, cairo::FontWeight::Normal,
                );
                cr.set_font_size(pct_sz);
                let pct_h = if show_pct {
                    cr.text_extents(&pct).map(|e| e.height()).unwrap_or(pct_sz)
                } else { 0.0 };

                let group_h   = if show_pct { sym_h + gap_lines + pct_h } else { sym_h };
                let group_top = y + (h - group_h) / 2.0;

                // Symbol
                cr.select_font_face(
                    "Sans", cairo::FontSlant::Normal, cairo::FontWeight::Bold,
                );
                cr.set_font_size(sym_sz);
                cr.set_source_rgba(1.0, 1.0, 1.0, 0.95);
                draw_hcentered(cr, symbol, cx, group_top);

                // Percentage
                if show_pct {
                    cr.select_font_face(
                        "Sans", cairo::FontSlant::Normal, cairo::FontWeight::Normal,
                    );
                    cr.set_font_size(pct_sz);
                    cr.set_source_rgba(1.0, 1.0, 1.0, 0.78);
                    draw_hcentered(cr, &pct, cx, group_top + sym_h + gap_lines);
                }

                // Price — anchored near bottom
                if show_price {
                    cr.select_font_face(
                        "Sans", cairo::FontSlant::Normal, cairo::FontWeight::Normal,
                    );
                    cr.set_font_size(price_sz);
                    cr.set_source_rgba(1.0, 1.0, 1.0, 0.45);
                    let ph = cr.text_extents(&price)
                        .map(|e| e.height()).unwrap_or(price_sz);
                    draw_hcentered(cr, &price, cx, y + h - ph - gap * 2.0);
                }
            }
        }
    }
}

glib::wrapper! {
    pub struct HeatmapView(ObjectSubclass<imp::HeatmapView>)
        @extends gtk4::Widget,
        @implements gtk4::Accessible, gtk4::Buildable, gtk4::ConstraintTarget;
}

impl HeatmapView {
    pub fn new() -> Self { glib::Object::new() }

    pub fn set_stocks(&self, stocks: Vec<Stock>) {
        *self.imp().stocks.borrow_mut() = stocks;
        self.queue_draw();
    }
}

impl Default for HeatmapView {
    fn default() -> Self { Self::new() }
}
