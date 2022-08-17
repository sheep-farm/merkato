install_data (
  app_id + '.svg',
  install_dir: join_paths (
  	app_install_prefix,
  	get_option('datadir'),
  	'icons',
  	'hicolor',
  	'scalable',
  	'apps'),
)

icon_gresource = gnome.compile_resources (
    'gresource',
    'icon.gresource.xml',
    source_dir: 'data'
)
