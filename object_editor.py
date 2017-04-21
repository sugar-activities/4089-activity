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
from gettext import gettext as _

from sugar.graphics import style
from sugar.graphics.xocolor import XoColor
from sugar.graphics.palette import Palette
from sugar.graphics.toolbutton import ToolButton
import port.widgets
import port.pixbuf

import model
import activity
from theme import *
from source import *
from object_menu import ObjectMenu, activate

this = None

class ObjectEditor(hippo.Canvas):
    def __init__(self):
        hippo.Canvas.__init__(self)

        global this
        this = self

        self.metadata = None

        workspace = hippo.CanvasBox(
                background_color=style.COLOR_WHITE.get_int(),
                padding=style.DEFAULT_SPACING,
                spacing=style.DEFAULT_SPACING)
        self.set_root(workspace)

        # title

        upper_box = hippo.CanvasBox(
                orientation=hippo.ORIENTATION_HORIZONTAL,
                spacing=style.DEFAULT_SPACING)
        workspace.append(upper_box)

        self.icon = port.widgets.Image()
        self.icon.connect('button-release-event', self._activate_cb)
        upper_box.append(self.icon)

        self.title = port.widgets.Entry()
        upper_box.append(self.title, hippo.PACK_EXPAND)

        self.mtime = hippo.CanvasText()
        upper_box.append(self.mtime)

        bottom_box = hippo.CanvasBox(
                orientation=hippo.ORIENTATION_HORIZONTAL,
                spacing=style.DEFAULT_SPACING)
        workspace.append(bottom_box, hippo.PACK_EXPAND)

        # preview

        self.preview = port.widgets.Image()
        self.preview.connect('button-release-event', self._activate_cb)
        preview_box = hippo.CanvasBox()
        preview_box.append(self.preview)
        bottom_box.append(preview_box)

        # description

        right_box = hippo.CanvasBox(
                spacing=style.DEFAULT_SPACING)
        bottom_box.append(right_box, hippo.PACK_EXPAND)

        self.description = port.widgets.TextView(
                box_height=gtk.gdk.screen_height() / 4)
        right_box.append(port.widgets.labelize(_('Description:'),
                self.description))

        # tags

        tags_box = hippo.CanvasBox(
                orientation=hippo.ORIENTATION_HORIZONTAL,
                spacing=style.DEFAULT_SPACING)
        right_box.append(tags_box, hippo.PACK_EXPAND)

        self.traits = TraitsView()
        self.traits_box = port.widgets.labelize(_('Traits:'), self.traits)
        tags_box.append(self.traits_box, hippo.PACK_EXPAND)

        self.tags = TagsView()
        tags_box.append(port.widgets.labelize(_('Tags:'), self.tags),
                hippo.PACK_EXPAND)

        # buddies

        self.buddies = hippo.CanvasBox(
                xalign=hippo.ALIGNMENT_START,
                orientation=hippo.ORIENTATION_HORIZONTAL)
        right_box.append(port.widgets.labelize(_('Participants:'),
                self.buddies))

    def load(self, row):
        icon_pixbuf = row[FIELD_ICON]
        self.icon.pixbuf = icon_pixbuf
        self.icon.palette_class = (ObjectMenu, row, icon_pixbuf, False)
        self.title.text = row[FIELD_TITLE]
        self.mtime.props.text = row[FIELD_MODIFY_TIME]
        self.preview.pixbuf = model.PREVIEW_STUB

        self.buddies.clear()
        for i in (row[FIELD_BUDDIES] or []):
            buddy = port.pixbuf.sugar_icon(
                    icon_name = 'computer-xo',
                    width=model.ICON_SIZE, height=model.ICON_SIZE,
                    color=XoColor(i[2]))
            self.buddies.append(port.widgets.Image(
                    tooltip=i[1],
                    pixbuf=buddy))

        traits = fields_by_mime_type(row.get(FIELD_MIME_TYPE))
        if traits:
            self.traits.model.clear()
            self.traits_box.set_visible(True)
            for field in traits:
                iter = self.traits.model.append()
                self.traits.model.set(iter,
                        0, row.get(field), 1,
                        model.NAMES.get(field, field), 2, field)
        else:
            self.traits_box.set_visible(False)

        self.tags.model.clear()
        for name, foo in (row[FIELD_TAGS] or []):
            iter = self.tags.model.append()
            self.tags.model.set(iter, 0, '/'.join(name))

        def reply_cb(metadata):
            self.metadata = metadata
            self.preview.pixbuf = metadata[FIELD_PREVIEW]
            self.description.view.props.sensitive = True
            self.description.text = metadata.get('description')

        metadata = model.object_model.fetch_metadata(row, reply_cb)
        if metadata:
            reply_cb(metadata)
        else:
            self.description.view.props.sensitive = False

    def save(self):
        metadata = self.metadata.object.copy()
        needs_to_write = False

        if self.title.text != metadata.get('title'):
            metadata['title'] = self.title.text
            metadata['title_set_by_user'] = '1'
            needs_to_write = True

        if self.description.text != metadata.get('description'):
            metadata['description'] = self.description.text
            needs_to_write = True

        if fields_by_mime_type(metadata.get('mime_type')):
            traits = []
            for i in self.traits.model:
                field = self.traits.model.get_value(i.iter, 2)
                value = self.traits.model.get_value(i.iter, 0)
                if value != metadata.get(field):
                    if value:
                        metadata[field] = value
                    else:
                        del metadata[field]
                    needs_to_write = True

        tags = []
        for i in self.tags.model:
            tag = self.tags.model.get_value(i.iter, 0)
            if tag:
                tags.append((tag.split('/'), None))
        if tags != metadata.get('_tags_'):
            metadata['_tags_'] = tags
            needs_to_write = True

        if needs_to_write:
            model.source.post_object(metadata)

    def _activate_cb(self, sender, event):
        activate(self.metadata.object)

