#!/usr/bin/python3

import sys
import dbus
import subprocess
from gi.repository import GObject
from dbus.mainloop.glib import DBusGMainLoop
from dbus.exceptions import DBusException
from threading import Timer

SIGNAL = sys.argv[1] if len(sys.argv) > 1 else 11

def debounce(wait):
    """ Decorator that will postpone a functions
        execution until after wait seconds
        have elapsed since the last time it was invoked. """
    def decorator(fn):
        def debounced(*args, **kwargs):
            def call_it():
                fn(*args, **kwargs)
            try:
                debounced.t.cancel()
            except(AttributeError):
                pass
            debounced.t = Timer(wait, call_it)
            debounced.t.start()
        return debounced
    return decorator

@debounce(0.1)
def send_i3blocks_signal():
    # print('pkill -RTMIN+%d i3blocks' % SIGNAL)
    subprocess.run('pkill -RTMIN+%d i3blocks' % SIGNAL, shell=True)

class SpotifyI3Blocks(object):
    def __init__(self):
        bus_loop = DBusGMainLoop(set_as_default=True)
        self.bus = dbus.SessionBus(mainloop=bus_loop)
        loop = GObject.MainLoop()
        try: 
            self.props_changed_listener()
        except DBusException as e:
            if not ("org.mpris.MediaPlayer2.spotify was not provided") in e.get_dbus_message():
                raise
        self.session_bus = self.bus.get_object(
            "org.freedesktop.DBus",
            "/org/freedesktop/DBus"
        )
        self.session_bus.connect_to_signal(
            "NameOwnerChanged", 
            self.handle_name_owner_changed,
            arg0="org.mpris.MediaPlayer2.spotify"
        )

        loop.run()

    def props_changed_listener(self):
        """Hook up callback to PropertiesChanged event."""
        self.spotify = self.bus.get_object(
            "org.mpris.MediaPlayer2.spotify", 
            "/org/mpris/MediaPlayer2"
        )
        self.spotify.connect_to_signal(
            "PropertiesChanged", 
            self.handle_properties_changed
        )

    def handle_name_owner_changed(self, name, older_owner, new_owner):
        """Introspect the NameOwnerChanged signal to work out if spotify has started."""
        if name == "org.mpris.MediaPlayer2.spotify":
            send_i3blocks_signal()
            if new_owner:
                # spotify has been launched - hook it up.
                self.props_changed_listener()
            else:
                self.spotify = None

    def handle_properties_changed(self, interface, changed_props, invalidated_props):
        """Handle track changes."""
        send_i3blocks_signal()
        # metadata = changed_props.get("Metadata", {})
        # status = changed_props.get("PlaybackStatus", {})
        # if metadata:
        #     title = metadata.get("xesam:title")
        #     album = metadata.get("xesam:album")
        #     artist = metadata.get("xesam:artist")
        #     print('%s, %s, %s' % (title, album, artist))
        # if status:
        #     print(status)

if __name__ == "__main__":
    SpotifyI3Blocks()