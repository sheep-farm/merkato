![](data/icons/com.ekonomikas.merkato.svg?raw=true)

# com.ekonomikas.merkato

Just another stock, currency and cryptocurrency tracker. Inspirated in Markets Project ([GitHub - bitstower/markets: A stock, currency and cryptocurrency tracker](https://github.com/bitstower/markets)), with some equals features.
The merkato application delivers financial data to your fingertips. Track stocks, currencies and cryptocurrencies.

## Screenshots

![](preview.png?raw=true)

## Features

* Create your personal portfolio
* Track stocks, currencies, cryptocurrencies, commodities and indexes
* Designed for Gnome
* Open any symbol in Yahoo Finance for more details
* Adjust the refresh rate
* Dark Mode

## Building from source

### Option 1: with GNOME Builder

1. Open GNOME Builder
2. Click the _Clone Repository_ button
3. Enter `https://github.com/sheep-farm/merkato.git` in the field _Repository URL_
4. Click the _Clone Project_ button
5. Click the _Run_ button to start building application

### Option 2: with Meson

You'll need the following dependencies:

* libsoup
* libgee
* libhandy
* json-glib
* gettext
* glib2
* gtk3
* meson
* vala
* ninja
* git

Clone the repository and change to the project directory

```
git clone https://github.com/sheep-farm/merkato.git
cd merkato
```

Run `meson build` to configure the build environment. Change to the build directory and run `ninja` to build

```
meson build --prefix=/usr
cd build
ninja
```

To install, use `ninja install`, then execute with `com.ekonomikas.merkato`

```
sudo ninja install
com.ekonomikas.merkato
```

## License

The GNU General Public License, version 3.0 or later
