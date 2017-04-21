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

class Source(gobject.GObject):
    __gsignals__ = {
            'objects-updated': (gobject.SIGNAL_RUN_FIRST, None, []) }

    def get_count(self):
        """ Returns number of objects """
        pass

    def get_row(self, frame_range, cb):
        """ Get object, returns {field_name: value, ...} """
        pass

    def get_order(self):
        """ Get current order, returns (field_name, gtk.SortType) """
        pass

    def set_order(self, field_name, sort_type):
        """ Set current order """
        pass

class Row:
    def __init__(self, model, path, iter, object):
        self.model = model
        self.iter = iter
        self.path = path
        self.object = object
        self.row = [None] * len(model._columns_by_name)
        self._calced_row = {}

        for name, value in object.items():
            column = model._columns_by_name.get(str(name), -1)
            if column != -1:
                self.row[column] = value

    def __getitem__(self, key):
        if isinstance(key, int):
            if key < len(self.row):
                return self.row[key]
            else:
                if self._calced_row.has_key(key):
                    return self._calced_row[key]
                else:
                    value = self.model.on_calc_value(self, key)
                    if value is not None:
                        self._calced_row[key] = value
                    return value
        else:
            return self.object[key]

    def __setitem__(self, key, value):
        if isinstance(key, int):
            if key < len(self.row):
                self.row[key] = value
            else:
                self._calced_row[key] = value
        else:
            self.object[key] = value

    def __delitem__(self, key):
        if isinstance(key, int):
            if key < len(self.row):
                del self.row[key]
            else:
                del self._calced_row[key]
        else:
            del self.object[key]

    def __contains__(self, key):
        if isinstance(key, int):
            return key < len(self.row)
        else:
            return self.object.__contains__(key)

    def has_key(self, key):
        return self.__contains__(key)

    def get(self, key, default=None):
        if self.has_key(key):
            return self.__getitem__(key)
        else:
            return default

