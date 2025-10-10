pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'merkato'
gnome = import('gnome')

subdir('blp')

gnome.compile_resources('merkato',
  'merkato.gresource.xml',
  gresource_bundle: true,
  dependencies: blueprints,
  install: true,
  install_dir: pkgdatadir,
)

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').full_path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', get_option('prefix') / get_option('localedir'))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'merkato.in',
  output: 'merkato',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'r-xr-xr-x'
)

merkato_sources = [
  '__init__.py',
  'main.py',
  'window.py',
  'stock.py',
  'search_stock.py',
  'list_stock.py',
  'yahoo_request.py',
  'watchlist_manager.py',
]

install_data(merkato_sources, install_dir: moduledir)
