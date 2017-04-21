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
import bisect

from sugar.bundle.activitybundle import ActivityBundle
import port.json

import ds
from source import *
from source_ds import *

FRAME_SIZE = 64

class DatastoreRichSource(DatastoreSource):
    def __init__(self, default_order=('uid', gtk.SORT_ASCENDING)):
        DatastoreSource.__init__(self)
        self._order = default_order

        self._init()

        ds.connect('Created', self._created_cb)
        ds.connect('Updated', self._updated_cb)
        ds.connect('Deleted', self._deleted_cb)

    def _init(self):
        self._request = None
        self._objects = {}
        self.tags = []
        self._index_by = {}
        self._index = None
        self._query_frame = (0, FRAME_SIZE)
        self._fields = FIELD_BASE_LIST.keys()

        for i in range(TAGS_LAST):
            self.tags.append({})

    def on_get_count(self):
        return self._index and len(self._index) or 0

    def on_query(self, request):
        self._init()
        self._request = request
        self._query()

    def get_row(self, offset, frame_range=None, cb=None, *args):
        if self._query_frame:
            logging.debug('get_row: skip %s before query' % offset)
            return False

        if offset < 0 or offset >= len(self._index):
            logging.debug('get_row: %s is out of range (%s:%s)' % \
                    (offset, 0, len(self._index)))
            return False

        if self._order[1] == gtk.SORT_ASCENDING:
            object = self._index[offset].object
        else:
            object = self._index[len(self._index) - offset - 1].object

        return object

    def get_order(self):
        return self._order

    def set_order(self, field, order):
        if (field, order) != self._order:
            self._updare_order((field, order))
            self.emit('objects-updated')

    def _query(self):
        ds.find(self._request, self._fields, frame=self._query_frame,
                reply_handler=self._query_reply_cb,
                error_handler=self._query_error_cb)

    def _query_reply_cb(self, entries, all_count):
        for obj in entries:
            oid = _get_oid(obj)
            old = self._objects.get(oid)

            if old and not _is_newer(obj, old):
                continue
            if old:
                self.update_tags(old, -1)

            self.decode_fields(obj)

            self._objects[oid] = obj
            self.update_tags(obj, +1)

        if self._query_frame and \
                self._query_frame[0] + len(entries) < all_count:
            self._query_frame = \
                    (self._query_frame[0] + len(entries), FRAME_SIZE)
            self._query()
        else:
            self._query_frame = None

            self._index = self._indexes_create('uid')
            if self._order[0] != 'uid':
                self._updare_order(self._order)

            for type in range(TAGS_LAST):
                self.emit('tags-updated', type)
            self.emit('objects-updated')

    def _query_error_cb(self, error):
        logging.error('query: %s' % error)

        for type in range(TAGS_LAST):
            self.emit('tags-updated', type)
        self.emit('objects-updated')

    def _updare_order(self, order):
        field = order[0]
        self._index = self._index_by.get(field, self._indexes_create(field))
        self._order = order

    def _created_cb(self, uid):
        if self._query_frame:
            logging.debug('_created_cb: skip %s before query' % uid)
            return

        new = ds.get_properties(uid)
        oid = _get_oid(new)
        old = self._objects.get(oid)

        if old and not _is_newer(new, old):
            logging.debug('_created_cb: %s is not newer then %s' % (new, old))
            return

        self._update_object(new, old)

    def _updated_cb(self, uid):
        if self._query_frame:
            logging.debug('_updated_cb: skip %s before query' % uid)
            return

        new = ds.get_properties(uid)
        oid = _get_oid(new)
        old = self._objects.get(oid)

        if not old:
            logging.debug('_updated_cb: cannot find %s, use _created_cb' % new)
            self._created_cb(uid)
            return

        if not _is_newer(new, old):
            logging.debug('_created_cb: is not newer %s <=> %s' \
                    % (new, old))
            return

        self._update_object(new, old)

    def _deleted_cb(self, uid):
        if self._query_frame:
            logging.debug('_deleted_cb: skip %s before query' % uid)
            return

        index = self._index_by['uid']
        i = bisect.bisect_left(index, IndexItem(value=uid))

        if i >= len(index) or index[i].value != uid:
            logging.warning('_deleted_cb: cannot find %s' % uid)
            return

        old = index[i].object
        oid = _get_oid(old)

        def delete():
            delta = self.update_tags(old, -1)
            for type in delta.keys():
                self.emit('tags-updated', type)

            self._indexes_delete(old)
            del self._objects[oid]

            self.emit('objects-updated')

        def reply_handler(entries, all_count):
            if all_count:
                self._update_object(entries[0], old)
            else:
                delete()

        def error_handler(error):
            logging.debug('_deleted_cb: %s; delete %s anyway' % (error, old))
            delete()

        oid_field = _get_oid_field(old)
        if not oid_field:
            delete()
            return

        request = self._request.copy()
        request['order'] = '-%s' % oid_field
        request[oid_field] = oid

        ds.find(request, self._fields, frame=(0, 1),
                reply_handler=reply_handler, error_handler=error_handler)

    def _update_object(self, new, old):
        self.decode_fields(new)

        if old:
            delta = self.diff_tags(old, new)
        else:
            delta = self.update_tags(new, +1)

        for type in delta.keys():
            self.emit('tags-updated', type)

        oid = _get_oid(new)

        if old:
            self._indexes_update(new, old)
        else:
            self._indexes_add(new)

        self._objects[oid] = new
        self.emit('objects-updated')

    def _indexes_create(self, field):
        index = self._index_by[field] = []
        for i in self._objects.values():
            bisect.insort_right(index, IndexItem(i, field))
        return index

    def _indexes_add(self, object):
        for field, index in self._index_by.items():
            bisect.insort_right(index, IndexItem(object, field))

    def _indexes_update(self, new, old):
        self._indexes_delete(old)
        self._indexes_add(new)

    def _indexes_delete(self, object):
        for field, index in self._index_by.items():
            i = bisect.bisect_left(index, IndexItem(object, field))
            if i < len(index) and index[i].object == object:
                del index[i]
            else:
                logging.error('_indexes_delete: can not find %s in %s index' \
                        % (object, field))

