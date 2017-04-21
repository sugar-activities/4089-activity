# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import logging
import dbus
from dbus.gobject_service import ExportedGObject
from dbus.service import method, signal

import port.json as json
from sugar.presence import presenceservice

SERVICE = 'org.sugarlabs.Library'
IFACE = SERVICE
PATH = '/org/sugarlabs/Library'

class Messenger(ExportedGObject):
    def __init__(self, tube, initiator):
        ExportedGObject.__init__(self, tube, PATH)

        self.initiator = initiator
        self._tube = tube
        self.me = None

        self._tube.watch_participants(self._participant_changed_cb)

    def _participant_changed_cb(self, added, removed):
        if not self.me and added:
            self.me = self._tube.get_unique_name()
            logging.debug('initiate session me=%s' % self.me)
            added = [i for i in added if i[1] != self.me]

        if removed:
            logging.error('2--------------')
            logging.error(removed)
            return

        logging.error('3--------------')
        logging.error(added)
        return

        logging.debug('join session me=%s' % self.me)

        self._tube.add_signal_receiver(self._tags_changed_cb,
                '_tags_changed', IFACE, path=PATH,
                sender_keyword='sender')
        self._tube.add_signal_receiver(self._objects_changed_cb,
                '_objects_changed', IFACE, path=PATH,
                sender_keyword='sender')

    @signal(IFACE, signature='s')
    def _tags_changed(self, raw_tags):
        pass

    @signal(IFACE, signature='')
    def _objects_changed(self):
        pass
