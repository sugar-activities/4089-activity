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
from sugar.graphics.toolbutton import ToolButton
from sugar.graphics.radiotoolbutton import RadioToolButton
import port.widgets

import model
from source import *

this = None

def select_tag(tag_type, tag, name):
    _add_tag(tag_type, tag, name, True)

def add_tag(tag_type, tag, name):
    _add_tag(tag_type, tag, name, False)

def _del_buttons(count):
    for i in range(count):
        for widget in this.path[-1][2]:
            this.remove(widget)
        del this.path[-1]

def _add_tag(tag_type, tag, name, replace):
    for type, i, widgets in this.path[0:this.pos+1]:
        if i == tag:
            return

    _del_buttons(len(this.path) - this.pos - 1)

    if replace and this.pos == -1:
        replace = False

    if replace:
        button = this.path[this.pos][2][0]
        button.props.icon_widget = None
        button.props.label_widget = None
        button.set_label(name)
        this.path[this.pos][0] = tag_type
        this.path[this.pos][1] = tag
        _query(button, this.pos)
    else:
        button = _create_button(name)
        this.path.append([tag_type, tag, [button]])
        this.insert(button, -1)
        button.props.active = True

def _create_button(name):
    button = RadioToolButton()
    button.show()
    button.props.group = this.all
    button.set_label(name)
    button.connect('toggled', _query, len(this.path))
    return button

def _query(button, pos):
    if button and not button.props.active:
        return

    this.pos = pos

    def make_request(path):
        request = []
        for i in range(TAGS_LAST):
            request.append([])
        for type, tag, widgets in path:
            request[type].append(tag)
        return request

    request = make_request(this.root)
    model.local_source.selected_tags = request
    logging.debug('path._query: root=%s' % model.local_source.selected_tags)

    request = make_request(this.path[0:pos+1])
    for type, tags in enumerate(request):
        model.source.selected_tags[type] += tags
    logging.debug('path._query: %s' % model.source.selected_tags)

    model.source.query()

class RootPalette(Palette):
    def __init__(self):
        Palette.__init__(self, _('Root'))

        self.connect('popup', self._popup_cb)

        box = gtk.VBox()
        self.set_content(box)

        self.radio = [None] * 3

        self.radio[0] = gtk.RadioButton(self.radio[0],
                _('Hide local objects'))
        box.pack_start(self.radio[0])

        self.radio[1] = gtk.RadioButton(self.radio[0],
                _('Show all local objects'))
        box.pack_start(self.radio[1])

        self.radio[2] = gtk.RadioButton(self.radio[0])
        box.pack_start(self.radio[2])

        separator = gtk.Label()
        box.pack_start(separator)

        self.setup = gtk.Button(_('Add current path to filter'))
        self.setup.connect('clicked', self._setup_cb)
        setup_box = gtk.HBox()
        setup_box.pack_start(self.setup, False)
        box.pack_start(setup_box)

        box.show_all()

        self.config = model.this['path']
        for tag_type, tag, name in self.config['root_path']:
            button = _create_button(name)
            this.last_root.append([tag_type, tag, [button]])
        this.pos = self.config['root_type']
        self.radio[this.pos].props.active = True
        model.local_source.set_active(this.pos)
        if this.pos == 2:
            this.root = [] + this.last_root
        _query(None, this.pos)

        self.radio[0].connect('toggled', self._non_filter_cb, 0, False)
        self.radio[1].connect('toggled', self._non_filter_cb, 1, True)
        self.radio[2].connect('toggled', self._filter_cb)

    def _popup_cb(self, window):
        path = []

        for i in this.last_root:
            path.append(i[2][0].props.label)

        self.radio[2].props.label = _('Filter local objects by [%s]') % \
                (path and ', '.join(path) or 'None')

        if self.radio[2].props.active:
            self.setup.props.label = _('Add current path to filter')
        else:
            self.setup.props.label = _('Use current path as a filter')
            self.setup.props.sensitive = True

    def _non_filter_cb(self, widget, index, active):
        if not widget.props.active:
            return
        self.config['root_type'] = index
        model.local_source.set_active(active)
        this.root = []
        _query(None, this.pos)
        self._popup_cb(None)

    def _filter_cb(self, widget):
        if not widget.props.active:
            return
        self.config['root_type'] = 2
        model.local_source.set_active(True)
        this.root = [] + this.last_root
        _query(None, this.pos)
        self._popup_cb(None)

    def _setup_cb(self, widget):
        if self.radio[2].props.active:
            this.root = this.last_root + this.path
        else:
            this.root = [] + this.path
            self.config['root_type'] = []
        this.last_root = [] + this.root

        for tag_type, tag, widgets in this.path:
            self.config['root_path'].append(
                    (tag_type, tag, widgets[0].props.label))

        _del_buttons(len(this.path))
        this.path = []

        if this.all.props.active:
            _query(None, -1)
        else:
            this.all.props.active = True

        self._popup_cb(None)

class Path(gtk.Toolbar):
    def __init__(self):
        gtk.Toolbar.__init__(self)

        global this
        this = self

        self.root = []
        this.last_root = []
        self.path = []
        self.pos = -1

        self.all = port.widgets.RadioToolButton(icon_name='go-home')
        self.all.props.palette = RootPalette()
        self.all.connect('toggled', _query, -1)
        self.insert(self.all, -1)

        self.show_all()
