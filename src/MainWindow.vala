/* Main.vala
 *
 * Copyright 2021 - 2022 Flávio Vasconcellos Corrêa
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

[GtkTemplate (ui = "/ui/MktMainWindow.ui")]
public class Mkt.MainWindow : Hdy.ApplicationWindow {
    [GtkChild]
    public unowned Gtk.AccelGroup accel_group {get;}
    [GtkChild]
    public unowned Gtk.Stack stack {get;}

    public MainWindow (Application app) {
        Object (application: app);
    }

    [GtkCallback]
    private void check_resize_set () {
        // int width;
        // int height;
        // get_size (out width, out height);
        // string res = "width: %i; height: %i\n".printf (width, height);
        // print (res);
    }
}
