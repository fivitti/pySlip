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

    def test_copy_list(self):
        """Check 'l_poly = list(poly)' gets us a new list.

        At a few places in pySlip we need a copy of a list, not the original.
        We do this by:
            l_poly = list(poly)
            new_poly = l_poly[:]
        Is the final ...[:] required?
        """

        # try to make copy without [:]
        old_list = [1, 2, 3, 4]
        old_list_id = id(old_list)
        new_list = list(old_list)
        new_list_id = id(new_list)

        # make sure we DO have a copy
        msg = ("'new_list = list(old_list)' DOESN'T give us a copy?\n"
                   "id(old_list)=%d, id(new_list)=%d"
               % (old_list_id, new_list_id))
        self.assertTrue(old_list_id != new_list_id, msg)

    def test_copy(self):
        """Test 'new_list = old_list[:]' does give us a copy.

        At a few places in pySlip we need a copy of a list, not the original.
        We do this by:
            new_poly = l_poly[:]
        """

        # try to make a copy with [:]
        old_list = [1, 2, 3, 4]
        old_list_id = id(old_list)
        new_list = old_list[:]
        new_list_id = id(new_list)

        msg = ("'new_list = old_list[:]' DOESN'T give us a copy?\n"
                   "id(old_list)=%d, id(new_list)=%d"
               % (old_list_id, new_list_id))
        self.assertTrue(old_list_id != new_list_id, msg)

    def test_copy2(self):
        """Check 'list(poly)' is faster than 'poly[:]'.

        At a few places in pySlip we need a copy of a list and we do:
            new_poly = list(poly)
        Is this faster than:
            new_poly = poly[:]
        """

        loops = 10000000

        # create the old list
        old_list = [1, 2, 3, 4, 5, 6]

        # time list() approach
        start = time.time()
        for _ in xrange(loops):
            new_list = list(old_list)
        list_delta = time.time() - start

        # time copy approach
        start = time.time()
        for _ in xrange(loops):
            new_list = old_list[:]
        copy_delta = time.time() - start

        msg = ("'old_list[:]' is SLOWER than 'list(old_list)'?\n"
                "old_list[:]=%.1f, list(old_list)=%.1f "
                "(list() is %.2f times faster)"
               % (list_delta, copy_delta,
                   (copy_delta/list_delta)))
        self.assertTrue(list_delta > copy_delta, msg)

    def test_dispatch_faster(self):
        """Test that dispatch is faster than inline if/elif/else.

        In pySlip we do all placement via an 'exec' instead of if/else code.
        The assumption is that this is FASTER.

        That is, this:
            dispatch = {0: 'x += 2',
                        1: 'x -= 1',
                        2: 'x = 4'}
            exec dispatch[i]
        is faster than:
            if i == 0:
                x += 2
            elif i == 1:
                x -= 1
            else:
                x = 4
        """

        import random

        loops = 1000000

        dispatch = {0: 'x += 2',
                    1: 'x -= 1',
                    2: 'x = 4'}
        for key in dispatch:
            dispatch[key] = compile(dispatch[key], 'string', 'exec')

        start = time.time()
        for _ in xrange(loops):
            x = 5
            i = 1
            exec dispatch[i]
        dispatch_delta = time.time() - start

        start = time.time()
        for _ in xrange(loops):
            x = 5
            i = 1
            if i == 0:
                x += 2
            elif i == 1:
                x -= 1
            else:
                x = 4
        elif_delta = time.time() - start

        msg = ("INLINE: if/else is faster than 'exec dispatch[i]'?\n"
                   "dispatch=%.2fs, elif=%.2fs (elif is %.1f times faster)"
               % (dispatch_delta, elif_delta, dispatch_delta/elif_delta))
        self.assertTrue(dispatch_delta < elif_delta, msg)

    def test_dispatch_faster2(self):
        """Test that dispatch is faster than function if/elif/else.

        In pySlip we do all placement via an 'exec' instead of if/else code.
        The assumption is that this is FASTER.

        That is, this:
            dispatch = {0: 'x += 2',
                        1: 'x -= 1',
                        2: 'x = 4'}
            exec dispatch[i]
        is faster than:
            def doit(i):
                if i == 0:
                    x += 2
                elif i == 1:
                    x -= 1
                else:
                    x = 4
            doit(i)
        """

        import random

        loops = 1000000

        dispatch = {0: 'x += 2',
                    1: 'x -= 1',
                    2: 'x = 4'}
        for key in dispatch:
            dispatch[key] = compile(dispatch[key], 'string', 'exec')

        start = time.time()
        for _ in xrange(loops):
            x = 5
            i = 1
            exec dispatch[i]
        dispatch_delta = time.time() - start

        def doit(i, x):
            if i == 0:
                x += 2
            elif i == 1:
                x -= 1
            else:
                x = 4
            return x

        start = time.time()
        for _ in xrange(loops):
            x = 5
            i = 1
            x = doit(i, x)
        elif_delta = time.time() - start

        msg = ("FUNCTION: if/else is faster than 'exec dispatch[i]'?\n"
                   "dispatch=%.2fs, elif=%.2fs (elif is %.1f times faster)"
               % (dispatch_delta, elif_delta, dispatch_delta/elif_delta))
        self.assertTrue(dispatch_delta < elif_delta, msg)

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
