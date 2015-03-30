#!/usr/bin/env python

"""
Test PySlip assumptions.

We make some assumptions in pySlip about relative speeds
of various operations.  Make sure those assumptions hold.
"""


import os
import time
import unittest


class TestAssumptions(unittest.TestCase):

    def test_copy_faster(self):
        """Test that a[:] copy is slower than copy.copy(a)."""

        import copy

        loops = 1000000

        a = [1,2,3,4,5,6,7,8,9,0]   # fake a Z-order list

        start = time.time()
        for _ in xrange(loops):
            b = copy.copy(a)
        copy_delta = time.time() - start

        start = time.time()
        for _ in xrange(loops):
            b = a[:]
        clone_delta = time.time() - start

        msg = ('Copy() is faster than clone[:]?\ncopy=%.2fs, clone=%.2fs'
               % (copy_delta, clone_delta))
        self.assertTrue(clone_delta < copy_delta, msg)

    def test_tuple_faster(self):
        """Test unpacking tuple is faster than data object attributes."""

        class DataObj(object):
            def __init__(self, *args, **kwargs):
                if len(args) > 0:
                    msg = 'DataObj() must be called with keyword args ONLY!'
                    raise RuntimeError(msg)

                self.__dict__ = kwargs

        tuple_obj = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
        data_obj = DataObj(one=1, two=2, three=3, four=4, five=5,
                           six=6, seven=7, eight=8, nine=9, ten=10)

        loops = 100000#0

        # time tuple object
        start = time.time()
        for _ in xrange(loops):
            (one, two, three, four, five, six, seven, eight, nine, ten) = tuple_obj
        tuple_delta = time.time() - start

        # time data object
        start = time.time()
        for _ in xrange(loops):
            one = data_obj.one
            two = data_obj.two
            three = data_obj.three
            four = data_obj.four
            five = data_obj.five
            six = data_obj.six
            seven = data_obj.seven
            eight = data_obj.eight
            nine = data_obj.nine
            ten = data_obj.ten
        data_delta = time.time() - start

        msg = ('Data object is faster than tuple?\ndata=%.2fs, tuple=%.2fs'
               % (data_delta, tuple_delta))
        self.assertTrue(tuple_delta < data_delta, msg)

################################################################################

if __name__ == '__main__':
    suite = unittest.makeSuite(TestAssumptions,'test')
    runner = unittest.TextTestRunner()
    runner.run(suite)
