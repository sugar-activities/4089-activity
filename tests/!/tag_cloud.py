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
import pango
from gobject import SIGNAL_RUN_FIRST, TYPE_PYOBJECT

from sugar.graphics import style

SORT_ALPHABET = 0
SORT_COUNT    = 1

GRADE_COUNT = 6
GRADE_MULT  = .2

FONT_SIZE_MIN = 9

class Cloud(gtk.TextView):
    __gsignals__ = {
            'tag-selected': (SIGNAL_RUN_FIRST, None, [TYPE_PYOBJECT]) }

    hand_cursor = gtk.gdk.Cursor(gtk.gdk.HAND2)
    regular_cursor = gtk.gdk.Cursor(gtk.gdk.XTERM)

    def __init__(self, tag_type):
        gtk.TextView.__init__(self)

        self.sort = SORT_ALPHABET
        self.reverse = False

        self._tags = []
        self._sel = None
        self._selected = None
        self._create_tags()

        self.props.wrap_mode = gtk.WRAP_WORD
        self.props.justification = gtk.JUSTIFY_CENTER
        self.props.cursor_visible = False
        self.props.editable = False

        self.connect('key-press-event', self._key_press_cb)
        self.connect('event-after', self._event_after_cb)
        self.connect('motion-notify-event', self._motion_cb)
        self.connect('visibility-notify-event', self._visibility_cb)

    def on_set_tags(self, all_tags, objects_count):
        tags = []

        def has_tag(key):
            for i, props in tags:
                if key[0:len(i)] == i:
                    return True
            return False

        for tag, props in all_tags.items():
            if props[2] and not has_tag(tag):
                tags.append((tag, props))

        if self.sort == SORT_ALPHABET:
            tags = sorted(tags, cmp=lambda x,y: cmp(x[1][0], y[1][0]),
                    reverse=self.reverse)
        else:
            tags = sorted(tags, cmp=lambda x,y: cmp(x[1][1], y[1][1]),
                    reverse=self.reverse)

        buffer = self.get_buffer()
        buffer.delete(buffer.get_start_iter(), buffer.get_end_iter())
        iter = buffer.get_start_iter()

        for tag, props in tags:
            grade = min(GRADE_COUNT-1,
                    int(props[1] * float(GRADE_COUNT-1) / objects_count))

            sel_tag = buffer.create_tag()
            sel_tag.props.underline = pango.UNDERLINE_SINGLE
            sel_tag.props.underline_set = False
            sel_tag.props.foreground_gdk = style.COLOR_WHITE.get_gdk_color()
            sel_tag.props.foreground_set = False
            sel_tag.props.background_gdk = style.COLOR_BLACK.get_gdk_color()
            sel_tag.props.background_set = False

            buffer.insert(iter, ' ')
            buffer.insert_with_tags(iter, props[0], self._tags[grade], sel_tag)
            buffer.insert(iter, ' ')

        buffer.insert(iter, "\n")

    def _create_tags(self):
        buffer = self.get_buffer()
        size = FONT_SIZE_MIN

        for i in range(GRADE_COUNT):
            tag = buffer.create_tag(None, size=size * pango.SCALE)
            self._tags.append(tag)
            size += size * GRADE_MULT

    def _select(self, iter):
        if not self._sel or not self._sel in iter.get_tags():
            return

        if self._selected:
            self._selected.props.foreground_set = False
            self._selected.props.background_set = False
        self._sel.props.foreground_set = True
        self._sel.props.background_set = True
        self._selected = self._sel

        #self.emit('tag-selected', sel[0].props.name)

    def _set_sel(self, x, y):
        iter = self.get_iter_at_location(x, y)
        tags = iter.get_tags()
        buffer = self.get_buffer()

        if self._sel and (not tags or not self._sel in tags):
            self._sel.props.underline_set = False
            self._sel = None

        if tags:
            self._sel = [i for i in tags if i.props.size == 0][0]
            self._sel.props.underline_set = True

            self.get_window(gtk.TEXT_WINDOW_TEXT) \
                    .set_cursor(self.hand_cursor)
        else:
            self.get_window(gtk.TEXT_WINDOW_TEXT) \
                    .set_cursor(self.regular_cursor)

    def _key_press_cb(self, widget, event):
        if event.keyval in (gtk.keysyms.Return, gtk.keysyms.KP_Enter):
            buffer = self.get_buffer()
            iter = buffer.get_iter_at_mark(buffer.get_insert())
            self._select(iter)
        return False

    def _event_after_cb(self, widget, event):
        if event.type != gtk.gdk.BUTTON_RELEASE or event.button != 1:
            return False

        x, y = self.window_to_buffer_coords(gtk.TEXT_WINDOW_WIDGET,
                int(event.x), int(event.y))
        iter = self.get_iter_at_location(x, y)

        self._select(iter)
        return False

    def _motion_cb(self, widget, event):
        x, y = self.window_to_buffer_coords(gtk.TEXT_WINDOW_WIDGET,
                int(event.x), int(event.y))
        self._set_sel(x, y)
        self.window.get_pointer()
        return False

    def _visibility_cb(self, widget, event):
        wx, wy, mod = self.window.get_pointer()
        bx, by = self.window_to_buffer_coords(
                gtk.TEXT_WINDOW_WIDGET, wx, wy)
        self._set_sel(bx, by)
        return False
