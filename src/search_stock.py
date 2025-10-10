import gi
import sys

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GObject

@Gtk.Template(resource_path='/com/github/sheepfarm/merkato/search_stock.ui')
class MerkatoSearchStock(Gtk.Box):
    __gtype_name__ = 'MerkatoSearchStock'

    __gsignals__ = {
        'activate': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'changed': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }

    _entry: Gtk.Entry = Gtk.Template.Child()
    _button: Gtk.Button = Gtk.Template.Child()


    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.reset()


    def clear_entry(self):
        self._entry.set_text('')


    def _on_activate(self, widget):
        self.emit('activate', self._entry.get_text())


    def _on_changed(self, widget):
        self.emit('changed', self._entry.get_text())


    def reset(self):
        self._button.set_sensitive(False)
        self._entry.connect('activate', self._on_activate)
        self._button.connect('clicked', self._on_activate)
        self._entry.connect('changed', self._on_changed)
        self._entry.connect('changed', lambda w: self._button.set_sensitive(len(self._entry.get_text()) > 0))



    def set_text(self, value):
        self._entry.set_text(value)


    def get_text(self):
        return self._entry.get_text()


    def freeze(self, value=True):
        self._button.set_sensitive(value == False)
        self._entry.set_sensitive(value == False)



