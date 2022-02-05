/* MerkatoJSON.vala
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

using Mkt, Json;

public class MerkatoJSON : GLib.Object, MerkatoIO {

    public Gee.List<Symbol> load_all_symbols () {
        return load_all_symbols_from_file (get_config_file ("symbols.json"));
    }

    public void save (Gee.List<Symbol> symbol_list) {
        save_to_file (symbol_list, get_config_file ("symbols.json"));
    }

    public Gee.List<Symbol> load_all_symbols_from_file (string path_file) {
        var symbol_list = new Gee.ArrayList<Symbol> ();
        try {
            Parser parser = new Parser ();
            parser.load_from_file (path_file);
            var objects = parser.get_root ().get_object ().get_array_member ("symbols");
            for (var i = 0; i < objects.get_length (); i++) {
                var symbol = new Symbol.from_json (objects.get_object_element (i));
                symbol_list.add (symbol);
            }
        }  catch (Error e) {
            warning (@"$(e.message)");
        }
        return symbol_list;
    }

    public void save_to_file (Gee.List<Symbol> symbol_list, string path_file) {
        try {
            Builder builder = new Builder ();

            builder.begin_object ();
                builder.set_member_name ("version");
                builder.add_int_value (1);

                builder.set_member_name ("symbols");
                builder.begin_array ();
                    foreach (var s in symbol_list) {
                        s.build_json (builder);
                    }
                builder.end_array ();
            builder.end_object ();

            Generator generator = new Generator ();
            generator.root = builder.get_root ();
            generator.pretty = false;
            generator.to_file (path_file);
        }  catch (Error e) {
            warning (@"$(e.message)");
        }
    }

    private string get_config_file (string file_name) {
        try {
            var path = string.join ("/", Environment.get_user_config_dir (), Environment.get_application_name ());
            var config_dir = File.new_for_path (path);
            if (!config_dir.query_exists ()) {
                config_dir.make_directory ();
            }
            return config_dir.resolve_relative_path (file_name).get_path ();
        }  catch (Error e) {
            warning (@"$(e.message)");
        }
        return (string) null;
    }
}
