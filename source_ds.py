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

import re
import logging

import port.json as json

import ds
from source import *

class DatastoreSource(Source):
    def __init__(self):
        Source.__init__(self)
        self._active = False

    def on_get_count(self):
        # stub
        pass

    def on_query(self, request):
        # stub
        return request

    def get_active(self):
        return self._active

    def set_active(self, value):
        self._active = value

    def get_count(self):
        if self._active:
            return self.on_get_count()
        else:
            return 0

    def query(self):
        if not self._active:
            for type in range(TAGS_LAST):
                self.emit('tags-updated', type)
            self.emit('objects-updated')
            return

        request = {}

        def add_query(string):
            request['query'] = request.get('query', '')
            if request['query']:
                request['query'] += ' AND '
            request['query'] += str(string)

        for i in self.selected_tags[TAGS_OBJECTIVE]:
            if i[0] == 'mime_type':
                request['mime_type'] = request.get('mime_type', []) \
                        + ['/'.join(i[1:])]
            elif i[0] == 'activity':
                request['activity'] = str(i[-1])
            elif i[0] == 'traits':
                add_query(i[-1])

        for i in self.selected_tags[TAGS_SUBJECTIVE]:
            add_query('__%s__*' % '__'.join(i))

        if self.search:
            add_query(self.search + '*')

        return self.on_query(request)

    def get_object(self, uid, cb, *args):
        def reply_cb(metadata):
            self.decode_fields(metadata)
            cb(metadata, *args)

        def error_cb(error):
            logging.error('get_object(%s): %s' % (uid, error))
            cb(None, *args)

        ds.get_properties(uid, reply_handler=reply_cb, error_handler=error_cb)

    def post_object(self, object):
        self.encode_fields(object)
        ds.write(object, update_mtime=False)

    def encode_key(self, text, prefix):
        def encode(str):
            return re.sub('\W+', '_', str).strip('_')
        if isinstance(text, str):
            text = encode(text)
        else:
            text = '__'.join([encode(i) for i in text])
        return '__%s_%s__' % (prefix, text)

    def encode_fields(self, object):
        if object.has_key('buddies'):
            encoded_buddies = {}
            for uid, name, color in object['buddies']:
                encoded_buddies[uid] = (name, color)
            object['buddies'] = json.dumps(encoded_buddies)
            if object.has_key('buddies_count'):
                del object['buddies_count']

        if object.has_key('_tags_'):
            tags = []
            for name, foo in object['_tags_']:
                if name:
                    tags.append((name, self.encode_key(name, 'tag')))
            object['_tags_'] = json.dumps(tags)

        for field in fields_by_mime_type(object.get('mime_type')):
            value = object.get(field)
            if not value:
                continue
            object[field] = json.dumps((value, self.encode_key(value, 'trait')))
        if object.has_key('_traits_'):
            del object['_traits_']

        return object

    def decode_fields(self, object):
        buddies = object.get('buddies', [])
        if buddies:
            try:
                buddies = json.loads(buddies)
                buddies = [(i[0], i[1][0], i[1][1]) for i in buddies.items()]
                buddies = sorted(buddies, cmp=lambda x,y: cmp(x[1], y[1]))
                object['buddies'] = buddies
            except Exception, e:
                logging.warning('decode_fields: buddies=%s %s' % (buddies, e))
        object['buddies_count'] = len(buddies)

        tags = object.get('_tags_')
        if tags:
            try:
                tags = json.loads(tags)
                for i, tag in enumerate(tags):
                    tags[i] = \
                            (tag[0], tag[1].strip('_').split('__'))
                object['_tags_'] = tags
            except Exception, e:
                logging.warning('decode_fields: tags=%s %s' % (tags, e))

        traits = {}
        for field in fields_by_mime_type(object.get('mime_type')):
            field_value = object.get(field)
            if not field_value:
                continue
            try:
                pretty_value, value = json.loads(field_value)
                traits[field] = (pretty_value, value)
                object[field] = pretty_value
            except Exception, e:
                logging.warning('decode_fields: value=%s %s' % (field_value, e))
        if traits:
            object['_traits_'] = traits

        return object

    def update_tags(self, obj, sign, delta=None):
        def shift(type, full_tag, full_tag_name, only_final=True):
            def get_leftset(x, y):
                for i in range(min(len(x), len(y))):
                    if x[0:i+1] != y[0:i+1]:
                        i -= 1
                        break
                return i+1

            for depth in range(len(full_tag)):
                tag = full_tag[0:depth+1]
                tag_name = full_tag_name[0:depth+1]

                leftset = 0
                for i in reversed(self.selected_tags[type]):
                    leftset = max(leftset, get_leftset(tag, i))
                if leftset == len(tag):
                    continue

                tag_count = self.tags[type].get(tag, (0, 0))[1] + sign

                if tag_count == 0:
                    del self.tags[type][tag]
                else:
                    self.tags[type][tag] = (tag_name[-1], tag_count,
                            not only_final or tag == full_tag)

                delta[type] = delta.get(type, {})
                delta[type][tag] = delta[type].get(tag, 0) + sign

        def name(x):
            return NAMES.get(x, x)

        if delta is None:
            delta = {}

        mime_type = obj.get('mime_type')
        if mime_type:
            mime_type = tuple(mime_type.split('/'))
            shift(TAGS_OBJECTIVE, ('mime_type',) + mime_type,
                    (name('mime_type'), name(mime_type[0]), name(mime_type[1])))

        activity = obj.get('activity')
        if activity:
            shift(TAGS_OBJECTIVE, ('activity', activity),
                    (name('activity'), name(activity)))

        if obj.has_key('_traits_'):
            for field, value in obj['_traits_'].items():
                shift(TAGS_OBJECTIVE, ('traits', field, value[1]),
                        (name('traits'), name(field), value[0]))

        for name, tag in obj.get('_tags_', []):
            shift(TAGS_SUBJECTIVE, tuple(tag), tuple(name), False)

        return delta

    def diff_tags(self, old, new):
        delta = {}

        self.update_tags(old, -1, delta)
        self.update_tags(new, +1, delta)

        for i, type in delta.items():
            for j, count in type.items():
                if not count:
                    del type[j]
            if not type:
                del delta[i]

        return delta