class TreeView(hippo.CanvasBox):
    def __init__(self, model, column_name):
        hippo.CanvasBox.__init__(self)

        self.toolbar = gtk.Toolbar()
        self.toolbar.modify_bg(gtk.STATE_NORMAL,
                style.COLOR_SELECTION_GREY.get_gdk_color())
        self.append(hippo.CanvasWidget(widget=self.toolbar))

        self.view = gtk.TreeView(model)
        self.view.show()
        self.view.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        self.view.props.enable_search = False

        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_shadow_type(gtk.SHADOW_OUT)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled_window.add(self.view)
        self.append(hippo.CanvasWidget(widget=scrolled_window),
                hippo.PACK_EXPAND)

        cell = gtk.CellRendererText()
        cell.props.editable = True
        #cell.props.cell_background_gdk = style.COLOR_WHITE.get_gdk_color()
        cell.connect('edited', self._cell_edited_cb)
        self.value_column = self.view.insert_column_with_attributes(0,
                column_name, cell, text=0)
        self.value_column.props.expand = True

    def _cell_edited_cb(self, cell, path_string, new_text):
        iter = self.model.get_iter_from_string(path_string)
        self.model.set(iter, 0, new_text)

class TraitsView(TreeView):
    def __init__(self):
        self.model = gtk.ListStore(str, str, str)
        TreeView.__init__(self, self.model, _('Value'))

        apply = port.widgets.ToolButton(
                icon_name='cancel',
                padding=0,
                tooltip=_('Add item'))
        apply.show()
        apply.connect('clicked', self._cancel_cb)
        self.toolbar.insert(apply, -1)

        cell = gtk.CellRendererText()
        cell.props.sensitive = False
        self.name = self.view.insert_column_with_attributes(0, _('Name'),
                cell, text=1)

        self.view.connect('key-press-event', self._key_press_event_cb)

    def _cancel_cb(self, widget):
        for path in self.view.get_selection().get_selected_rows()[1]:
            self.model.set(self.model.get_iter(path), 0, None)

    def _key_press_event_cb(self, widget, event):
        keyname = gtk.gdk.keyval_name(event.keyval)

        if keyname == 'Delete':
            self._cancel_cb(None)
        else:
            return False

        return True

class TagsView(TreeView):
    def __init__(self):
        self.model = gtk.ListStore(str)
        TreeView.__init__(self, self.model, _('Tag name'))

        cancel = port.widgets.ToolButton(
                icon_name='remove',
                padding=0,
                tooltip=_('Delete item'))
        cancel.show()
        cancel.connect('clicked', self._remove_cb)
        self.toolbar.insert(cancel, 0)

        apply = port.widgets.ToolButton(
                icon_name='add',
                padding=0,
                tooltip=_('Add item'))
        apply.show()
        apply.connect('clicked', self._add_cb)
        self.toolbar.insert(apply, 0)

        self.view.connect('key-press-event', self._key_press_event_cb)

    def _add_cb(self, widget):
        iter = self.model.append()

        if not self.model.get_value(iter, 0):
            self.model.remove(iter)
            iter = self.model.append()

        self.view.set_cursor(self.model.get_path(iter), self.value_column, True)

    def _set_cursor(self, path):
        path = (min(path[0], self.model.iter_n_children(None)-1),)
        if path[0] < 0:
            return
        self.view.set_cursor(path, None, False)

    def _remove_cb(self, widget):
        prev_path, column = self.view.get_cursor()
        if not prev_path:
            return
        for path in reversed(self.view.get_selection().get_selected_rows()[1]):
            self.model.remove(self.model.get_iter(path))
        self._set_cursor(prev_path)

    def _key_press_event_cb(self, widget, event):
        keyname = gtk.gdk.keyval_name(event.keyval)

        if keyname == 'Delete':
            self._remove_cb(None)
        elif keyname == 'Insert':
            self._add_cb(None)
        else:
            return False

        return True

class EditToolbar(gtk.Toolbar):
    def __init__(self):
        gtk.Toolbar.__init__(self)

        apply = ToolButton(
                icon_name='dialog-apply',
                tooltip=_('Apply'))
        apply.connect('clicked', self._apply_cb)
        self.insert(apply, -1)

        cancel = ToolButton(
                icon_name='dialog-cancel',
                tooltip=_('Cancel'))
        cancel.connect('clicked', self._cancel_cb)
        self.insert(cancel, -1)

        self.show_all()

    def _apply_cb(self, widget):
        this.save()
        activity.this.browse()

    def _cancel_cb(self, widget):
        activity.this.browse()
