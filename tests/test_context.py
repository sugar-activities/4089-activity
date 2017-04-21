#!/bin/env python

import unittest

import os, sys
sys.path += [os.path.join(os.path.dirname(__file__), '..')]

from source import *

class TestContext(unittest.TestCase):
    pass

if __name__ == '__main__':
    unittest.main()
