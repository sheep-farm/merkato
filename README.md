
# Merkato

A modern financial markets tracker for GNOME, built with **Rust**, GTK4 and Libadwaita.

![License](https://img.shields.io/badge/license-GPL--3.0-blue.svg)
![Version](https://img.shields.io/badge/version-0.3.0-orange.svg)
![Platform](https://img.shields.io/badge/platform-Linux-lightgrey.svg)
![Language](https://img.shields.io/badge/language-Rust-brown.svg)

## Overview

Merkato is a beautiful and intuitive application for tracking stocks, currencies, and cryptocurrencies. It provides real-time market data from Yahoo Finance with a clean, native GNOME interface. Esta versão foi refatorada em Rust para oferecer maior performance e segurança.

### Key Features

- 📊 **Real-time Market Data** - Track stocks, indices, currencies, and cryptocurrencies.
- 🎨 **Modern Interface** - Built with GTK4 and Libadwaita for a native GNOME experience.
- 🦀 **Rust Core** - Desenvolvido com foco em segurança de memória e concorrência.
- 🗂️ **Smart Categories** - Automatic categorization by sector (Technology, Healthcare, Energy, etc.).
- 🔥 **Heatmap View** - Visual representation of market performance with color-coded tiles.
- 📋 **List View** - Detailed stock information in an organized list.
- 💾 **Persistent Watchlist** - Your selections are automatically saved.
- 🔔 **Price Alerts** - Set alerts for target prices with automatic notifications.
- 🔄 **Auto-refresh** - Automatic updates every 60 seconds.
- 🌍 **Multi-language** - Support for 27 languages.

## Screenshots

### List View

![List View](screenshots/list_view.png)

View your stocks in a clean, organized list with real-time prices and changes.

### Heatmap View

![Heatmap View](screenshots/heatmap_view.png)

Visualize market performance with color-coded tiles - green for gains, red for losses.

### Price Alerts

![Price Alerts](screenshots/alerts_view.png)

Set custom price alerts to be notified when stocks reach your target prices.

## Installation

### From Flatpak (Recommended)

```sh
flatpak install flathub com.ekonomikas.merkato

```

### From Source

#### Dependencies

* **Rust (Cargo)** 1.75+
* **GTK 4** development files
* **Libadwaita 1** development files

#### Build Instructions

```sh
# Clone the repository
git clone [https://github.com/sheep-farm/merkato.git](https://github.com/sheep-farm/merkato.git)
cd merkato

# Build and run the application
cargo run --release

```

## Architecture

### Core Components (Rust Implementation)

* **Stock Controller** - Manages stock data fetching and auto-updates via **Tokio**.
* **Yahoo Request** - Handles concurrent API requests using **Reqwest**.
* **Category Model** - Organizes stocks by sector.
* **Watchlist Manager** - Persists user selections via **Serde**.
* **Alert Manager** - Manages price alerts (CRUD, persistence, verification).
* **Heatmap View** - Custom Cairo-based visualization widget.

### Data Flow

1. User searches for ticker symbols.
2. Reqwest fetches data concurrently using asynchronous tasks.
3. Stock objects are created with price, change, and sector information.
4. CategoryModel organizes stocks by sector.
5. Views (List/Heatmap) display the filtered data.
6. Serde handles persistence to `~/.config/merkato/`.
7. AlertManager checks price conditions and triggers notifications.

## Development

### Project Structure

```
merkato/
├── Cargo.toml                  # Rust dependencies and metadata
├── src/
│   ├── alert.rs                # Alert data model
│   ├── alert_manager.rs        # Alert CRUD and persistence
│   ├── category_model.rs       # Sector categorization
│   ├── heatmap_view.rs         # Visual grid view
│   ├── stock.rs                # Stock data model
│   ├── stock_controller.rs     # Business logic
│   ├── watchlist_manager.rs    # Persistence layer
│   └── window.rs               # Main window
├── po/                         # Translations
├── data/                       # UI files, icons, schemas
└── README.md

```

## Credits

### Author

* **Flávio de Vasconcellos Corrêa** - Main developer.


### Data Source

* **Yahoo Finance** - Real-time market data via **Reqwest**.

## License

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License.
