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

""" Various shell related routines """

import os
import gio
import logging

from sugar import mime
from sugar.graphics.icon import get_icon_file_name
from sugar.bundle.activitybundle import ActivityBundle
from sugar.util import LRU
from sugar.activity import activityfactory
from sugar import env
from sugar.activity.activityhandle import ActivityHandle

_bundles = {}
_bundles_by_mime = {}

def activate(metadata, bundle_id=None):
    if bundle_id is None:
        activities = get_bundles_by_metadata(metadata)
        if not activities:
            logging.warning('No activity can open this object, %s.' %
                    metadata.get('mime_type', None))
            return
        bundle_id = activities[0].get_bundle_id()

    bundle = get_bundle(bundle_id)
    if not bundle:
        logging.warning('activate: cannot get bundle for %s' % bundle_id)
        return

    activity_id = metadata.get('activity_id')
    object_id = metadata['uid']

    if activity_id:
        handle = ActivityHandle(object_id=object_id,
                                activity_id=activity_id)
        activityfactory.create(bundle, handle)
    else:
        activityfactory.create_with_object_id(bundle, object_id)

def get_icon_filename(metadata=None, activity=None, mime_type=None):
    """ Get filename for object icon """

    file_name = None
    bundle_id = activity

    if not bundle_id and metadata:
        bundle_id = metadata.get('activity')

    if not bundle_id and metadata:
        bundle_id = metadata.get('bundle_id')

    if bundle_id:
        bundle = get_bundle(bundle_id)
        file_name = bundle and bundle.get_icon()

    if not file_name and mime_type:
        file_name = _get_icon_for_mime(mime_type)

    if not file_name and metadata:
        file_name = _get_icon_for_mime(metadata.get('mime_type'))

    if file_name is None:
        file_name = get_icon_file_name('application-octet-stream')

    return file_name

def get_bundle(bundle_id):
    if not _bundles:
        dirs = []

        try:
            from jarabe import config
            dirs.append(config.activities_path)
        except ImportError:
            if os.environ.has_key('SUGAR_ACTIVITIES'):
                dirs.extend(os.environ['SUGAR_ACTIVITIES'].split(':'))

        for i in dirs + [env.get_user_activities_path()]:
            _scan_directory(i)

    return _bundles.get(bundle_id)

def get_bundles_by_mime(mime_type):
    out = _bundles_by_mime.get(mime_type, [])

    for parent_mime in mime.get_mime_parents(str(mime_type)):
        for i in get_bundles_by_mime(parent_mime):
            if i not in out:
                out.append(i)

    return out

def get_bundles_by_metadata(metadata):
    out = []

    bundle_id = metadata.get('activity')
    if bundle_id:
        bundle = get_bundle(bundle_id)
        if bundle:
            out.append(bundle)

    mime_type = metadata.get('mime_type')
    if mime_type:
        for i in get_bundles_by_mime(mime_type):
            if i not in out:
                out.append(i)

    return out

def _scan_directory(path):
    if not os.path.isdir(path):
        return

    for f in os.listdir(path):
        if not f.endswith('.activity'):
            continue

        try:
            bundle_dir = os.path.join(path, f)
            bundle = ActivityBundle(bundle_dir)

            _bundles[bundle.get_bundle_id()] = bundle

            for i in (bundle.get_mime_types() or []):
                _bundles_by_mime[i] = _bundles_by_mime.get(i, [])
                _bundles_by_mime[i].append(bundle)

        except Exception, e:
            logging.error('Error while processing installed activity ' \
                          'bundle: %s, %s, %s' % (f, e.__class__, e))

def _get_icon_for_mime(mime_type):
    generic_types = mime.get_all_generic_types()
    for generic_type in generic_types:
        if mime_type in generic_type.mime_types:
            file_name = get_icon_file_name(generic_type.icon)
            if file_name is not None:
                return file_name

    icons = gio.content_type_get_icon(mime_type)
    logging.debug('icons for this file: %r' % icons.props.names)
    for icon_name in icons.props.names:
        file_name = get_icon_file_name(icon_name)
        if file_name is not None:
            return file_name
