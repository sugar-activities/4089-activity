import gobject
import zipfile

MANIFEST = """
[Activity]
name = Library
bundle_id = org.sugarlabs.Library
exec = sugar-activity activity.Activity
icon = activity-library
activity_version = 1
license = GPLv2+
"""

OBJECTS = {}
SUBSCRIBERS = None

class FakeMetadata:
    def get_dictionary(self):
        return self.dic

    def __init__(self, dic):
        self.dic = dic

class FakeDSObject:
    def get_file_path(self):
        zip = zipfile.ZipFile('.test', 'w')
        zip.writestr('foobar.activity/activity/activity.info', MANIFEST)
        zip.close()
        return '.test'

    def __init__(self, uid):
        self.metadata = OBJECTS.get(uid, {})

    def get_metadata(self):
        return FakeMetadata(self.metadata)

    def destroy(self):
        pass

def cleanup():
    global OBJECTS, SUBSCRIBERS
    OBJECTS = {}
    SUBSCRIBERS = { 'Created': [], 'Updated': [], 'Deleted': [] }

def call(signal, obj):
    for i in SUBSCRIBERS[signal]:
        OBJECTS[obj['uid']] = obj
        i(obj['uid'])

def connect(signal, cb):
    SUBSCRIBERS[signal].append(cb)

def disconnect(subscriber):
    pass

def find(request, properties, frame=(0, 0),
        reply_handler=None, error_handler=None):
    if request.get('order'):
        out = request.get('order_out')
    else:
        out = request.get('out')

    if out:
        def idle_cb():
            rs = []
            for i in range(frame[0], min(frame[0]+frame[1], len(out))):
                rs.append(out[i])
                if out[i].get('BREAK'):
                    break
            reply_handler(rs, request['all_count'])
            return False
    else:
        def idle_cb():
            error_handler(None)
            return False

    gobject.idle_add(idle_cb)

def get(uid):
    return FakeDSObject(uid)

def get_properties(uid):
    return OBJECTS.get(uid, {})
