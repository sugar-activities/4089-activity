#!/bin/env python

import unittest
import gobject
import glib
import gtk

import os, sys
sys.path += [os.path.join(os.path.dirname(__file__), '..')]

import ds
from source import *
from source_ds_rich import *

class TestDatastoreRichSource(unittest.TestCase):
    def setUp(self):
        ds.cleanup()

    def test_fetch_empty(self):
        s = DatastoreRichSource()
        s.connect('objects-updated', lambda x: gtk.main_quit())
        s.on_query({})
        gtk.main()

        self.assertEqual(0, s.get_count())

    def test_fetch_one_frame(self):
        request = { 'all_count': 3,
                    'out': [ { 'uid': 1, 'activity_id': '1' },
                             { 'uid': 2, 'activity_id': '2' },
                             { 'uid': 3, 'activity_id': '3' } ] }

        s = DatastoreRichSource()
        s.connect('objects-updated', lambda x: gtk.main_quit())
        s.on_query(request)
        gtk.main()

        self.assertEqual(request['out'][0], s.get_row(0))
        self.assertEqual(request['out'][1], s.get_row(1))
        self.assertEqual(request['out'][2], s.get_row(2))
        self.assertEqual(3, s.get_count())

    def test_fetch_several_frames(self):
        request = { 'all_count': 6,
                    'out': [ { 'uid': 3, 'activity_id': '3', 'BREAK': True },
                             { 'uid': 5, 'activity_id': '5' },
                             { 'uid': 6, 'activity_id': '6', 'BREAK': True },
                             { 'uid': 7, 'activity_id': '7' },
                             { 'uid': 8, 'activity_id': '8' },
                             { 'uid': 9, 'activity_id': '9' } ] }

        s = DatastoreRichSource()
        s.connect('objects-updated', lambda x: gtk.main_quit())
        s.on_query(request)
        gtk.main()

        self.assertEqual(request['out'][0], s.get_row(0))
        self.assertEqual(request['out'][1], s.get_row(1))
        self.assertEqual(request['out'][2], s.get_row(2))
        self.assertEqual(request['out'][3], s.get_row(3))
        self.assertEqual(request['out'][4], s.get_row(4))
        self.assertEqual(request['out'][5], s.get_row(5))
        self.assertEqual(6, s.get_count())

    def test_oid_by_activity_id(self):
        request = { 'all_count': 3,
                    'out': [ { 'uid': 1, 'activity_id': '1', 'timestamp': 1 },
                             { 'uid': 2, 'activity_id': '2', 'timestamp': 2 },
                             { 'uid': 3, 'activity_id': '2', 'timestamp': 3 },
                             { 'uid': 4, 'activity_id': '2', 'timestamp': 4 },
                             { 'uid': 5, 'activity_id': '3', 'timestamp': 5 } ] }

        s = DatastoreRichSource()
        s.connect('objects-updated', lambda x: gtk.main_quit())
        s.on_query(request)
        gtk.main()

        self.assertEqual(request['out'][0], s.get_row(0))
        self.assertEqual(request['out'][3], s.get_row(1))
        self.assertEqual(request['out'][4], s.get_row(2))
        self.assertEqual(3, s.get_count())

    def test_oid_by_bundle_id(self):
        request = { 'all_count': 3,
                    'out': [ { 'uid': 1, 'bundle_id': '1', 'activity_version': 1 },
                             { 'uid': 2, 'bundle_id': '2', 'activity_version': 2 },
                             { 'uid': 3, 'bundle_id': '2', 'activity_version': 3 },
                             { 'uid': 4, 'bundle_id': '2', 'activity_version': 4 },
                             { 'uid': 5, 'bundle_id': '3', 'activity_version': 5 } ] }

        s = DatastoreRichSource()
        s.connect('objects-updated', lambda x: gtk.main_quit())
        s.on_query(request)
        gtk.main()

        self.assertEqual(request['out'][0], s.get_row(0))
        self.assertEqual(request['out'][3], s.get_row(1))
        self.assertEqual(request['out'][4], s.get_row(2))
        self.assertEqual(3, s.get_count())

    def test_oid_by_uid(self):
        request = { 'all_count': 3,
                    'out': [ { 'uid': 1 },
                             { 'uid': 2 },
                             { 'uid': 3 } ] }

        s = DatastoreRichSource()
        s.connect('objects-updated', lambda x: gtk.main_quit())
        s.on_query(request)
        gtk.main()

        self.assertEqual(request['out'][0], s.get_row(0))
        self.assertEqual(request['out'][1], s.get_row(1))
        self.assertEqual(request['out'][2], s.get_row(2))
        self.assertEqual(3, s.get_count())

    def _test_load_bundle_id(self):
        request = { 'all_count': 1,
                    'out': [ { 'uid': 1, 'mime_type': 'application/vnd.olpc-sugar' },
                             { 'uid': 2, 'mime_type': 'application/vnd.olpc-sugar', 'bundle_id': 'org.sugarlabs.Library', 'activity_version': 2 } ] }

        s = DatastoreRichSource()
        s.connect('objects-updated', lambda x: gtk.main_quit())
        s.on_query(request)
        gtk.main()

        self.assertEqual('org.sugarlabs.Library', request['out'][0].get('bundle_id'))
        self.assertEqual(1, request['out'][0].get('activity_version'))
        self.assertEqual(request['out'][1], s.get_row(0))
        self.assertEqual(1, s.get_count())

    def _test_load_activity_version(self):
        request = { 'all_count': 1,
                    'out': [ { 'uid': 1, 'bundle_id': 'org.sugarlabs.Library' },
                             { 'uid': 2, 'bundle_id': 'org.sugarlabs.Library', 'activity_version': 2 } ] }

        s = DatastoreRichSource()
        s.connect('objects-updated', lambda x: gtk.main_quit())
        s.on_query(request)
        gtk.main()

        self.assertEqual(1, request['out'][0].get('activity_version'))
        self.assertEqual(request['out'][1], s.get_row(0))
        self.assertEqual(1, s.get_count())

    def test_is_newer_by_activity_id(self):
        request = { 'all_count': 3,
                    'out': [ { 'uid': 1, 'activity_id': '1', 'timestamp': 1 },
                             { 'uid': 2, 'activity_id': '1', 'timestamp': 2 },
                             { 'uid': 3, 'activity_id': '1', 'timestamp': 3 },

                             { 'uid': 4, 'activity_id': '2', 'timestamp': 3 },
                             { 'uid': 5, 'activity_id': '2', 'timestamp': 2 },
                             { 'uid': 6, 'activity_id': '2', 'timestamp': 1 },

                             { 'uid': 7, 'activity_id': '3', 'timestamp': 2 },
                             { 'uid': 8, 'activity_id': '3', 'timestamp': 2 } ] }

        s = DatastoreRichSource()
        s.connect('objects-updated', lambda x: gtk.main_quit())
        s.on_query(request)
        gtk.main()

        self.assertEqual(request['out'][2], s.get_row(0))
        self.assertEqual(request['out'][3], s.get_row(1))
        self.assertEqual(request['out'][6], s.get_row(2))
        self.assertEqual(3, s.get_count())

    def test_is_newer_by_activity_version(self):
        request = { 'all_count': 3,
                    'out': [ { 'uid': 1, 'bundle_id': '1', 'activity_version': 1 },
                             { 'uid': 2, 'bundle_id': '1', 'activity_version': 2 },
                             { 'uid': 3, 'bundle_id': '1', 'activity_version': 3 },

                             { 'uid': 4, 'bundle_id': '2', 'activity_version': 3 },
                             { 'uid': 5, 'bundle_id': '2', 'activity_version': 2 },
                             { 'uid': 6, 'bundle_id': '2', 'activity_version': 1 },

                             { 'uid': 7, 'bundle_id': '3', 'activity_version': 2 },
                             { 'uid': 8, 'bundle_id': '3', 'activity_version': 2 } ] }

        s = DatastoreRichSource()
        s.connect('objects-updated', lambda x: gtk.main_quit())
        s.on_query(request)
        gtk.main()

        self.assertEqual(request['out'][2], s.get_row(0))
        self.assertEqual(request['out'][3], s.get_row(1))
        self.assertEqual(request['out'][6], s.get_row(2))
        self.assertEqual(3, s.get_count())

    def test_signal_tags_before_fetch(self):
        request = { 'all_count': 3,
                    'out': [ { 'uid': 1, '_tags_': '[[["A"], "__tag_A__"]]' },
                             { 'uid': 2, '_tags_': '[[["A"], "__tag_A__"], [["B"], "__tag_B__"]]' },
                             { 'uid': 3, '_tags_': '[[["A"], "__tag_A__"], [["B"], "__tag_B__"], [["C"], "__tag_C__"]]' } ] }
        signals = []

        def tags_cb(s, type):
            signals.append(type)

        def timeout_cb():
            gtk.main_quit()

        s = DatastoreRichSource()
        s.connect('tags-updated', tags_cb)
        s.on_query(request)
        glib.timeout_add(500, timeout_cb)
        gtk.main()

        self.assertEqual([TAGS_OBJECTIVE, TAGS_SUBJECTIVE, TAGS_SOURCE], signals)
        self.assertEqual([{}, {('tag_A',): ('A', 3, True), ('tag_B',): ('B', 2, True), ('tag_C',): ('C', 1, True)}, {}], s.tags)

    def test_signal_before_query(self):
        request = { 'all_count': 1,
                    'out': [ { 'uid': 1 } ] }

        signals = []

        def signals_cb(s):
            signals.append(s)
            def timeout_cb():
                gtk.main_quit()
            glib.timeout_add(500, timeout_cb)

        s = DatastoreRichSource()
        s.connect('objects-updated', signals_cb)

        ds.call('Created', { 'uid': 1 })
        ds.call('Created', { 'uid': 2 })
        ds.call('Updated', { 'uid': 2 })
        ds.call('Created', { 'uid': 3 })
        ds.call('Deleted', { 'uid': 3 })

        s.on_query(request)
        gtk.main()

        self.assertEqual([s], signals)
        self.assertEqual(request['out'][0], s.get_row(0))
        self.assertEqual(1, s.get_count())

    def test_signal_after_query(self):
        request = { 'all_count': 1,
                'out': [ { 'uid': 1, '_tags_': '[[["A"], "__tag_A__"]]' } ] }

        tags = []
        signals = []

        def tags_cb(s, type):
            tags.append(type)

        def call_cb():
            ds.call('Created', { 'uid': 2, '_tags_': '[[["B"], "__tag_B__"]]' })
            ds.call('Created', { 'uid': 3, '_tags_': '[[["B"], "__tag_B__"]]', 'timestamp': 1 })
            ds.call('Updated', { 'uid': 3, '_tags_': '[[["C"], "__tag_C__"]]', 'timestamp': 2 })
            ds.call('Created', { 'uid': 4, '_tags_': '[[["C"], "__tag_C__"]]' })
            ds.call('Deleted', { 'uid': 4 })
            def timeout_cb():
                gtk.main_quit()
            glib.timeout_add(500, timeout_cb)
            return False

        def signal_cb(s):
            if not signals:
                gobject.idle_add(call_cb)
            signals.append(s)

        s = DatastoreRichSource()
        s.connect('tags-updated', tags_cb)
        s.connect('objects-updated', signal_cb)
        s.on_query(request)
        gtk.main()

        self.assertEqual([TAGS_OBJECTIVE, TAGS_SUBJECTIVE, TAGS_SOURCE,\
                          TAGS_SUBJECTIVE, TAGS_SUBJECTIVE, TAGS_SUBJECTIVE, \
                          TAGS_SUBJECTIVE, TAGS_SUBJECTIVE], tags)

        self.assertEqual([{}, {('tag_A',): ('A', 1, True), ('tag_B',): ('B', 1, True), ('tag_C',): ('C', 1, True)}, {}], s.tags)

        self.assertEqual(6, len(signals))

        self.assertEqual(request['out'][0], s.get_row(0))
        self.assertEqual({ 'buddies_count': 0, 'uid': 2, '_tags_': [(['B'], ['tag_B'])] }, s.get_row(1))
        self.assertEqual({ 'buddies_count': 0, 'uid': 3, '_tags_': [(['C'], ['tag_C'])], 'timestamp': 2 }, s.get_row(2))
        self.assertEqual(3, s.get_count())

    def test_signal_do_not_count_old_versions(self):
        request = { 'all_count': 1,
                'out': [ { 'uid': 1, 'bundle_id': 1, 'activity_version': 1, '_tags_': '[[["A"], "__tag_A__"]]' } ] }

        def signal_cb(s):
            ds.call('Created', { 'uid': 2, 'bundle_id': 1, 'activity_version': 1, '_tags_': '[[["B"], "__tag_B__"]]' })
            ds.call('Updated', { 'uid': 3, 'bundle_id': 1, 'activity_version': 1, '_tags_': '[[["C"], "__tag_C__"]]' })
            gtk.main_quit()

        s = DatastoreRichSource()
        s.connect('objects-updated', signal_cb)
        s.on_query(request)
        gtk.main()

        self.assertEqual(request['out'][0], s.get_row(0))
        self.assertEqual(1, s.get_count())

    def test_signal_do_not_notify_then_new_versions_do_not_change_tags(self):
        request = { 'all_count': 1,
                    'out': [ { 'uid': 1, 'activity_id': 1, 'timestamp': 1, '_tags_': '[[["A"], "__tag_A__"]]' } ] }

        errors = []

        def tags_cb(s, type):
            errors.append(type)

        semaphore = [1]

        def signal_cb(s):
            if len(semaphore):
                semaphore.pop()
                ds.call('Created', { 'uid': 2, 'activity_id': 1, 'timestamp': 2, '_tags_': '[[["A"], "__tag_A__"]]' })
                ds.call('Updated', { 'uid': 3, 'activity_id': 1, 'timestamp': 3, '_tags_': '[[["A"], "__tag_A__"]]' })

        def timeout_cb():
            gtk.main_quit()

        s = DatastoreRichSource()
        s.connect('tags-updated', tags_cb)
        s.connect('objects-updated', signal_cb)
        s.on_query(request)
        glib.timeout_add(500, timeout_cb)
        gtk.main()

        self.assertEqual(3, len(errors))

        self.assertEqual({ 'buddies_count': 0, 'uid': 3, 'activity_id': 1, 'timestamp': 3, '_tags_': [(['A',], ['tag_A'])] }, s.get_row(0))
        self.assertEqual(1, s.get_count())

    def test_signal_created_to_update_top_version_of_existed_oid(self):
        request = { 'all_count': 1,
                'out': [ { 'uid': 1, 'activity_id': 1, 'timestamp': 1, '_tags_': '[[["A"], "__tag_A__"]]' } ] }

        signals = []

        def call_cb():
            ds.call('Created', { 'uid': 2, 'activity_id': 1, 'timestamp': 2, '_tags_': '[[["B"], "__tag_B__"]]' })
            return False

        def signal_cb(s):
            if not signals:
                gobject.idle_add(call_cb)
            else:
                gtk.main_quit()
            signals.append(s)

        s = DatastoreRichSource()
        s.connect('objects-updated', signal_cb)
        s.on_query(request)
        gtk.main()

        self.assertEqual({('tag_B',): ('B', 1, True)}, s.tags[TAGS_SUBJECTIVE])

        self.assertEqual({ 'buddies_count': 0, 'uid': 2, 'activity_id': 1, 'timestamp': 2, '_tags_': [(['B',], ['tag_B'])] }, s.get_row(0))
        self.assertEqual(1, s.get_count())

    def test_signal_updated_previous_version_and_move_it_to_the_top(self):
        request = { 'all_count': 1,
                'out': [ { 'uid': 1, 'activity_id': 1, 'timestamp': 1, '_tags_': '[[["A"], "__tag_A__"]]' },
                         { 'uid': 2, 'activity_id': 1, 'timestamp': 2, '_tags_': '[[["B"], "__tag_B__"]]' } ] }

        signals = []

        def call_cb():
            self.assertEqual(request['out'][1], s.get_row(0))
            self.assertEqual(1, s.get_count())
            ds.call('Updated', { 'uid': 1, 'activity_id': 1, 'timestamp': 3, '_tags_': '[[["C"], "__tag_C__"]]' })
            return False

        def signal_cb(s):
            if not signals:
                gobject.idle_add(call_cb)
            else:
                gtk.main_quit()
            signals.append(s)

        s = DatastoreRichSource()
        s.connect('objects-updated', signal_cb)
        s.on_query(request)
        gtk.main()

        self.assertEqual({('tag_C',): ('C', 1, True)}, s.tags[TAGS_SUBJECTIVE])

        self.assertEqual({ 'buddies_count': 0, 'uid': 1, 'activity_id': 1, 'timestamp': 3, '_tags_': [(['C',], ['tag_C'])] }, s.get_row(0))
        self.assertEqual(1, s.get_count())

    def test_signal_delete_top_version_and_fallback_to_previous(self):
        request = { 'all_count': 1,
                    'out'      : [ { 'uid': 1, 'activity_id': 1, 'timestamp': 1, '_tags_': '[[["A"], "__tag_A__"]]' },
                                   { 'uid': 2, 'activity_id': 1, 'timestamp': 2, '_tags_': '[[["B"], "__tag_B__"]]' } ],
                    'order_out': [ { 'uid': 1, 'activity_id': 1, 'timestamp': 1, '_tags_': '[[["A"], "__tag_A__"]]' } ] }

        signals = []

        def call_cb():
            self.assertEqual(request['out'][1], s.get_row(0))
            self.assertEqual(1, s.get_count())
            ds.call('Deleted', { 'uid': 2 })
            return False

        def signal_cb(s):
            if not signals:
                gobject.idle_add(call_cb)
            else:
                gtk.main_quit()
            signals.append(s)

        s = DatastoreRichSource()
        s.connect('objects-updated', signal_cb)
        s.on_query(request)
        gtk.main()

        self.assertEqual({('tag_A',): ('A', 1, True)}, s.tags[TAGS_SUBJECTIVE])

        self.assertEqual(request['out'][0], s.get_row(0))
        self.assertEqual(1, s.get_count())

    def test_indexes_creare(self):
        request = { 'all_count': 3,
                    'out': [ { 'uid': 1, 'title': '4', 'timestamp': 8 },
                             { 'uid': 2, 'title': '6', 'timestamp': 7 },
                             { 'uid': 3, 'title': '5', 'timestamp': 9 } ] }

        s = DatastoreRichSource()
        s.connect('objects-updated', lambda x: gtk.main_quit())

        s.on_query(request)
        gtk.main()
        self.assertEqual(request['out'][0], s.get_row(0))
        self.assertEqual(request['out'][1], s.get_row(1))
        self.assertEqual(request['out'][2], s.get_row(2))
        self.assertEqual(3, s.get_count())

        def order_cb(column, order):
            s.set_order(column, order)
            return False

        gobject.idle_add(order_cb, 'uid', gtk.SORT_DESCENDING)
        gtk.main()
        self.assertEqual(request['out'][2], s.get_row(0))
        self.assertEqual(request['out'][1], s.get_row(1))
        self.assertEqual(request['out'][0], s.get_row(2))
        self.assertEqual(3, s.get_count())

        gobject.idle_add(order_cb, 'title', gtk.SORT_ASCENDING)
        gtk.main()
        self.assertEqual(request['out'][0], s.get_row(0))
        self.assertEqual(request['out'][2], s.get_row(1))
        self.assertEqual(request['out'][1], s.get_row(2))
        self.assertEqual(3, s.get_count())

        gobject.idle_add(order_cb, 'title', gtk.SORT_DESCENDING)
        gtk.main()
        self.assertEqual(request['out'][1], s.get_row(0))
        self.assertEqual(request['out'][2], s.get_row(1))
        self.assertEqual(request['out'][0], s.get_row(2))
        self.assertEqual(3, s.get_count())

        gobject.idle_add(order_cb, 'timestamp', gtk.SORT_ASCENDING)
        gtk.main()
        self.assertEqual(request['out'][1], s.get_row(0))
        self.assertEqual(request['out'][0], s.get_row(1))
        self.assertEqual(request['out'][2], s.get_row(2))
        self.assertEqual(3, s.get_count())

        gobject.idle_add(order_cb, 'timestamp', gtk.SORT_DESCENDING)
        gtk.main()
        self.assertEqual(request['out'][2], s.get_row(0))
        self.assertEqual(request['out'][0], s.get_row(1))
        self.assertEqual(request['out'][1], s.get_row(2))
        self.assertEqual(3, s.get_count())

    def test_indexes_update(self):
        request = { 'all_count': 1,
                    'out': [ { 'uid': 2, 'title': '2', 'timestamp': 2 } ] }

        s = DatastoreRichSource()
        s.connect('objects-updated', lambda x: gtk.main_quit())

        def order_cb(column, order):
            s.set_order(column, order)
            return False

        s.on_query(request)
        gtk.main()
        gobject.idle_add(order_cb, 'title', gtk.SORT_ASCENDING)
        gtk.main()
        gobject.idle_add(order_cb, 'timestamp', gtk.SORT_ASCENDING)
        gtk.main()
        gobject.idle_add(order_cb, 'uid', gtk.SORT_ASCENDING)
        gtk.main()

        def add_cb():
            ds.call('Created', { 'uid': 3, 'title': '4', 'timestamp': 3 })
            ds.call('Created', { 'uid': 4, 'title': '3', 'timestamp': 4 })
            return False
        gobject.idle_add(add_cb)
        gtk.main()

        gobject.idle_add(order_cb, 'title', gtk.SORT_DESCENDING)
        gtk.main()
        self.assertEqual({ 'buddies_count': 0, 'uid': 3, 'title': '4', 'timestamp': 3 }, s.get_row(0))
        self.assertEqual({ 'buddies_count': 0, 'uid': 4, 'title': '3', 'timestamp': 4 }, s.get_row(1))
        self.assertEqual(request['out'][0], s.get_row(2))
        self.assertEqual(3, s.get_count())

        gobject.idle_add(order_cb, 'timestamp', gtk.SORT_ASCENDING)
        gtk.main()
        self.assertEqual(request['out'][0], s.get_row(0))
        self.assertEqual({ 'buddies_count': 0, 'uid': 3, 'title': '4', 'timestamp': 3 }, s.get_row(1))
        self.assertEqual({ 'buddies_count': 0, 'uid': 4, 'title': '3', 'timestamp': 4 }, s.get_row(2))
        self.assertEqual(3, s.get_count())

        gobject.idle_add(order_cb, 'uid', gtk.SORT_DESCENDING)
        gtk.main()
        self.assertEqual({ 'buddies_count': 0, 'uid': 4, 'title': '3', 'timestamp': 4 }, s.get_row(0))
        self.assertEqual({ 'buddies_count': 0, 'uid': 3, 'title': '4', 'timestamp': 3 }, s.get_row(1))
        self.assertEqual(request['out'][0], s.get_row(2))
        self.assertEqual(3, s.get_count())

        def update_cb():
            ds.call('Updated', { 'uid': 3, 'title': '1', 'timestamp': 5 })
            return False
        gobject.idle_add(update_cb)
        gtk.main()

        gobject.idle_add(order_cb, 'title', gtk.SORT_ASCENDING)
        gtk.main()
        self.assertEqual({ 'buddies_count': 0, 'uid': 3, 'title': '1', 'timestamp': 5 }, s.get_row(0))
        self.assertEqual(request['out'][0], s.get_row(1))
        self.assertEqual({ 'buddies_count': 0, 'uid': 4, 'title': '3', 'timestamp': 4 }, s.get_row(2))
        self.assertEqual(3, s.get_count())

        gobject.idle_add(order_cb, 'timestamp', gtk.SORT_ASCENDING)
        gtk.main()
        self.assertEqual(request['out'][0], s.get_row(0))
        self.assertEqual({ 'buddies_count': 0, 'uid': 4, 'title': '3', 'timestamp': 4 }, s.get_row(1))
        self.assertEqual({ 'buddies_count': 0, 'uid': 3, 'title': '1', 'timestamp': 5 }, s.get_row(2))
        self.assertEqual(3, s.get_count())

        gobject.idle_add(order_cb, 'uid', gtk.SORT_DESCENDING)
        gtk.main()
        self.assertEqual({ 'buddies_count': 0, 'uid': 4, 'title': '3', 'timestamp': 4 }, s.get_row(0))
        self.assertEqual({ 'buddies_count': 0, 'uid': 3, 'title': '1', 'timestamp': 5 }, s.get_row(1))
        self.assertEqual(request['out'][0], s.get_row(2))
        self.assertEqual(3, s.get_count())

        def delete_cb():
            ds.call('Deleted', { 'uid': 4 })
            return False
        gobject.idle_add(delete_cb)
        gtk.main()

        gobject.idle_add(order_cb, 'title', gtk.SORT_ASCENDING)
        gtk.main()
        self.assertEqual({ 'buddies_count': 0, 'uid': 3, 'title': '1', 'timestamp': 5 }, s.get_row(0))
        self.assertEqual(request['out'][0], s.get_row(1))
        self.assertEqual(2, s.get_count())

        gobject.idle_add(order_cb, 'timestamp', gtk.SORT_ASCENDING)
        gtk.main()
        self.assertEqual(request['out'][0], s.get_row(0))
        self.assertEqual({ 'buddies_count': 0, 'uid': 3, 'title': '1', 'timestamp': 5 }, s.get_row(1))
        self.assertEqual(2, s.get_count())

        gobject.idle_add(order_cb, 'uid', gtk.SORT_DESCENDING)
        gtk.main()
        self.assertEqual({ 'buddies_count': 0, 'uid': 3, 'title': '1', 'timestamp': 5 }, s.get_row(0))
        self.assertEqual(request['out'][0], s.get_row(1))
        self.assertEqual(2, s.get_count())

    def test_updated_wo_changing_mtime(self):
        request = { 'all_count': 1,
                'out': [ { 'uid': 1, 'timestamp': 1 } ] }

        signals = []

        def call_cb():
            ds.call('Updated', { 'uid': 1, 'activity_id': 1, 'timestamp': 1 })
            return False

        def signal_cb(s):
            if not signals:
                gobject.idle_add(call_cb)
            else:
                gtk.main_quit()
            signals.append(s)

        s = DatastoreRichSource()
        s.connect('objects-updated', signal_cb)
        s.on_query(request)
        gtk.main()

if __name__ == '__main__':
    unittest.main()
