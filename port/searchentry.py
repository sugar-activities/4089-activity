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

"""Search entry widget"""

import gtk
import gobject
from gobject import SIGNAL_RUN_FIRST, TYPE_PYOBJECT

from sugar.graphics import iconentry

_AUTOSEARCH_TIMEOUT = 1000

class SearchEntry(iconentry.IconEntry):
    __gsignals__ = {
            'query-changed': (SIGNAL_RUN_FIRST, None, [TYPE_PYOBJECT]) } 

    def __init__(self):
        iconentry.IconEntry.__init__(self)

        self._query = None
        self._autosearch_timer = None

        self.set_icon_from_name(iconentry.ICON_ENTRY_PRIMARY, 'system-search')
        self.add_clear_button()

        self.connect('activate', self._activated_cb)
        self.connect('changed', self._changed_cb)

    def _activated_cb(self, widget):
        if self._autosearch_timer:
            gobject.source_remove(self._autosearch_timer)

        new_query = self.props.text.strip()

        if new_query != self._query:
            self._query = new_query
            self.emit('query-changed', new_query)

    def _changed_cb(self, widget):
        if not self.props.text:
            self.hide_clear_button()
        else:
            self.show_clear_button()

        if not self.props.text:
            self.activate()
            return

        if self._autosearch_timer:
            gobject.source_remove(self._autosearch_timer)

        self._autosearch_timer = gobject.timeout_add(
                _AUTOSEARCH_TIMEOUT, self._autosearch_timer_cb)

    def _autosearch_timer_cb(self):
        self._autosearch_timer = None
        self.activate()
        return False
