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

from sugar.graphics import style

from tag_model import *

SORT_ALPHABET = 0
SORT_COUNT    = 1

GRADE_COUNT = 6
GRADE_MULT  = .2

FONT_SIZE_MIN = 9

class Cloud(TagModel, gtk.TextView):
    hand_cursor = gtk.gdk.Cursor(gtk.gdk.HAND2)
    regular_cursor = gtk.gdk.Cursor(gtk.gdk.XTERM)

    def __init__(self, tag_type):
        TagModel.__init__(self, tag_type)
        gtk.TextView.__init__(self)

        self.sort = SORT_ALPHABET
        self.reverse = False

        self._tags = {}
        self._grades = []
        self._underlined = None
        self._selected = None
        self._create_grades()

        self.props.wrap_mode = gtk.WRAP_WORD
        self.props.justification = gtk.JUSTIFY_CENTER
        self.props.cursor_visible = False
        self.props.editable = False

        self.connect('event-after', self._event_after_cb)
        self.connect('motion-notify-event', self._motion_cb)
        self.connect('visibility-notify-event', self._visibility_cb)

    def on_set_tags(self, all_tags, objects_count):
        buffer = self.get_buffer()
        buffer.delete(buffer.get_start_iter(), buffer.get_end_iter())

        if not objects_count:
            return

        tags = []

        def has_tag(key):
            for i, props in tags:
                if key[0:len(i)] == i:
                    return True
            return False

        for tag, props in sorted(all_tags.items(), \
                cmp=lambda x, y: cmp(x[0], y[0])):
            if props[2] and not has_tag(tag):
                tags.append((tag, props))

        if self.sort == SORT_ALPHABET:
            tags = sorted(tags, cmp=lambda x,y: cmp(x[1][0], y[1][0]),
                    reverse=self.reverse)
        else:
            tags = sorted(tags, cmp=lambda x,y: cmp(x[1][1], y[1][1]),
                    reverse=self.reverse)

        iter = buffer.get_start_iter()
        buffer.insert(iter, "\n")

        for tag, props in tags:
            grade = min(GRADE_COUNT-1,
                    int(props[1] * float(GRADE_COUNT-1) / objects_count))

            underlined = buffer.create_tag()
            underlined.props.underline = pango.UNDERLINE_SINGLE
            underlined.props.underline_set = False
            underlined.props.foreground_gdk = style.COLOR_WHITE.get_gdk_color()
            underlined.props.foreground_set = False
            underlined.props.background_gdk = style.COLOR_BLACK.get_gdk_color()
            underlined.props.background_set = False

            buffer.insert(iter, ' ')
            buffer.insert_with_tags(iter, props[0], self._grades[grade],
                    underlined)
            buffer.insert(iter, ' ')

            self._tags[underlined] = (tag, props[0])

        buffer.insert(iter, "\n")

    def _create_grades(self):
        buffer = self.get_buffer()
        size = FONT_SIZE_MIN

        for i in range(GRADE_COUNT):
            tag = buffer.create_tag(None, size=size * pango.SCALE)
            self._grades.append(tag)
            size += size * GRADE_MULT

    def _set_underlined(self, x, y):
        iter = self.get_iter_at_location(x, y)
        tags = iter.get_tags()
        buffer = self.get_buffer()

        if self._underlined and (not tags or not self._underlined in tags):
            self._underlined.props.underline_set = False
            self._underlined = None

        if tags:
            self._underlined = [i for i in tags if i.props.size == 0][0]
            self._underlined.props.underline_set = True

            self.get_window(gtk.TEXT_WINDOW_TEXT) \
                    .set_cursor(self.hand_cursor)
        else:
            self.get_window(gtk.TEXT_WINDOW_TEXT) \
                    .set_cursor(self.regular_cursor)

    def _event_after_cb(self, widget, event):
        if not self._underlined or event.type != gtk.gdk.BUTTON_RELEASE:
            return False

        def select(do_select):
            if self._selected:
                self._selected.props.foreground_set = False
                self._selected.props.background_set = False
            self._underlined.props.foreground_set = True
            self._underlined.props.background_set = True
            self._selected = self._underlined

            tag, name = self._tags[self._underlined]
            self.select(tag, name, do_select)

        if event.button == 1 and event.state & gtk.gdk.SHIFT_MASK \
                or event.button == 2:
            select(True)
        elif event.button == 1:
            select(False)

        return False

    def _motion_cb(self, widget, event):
        x, y = self.window_to_buffer_coords(gtk.TEXT_WINDOW_WIDGET,
                int(event.x), int(event.y))
        self._set_underlined(x, y)
        self.window.get_pointer()
        return False

    def _visibility_cb(self, widget, event):
        wx, wy, mod = self.window.get_pointer()
        bx, by = self.window_to_buffer_coords(
                gtk.TEXT_WINDOW_WIDGET, wx, wy)
        self._set_underlined(bx, by)
        return False
