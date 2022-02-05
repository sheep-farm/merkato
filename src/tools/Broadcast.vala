/* Broadcast.vala
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

public class Mkt.Broadcast : GLib.Object {
    public const string ID = "Mkt.Broadcast";

    public enum ChannelEvent {
        ON, CHANGE, OFF
    }

    public enum ChannelState {
        ON, OFF
    }

    private Gee.Map<string, Channel> channel_map = new Gee.HashMap<string, Channel> ();

    private Gee.Map<string, Gee.List<Consumer>> orphan_consumer = new Gee.HashMap<string, Gee.List<Consumer>> ();

    public void register (Channel channel) {
        if (!channel_map.has_key (channel.uuid)) {
            channel_map.@set (channel.uuid, channel);
            if (orphan_consumer.has_key (channel.uuid)) {
                Gee.List<Consumer> consumers = orphan_consumer.@get (channel.uuid);
                foreach (var consumer in consumers) {
                    channel.connector.connect (consumer.receive);
                }
                consumers.clear ();
            }
            channel.channel_on ();
        }
    }

    // public void unregister (Channel channel) {
    //     var uuid = channel.get_uuid ();
    //     if (channel_map.has_key (uuid)) {
    //         channel_map.unset (uuid);
    //     }
    // }

    public void consumer (string uuid, Consumer consumer) {
        if (channel_map.has_key (uuid)) {
            Channel channel = channel_map.@get (uuid);
            channel.connector.connect (consumer.receive);
        } else {
            if (!orphan_consumer.has_key (uuid)) {
                orphan_consumer.@set (uuid, new Gee.ArrayList<Consumer> ());
            }
            Gee.List<Consumer> consumers = orphan_consumer.@get (uuid);
            if (!consumers.contains (consumer)) {
                consumers.add (consumer);
            }
        }
    }

    public void unconsumer (string uuid, Consumer consumer) {
        if (channel_map.has_key (uuid)) {
            Channel channel = channel_map.@get (uuid);
            channel.connector.disconnect (consumer.receive);
        } else {
            if (orphan_consumer.has_key (uuid)) {
                Gee.List<Consumer> consumers = orphan_consumer.@get (uuid);
                if (!consumers.contains (consumer)) {
                    consumers.remove (consumer);
                }
            }
        }
    }

}
