/* MerkatoIOFactory.vala
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

public class Mkt.MerkatoIOFactory : GLib.Object {

    public enum Type {
        JSON, DEFAULT
    }

    public static MerkatoIO make_default () {
        return make_with_parameter (Type.DEFAULT);
    }

    public static MerkatoIO make_with_parameter (Type type) {
        switch (type) {
            case JSON:
            case DEFAULT:
            default:
                return new MerkatoJSON ();

        }
    }

}