class Model(gtk.GenericTreeModel):
    def __init__(self, source, columns, calc_columns={}):
        """ columns/calc_columns = {field_name: (column_num, column_type)} """
        gtk.GenericTreeModel.__init__(self)

        self._columns_by_name = {}
        self._columns_by_num = {}
        self._columns_types = {}
        self._calc_columns_by_num = {}

        for name, i in columns.items():
            self._columns_by_name[name] = i[0]
            self._columns_by_num[i[0]] = name
            self._columns_types[i[0]] = i[1]

        for name, i in calc_columns.items():
            self._calc_columns_by_num[i[0]] = name
            self._columns_types[i[0]] = i[1]

        self._n_columns = max(self._columns_types.keys()) + 1

        self.source = source
        self.source.connect('objects-updated', self.refresh)

        self._closing = False
        self._view = None
        self._view_cursors = {}
        self.set_view(None, force=True)

    def on_calc_value(self, row, column):
        # stub
        pass

    def get_view(self, view):
        return self._view

    def set_view(self, view, force=False):
        if self._view == view and not force:
            return

        if self._view:
            self._view_cursors[self._view] = self._view.get_cursor()
            try:
                self._closing = True
                self._view.set_model(None)
            finally:
                self._closing = False

        self._view = view
        self._cache = {}
        self._frame = (0, -1)
        self._in_process = {}
        self._postponed = []
        self._last_order = self.get_order()
        self._last_count = self.source.get_count()

        if view:
            self._update_columns()
            view.set_model(self)

            cursor = self._view_cursors.get(view)
            if cursor:
                view.set_cursor(*cursor)

    view = property(get_view, set_view)

    def get_order(self):
        order = self.source.get_order()
        return (self._columns_by_name[order[0]], order[1])

    def set_order(self, column, order):
        if (column, order) != self._last_order:
            self._last_order = (column, order)
            self.source.set_order(self._columns_by_num[column], order)

    def refresh(self, source=None):
        if self._last_count == 0:
            self.set_view(self._view, force=True)

        self._update_columns()

        count = self.source.get_count()

        for i in range(self._last_count, count):
            self.emit('row-inserted', (i,), self.get_iter((i,)))

        for i in reversed(range(count, self._last_count)):
            self.emit('row-deleted', (i,))

        if self._frame:
            if self._frame[0] >= count:
                self._frame = (0, -1)
            elif self._frame[1] >= count:
                for i in range(count, self._frame[1]):
                    if self._cache.has_key(i):
                        del self._cache[i]
                self._frame = (self._frame[0], count-1)
            self._cache = {}
            for i in range(self._frame[0], self._frame[1]+1):
                self.emit('row-changed', (i,), self.get_iter((i,)))

        self._last_order = self.get_order()
        self._last_count = count

    def get_row(self, pos, frame=None, cb=None):
        if not isinstance(pos, tuple):
            pos = self.get_path(pos)
        return self._get_row(pos[0], frame or (pos, pos), cb)

    def _get_row(self, offset, frame, get_row_cb=None):
        def postfetch(offset, object):
            if not self._in_process.has_key(offset):
                return

            path = (offset,)
            iter = self.get_iter(path)
            row = Row(self, path, iter, object)

            if self.in_frame(offset):
                self._cache[offset] = row

            cb = self._in_process[offset]
            del self._in_process[offset]

            if cb:
                cb(self, row)
            self.emit('row-changed', path, iter)

            if self._in_process:
                return

            while self._postponed:
                offset, force, cb = self._postponed.pop()
                if not force and not self.in_frame(offset):
                    continue
                row = self.get_row((offset,), cb=cb)
                if row:
                    if cb:
                        cb(self, row)
                    self.emit('row-changed', row.path, row.iter)
                else:
                    break

        def fetch():
            row = self.source.get_row(offset, postfetch)

            if not row:
                if row is None:
                    logging.debug('_get_row: wait for reply for %s' % offset)
                else:
                    logging.debug('_get_row: can not find row for %s' % offset)
                self._in_process[offset] = get_row_cb
                return None

            row = Row(self, (offset,), self.get_iter(offset), row)
            self._cache[offset] = row
            return row

        out = self._cache.get(offset)
        if out:
            return out

        if frame[0] >= frame[1]:
            # just return requested single row and do not change cache
            # if requested frame has <= 1 rows
            if self._in_process.has_key(offset):
                self._postponed.append((offset, True, get_row_cb))
                return None
            else:
                return fetch()

        if frame != self._frame:
            # switch to new frame
            intersect_min = max(frame[0], self._frame[0])
            intersect_max = min(frame[1], self._frame[1])
            if intersect_min > intersect_max:
                self._cache = {}
            else:
                for i in range(self._frame[0], intersect_min):
                    if self._cache.has_key(i):
                        del self._cache[i]
                for i in range(intersect_max+1, self._frame[1]+1):
                    if self._cache.has_key(i):
                        del self._cache[i]
            self._frame = frame

        for in_process_offset, in_process_cb in self._in_process.items():
            if in_process_offset == offset or self.in_frame(in_process_offset):
                self._postponed.append((offset, False, get_row_cb))
                return None

        return fetch()

    def _update_columns(self):
        if not hasattr(self._view, 'get_columns'):
            return

        for i, column in enumerate(self._view.get_columns()):
            if not hasattr(column, 'order_by'):
                continue
            if self._columns_by_num.has_key(i) or \
                    self._calc_columns_by_num.has_key(i):
                column.props.visible = True
                if column.order_by == self._last_order[0]:
                    column.props.sort_indicator = True
                    column.props.sort_order = self._last_order[1]
                else:
                    column.props.sort_indicator = False
            else:
                column.props.visible = False

    def in_frame(self, offset):
        return offset >= self._frame[0] and offset <= self._frame[1]

    # interface implementation -------------------------------------------------

    def on_get_n_columns(self):
        return self._n_columns

    def on_get_column_type(self, index):
        return self._columns_types.get(index, bool)

    def on_iter_n_children(self, iter):
        if iter == None and not self._closing:
            return self.source.get_count()
        else:
            return 0

    def on_get_value(self, offset, column):
        if not self._view or offset >= self.source.get_count():
            return None

        # return value only if iter came from visible range
        # (on setting model, gtk.TreeView scans all items)
        range = self._view.get_visible_range()
        if range and offset >= range[0][0] and offset <= range[1][0]:
            row = self._get_row(offset, (range[0][0], range[1][0]))
            return row and row[column]

        return None

    def on_iter_nth_child(self, iter, n):
        return n

    def on_get_path(self, iter):
        return (iter)

    def on_get_iter(self, path):
        if self.source.get_count() and not self._closing:
            return path[0]
        else:
            return False

    def on_iter_next(self, iter):
        if iter != None:
            if iter >= self.source.get_count() - 1 or self._closing:
                return None
            return iter + 1
        return None

    def on_get_flags(self):
        return gtk.TREE_MODEL_ITERS_PERSIST | gtk.TREE_MODEL_LIST_ONLY

    def on_iter_children(self, iter):
        return None

    def on_iter_has_child(self, iter):
        return False

    def on_iter_parent(self, iter):
        return None
