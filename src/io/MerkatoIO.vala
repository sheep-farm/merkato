/* MerkatoIO.vala
 *
 * Copyright 2022 Flávio Vasconcellos Corrêa
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

public interface Mkt.MerkatoIO : GLib.Object {
    public abstract Gee.List<Symbol> load_all_symbols ();
    public abstract void save (Gee.List<Symbol> symbol_list);
    public abstract Gee.List<Symbol> load_all_symbols_from_file (string path_file);
    public abstract void save_to_file (Gee.List<Symbol> symbol_list, string path_file);
}
