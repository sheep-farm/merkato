#!/usr/bin/env python3

from os import environ, path
from subprocess import call

prefix = environ.get('MESON_INSTALL_PREFIX', '/usr/local')
schemadir = path.join(environ['MESON_INSTALL_PREFIX'], 'share', 'glib-2.0', 'schemas')
datadir = path.join(prefix, 'share')

desktop_database_dir = path.join(datadir, 'applications')

# Package managers set this so we don't need to run
if not environ.get('DESTDIR'):
    print('Updating icon cache...')
    call(['gtk-update-icon-cache', '-qtf', path.join(datadir, 'icons', 'hicolor')])

    print('Updating desktop database...')
    call(['update-desktop-database', '-q', path.join(datadir, desktop_database_dir)])

    print('Compiling GSettings schemas...')
    call(['glib-compile-schemas', path.join(datadir, 'glib-2.0', 'schemas')])