class IndexItem:
    def __init__(self, object=None, field=None, value=None):
        if value:
            self.object = None
            self.value = value
        else:
            self.object = object
            self.value = object.get(field)

    def __lt__(self, other):
        return self.value < other.value

def _is_newer(new, old):
    if old.has_key('bundle_id'):
        new_version = new.get('activity_version') \
                #or _load_bundle(new).get_activity_version()
        old_version = old.get('activity_version') \
                #or _load_bundle(old).get_activity_version()
        result = int(new_version or 0) - int(old_version or 0)
    else:
        new_ts = new.get('timestamp')
        old_ts = old.get('timestamp')
        result =  int(new_ts or 0) - int(old_ts or 0)

    if result == 0:
        if new['uid'] == old['uid']:
            return True
        else:
            return False
    else:
        return result > 0

def _get_oid(object):
    oid = object.get('bundle_id')
    if oid:
        return oid

    #if object.get('mime_type') == 'application/vnd.olpc-sugar':
    #    return _load_bundle(object).get_bundle_id()

    oid = object.get('activity_id')
    if oid:
        return oid

    return object.get('uid')

def _load_bundle(object):
    logging.debug('have to load bundle to activity parameters')

    jobject = ds.get(object['uid'])
    bundle = ActivityBundle(jobject.get_file_path())
    object['bundle_id'] = bundle.get_bundle_id()
    object['activity_version'] = bundle.get_activity_version()
    jobject.destroy()

    return bundle

def _get_oid_field(object):
    if object.get('mime_type') == 'application/vnd.olpc-sugar':
        return 'bundle_id'

    if object.get('activity_id'):
        return 'activity_id'

    return None
