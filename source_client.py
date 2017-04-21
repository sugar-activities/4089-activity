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

class ClientSource(Source):
    def __init__(self):
        Source.__init__(self)
        self._active = False

    def get_active(self):
        pass

    def set_active(self, value):
        pass

    def query(self):
        pass

    def get_count(self):
        """ Returns number of objects """
        pass

    def get_row(self, offset, frame_range, cb, *args):
        """ Get object """
        pass

    def get_object(self, uid, cb, *args):
        pass

    def post_object(self, object):
        pass

    def get_order(self):
        # stub
        pass

    def set_order(self, column, order):
        # stub
        pass
