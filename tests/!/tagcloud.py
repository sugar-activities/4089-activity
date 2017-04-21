#!/usr/bin/env python

import gtk

from tag_cloud import *

class TextViewDemo(gtk.Window):
    def __init__(self, parent=None):
        # Create the toplevel window
        gtk.Window.__init__(self)
        try:
            self.set_screen(parent.get_screen())
        except AttributeError:
            self.connect('destroy', lambda *w: gtk.main_quit())

        box = gtk.HBox()
        box.set_size_request(200,-1)
        self.add(box)

        self.e = gtk.Entry()
        box.pack_start(self.e)

        view1 = Cloud(0)
        view1.on_set_tags(
                {
                    ('A',): ('A', 10, True),
                    ('B',): ('B', 1, True)
                    },
                10)
        def foo(cloud, tag):
            self.e.props.text = tag
        view1.connect('tag-selected', foo)
        box.pack_start(view1)

        self.show_all()

def main():
    TextViewDemo()
    gtk.main()

if __name__ == '__main__':
    main()

