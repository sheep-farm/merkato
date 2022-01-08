/* Lookup.vala
 *
 * Copyright 2021 Flávio Vasconcellos Corrêa
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */
using Mkt;

public class Mkt.Lookup : Object {
    private Gee.Map<string, Object> lookup_list = new Gee.HashMap<string, Object> ();
    private static GLib.Once<Lookup> _instance;


    public static unowned Mkt.Lookup singleton () {
        return _instance.once (() => { return new Lookup (); });
    }

    public Object find (string key) {
        return lookup_list.get (key);
    }

    public void put (string key, Object _value) {
        if (key.length == 0) return;
        if (_value == null) return;
        lookup_list.@set(key, _value);
    }
}
