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

import os
import gtk

from sugar.graphics import style
from sugar.activity.activity import get_bundle_path
import port.pixbuf

from source import *

ICON_SIZE = 32

THUMB_WIDTH  = gtk.gdk.screen_width() / 8
THUMB_HEIGHT = int(float(THUMB_WIDTH) / 4 * 3)

CELL_WIDTH  = THUMB_WIDTH + style.DEFAULT_PADDING*2
CELL_HEIGHT = THUMB_HEIGHT + style.DEFAULT_PADDING*2 + ICON_SIZE

PREVIEW_WIDTH  = gtk.gdk.screen_width() / 3
PREVIEW_HEIGHT = int(float(PREVIEW_WIDTH) / 4 * 3)

THUMB_STUB = port.pixbuf.from_svg_at_size(
        os.path.join(get_bundle_path(), 'icons', 'no-image.svg'),
        THUMB_WIDTH, THUMB_HEIGHT)
PREVIEW_STUB = port.pixbuf.from_svg_at_size(
        os.path.join(get_bundle_path(), 'icons', 'no-image.svg'),
        PREVIEW_WIDTH, PREVIEW_WIDTH)

VISIBLE_BUDDIES_WIDTH = VISIBLE_BUDDIES_COUNT * ICON_SIZE + \
                        VISIBLE_BUDDIES_COUNT * 2 # XXX can not eliminate
                                                  # this pad between renderers
