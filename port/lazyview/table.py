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
import hippo
import math
import gobject
import logging

from sugar.graphics import style
from sugar.graphics.roundbox import CanvasRoundBox

from model import Model

class TableView(gtk.HBox):
    def __init__(self, cell_class, cell_sizes=None, cell_numbers=None):
        gtk.HBox.__init__(self)

        self._cell_class = cell_class
        self._cell_sizes = cell_sizes
        self._cell_numbers = cell_numbers
        self._rows = 0
        self._columns = 0
        self._cells = []
        self._model = None
        self._table = None
        self._hover_selection = False

        self.connect('scroll-event', self._scroll_event_cb)
        self.connect('key-press-event', self._key_press_event_cb)

        self.table_box = gtk.EventBox()
        self.table_box.show()
        self.pack_start(self.table_box)

        self._adj = gtk.Adjustment(value=0, lower=0, upper=0, step_incr=1,
                page_incr=0, page_size=0)
        self._adj.connect('value-changed', self._fillin)

        self._scrollbar = gtk.VScrollbar(self._adj)
        self._scrollbar.show()
        self.pack_end(self._scrollbar, expand=False, fill=False)

    def get_size(self):
        return (self._columns, self._rows)

    def get_cursor(self):
        return (self._adj.props.value,)

    def set_cursor(self, cursor):
        self._adj.props.value = cursor

    def get_model(self):
        return self._model

    def set_model(self, model):
        if self._model == model:
            return

        if self._model:
            self._model.disconnect_by_func(self._changed_cb)
            self._model.disconnect_by_func(self._resized_cb)

        self._model = model

        if model:
            self._model.connect('row-changed', self._changed_cb)
            self._model.connect('row-inserted', self._resized_cb)
            self._model.connect('row-deleted', self._resized_cb)

        self._resized_cb()

    def get_hover_selection(self):
        return self._hover_selection

    def set_hover_selection(self, value):
        self._hover_selection = value

    model = gobject.property(type=object,
            getter=get_model, setter=set_model)
    hover_selection = gobject.property(type=object,
            getter=get_hover_selection, setter=set_hover_selection)

    def get_frame(self):
        return (int(self._adj.props.value) * self._columns,
                (int(self._adj.props.value)+self._rows) * self._columns - 1)

    def get_visible_range(self):
        frame = self.get_frame()
        return ((frame[0],), (frame[1],))

    def _fillin(self, adj):
        if self._model:
            count = self._model.iter_n_children(None)
        else:
            count = 0
        i = int(self._adj.props.value) * self._columns

        for y in range(self._rows):
            for x in range(self._columns):
                canvas, cell = self._cells[y][x]
                cell.row = None
                cell.set_visible(False)

                if i < count:
                    cell.row = self._model.get_row((i,), self.get_frame())
                    if cell.row:
                        cell.fillin()
                        cell.set_visible(True)

                i += 1

    def do_size_allocate(self, alloc):
        gtk.HBox.do_size_allocate(self, alloc)

        if self._cell_numbers:
            rows, columns = self._cell_numbers
        elif self._cell_sizes:
            columns = max(1, alloc.width / max(1, self._cell_sizes[0]))
            rows = max(1, alloc.height / max(1, self._cell_sizes[1]))

        if not self._table or columns != self._columns or rows != self._rows:
            logging.debug('resize TableView to %s:%s' % (rows, columns))

            if self._table:
                self.table_box.remove(self._table)

            self._table = gtk.Table()
            self._table.resize(rows, columns)

            self._cells = []
            self._columns = columns
            self._rows = rows

            for y in range(rows):
                self._cells.append(columns * [None])
                for x in range(columns):
                    canvas = hippo.Canvas()
                    canvas.show()
                    canvas.modify_bg(gtk.STATE_NORMAL,
                            style.COLOR_TEXT_FIELD_GREY.get_gdk_color())
                    canvas.set_size_request(alloc.width/columns,
                            alloc.height/rows)

                    sel_box = CanvasRoundBox()
                    sel_box.props.border_color = \
                            style.COLOR_TEXT_FIELD_GREY.get_int()
                    canvas.set_root(sel_box)

                    if self._hover_selection:
                        canvas.connect('enter-notify-event',
                                self._cell_enter_cb, sel_box, y, x)
                        canvas.connect('leave-notify-event',
                                self._cell_leave_cb, sel_box, y, x)

                    cell = self._cell_class()
                    sel_box.append(cell, hippo.PACK_EXPAND)

                    canvas.connect('button-release-event',
                            self._cell_release_cb, cell)

                    self._table.attach(canvas, x, x+1, y, y+1,
                            gtk.EXPAND|gtk.FILL, gtk.EXPAND|gtk.FILL, 0, 0)
                    self._cells[y][x] = (canvas, cell)

            self._setup_adj()
            self._fillin(None)

            self._table.show_all()
            self.table_box.add(self._table)

        else:
            for y in range(rows):
                for x in range(columns):
                    self._cells[y][x][0].set_size_request(
                            alloc.width/columns, alloc.height/rows)

    def _cell_release_cb(self, widget, event, cell):
        cell.on_button_release(widget, event)

    def _cell_enter_cb(self, widget, event, sel_box, y, x):
        i = int(self._adj.props.value + y) * self._columns + x
        if i < self._model.iter_n_children(None):
            sel_box.props.background_color = style.COLOR_WHITE.get_int()

    def _cell_leave_cb(self, widget, event, sel_box, y, x):
        sel_box.props.background_color = style.COLOR_TEXT_FIELD_GREY.get_int()

    def _key_press_event_cb(self, widget, event):
        keyname = gtk.gdk.keyval_name(event.keyval)

        uplimit = self._adj.props.upper - self._rows

        if keyname == 'Up':
            self._adj.props.value -= 1
        elif keyname == 'Down':
            if self._adj.props.value + 1 <= uplimit:
                self._adj.props.value += 1
        elif keyname == 'Page_Up' or keyname == 'KP_Page_Up':
            self._adj.props.value -= self._rows
        elif keyname == 'Page_Down' or keyname == 'KP_Page_Down':
            if self._adj.props.value + self._rows <= uplimit:
                self._adj.props.value += self._rows
        elif keyname == 'Home' or keyname == 'KP_Home':
            self._adj.props.value = 0
        elif keyname == 'End' or keyname == 'KP_End':
            self._adj.props.value = uplimit
        else:
            return False

        return True

    def _scroll_event_cb(self, sender, event):
        uplimit = self._adj.props.upper - self._rows

        if event.direction == gtk.gdk.SCROLL_UP:
            self._adj.props.value -= 1
        elif event.direction == gtk.gdk.SCROLL_DOWN:
            if self._adj.props.value + 1 <= uplimit:
                self._adj.props.value += 1

    def _setup_adj(self):
        if not self._model:
            return

        if self._columns == 0:
            self._adj.props.upper = 0
        else:
            count = self._model.iter_n_children(None)
            self._adj.props.upper = int(math.ceil(float(count) / self._columns))

        self._adj.props.value = \
                min(self._adj.props.value, self._adj.props.upper - self._rows)

        self._adj.props.page_size = self._rows
        self._adj.props.page_increment = self._rows
        self._adj.changed()

        if self._adj.props.upper > self._rows:
            self._scrollbar.show()
        else:
            self._scrollbar.hide()

    def _changed_cb(self, model, path, iter):
        range = self.get_frame()
        if path[0] < range[0] or path[0] > range[1]:
            return

        y = (path[0] - range[0]) / self._columns
        x = (path[0] - range[0]) % self._columns

        cell = self._cells[y][x][1]

        cell.row = self._model.get_row(path)
        if cell.row:
            cell.fillin()
            cell.set_visible(True)
        else:
            cell.set_visible(False)

    def _resized_cb(self, model=None, path=None, iter=None):
        if self.model:
            self._setup_adj()
        else:
            self._adj.props.upper = 0
            self._adj.props.value = 0
            self._scrollbar.hide()
        self._fillin(None)

class TableCell:
    def __init__(self):
        self.row = None

    def fillin(self):
        pass

    def on_button_release(self, widget, event):
        pass
