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
import pango
import logging
from gettext import gettext as _

from sugar.graphics import style
from sugar.graphics.palette import Palette, Invoker
from port.lazyview import TreeView, TreeViewColumn
from port.widgets import ToolButton

import model
import activity
from object_menu import activate
from theme import *
from source import *

this = None

class ObjectCompact(TreeView):
    def __init__(self):
        TreeView.__init__(self)

        global this
        this = self

        self._cached_buddies = None
        self.columns = {}
        self.config = model.this['object_compact']

        self.props.hover_selection = True

        activity.this.on_save_instance(self._save_columns)
        self.connect('map', lambda x: self._load_columns())
        self.connect('button-press-event', self._press_cb)
        self.connect('button-release-event', self._release_cb)

        self._buddies_palette = []
        for i in range(VISIBLE_BUDDIES_COUNT):
            self._buddies_palette.append(Palette())

        def make_cell_pix():
            cell = gtk.CellRendererPixbuf()
            cell.props.height = model.ICON_SIZE
            cell.props.width = model.ICON_SIZE
            cell.props.xalign = 0.
            return cell
        cell_pix = [make_cell_pix() for i in range(VISIBLE_BUDDIES_COUNT)]

        cell_text = gtk.CellRendererText()
        cell_text.props.ellipsize = pango.ELLIPSIZE_END
        cell_text.props.ellipsize_set = True

        column = TreeViewColumn(_('Title'))
        column.palette_cb = self._icon_palette_cb
        column.props.sizing = gtk.TREE_VIEW_COLUMN_FIXED
        column.props.min_width = 50
        column.props.resizable = True
        column.props.reorderable = True
        column.set_sort_column_id(FIELD_TITLE)
        column.pack_start(cell_pix[0], False)
        column.add_attribute(cell_pix[0], 'pixbuf', FIELD_ICON)
        column.pack_start(cell_text, True)
        column.add_attribute(cell_text, 'text', FIELD_TITLE)
        self.columns['title'] = column

        column = TreeViewColumn(_('Participants'))
        column.palette_cb = self._buddies_palette_cb
        column.props.sizing = gtk.TREE_VIEW_COLUMN_FIXED
        column.props.reorderable = True
        for i in range(VISIBLE_BUDDIES_COUNT):
            column.pack_start(cell_pix[i], False)
            column.add_attribute(cell_pix[i], 'pixbuf',
                    FIELD_BUDDY_FIRST+i)
        column.set_sort_column_id(FIELD_BUDDIES_COUNT)
        self.columns['buddies'] = column

        column = TreeViewColumn(_('Modify time'), cell_text,
                text=FIELD_MODIFY_TIME)
        column.props.sizing = gtk.TREE_VIEW_COLUMN_FIXED
        column.props.min_width = 50
        column.props.resizable = True
        column.props.reorderable = True
        column.set_sort_column_id(FIELD_TIMESTAMP)
        self.columns['mtime'] = column

        def column_new(field):
            column_number = FIELD_BASE_LIST[field][0]
            column = TreeViewColumn(NAMES[field], cell_text, text=column_number)
            column.props.sizing = gtk.TREE_VIEW_COLUMN_FIXED
            column.props.min_width = 50
            column.props.resizable = True
            column.props.reorderable = True
            column.set_sort_column_id(column_number)
            self.columns[field] = column

        for i in ('version', 'author', 'genre', 'artist', 'album', 'composer',
                  'date', 'track_number', 'track_count', 'disc_number',
                  'disc_count', 'copyright'):
            column_new(i)

        self.show_all()

    def _load_columns(self):
        for i in self.get_columns():
            self.remove_column(i)

        for i in self.config[self.config['list_type']]:
            column = self.columns[i['column']]
            column.props.fixed_width = i['width']
            column.props.expand = i['expand']
            column.props.visible = i['visible']
            self.append_column(column)

    def _save_columns(self):
        save = []

        for column in self.get_columns():
            column_name = [name for name, value in self.columns.items() \
                    if value == column][0]
            save.append( { 'column' : column_name,
                           'width'  : column.props.width,
                           'visible': column.props.visible,
                           'expand' : column.props.expand } )

        self.config[self.config['list_type']] = save

    def _icon_palette_cb(self, tmodel, row, x, y):
        if x >= model.ICON_SIZE:
            return None
        else:
            return row[FIELD_BUDDY_MENU]

    def _buddies_palette_cb(self, tmodel, row, x, y):
        buddies = row[FIELD_BUDDIES] or []
        index = x / model.ICON_SIZE

        if not buddies or index >= len(buddies):
            return None

        palette = self._buddies_palette[index]
        palette.props.primary_text = buddies[index][1]

        return palette

    def _press_cb(self, sender, event):
        coords = event.get_coords()
        if self.convert_tree_to_widget_coords(0, int(coords[1]))[1] < \
                self.convert_tree_to_widget_coords(0, 0)[1]:
            self._button_pressed = None
        else:
            self._button_pressed = event.button

    def _release_cb(self, sender, event):
        if self._button_pressed != event.button:
            self._button_pressed = None
            return
        self._button_pressed = None

        coords = event.get_coords()
        pos = self.get_path_at_pos(int(coords[0]), int(coords[1]))
        if not pos:
            return

        if event.button == 1:
            def cb(model, row):
                activate(row.object)
            row = self.props.model.get_row(pos[0], cb)
            if row:
                cb(None, row)

        elif event.button == 3:
            def cb(model, row):
                palette = row[FIELD_BUDDY_MENU]
                palette.popup(immediate=True, state=Palette.SECONDARY)
            row = self.props.model.get_row(pos[0], cb)
            if row:
                cb(None, row)

