app_sources = [
  'beans/Symbol.vala',
  'beans/Ticker.vala',
  'persistence/SymbolPersistence.vala',
  'rest/RestClient.vala',
  'rest/YahooFinanceClient.vala',
  'tools/Lookup.vala',
  'views/symbol/NoSymbolView.vala',
  'views/symbol/SymbolRow.vala',
  'views/symbol/SymbolView.vala',
  'views/symbol/SymbolViewBox.vala',
  'views/ticker/NoTickerView.vala',
  'views/ticker/TickerRow.vala',
  'views/ticker/TickerView.vala',
  'views/ticker/TickerViewBox.vala',
  'views/ErrorView.vala',
  'AboutDialog.vala',
  'Application.vala',
  'ApplicationSet.vala',
  'PreferencesWindow.vala',
  'MainWindow.vala',
   app_constants,
   app_ui_resources,
]

app_deps = [
  dependency ('gio-2.0'    , version: '>= 2.50' ),
  dependency ('gtk+-3.0'   , version: '>= 3.22' ),
  dependency ('libhandy-1' , version: '>= 1.0.0'),
  dependency ('libsoup-2.4', version: '>= 2.66' ),
  dependency ('json-glib-1.0'),
  dependency ('gee-0.8')
]

# gnome = import ('gnome')

# app_sources += gnome.compile_resources (
#   'merkato-resources',
#   'merkato.gresource.xml',
#   c_name: 'merkato'
# )

app_c_args = [
  '-DHANDY_USE_UNSTABLE_API',
]

executable (app_binary, app_sources,
  vala_args: '--target-glib=2.50',
  dependencies: app_deps,
  c_args: app_c_args,
  install: true,
)
