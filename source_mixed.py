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

import logging
from gobject import property, GObject, SIGNAL_RUN_FIRST, TYPE_PYOBJECT

from sugar.bundle.activitybundle import ActivityBundle

import ds

TAGS_OBJECTIVE    = 0
TAGS_TRAITS       = 1
TAGS_SUBJECTIVE   = 2
TAGS_SOURCE       = 3
TAGS_LAST         = 4

FIELD_UID         = 0
FIELD_TITLE       = 1
FIELD_TIMESTAMP   = 2
FIELD_MTIME       = 3
FIELD_ICON_COLOR  = 4
FIELD_MIME_TYPE   = 5
FIELD_ACTIVITY    = 6
FIELD_ACTIVITY_ID = 7
FIELD_BUNDLE_ID   = 8

FIELD_ICON        = 30
FIELD_MODIFY_TIME = 31

FIELD_BASE_LIST   = { 'uid'        : (FIELD_UID, str),
                      'title'      : (FIELD_TITLE, str),
                      'timestamp'  : (FIELD_TIMESTAMP, int),
                      'mtime'      : (FIELD_MTIME, str),
                      'icon-color' : (FIELD_ICON_COLOR, str),
                      'mime_type'  : (FIELD_MIME_TYPE, str),
                      'activity'   : (FIELD_ACTIVITY, str),
                      'activity_id': (FIELD_ACTIVITY_ID, str),
                      'bundle_id'  : (FIELD_BUNDLE_ID, str) }

class Source(GObject):
    tags = []

    __gsignals__ = {
            'tags-init'      : (SIGNAL_RUN_FIRST, None, []),
            'tags-updated'   : (SIGNAL_RUN_FIRST, None, 2*[TYPE_PYOBJECT]),
            'objects-updated': (SIGNAL_RUN_FIRST, None, []) }

    def query(self, filter):
        # stub
        pass

    def get_count(self):
        """ Returns number of objects """
        pass

    def get_row(self, offset, frame_range, cb, *args):
        """ Get object """
        pass

    def get_columns(self):
        """ Get columns - [column_num, ...] """
        pass

    def get_order(self):
        # stub
        pass

    def set_order(self, column, order):
        # stub
        pass

    def __init__(self):
        GObject.__init__(self)

class Context(GObject):
    __gsignals__ = {
            'init'           : (SIGNAL_RUN_FIRST, None, []),
            'tags-updated'   : (SIGNAL_RUN_FIRST, None, 2*[TYPE_PYOBJECT]),
            'objects-updated': (SIGNAL_RUN_FIRST, None, []) }

    def get_sources(self):
        return self._sources

    def set_sources(self, sources):
        for i in set(sources) - set(self._sources):
            i.emiter = self
        self._sources = sources

    def get_tags(self):
        result = []
        for i in range(TAGS_LAST):
            result.append({})

        for i in self._sources:
            for j in range(TAGS_LAST):
                result[j].append(i[j])

        return result

    sources = property(type=object, getter=get_sources, setter=set_sources)
    tags    = property(type=object, getter=get_tags, setter=None)

    def query(self, filter):
        def fetch_cb(oid, object):
            self.emit('object-added', oid, object)
            return True

        countdown = [len(self._sources)]

        def query_cb(status):
            if not status:
                logging.error('query_cb')
                return

            countdown[0] -= 1
            if countdown[0]:
                return

            self.emit('init')

            for i in self._sources:
                i.fetch(fetch_cb)

        for i in self._sources:
            i.query(filter, query_cb)

    def __init__(self):
        GObject.__init__(self)
        self._sources = []

def diff_tags(tags, obj, sign):
    delta = {}

    def shift(type, tag):
        tag_count = tags[type][tag] = \
                tags[type].get(tag, 0) + sign
        if tag_count == 0:
            del tags[type][tag]
        delta[type] = delta.get(type, {})
        delta[type][tag] = tag_count

    def shift_by_field(type, field):
        tags = obj.get(field)
        if not tags:
            return

        for i in tags.split():
            if not i:
                continue
            composite_tag = None
            for j in i.strip('_').split('_'):
                composite_tag = composite_tag and composite_tag+'_'+j or j
                shift(type, composite_tag)

    if obj.get('mime_type') == 'application/vnd.olpc-sugar':
        shift(TAGS_OBJECTIVE, 'creator')
    if obj.get('activity_id') is None:
        shift(TAGS_OBJECTIVE, 'unbind')
    else:
        shift(TAGS_OBJECTIVE, 'creation')
    shift_by_field(TAGS_TRAITS, 'traits')
    shift_by_field(TAGS_SUBJECTIVE, 'tags')

    return delta

def get_oid(object):
    oid = object.get('bundle_id')
    if oid:
        return oid

    if object.get('mime_type') == 'application/vnd.olpc-sugar':
        return _load_bundle(object).get_bundle_id()

    oid = object.get('activity_id')
    if oid:
        return oid

    return object.get('uid')

def is_newer(new, old):
    if not old.has_key('bundle_id'):
        new_ts = new.get('timestamp')
        old_ts = old.get('timestamp')
        return new_ts and int(new_ts) > int(old_ts)

    new_version = new.get('activity_version') \
            or _load_bundle(new).get_activity_version()
    old_version = old.get('activity_version') \
            or _load_bundle(old).get_activity_version()

    return new_version and new_version > old_version

def get_oid_field(object):
    if object.get('mime_type') == 'application/vnd.olpc-sugar':
        return 'bundle_id'

    if object.get('activity_id'):
        return 'activity_id'

    return None

def _load_bundle(object):
    logging.debug('have to load bundle to activity parameters')

    jobject = ds.get(object['uid'])
    bundle = ActivityBundle(jobject.get_file_path())
    object['bundle_id'] = bundle.get_bundle_id()
    object['activity_version'] = bundle.get_activity_version()

    return bundle
