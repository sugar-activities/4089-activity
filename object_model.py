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

import gtk
import gobject

from sugar import util
from sugar.graphics.xocolor import XoColor
from port.lazyview import Model
import port.pixbuf
import port.shell

import model
from theme import *
from source import *
from object_menu import ObjectMenu

class ObjectModel(Model):
    def __init__(self):
        Model.__init__(self, model.source, FIELD_BASE_LIST, FIELD_CALC_LIST)
        self._fetch_queue = []

    def fetch_metadata(self, row, fetch_cb=None):
        def reply_cb(metadata):
            row = self._fetch_queue[0]
            del self._fetch_queue[0]

            pixbuf = port.pixbuf.from_str(metadata.get('preview', ''))
            if pixbuf:
                row[FIELD_THUMB] = port.pixbuf.at_size_with_ratio(pixbuf,
                        model.THUMB_WIDTH, model.THUMB_HEIGHT)
                row[FIELD_PREVIEW] = port.pixbuf.at_size_with_ratio(pixbuf,
                        model.PREVIEW_WIDTH, model.PREVIEW_HEIGHT)

            row.object.update(metadata)
            row[FIELD_LAST] = True

            self.emit('row-changed', row.path, row.iter)
            if fetch_cb:
                fetch_cb(row)

            if len(self._fetch_queue):
                idle_cb()

        def idle_cb():
            while len(self._fetch_queue):
                row = self._fetch_queue[0]
                if self.in_frame(row.path[0]):
                    self.source.get_object(row['uid'], reply_cb)
                    break
                del self._fetch_queue[0]
            return False

        if row.has_key(FIELD_LAST):
            return row

        self._fetch_queue.append(row)
        if len(self._fetch_queue) == 1:
            gobject.idle_add(idle_cb)

    def on_calc_value(self, row, column):
        if column == FIELD_ICON:
            return port.pixbuf.sugar_icon(
                    file_name=port.shell.get_icon_filename(
                        activity=row[FIELD_ACTIVITY] or row[FIELD_BUNDLE_ID],
                        mime_type=row[FIELD_MIME_TYPE]),
                    width=model.ICON_SIZE, height=model.ICON_SIZE,
                    color=XoColor(row[FIELD_ICON_COLOR]))

        elif column == FIELD_MODIFY_TIME:
            if row[FIELD_TIMESTAMP]:
                timestamp = float(row[FIELD_TIMESTAMP])
                return util.timestamp_to_elapsed_string(timestamp)
            elif row[FIELD_MTIME]:
                ti = time.strptime(row[FIELD_MTIME], '%Y-%m-%dT%H:%M:%S')
                return util.timestamp_to_elapsed_string(time.mktime(ti))
            else:
                return _('No date')

        elif column >= FIELD_BUDDY_FIRST \
                and column < FIELD_BUDDY_FIRST + VISIBLE_BUDDIES_COUNT:
            buddies = row[FIELD_BUDDIES] or []
            if not buddies:
                return None
            buddy_num = column - FIELD_BUDDY_FIRST
            if buddy_num >= len(buddies):
                return None
            return port.pixbuf.sugar_icon(
                    icon_name = 'computer-xo',
                    width=model.ICON_SIZE, height=model.ICON_SIZE,
                    color=XoColor(buddies[buddy_num][2]))

        elif column == FIELD_THUMB:
            self.fetch_metadata(row)
            return model.THUMB_STUB

        elif column == FIELD_PREVIEW:
            self.fetch_metadata(row)
            return model.PREVIEW_STUB

        elif column == FIELD_BUDDY_MENU:
            return ObjectMenu(row, row[FIELD_ICON])

        return None
