/* AboutStocksDialog.vala
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
class Mkt.AboutDialog : Gtk.AboutDialog {
    public const string ID = "Mkt.AboutDialog";

    public AboutDialog (Gtk.Window owner) {
        set_destroy_with_parent (true);
        set_transient_for (owner);
        set_modal (true);
        logo_icon_name = Constants.APP_ID;
        version        = Constants.APP_VERSION;
        program_name  = "Merkato";
        comments      = _("Track of your investiments.");
        authors       = {"Flávio Vasconcellos Corrêa"};
        artists       = {"Flávio Vasconcellos Corrêa"};
        license_type  = Gtk.License.GPL_3_0;
        website       = "https://github.com/sheep-farm/merkato";
        website_label = _("Official webpage");
    }
}

