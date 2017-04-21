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
from gobject import property, GObject, SIGNAL_RUN_FIRST, TYPE_PYOBJECT
from gettext import gettext as _

VISIBLE_BUDDIES_COUNT = gtk.gdk.screen_width() > 800 and 5 or 3


TAGS_OBJECTIVE        = 0
TAGS_SUBJECTIVE       = 1
TAGS_SOURCE           = 2
TAGS_LAST             = 3

FIELD_UID             = 0
FIELD_TITLE           = 1
FIELD_TIMESTAMP       = 2
FIELD_MTIME           = 3
FIELD_ICON_COLOR      = 4
FIELD_MIME_TYPE       = 5
FIELD_ACTIVITY        = 6
FIELD_ACTIVITY_ID     = 7
FIELD_BUNDLE_ID       = 8
FIELD_BUDDIES         = 9

FIELD_TAGS            = 10
FIELD_TRAITS          = 11
FIELD_BUDDIES_COUNT   = 12

FIELD_AUTHOR          = 13
FIELD_GENRE           = 14
FIELD_ARTIST          = 15
FIELD_ALBUM           = 16
FIELD_COMPOSER        = 17
FIELD_DATE            = 18
FIELD_TRACK_NUMBER    = 19
FIELD_TRACK_COUNT     = 20
FIELD_DISC_NUMBER     = 21
FIELD_DISC_COUNT      = 22
FIELD_COPYRIGHT       = 23
FIELD_VERSION         = 24

FIELD_ICON            = 30
FIELD_MODIFY_TIME     = 31
FIELD_THUMB           = 32
FIELD_PREVIEW         = 33
FIELD_BUDDY_MENU      = 34
FIELD_BUDDY_FIRST     = 35
FIELD_LAST            = FIELD_BUDDY_FIRST + VISIBLE_BUDDIES_COUNT

FIELD_BASE_LIST       = { 'uid'           : (FIELD_UID, str),
                          'title'         : (FIELD_TITLE, str),
                          'timestamp'     : (FIELD_TIMESTAMP, int),
                          'mtime'         : (FIELD_MTIME, str),
                          'icon-color'    : (FIELD_ICON_COLOR, str),
                          'mime_type'     : (FIELD_MIME_TYPE, str),
                          'activity'      : (FIELD_ACTIVITY, str),
                          'activity_id'   : (FIELD_ACTIVITY_ID, str),
                          'bundle_id'     : (FIELD_BUNDLE_ID, str),
                          'buddies'       : (FIELD_BUDDIES, TYPE_PYOBJECT),

                          '_tags_'        : (FIELD_TAGS, str),
                          '_traits_'      : (FIELD_TRAITS, TYPE_PYOBJECT),
                          'buddies_count' : (FIELD_BUDDIES_COUNT, int),

                          'version'       : (FIELD_VERSION, str),
                          'author'        : (FIELD_AUTHOR, str),
                          'artist'        : (FIELD_ARTIST, str),
                          'album'         : (FIELD_ALBUM, str),
                          'composer'      : (FIELD_COMPOSER, str),
                          'date'          : (FIELD_DATE, str),
                          'genre'         : (FIELD_GENRE, str),
                          'track_number'  : (FIELD_TRACK_NUMBER, str),
                          'track_count'   : (FIELD_TRACK_COUNT, str),
                          'disc_number'   : (FIELD_DISC_NUMBER, str),
                          'disc_count'    : (FIELD_DISC_COUNT, str),
                          'copyright'     : (FIELD_COPYRIGHT, str) }

FIELD_CALC_LIST       = { 'icon'          : (FIELD_ICON, gtk.gdk.Pixbuf),
                          'modify_time'   : (FIELD_MODIFY_TIME, str),
                          'thumb'         : (FIELD_THUMB, gtk.gdk.Pixbuf),
                          'preview'       : (FIELD_PREVIEW, gtk.gdk.Pixbuf),
                          'buddy_menu'    : (FIELD_BUDDY_MENU, TYPE_PYOBJECT) }

TRAITS = { 'application': { 'title' : _('Activities list view'),
                            'fields': [ 'version', 'author' ] },

           'text'       : { 'title' : _('Books list view'),
                            'fields': [ 'author', 'genre', 'date' ] },

           'audio'      : { 'title' : _('Audio list view'),
                            'fields': [ 'artist', 'album', 'composer', 'date',
                                        'genre', 'track_number', 'track_count',
                                        'disc_number', 'disc_count',
                                        'copyright' ] },

           'video'      : { 'title' : _('Video list view'),
                            'fields': [ 'date', 'genre', 'copyright' ] } }

NAMES = { 'mime_type'   : _('Type'),
          'activity'    : _('Activity'),
          'traits'      : _('Traits'),

          'application' : _('Activity'),
          'text'        : _('Text'),
          'audio'       : _('Audio'),
          'video'       : _('Video'),

          'version'     : _('Version'),
          'author'      : _('Author'),
          'genre'       : _('Genre'),
          'artist'      : _('Artist'),
          'album'       : _('Album'),
          'composer'    : _('Composer'),
          'date'        : _('Date'),
          'track_number': _('Track'),
          'track_count' : _('Track count'),
          'disc_number' : _('Disc'),
          'disc_count'  : _('Disc count'),
          'copyright'   : _('Copyright') }

for i in range(VISIBLE_BUDDIES_COUNT):
    FIELD_CALC_LIST['buddy' + `i`] = (FIELD_BUDDY_FIRST+i, gtk.gdk.Pixbuf)

def fields_by_mime_type(mime_type):
    if not mime_type:
        return []
    trait = TRAITS.get(mime_type)
    if trait:
        return trait['fields']
    trait = TRAITS.get(mime_type.split('/')[0])
    return trait and trait['fields'] or []

class Source(GObject):
    __gsignals__ = {
            'tags-updated'   : (SIGNAL_RUN_FIRST, None, [TYPE_PYOBJECT]),
            'objects-updated': (SIGNAL_RUN_FIRST, None, []) }

    def get_active(self):
        pass

    def set_active(self, value):
        pass

    def query(self):
        pass

    def get_count(self):
        """ Returns number of objects """
        pass

    def get_row(self, offset, frame_range, cb, *args):
        """ Get object """
        pass

    def get_object(self, uid, cb, *args):
        pass

    def post_object(self, object):
        pass

    def get_order(self):
        # stub
        pass

    def set_order(self, column, order):
        # stub
        pass

    def __init__(self):
        GObject.__init__(self)

        self.tags = []
        self.selected_tags = []
        self.search = None

        for i in range(TAGS_LAST):
            self.tags.append({})
            self.selected_tags.append([])
