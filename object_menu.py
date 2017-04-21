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
from gettext import gettext as _

from sugar.graphics.icon import Icon
from sugar.graphics.menuitem import MenuItem
from port.widgets import Palette
import port.shell

import model
import activity
from theme import *
from source import *

def activate(metadata):
    logging.debug('activate %s' % str(metadata))

    bundle_id = metadata.get('activity')
    if not bundle_id:
        bundle_id = model.this['viewers'].get(metadata.get('mime_type'))
    port.shell.activate(metadata, bundle_id)

class ObjectMenu(Palette):
    def __init__(self, metadata, icon, edit_menu=True):
        self._metadata = metadata
        self._temp_file_path = None

        activity_icon = gtk.Image()
        activity_icon.props.pixbuf = icon
        title = metadata.get('title') or _('Untitled')

        Palette.__init__(self, primary_text=title, icon=activity_icon)

        bundles = port.shell.get_bundles_by_metadata(self._metadata)

        if bundles:
            start_bundle = None

            if metadata.get('activity'):
                resume_label = _('Resume')
                start_bundle = port.shell.get_bundle(metadata.get('activity'))
            else:
                resume_label = _('Start')
                bundle_id = model.this['viewers'].get(metadata.get('mime_type'))
                if bundle_id:
                    start_bundle = port.shell.get_bundle(bundle_id)

            if start_bundle:
                menu_icon = Icon(file=start_bundle.get_icon(),
                        icon_size=gtk.ICON_SIZE_MENU)
            else:
                menu_icon = Icon(icon_name='activity-start',
                        icon_size=gtk.ICON_SIZE_MENU)

            menu_item = MenuItem(resume_label)
            menu_item.set_image(menu_icon)
            menu_item.connect('activate', self._resume_cb)
            self.menu.append(menu_item)
            menu_item.show()

            self.resum_bundle_id = start_bundle and start_bundle.get_bundle_id()
            self.resum_item = menu_item

            menu_item = gtk.SeparatorMenuItem()
            self.menu.append(menu_item)
            menu_item.show()

            for i in bundles:
                menu_item = MenuItem(i.get_name())
                menu_item.set_image(Icon(file=i.get_icon(),
                        icon_size=gtk.ICON_SIZE_MENU))
                menu_item.connect('activate', self._start_cb,
                        metadata.get('mime_type'), i)
                self.menu.append(menu_item)
                menu_item.show()

            if edit_menu:
                menu_item = gtk.SeparatorMenuItem()
                self.menu.append(menu_item)
                menu_item.show()

        if edit_menu:
            menu_item = MenuItem(_('View Details'), 'go-right')
            menu_item.connect('activate', self._detail_cb)
            self.menu.append(menu_item)
            menu_item.show()

    def _resume_cb(self, menu_item):
        port.shell.activate(self._metadata, self.resum_bundle_id)

    def _start_cb(self, menu_item, mime_type, bundle):
        bundle_id = bundle.get_bundle_id()
        model.this['viewers'][mime_type] = bundle_id
        self.resum_item.set_image(Icon(file=bundle.get_icon(),
                icon_size=gtk.ICON_SIZE_MENU))
        self.resum_bundle_id = bundle_id
        port.shell.activate(self._metadata, bundle_id)

    def _detail_cb(self, menu_item):
        activity.this.edit(self._metadata)
