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
from gettext import gettext as _

from sugar.graphics.palette import Palette
from sugar.activity.activity import ActivityToolbox
from sugar.graphics.radiotoolbutton import RadioToolButton
from sugar.graphics import style
from port.activity import SharedActivity
from port.searchentry import SearchEntry
from port.widgets import ToggleToolButton

import model
from source import *
from path import Path
from tag_sidebar import TagSidebar
from object_compact import ObjectCompact, ObjectPalette
from object_thumbs import ObjectThumbs
from object_editor import ObjectEditor, EditToolbar
from messenger import Messenger, SERVICE

this = None

class Library(SharedActivity):
    def __init__(self, handle):
        global this
        this = self

        self.config = model.this['activity']

        canvas = gtk.Notebook()
        canvas.props.show_border = False
        canvas.props.show_tabs = False
        canvas.show()

        SharedActivity.__init__(self, canvas, SERVICE, handle)

    def new_instance(self):
        browser = gtk.VBox()
        browser.show()
        self.canvas.append_page(browser)

        self.path = Path()
        path_box = gtk.EventBox()
        path_box.modify_bg(gtk.STATE_NORMAL,
                style.COLOR_TOOLBAR_GREY.get_gdk_color())
        path_box.add(self.path)
        path_box.show_all()
        browser.pack_end(path_box, False)

        self.workspace = gtk.HPaned()
        self.workspace.show()
        self.workspace.connect('notify::position', self._workspace_position_cb)
        browser.pack_start(self.workspace)

        self.tags = TagSidebar()
        self.tags.show()
        self.workspace.add1(self.tags)

        self.objects = gtk.Notebook()
        self.objects.show()
        self.objects.props.show_border = False
        self.objects.props.show_tabs = False
        self.workspace.add2(self.objects)

        scrollbox = gtk.ScrolledWindow()
        scrollbox.show()
        scrollbox.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.objects_compat = ObjectCompact()
        scrollbox.add(self.objects_compat)
        self.objects.append_page(scrollbox)
        model.object_model.view = self.objects_compat

        self.object_thumbs = ObjectThumbs()
        self.object_thumbs.show()
        self.objects.append_page(self.object_thumbs)

        self.editor = ObjectEditor()
        self.editor.show()
        self.canvas.append_page(self.editor)

        toolbox = ActivityToolbox(self)
        toolbox.show()
        self.set_toolbox(toolbox)

        self.toolbars = [ [ (_('Library'), BrowseToolbar()) ],
                          [ (_('Edit'), EditToolbar()) ] ]

        self.browse()
        model.source.query()

    def resume_instance(self, filepath):
        model.this.deserialize(file(filepath).read())
        self.new_instance()

    def save_instance(self, filepath):
        f = file(filepath, 'w')
        f.write(model.this.serialize())
        f.close()

    def share_instance(self, connection, initiating):
        pass
        #self.messenger = Messenger(connection, initiating)

    def browse(self):
        self._switch_toolbar(0, 0)

    def edit(self, row):
        self.editor.load(row)
        self._switch_toolbar(1, 1)

    def _switch_toolbar(self, tool_page, view_page):
        if self.toolbars[tool_page][0][1].parent:
            self.toolbox.set_current_toolbar(1)
            return

        self.canvas.set_current_page(view_page)

        for page in self.toolbars:
            if page[0][1].parent:
                for title, i in page:
                    i.parent.remove(i)
                    self.toolbox.remove_toolbar(1)
                break

        for title, i in self.toolbars[tool_page]:
            self.toolbox.add_toolbar(title, i)

        self.toolbox.set_current_toolbar(1)

    def _workspace_position_cb(self, separator, event):
        this.config['sidebar_separator'] = separator.props.position

class BrowseToolbar(gtk.Toolbar):
    def __init__(self):
        gtk.Toolbar.__init__(self)

        sidebar = ToggleToolButton(
                named_icon='sidebar',
                palette=TagPalette())
        sidebar.connect('toggled', self._tags_cb)
        sidebar.props.active = this.config['sidebar_visible']
        self.insert(sidebar, -1)

        separator = gtk.SeparatorToolItem()
        self.insert(separator, -1)

        objects = [None] * 3

        objects[0] = RadioToolButton(
                named_icon='view-list',
                group=None,
                palette=ObjectPalette(_('Compact object list'),
                    this.objects_compat))
        objects[0].connect('toggled', self._objects_cb, 0, this.objects_compat)
        self.insert(objects[0], -1)

        objects[1] = RadioToolButton(
                named_icon='view-thumbs',
                tooltip=_('Thumbs object list'),
                group=objects[0])
        objects[1].connect('toggled', self._objects_cb, 1, this.object_thumbs)
        self.insert(objects[1], -1)

        objects[this.config['objects_view']].props.active = True

        separator = gtk.SeparatorToolItem()
        separator.set_draw(False)
        self.insert(separator, -1)

        search = SearchEntry()
        search.connect('query-changed', self._search_changed_cb)
        search_toolitem = gtk.ToolItem()
        search_toolitem.add(search)
        search_toolitem.set_expand(True)
        self.insert(search_toolitem, -1)

        self.show_all()

    def _tags_cb(self, widget):
        if widget.props.active:
            this.tags.show()
        else:
            this.tags.hide()
        this.config['sidebar_visible'] = widget.props.active

    def _objects_cb(self, widget, index, view):
        if widget.props.active:
            model.object_model.view = view
            this.objects.set_current_page(index)
            this.config['objects_view'] = index

    def _search_changed_cb(self, widget, query):
        model.source.search = widget.props.text
        model.source.query()

class TagPalette(Palette):
    def __init__(self):
        Palette.__init__(self, _('Tag sidebar'))

        box = gtk.VBox()
        self.set_content(box)

        pos = 2*[None]

        pos[0] = gtk.RadioButton(None, _('On the left side'))
        pos[0].connect('clicked', self._cb, 0)
        box.pack_start(pos[0])

        pos[1] = gtk.RadioButton(pos[0], _('On the right side'))
        pos[1].connect('clicked', self._cb, 1)
        box.pack_start(pos[1])

        saved_pos = this.config['sidebar_separator']
        pos[this.config['sidebar_position']].props.active = True
        this.workspace.props.position = saved_pos

        box.show_all()

    def _cb(self, widget, pos):
        def swap():
            child1 = this.workspace.get_child1()
            child2 = this.workspace.get_child2()

            new_pos = gtk.gdk.screen_width() - this.workspace.props.position
            this.workspace.props.position = new_pos

            this.workspace.remove(child1)
            this.workspace.remove(child2)
            this.workspace.add1(child2)
            this.workspace.add2(child1)

        if pos == 0:
            if this.workspace.get_child1() != this.tags:
                swap()
        else:
            if this.workspace.get_child1() != this.objects:
                swap()

        this.config['sidebar_position'] = pos
