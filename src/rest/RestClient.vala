/* RestClient.vala
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

public class Mkt.RestClient {
    private Soup.Session session;
    private ApplicationSet app_set;

    public RestClient () {
        this.session = new Soup.Session ();
    }

    public async Json.Node fetch (string url) {
        app_set = (ApplicationSet) Lookup.singleton ().find (ApplicationSet.ID);
        try {
            app_set.network_status = ApplicationSet.NetworkStatus.IN_PROGRESS;
            var message = new Soup.Message ("GET", url);
            yield this.queue_message (this.session, message);
            if (message.status_code < 200 || message.status_code >= 300) {
                warning (@"Unexpected response: $(message.status_code) $(message.reason_phrase)");
            } else {
                var body = (string) message.response_body.data;
                if (body != null && body != "") {
                    app_set.network_status = ApplicationSet.NetworkStatus.IDLE;
                    app_set.query_status = ApplicationSet.QueryStatus.SUCCESS;
                    return Json.from_string (body);
                }
            }
        } catch (Error e) {}
        app_set.query_status = ApplicationSet.QueryStatus.FAILURE;
        return (Json.Node) null;
    }

    public async void queue_message (Soup.Session session, Soup.Message message) {
        SourceFunc async_callback = queue_message.callback;
        session.queue_message (message, () => { async_callback (); });
        yield;
    }
}
