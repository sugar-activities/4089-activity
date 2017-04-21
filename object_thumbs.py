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
import logging

from sugar.graphics import style
from port.lazyview import TableView, TableCell
from sugar.graphics.palette import Palette
import port.widgets

import model
from source import *
from object_menu import ObjectMenu, activate

class Cell(TableCell, hippo.CanvasBox):
    def __init__(self):
        TableCell.__init__(self)
        hippo.CanvasBox.__init__(self,
                orientation=hippo.ORIENTATION_VERTICAL)

        self.thumb = port.widgets.Image(
                padding=style.DEFAULT_PADDING)
        self.append(self.thumb, hippo.PACK_EXPAND)

        label_box = hippo.CanvasBox(
                orientation=hippo.ORIENTATION_HORIZONTAL,
                xalign=hippo.ALIGNMENT_CENTER)
        self.append(label_box)

        self.icon = port.widgets.Image()
        label_box.append(self.icon)

        self.label = hippo.CanvasText(
                size_mode=hippo.CANVAS_SIZE_ELLIPSIZE_END)
        label_box.append(self.label)

    def on_button_release(self, widget, event):
        if not self.row:
            return

        if event.button == 1:
            activate(self.row.object)

        elif event.button == 3:
            palette = self.row[FIELD_BUDDY_MENU]
            palette.popup(immediate=True, state=Palette.SECONDARY)

    def fillin(self):
        icon_pixbuf = self.row[FIELD_ICON]
        self.icon.pixbuf = icon_pixbuf
        self.icon.palette_class = (ObjectMenu, self.row, icon_pixbuf)
        self.thumb.pixbuf = self.row[FIELD_THUMB]
        self.label.props.text = self.row[FIELD_TITLE] or ''

class ObjectThumbs(TableView):
    def __init__(self):
        TableView.__init__(self, Cell,
                cell_sizes=(model.CELL_WIDTH, model.CELL_HEIGHT))

        self.props.hover_selection = True
