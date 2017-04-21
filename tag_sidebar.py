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
from sugar.graphics.radiotoolbutton import RadioToolButton
from sugar.graphics import style
from sugar.graphics.notebook import Notebook

import model
from source import *
from tag_tree import Tree
from tag_cloud import Cloud, SORT_ALPHABET, SORT_COUNT

class TagSidebar(Notebook):
    def __init__(self):
        Notebook.__init__(self)

        self._view_by_page = [None, None, None]

        self.add_page(_('Traits'), self._page_new(TAGS_OBJECTIVE))
        self.add_page(_('Tags'), self._page_new(TAGS_SUBJECTIVE))
        #self.add_page(_('Sources'), self._page_new(TAGS_SOURCE))

        self.connect('notify::page', self._notify_page_cb)
        self.show_all()

        self._last_page = 0
        self.props.page = model.this['tag_sidebar']['page']

    def _page_new(self, tag_type):
        def page_cb(widget,  view_index, view):
            lists.props.page = view_index
            self._view_by_page[tag_type].freeze()
            self._view_by_page[tag_type] = view
            view.update()
            model.this['tag_sidebar'][`tag_type`]['cloud_active'] = \
                    view_index == 1

        vbox = gtk.VBox()

        lists = gtk.Notebook()
        lists.props.show_border = False
        lists.props.show_tabs = False
        vbox.pack_start(lists)

        tree = Tree(tag_type)
        tree.props.hover_selection = True
        scrolled = gtk.ScrolledWindow()
        scrolled.set_shadow_type(gtk.SHADOW_OUT)
        scrolled.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled.add(tree)
        lists.append_page(scrolled)
        self._view_by_page[tag_type] = tree

        cloud = Cloud(tag_type)
        scrolled = gtk.ScrolledWindow()
        scrolled.set_shadow_type(gtk.SHADOW_OUT)
        scrolled.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled.add(cloud)
        lists.append_page(scrolled)

        toolbar = gtk.Toolbar()
        toolbar.modify_bg(gtk.STATE_NORMAL,
                style.COLOR_PANEL_GREY.get_gdk_color())
        vbox.pack_end(toolbar, False)

        tree_button = RadioToolButton(
                named_icon='view-list',
                tooltip=_('Tree view'),
                group=None)
        tree_button.connect('toggled', page_cb, 0, tree)
        toolbar.insert(tree_button, -1)

        cloud_button = RadioToolButton(
                named_icon='view-cloud',
                group=tree_button,
                palette=CloudPalette(_('Cloud view'), tag_type, cloud))

        cloud_button.connect('toggled', page_cb, 1, cloud)
        toolbar.insert(cloud_button, -1)

        vbox.show_all()

        if model.this['tag_sidebar'][`tag_type`]['cloud_active']:
            cloud_button.props.active = True

        return vbox

    def _notify_page_cb(self, notebook, event):
        self._view_by_page[self._last_page].freeze()
        self._last_page = notebook.props.page
        view = self._view_by_page[self._last_page]
        view.update()
        model.this['tag_sidebar']['page'] = self._last_page

class CloudPalette(Palette):
    def __init__(self, label, tag_type, view):
        Palette.__init__(self, label)

        box = gtk.VBox()
        self.set_content(box)

        def sort_cb(widget, sort):
            if not widget.props.active:
                return
            view.sort = sort
            model.this['tag_sidebar'][`tag_type`]['cloud_by_size'] = \
                    (sort == SORT_COUNT)
            view.update(force=True)

        alphabet = gtk.RadioButton(None, _('Sort alphabetically'))
        alphabet.connect('clicked', sort_cb, SORT_ALPHABET)
        box.pack_start(alphabet)

        by_size = gtk.RadioButton(alphabet, _('Sort by size'))
        by_size.connect('clicked', sort_cb, SORT_COUNT)
        box.pack_start(by_size)

        separator = gtk.HSeparator()
        box.pack_start(separator)

        def reverse_cb(widget):
            view.reverse = widget.props.active
            model.this['tag_sidebar'][`tag_type`]['cloud_reverse'] = \
                    widget.props.active
            view.update(force=True)

        reverse = gtk.CheckButton(_('Reverse order'))
        reverse.connect('clicked', reverse_cb)
        box.pack_start(reverse)

        box.show_all()

        if model.this['tag_sidebar'][`tag_type`]['cloud_by_size']:
            by_size.props.active = True
        reverse.props.active = \
                model.this['tag_sidebar'][`tag_type`]['cloud_reverse']
