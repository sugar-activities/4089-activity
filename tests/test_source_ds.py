#!/bin/env python

import unittest
import gobject
import glib
import gtk

import os, sys
sys.path += [os.path.join(os.path.dirname(__file__), '..')]

import port.json as json

import ds
from source import *
from source_ds import *

class TestDatastoreSource(unittest.TestCase):
    def setUp(self):
        ds.cleanup()

    def test_update_tags(self):
        s = DatastoreSource()
        self.assertEqual({TAGS_OBJECTIVE: {('mime_type',): 1, ('mime_type', 'A'): 1, ('mime_type', 'A', 'B'): 1}},
                s.update_tags({ 'mime_type': 'A/B' }, +1))
        self.assertEqual({TAGS_OBJECTIVE: {('mime_type',): 1, ('mime_type', 'A'): 1, ('mime_type', 'A', 'B'): 1}},
                s.update_tags({ 'mime_type': 'A/B' }, +1))
        self.assertEqual({TAGS_OBJECTIVE: {('mime_type',): 1, ('mime_type', 'B'): 1, ('mime_type', 'B', 'A'): 1}},
                s.update_tags({ 'mime_type': 'B/A' }, +1))
        self.assertEqual([{('mime_type',): (NAMES['mime_type'], 3, False),
                           ('mime_type', 'A'): ('A', 2, False),
                           ('mime_type', 'A', 'B'): ('B', 2, True),
                           ('mime_type', 'B'): ('B', 1, False),
                           ('mime_type', 'B', 'A'): ('A', 1, True)}, {}, {}], s.tags)

        s = DatastoreSource()
        self.assertEqual({TAGS_OBJECTIVE: {('activity',): 1, ('activity', 'foo.bar'): 1}},
                s.update_tags({ 'activity': 'foo.bar' }, +1))
        self.assertEqual({TAGS_OBJECTIVE: {('activity',): 1, ('activity', 'foo.bar'): 1}},
                s.update_tags({ 'activity': 'foo.bar' }, +1))
        self.assertEqual({TAGS_OBJECTIVE: {('activity',): 1, ('activity', 'bar.foo'): 1}},
                s.update_tags({ 'activity': 'bar.foo' }, +1))
        self.assertEqual([{('activity',): (NAMES['activity'], 3, False),
                           ('activity', 'foo.bar'): ('foo.bar', 2, True),
                           ('activity', 'bar.foo'): ('bar.foo', 1, True)}, {}, {}], s.tags)

        s = DatastoreSource()
        self.assertEqual({TAGS_OBJECTIVE: {('traits',): 1, ('traits', 'foo'): 1, ('traits', 'foo', 'bar'): 1}},
                s.update_tags({ '_traits_': {'foo': ('pretty_bar', 'bar')} }, +1))
        self.assertEqual({TAGS_OBJECTIVE: {('traits',): 1, ('traits', 'foo'): 1, ('traits', 'foo', 'bar'): 1}},
                s.update_tags({ '_traits_': {'foo': ('pretty_bar', 'bar')} }, +1))
        self.assertEqual({TAGS_OBJECTIVE: {('traits',): 1, ('traits', 'bar'): 1, ('traits', 'bar', 'foo'): 1}},
                s.update_tags({ '_traits_': {'bar': ('pretty_foo', 'foo')} }, +1))
        self.assertEqual([{('traits',): (NAMES['traits'], 3, False),
                           ('traits', 'foo'): ('foo', 2, False),
                           ('traits', 'foo', 'bar'): ('pretty_bar', 2, True),
                           ('traits', 'bar'): ('bar', 1, False),
                           ('traits', 'bar', 'foo'): ('pretty_foo', 1, True)}, {}, {}], s.tags)

        s = DatastoreSource()
        self.assertEqual({TAGS_SUBJECTIVE: {('A',): 1, ('X',): 2, ('X', 'Y'): 1, ('X', 'Y', 'Z'): 1}},
                s.update_tags({ '_tags_': [(('pretty_A',), ('A',)), (('pretty_X',), ('X',)), (('pretty_X', 'pretty_Y', 'pretty_Z'), ('X', 'Y', 'Z'))] }, +1))
        self.assertEqual({TAGS_SUBJECTIVE: {('A',): 1}},
                s.update_tags({ '_tags_': [(('pretty_A',), ('A',))] }, +1))
        self.assertEqual({TAGS_SUBJECTIVE: {('A',): 1, ('A', 'B'): 1}},
                s.update_tags({ '_tags_': [(('pretty_A', 'pretty_B'), ('A', 'B'))] }, +1))
        self.assertEqual({TAGS_SUBJECTIVE: {('A',): 1, ('A', 'B'): 1, ('A', 'B', 'C'): 1}},
                s.update_tags({ '_tags_': [(('pretty_A', 'pretty_B', 'pretty_C'), ('A', 'B', 'C'))] }, +1))
        self.assertEqual({TAGS_SUBJECTIVE: {('B',): 1, ('B', 'C'): 1}},
                s.update_tags({ '_tags_': [(('pretty_B', 'pretty_C'), ('B', 'C'))] }, +1))
        self.assertEqual([{}, {('A',): ('pretty_A', 4, True),
                               ('A', 'B'): ('pretty_B', 2, True),
                               ('A', 'B', 'C'): ('pretty_C', 1, True),
                               ('B',): ('pretty_B', 1, True),
                               ('B', 'C'): ('pretty_C', 1, True),
                               ('X',): ('pretty_X', 2, True),
                               ('X', 'Y'): ('pretty_Y', 1, True),
                               ('X', 'Y', 'Z'): ('pretty_Z', 1, True)}, {}], s.tags)

    def test_diff_tags(self):
        s = DatastoreSource()

        self.assertEqual({}, s.diff_tags({ '_tags_': [(('A',), ('A',))], 'activity': 'foo.bar', 'mime_type': 'M/T', '_traits_': {'key': ('value', 'value')} },
                                         { '_tags_': [(('A',), ('A',))], 'activity': 'foo.bar', 'mime_type': 'M/T', '_traits_': {'key': ('value', 'value')} }))

        self.assertEqual({TAGS_OBJECTIVE:  {('activity', 'foo.bar'): -1,
                                            ('activity', 'bar.foo'): +1,
                                            ('mime_type', 'M'): -1, ('mime_type', 'M', 'T'): -1,
                                            ('mime_type', 'T'): +1, ('mime_type', 'T', 'M'): +1,
                                            ('traits', 'foo'): -1, ('traits', 'foo', 'bar'): -1,
                                            ('traits', 'bar'): +1, ('traits', 'bar', 'foo'): +1},
                          TAGS_SUBJECTIVE: {('A',): -1, ('B',): +1}},
                               s.diff_tags({ '_tags_': [(('A',), ('A',))], 'activity': 'foo.bar', 'mime_type': 'M/T', '_traits_': {'foo': ('bar', 'bar')} },
                                           { '_tags_': [(('B',), ('B',))], 'activity': 'bar.foo', 'mime_type': 'T/M', '_traits_': {'bar': ('foo', 'foo')} }))

    def test_update_tags_with_selected(self):
        s = DatastoreSource()
        s.selected_tags = [[], [('A',)], []]
        self.assertEqual({},
                s.update_tags({ '_tags_': [(('A',), ('A',))] }, +1))
        self.assertEqual({TAGS_SUBJECTIVE: {('B',): 1}},
                s.update_tags({ '_tags_': [(('B',), ('B',))] }, +1))
        self.assertEqual({TAGS_SUBJECTIVE: {('C',): 1, ('C', 'D'): 1}},
                s.update_tags({ '_tags_': [(('C', 'D'), ('C', 'D'))] }, +1))
        self.assertEqual([{}, {('B',): ('B', 1, True), ('C',): ('C', 1, True), ('C', 'D'): ('D', 1, True)}, {}], s.tags)

        s = DatastoreSource()
        s.selected_tags = [[], [('A',), ('B',)], []]
        self.assertEqual({},
                s.update_tags({ '_tags_': [(('A',), ('A',)), (('B',), ('B',))] }, +1))
        self.assertEqual({},
                s.update_tags({ '_tags_': [(('B',), ('B',)), (('A',), ('A',))] }, +1))
        self.assertEqual({TAGS_SUBJECTIVE: {('A', 'B'): 1}},
                s.update_tags({ '_tags_': [(('A', 'B'), ('A', 'B'))] }, +1))
        self.assertEqual({TAGS_SUBJECTIVE: {('A', 'B'): 1, ('A', 'B', 'C'): 1}},
                s.update_tags({ '_tags_': [(('A', 'B', 'C'), ('A', 'B', 'C'))] }, +1))
        self.assertEqual({TAGS_SUBJECTIVE: {('B', 'A'): 1}},
                s.update_tags({ '_tags_': [(('B', 'A'), ('B', 'A'))] }, +1))
        self.assertEqual({TAGS_SUBJECTIVE: {('B', 'A'): 1, ('B', 'A', 'C'): 1}},
                s.update_tags({ '_tags_': [(('B', 'A', 'C'), ('B', 'A', 'C'))] }, +1))
        self.assertEqual([{}, {('A', 'B'): ('B', 2, True),
                               ('A', 'B', 'C'): ('C', 1, True),
                               ('B', 'A'): ('A', 2, True),
                               ('B', 'A', 'C'): ('C', 1, True)}, {}], s.tags)

        s = DatastoreSource()
        s.selected_tags = [[], [('AA', 'BB'), ('BB', 'AA')], []]
        self.assertEqual({},
                s.update_tags({ '_tags_': [(('AA',), ('AA',)), (('BB',), ('BB',))] }, +1))
        self.assertEqual({},
                s.update_tags({ '_tags_': [(('BB',), ('BB',)), (('AA',), ('AA',))] }, +1))
        self.assertEqual({},
                s.update_tags({ '_tags_': [(('AA', 'BB'), ('AA', 'BB')), (('BB', 'AA'), ('BB', 'AA'))] }, +1))
        self.assertEqual({},
                s.update_tags({ '_tags_': [(('BB','AA'),)*2, (('AA', 'BB'),)*2] }, +1))
        self.assertEqual({TAGS_SUBJECTIVE: {('AA', 'CC'): 1}},
                s.update_tags({ '_tags_': [(('AA', 'CC'),)*2] }, +1))
        self.assertEqual({TAGS_SUBJECTIVE: {('AA', 'CC'): 1, ('AA', 'CC', 'DD'): 1}},
                s.update_tags({ '_tags_': [(('AA', 'CC', 'DD'),)*2] }, +1))
        self.assertEqual({TAGS_SUBJECTIVE: {('AA', 'BB', 'CC'): 1}},
                s.update_tags({ '_tags_': [(('AA', 'BB', 'CC'),)*2] }, +1))
        self.assertEqual({TAGS_SUBJECTIVE: {('AA', 'BB', 'CC'): 1, ('AA', 'BB', 'CC', 'DD'): 1}},
                s.update_tags({ '_tags_': [(('AA', 'BB', 'CC', 'DD'),)*2] }, +1))
        self.assertEqual([{}, {('AA', 'CC'): ('CC', 2, True),
                               ('AA', 'CC', 'DD'): ('DD', 1, True),
                               ('AA', 'BB', 'CC'): ('CC', 2, True),
                               ('AA', 'BB', 'CC', 'DD'): ('DD', 1, True)}, {}], s.tags)

    def test_query(self):
        s = DatastoreSource()
        s.selected_tags = [[], [], []]
        self.assertEqual({}, s.query())

        s = DatastoreSource()
        s.selected_tags = [[('mime_type', 'A', 'B')], [], []]
        self.assertEqual({'mime_type': ['A/B']}, s.query())

        s = DatastoreSource()
        s.selected_tags = [[('mime_type', 'A', 'B'), ('mime_type', 'B', 'A')], [], []]
        self.assertEqual({'mime_type': ['A/B', 'B/A']}, s.query())

        s = DatastoreSource()
        s.selected_tags = [[('activity', 'A.B')], [], []]
        self.assertEqual({'activity': 'A.B'}, s.query())

        s = DatastoreSource()
        s.selected_tags = [[('activity', 'A.B'), ('activity', 'B.A')], [], []]
        self.assertEqual({'activity': 'B.A'}, s.query())

        s = DatastoreSource()
        s.selected_tags = [[('traits', 'foo', 'bar')], [], []]
        self.assertEqual({'query': 'bar'}, s.query())

        s = DatastoreSource()
        s.selected_tags = [[('traits', 'foo', 'bar'), ('traits', 'bar', 'foo')], [], []]
        self.assertEqual({'query': 'bar AND foo'}, s.query())

        s = DatastoreSource()
        s.selected_tags = [[], [('A',)], [], []]
        self.assertEqual({'query': '__A__*'}, s.query())

        s = DatastoreSource()
        s.selected_tags = [[], [('A',), ('A', 'B'), ('A', 'B', 'C'), ('D',)], [], []]
        self.assertEqual({'query': '__A__* AND __A__B__* AND __A__B__C__* AND __D__*'}, s.query())

        s = DatastoreSource()
        s.selected_tags = [[], [], [], []]
        s.search = 'foo'
        self.assertEqual({'query': 'foo*'}, s.query())

    def test_same_names_in_tags(self):
        s = DatastoreSource()
        s.selected_tags = [[], [('A',)], []]
        self.assertEqual({TAGS_SUBJECTIVE: {('A', 'B'): 1}},
                s.update_tags({ '_tags_': [(('A', 'B'), ('A', 'B'))] }, +1))
        self.assertEqual({TAGS_SUBJECTIVE: {('B',): 1}},
                s.update_tags({ '_tags_': [(('B',), ('B',))] }, +1))
        self.assertEqual({TAGS_SUBJECTIVE: {('B',): 1}},
                s.update_tags({ '_tags_': [(('B',), ('B',))] }, +1))
        self.assertEqual([{}, { ('A', 'B'): ('B', 1, True),
                                ('B',): ('B', 2, True) }, {}], s.tags)

    def test_encode_fields(self):
        s = DatastoreSource()

        self.assertEqual({}, s.encode_fields({}))

        self.assertEqual(
                { 'buddies': json.dumps( { 'uid1': ('nick1', 'color1'),
                                           'uid2': ('nick2', 'color2'),
                                           'uid3': ('nick3', 'color3') } ) },

                s.encode_fields( { 'buddies': [ ('uid1', 'nick1', 'color1' ),
                                                ('uid2', 'nick2', 'color2' ),
                                                ('uid3', 'nick3', 'color3' ) ] } ) )
        self.assertEqual(
                { '_tags_': json.dumps( [ (('pretty_A',), '__tag_pretty_A__'),
                                          (('pretty_A', 'pretty_B'), '__tag_pretty_A__pretty_B__') ] ) },

                s.encode_fields( { '_tags_': [ (('pretty_A',), ('old_A',)),
                                               (('pretty_A', 'pretty_B'), ('old_A', 'old_B')) ] } ) )

        self.assertEqual(
                { 'mime_type': 'text/plain',
                  'author': json.dumps(('pretty_value1', '__trait_pretty_value1__')),
                  'genre': json.dumps(('pretty_value2', '__trait_pretty_value2__')) },

                s.encode_fields( { 'mime_type': 'text/plain', 
                                   'author': 'pretty_value1',
                                   'genre': 'pretty_value2' } ) )

    def test_decode_fields(self):
        s = DatastoreSource()

        self.assertEqual({'buddies_count': 0}, s.decode_fields({}))

        self.assertEqual(
                { 'buddies': [ ('uid1', 'nick1', 'color1' ),
                               ('uid2', 'nick2', 'color2' ),
                               ('uid3', 'nick3', 'color3' ) ],
                  'buddies_count': 3 },

                s.decode_fields( { 'buddies': json.dumps( { 'uid1': ('nick1', 'color1'),
                                                            'uid2': ('nick2', 'color2'),
                                                            'uid3': ('nick3', 'color3') } ) } ) )
        self.assertEqual(
                { 'buddies_count': 0,
                  '_tags_': [ (['pretty_A',], ['tag_pretty_A',]),
                              (['pretty_A', 'pretty_B'], ['tag_pretty_A', 'pretty_B']) ] },

                s.decode_fields( { '_tags_': json.dumps( [ (('pretty_A',), '__tag_pretty_A__'),
                                                           (('pretty_A', 'pretty_B'), '__tag_pretty_A__pretty_B__') ] ) } ) )

        self.assertEqual(
                { 'buddies_count': 0,
                  'mime_type': 'text/plain',
                  '_traits_': { 'author': ('pretty_value1', '__trait_pretty_value1__'),
                                'genre': ('pretty_value2', '__trait_pretty_value2__') },
                  'author': 'pretty_value1',
                  'genre': 'pretty_value2' },

                s.decode_fields( { 'mime_type': 'text/plain',
                                   'author': json.dumps(('pretty_value1', '__trait_pretty_value1__')),
                                   'genre': json.dumps(('pretty_value2', '__trait_pretty_value2__')) } ) )

if __name__ == '__main__':
    unittest.main()
