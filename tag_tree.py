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
import logging
import gobject
from gettext import gettext as _

from tag_model import *

class Tree(TagModel, gtk.TreeView):
    def __init__(self, tag_type):
        TagModel.__init__(self, tag_type)
        self.model = gtk.TreeStore(str, int, bool, gobject.TYPE_PYOBJECT)
        gtk.TreeView.__init__(self, self.model)

        column = self.insert_column_with_attributes(0, _('Tag name'),
                gtk.CellRendererText(), text=0, sensitive=2)
        column.set_sort_column_id(0)
        column.props.expand = True

        column = self.insert_column_with_attributes(1, _('Count'),
                gtk.CellRendererText(), text=1)
        column.set_sort_column_id(1)

        self.connect_after('button-release-event', self._release_cb)

        self.model.set_sort_column_id(0, gtk.SORT_ASCENDING)

    def on_set_tags(self, tags, objects_count):
        self.model.clear()

        parents = {}

        for i in sorted(tags.keys()):
            parent = i[0:-1]
            iter = self.model.append(parents.get(parent))
            tag = tags[i]
            self.model.set(iter, 0, tag[0], 1, tag[1], 2, tag[2], 3, i)
            parents[i] = iter

    def _release_cb(self, sender, event):
        def select(do_select):
            cursor_path = self.get_cursor()[0]
            if not cursor_path:
                return
            iter = self.model.get_iter(cursor_path)
            if not self.model.get(iter, 2)[0]:
                return

            tag = self.model.get(iter, 3)[0]
            name = self.model.get(iter, 0)[0]
            self.select(tag, name, do_select)

        if event.button == 1 and event.state & gtk.gdk.SHIFT_MASK \
                or event.button == 2:
            select(True)
        elif event.button == 1:
            select(False)