class ObjectPalette(Palette):
    def __init__(self, label, tree):
        Palette.__init__(self, label)
        self.tree = tree

        background = gtk.VBox()
        self.set_content(background)

        default_view = gtk.RadioButton()
        default_view.props.label = _('Default list view')
        default_view.connect('clicked', self._listview_cb, 'default')
        background.pack_start(default_view)

        for type, props in sorted(TRAITS.items(),
                cmp=lambda x, y: cmp(x[1]['title'], y[1]['title'])):
            i = gtk.RadioButton()
            i.props.label = props['title']
            i.props.group = default_view
            background.pack_start(i)
            if type == this.config['list_type']:
                i.props.active = True
            i.connect('clicked', self._listview_cb, type)

        separator = gtk.Label(' ')
        background.pack_start(separator)

        self.expander = gtk.Expander(_('Columns'))

        # XXX suppress gtk artifacts during the second showing
        # if expander was expanded/unexpanded before
        expander_box = gtk.EventBox()
        expander_box.add(self.expander)
        background.pack_start(expander_box)

        self.model = gtk.ListStore(bool, str)
        self.view = gtk.TreeView(self.model)
        self.view.props.headers_visible = False
        self.expander.add(self.view)

        cell = gtk.CellRendererToggle()
        cell.props.activatable = True
        cell.props.cell_background_gdk = style.COLOR_BLACK.get_gdk_color()
        cell.connect('toggled', self._toggled_cb)
        self.view.insert_column_with_attributes(0, '', cell, active=0)

        cell = gtk.CellRendererText()
        cell.props.cell_background_gdk = style.COLOR_BLACK.get_gdk_color()
        cell.props.foreground_gdk = style.COLOR_WHITE.get_gdk_color()
        self.view.insert_column_with_attributes(1, '', cell, text=1)

        background.show_all()

        self.connect('popup', self._popup_cb)
        self.connect('popdown', self._popdown_cb)

    def _popdown_cb(self, window):
        self.expander.props.expanded = False

    def _popup_cb(self, window):
        self.model.clear()
        for i in self.tree.get_columns():
            self.model.append((i.props.visible, i.props.title))
        self.view.grab_focus()

    def _toggled_cb(self, cell, index):
        index = int(index)
        value = not self.model[index][0]
        self.model[index][0] = value
        self.tree.get_columns()[index].props.visible = value

    def _listview_cb(self, widget, type):
        if not widget.props.active:
            return
        this._save_columns()
        this.config['list_type'] = type
        this._load_columns()
        self._popup_cb(None)
