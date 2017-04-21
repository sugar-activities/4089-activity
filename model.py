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

from sugar.presence import presenceservice
import port.json as json

from theme import *
from source import *
from object_model import ObjectModel
from source_ds_rich import DatastoreRichSource

source = DatastoreRichSource(default_order=('timestamp', gtk.SORT_DESCENDING))
local_source = source
object_model = ObjectModel()
owner = presenceservice.get_instance().get_owner()

class Model(dict):
    def __init__(self):
        dict.__init__(self)

        self['activity'] = {
                'sidebar_visible'   : True,
                'sidebar_position'  : 1,
                'sidebar_separator' : gtk.gdk.screen_width() / 4 * 3,
                'objects_view'      : 0 }

        self['tag_sidebar'] = {
                'page': 0,
                `TAGS_OBJECTIVE` : { 'cloud_active' : False,
                                     'cloud_by_size': False,
                                     'cloud_reverse': False },
                `TAGS_SUBJECTIVE`: { 'cloud_active' : True,
                                     'cloud_by_size': False,
                                     'cloud_reverse': False },
                `TAGS_SOURCE`    : { 'cloud_active' : True,
                                     'cloud_by_size': False,
                                     'cloud_reverse': False } }

        self['object_compact'] = {
                'list_type' : 'default',

                'default'    : [ { 'column'  : 'title',
                                   'width'   : 50,
                                   'visible' : True,
                                   'expand'  : True },

                                 { 'column'  : 'buddies',
                                   'width'   : VISIBLE_BUDDIES_WIDTH,
                                   'visible' : True,
                                   'expand'  : False },

                                 { 'column'  : 'mtime',
                                   'width'   : 180,
                                   'visible' : True,
                                   'expand'  : False } ],

                'application': [ { 'column'  : 'title',
                                   'width'   : 300,
                                   'visible' : True,
                                   'expand'  : False },

                                 { 'column'  : 'buddies',
                                   'width'   : VISIBLE_BUDDIES_WIDTH,
                                   'visible' : True,
                                   'expand'  : False },

                                 { 'column'  : 'mtime',
                                   'width'   : 180,
                                   'visible' : True,
                                   'expand'  : False },

                                 { 'column'  : 'author',
                                   'width'   : 180,
                                   'visible' : True,
                                   'expand'  : False },

                                 { 'column'  : 'genre',
                                   'width'   : 180,
                                   'visible' : True,
                                   'expand'  : False } ],

                'text'       : [ { 'column'  : 'title',
                                   'width'   : 300,
                                   'visible' : True,
                                   'expand'  : False },

                                 { 'column'  : 'buddies',
                                   'width'   : VISIBLE_BUDDIES_WIDTH,
                                   'visible' : True,
                                   'expand'  : False },

                                 { 'column'  : 'mtime',
                                   'width'   : 180,
                                   'visible' : True,
                                   'expand'  : False },

                                 { 'column'  : 'author',
                                   'width'   : 180,
                                   'visible' : True,
                                   'expand'  : False },

                                 { 'column'  : 'genre',
                                   'width'   : 180,
                                   'visible' : True,
                                   'expand'  : False } ],

                'audio'      : [ { 'column'  : 'title',
                                   'width'   : 300,
                                   'visible' : True,
                                   'expand'  : False },

                                 { 'column'  : 'buddies',
                                   'width'   : VISIBLE_BUDDIES_WIDTH,
                                   'visible' : True,
                                   'expand'  : False },

                                 { 'column'  : 'mtime',
                                   'width'   : 180,
                                   'visible' : True,
                                   'expand'  : False },

                                 { 'column'  : 'artist',
                                   'width'   : 200,
                                   'visible' : True,
                                   'expand'  : False },

                                 { 'column'  : 'album',
                                   'width'   : 200,
                                   'visible' : True,
                                   'expand'  : False },

                                 { 'column'  : 'composer',
                                   'width'   : 200,
                                   'visible' : True,
                                   'expand'  : False },

                                 { 'column'  : 'date',
                                   'width'   : 200,
                                   'visible' : True,
                                   'expand'  : False },

                                 { 'column'  : 'genre',
                                   'width'   : 200,
                                   'visible' : True,
                                   'expand'  : False },

                                 { 'column'  : 'track_number',
                                   'width'   : 200,
                                   'visible' : True,
                                   'expand'  : False },

                                 { 'column'  : 'track_count',
                                   'width'   : 200,
                                   'visible' : True,
                                   'expand'  : False },

                                 { 'column'  : 'disc_number',
                                   'width'   : 200,
                                   'visible' : True,
                                   'expand'  : False },

                                 { 'column'  : 'disc_count',
                                   'width'   : 200,
                                   'visible' : True,
                                   'expand'  : False },

                                 { 'column'  : 'copyright',
                                   'width'   : 200,
                                   'visible' : True,
                                   'expand'  : False } ],

                'video'      : [ { 'column'  : 'title',
                                   'width'   : 300,
                                   'visible' : True,
                                   'expand'  : False },

                                 { 'column'  : 'buddies',
                                   'width'   : VISIBLE_BUDDIES_WIDTH,
                                   'visible' : True,
                                   'expand'  : False },

                                 { 'column'  : 'mtime',
                                   'width'   : 180,
                                   'visible' : True,
                                   'expand'  : False },

                                 { 'column'  : 'date',
                                   'width'   : 200,
                                   'visible' : True,
                                   'expand'  : False },

                                 { 'column'  : 'genre',
                                   'width'   : 200,
                                   'visible' : True,
                                   'expand'  : False },

                                 { 'column'  : 'copyright',
                                   'width'   : 200,
                                   'visible' : True,
                                   'expand'  : False } ] }

        self['path'] = { 'root_type': 1,
                         'root_path': [] }

        self['viewers'] = {
                'text/plain'        : 'org.laptop.sugar.ReadEtextsActivity',
                'application/zip'   : 'org.laptop.sugar.ReadEtextsActivity' }

    def serialize(self):
        return json.dumps(self)

    def deserialize(self, data):
        self.update(json.loads(data))

this = Model()
