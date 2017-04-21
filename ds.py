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

import dbus
import logging
from datetime import datetime
import time

from sugar.datastore import datastore

_ds = dbus.Interface(
        dbus.SessionBus().get_object(
            'org.laptop.sugar.DataStore',
            '/org/laptop/sugar/DataStore'),
        'org.laptop.sugar.DataStore')

def connect(signal, cb):
    _ds.connect_to_signal(signal, cb)

def disconnect(subscriber):
    pass

def find(filter, properties, frame=(0, 0),
        reply_handler=None, error_handler=None, *args):
    query = filter.copy()
    logging.debug('find: %s' % query)

    if frame[0]:
        query['offset'] = frame[0]
    if frame[1]:
        query['limit'] = frame[1]

    _ds.find(query, properties, byte_arrays=True,
            reply_handler=reply_handler, error_handler=error_handler)

def get(uid):
    return datastore.get(uid)

def get_properties(uid, reply_handler=None, error_handler=None, *args):
    return _ds.get_properties(uid, byte_arrays=True,
            reply_handler=reply_handler, error_handler=error_handler)

def write(metadata, update_mtime=True):
    if update_mtime:
        metadata['mtime'] = datetime.now().isoformat()
        metadata['timestamp'] = int(time.time())

    return _ds.update(metadata['uid'], metadata, '', True)
