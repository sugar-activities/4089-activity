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
import logging

import model
import path

STATUS_ACTIVE    = 0
STATUS_FREEZE    = 1
STATUS_POSTPONED = 2

NOTIFY_TIMEOUT = 500

class TagModel:
    def __init__(self, tag_type):
        self.tag_type = tag_type
        self._status = STATUS_FREEZE
        self._select_mode = False
        self._select_timer = None

        model.source.connect('tags-updated', self._tags_updated_cb)

    def update(self, force=False):
        if (self._status == STATUS_POSTPONED or force) and \
                not self._select_mode:
            self.on_set_tags(model.source.tags[self.tag_type],
                    model.source.get_count())
        self._status = STATUS_ACTIVE

    def freeze(self):
        if self._status == STATUS_ACTIVE:
            self._status = STATUS_FREEZE
        self._select_mode = False

    def select(self, tag, name, do_select):
        if self._select_timer:
            gobject.source_remove(self._select_timer)

        if not do_select:
            self._select_mode = False
            path.add_tag(self.tag_type, tag, name)
            return

        #def notify_timer_cb():
        self._select_mode = True
        self._select_timer = None
        path.select_tag(self.tag_type, tag, name)

        #self._select_timer = \
        #        gobject.timeout_add(NOTIFY_TIMEOUT, notify_timer_cb)

    def on_set_tags(self, tags, objects_count):
        # stub
        pass

    def _tags_updated_cb(self, model, type):
        if type != self.tag_type:
            return
        if self._status == STATUS_ACTIVE:
            self.update(True)
        else:
            self._status = STATUS_POSTPONED
