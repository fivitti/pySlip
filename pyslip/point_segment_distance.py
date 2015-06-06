#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module to test the point_segment_distance() and point_near_polyline() functions.

A polyline is a series of points [(x1,y1), (x2,y2), ...].
"""

import math


def close_to_polyline(polyline, point, delta):
    """Decide if point is within 'delta' of the given polyline.

    polyline  iterable of (x, y) point tuples
    point     point (x, y)
    delta     maximum distance before 'not close enough'

    Returns True if point within delta distance of the polyline.
    """

    last_pp = polyline[0]
    for pp in polyline[1:]:
        if point_segment_distance(point, last_pp, pp) <= delta:
            return True
        last_pp = pp

    return False

def point_segment_distance_OLD(point, s1, s2):
    """Get distance from a point to segment (s1, s2).

    point   tuple (x, y)
    s1, s2  tuples (x, y) of segment endpoints

    Return the distance squared.
    """

    (ptx, pty) = point
    (s1x, s1y) = s1
    (s2x, s2y) = s2

    px = s2x - s1x
    py = s2y - s1y

    something = px*px + py*py

    u = ((ptx - s1x)*px + (pty - s1y)*py) / float(something)

    if u > 1:
        u = 1
    elif u < 0:
        u = 0

    x = s1x + u*px
    y = s1y + u*py

    dx = x - ptx
    dy = y - pty

    dist = math.sqrt(dx*dx + dy*dy)

    return dist

def point_segment_distance(point, s1, s2):
    """Get distance from a point to segment (s1, s2).

    point   tuple (x, y)
    s1, s2  tuples (x, y) of segment endpoints

    Return the distance squared.
    """

    (ptx, pty) = point
    (s1x, s1y) = s1
    (s2x, s2y) = s2

    px = s2x - s1x
    py = s2y - s1y

    u = ((ptx - s1x)*px + (pty - s1y)*py) / float(px**2 + py**2)

    if u > 1:
        u = 1
    elif u < 0:
        u = 0

    dx = s1x + u*px - ptx
    dy = s1y + u*py - pty

    return dx**2 + dy**2


if __name__ == '__main__':
    import unittest
    import time

    Loops = 10000000

    start = time.time()
    for i in xrange(Loops):
        a = point_segment_distance_OLD((1,1), (0,1), (0,-1))
    delta = time.time() - start
    print('Orig: %.2fs' % delta)

    start = time.time()
    for i in xrange(Loops):
        a = point_segment_distance((1,1), (0,1), (0,-1))
    delta = time.time() - start
    print('   Y: %.2fs' % delta)

    TestFunc = point_segment_distance

    NumPlaces = 11


    class TestAssumptions(unittest.TestCase):                                        
                                                                                         
        def test_simple1(self):                                                    
            """Check simple point/segment cases.
            
            This case is a vertical segment of 2 units length.
            All points should be 1 unit from the segment.
            """

            seg1 = (0,1)
            seg2 = (0,-1)
            points = [(1,1),(1,0),(1,-1),(0,-2),(-1,-1),(-1,0),(-1,1),(0,2)]
            expected = 1.0**2

            for point in points:
                dist = TestFunc(point, seg1, seg2)
                msg = ('Segment [%s,%s], point %s distance should be %s, got %s'
                        % (str(seg1), str(seg2), str(point),
                            str(expected), str(dist)))

                self.assertEqual(dist, expected, msg=msg)

            # reverse segment, test again
            (seg1, seg2) = (seg2, seg1)
            for point in points:
                dist = TestFunc(point, seg1, seg2)
                msg = ('Segment [%s,%s], point %s distance should be %s, got %s'
                        % (str(seg1), str(seg2), str(point),
                            str(expected), str(dist)))

                self.assertEqual(dist, expected, msg=msg)

        def test_simple2(self):                                                    
            """Check simple point/segment cases.
            
            This case is a horizontal segment of 2 units length.
            All points should be 1 unit from the segment.
            """

            seg1 = (-1,0)
            seg2 = (1,0)
            points = [(0,1),(1,1),(2,0),(1,-1),(0,-1),(-1,-1),(-2,0),(-1,1)]
            expected = 1.0**2

            for point in points:
                dist = TestFunc(point, seg1, seg2)
                msg = ('Segment [%s,%s], point %s distance should be %s, got %s'
                        % (str(seg1), str(seg2), str(point),
                            str(expected), str(dist)))

                self.assertEqual(dist, expected, msg=msg)

            # reverse segment, test again
            (seg1, seg2) = (seg2, seg1)
            for point in points:
                dist = TestFunc(point, seg1, seg2)
                msg = ('Segment [%s,%s], point %s distance should be %s, got %s'
                        % (str(seg1), str(seg2), str(point),
                            str(expected), str(dist)))

                self.assertEqual(dist, expected, msg=msg)

        def test_simple3(self):                                                    
            """Check simple point/segment cases.
            
            This case is a slant segment.
            All points should be about 0.707 units from the segment.
            """

            seg1 = (-1,-1)
            seg2 = (1,1)
            points = [(1,0),(0,-1),(-1,0),(0,1)]
            expected = 0.707106781187**2

            for point in points:
                dist = TestFunc(point, seg1, seg2)
                msg = ('Segment [%s,%s], point %s distance should be %s, got %s'
                        % (str(seg1), str(seg2), str(point),
                            str(expected), str(dist)))

                self.assertAlmostEqual(dist, expected, places=NumPlaces, msg=msg)

            # reverse segment, test again
            (seg1, seg2) = (seg2, seg1)
            for point in points:
                dist = TestFunc(point, seg1, seg2)
                msg = ('Segment [%s,%s], point %s distance should be %s, got %s'
                        % (str(seg1), str(seg2), str(point),
                            str(expected), str(dist)))

                self.assertAlmostEqual(dist, expected, places=NumPlaces, msg=msg)

        def test_simple4(self):                                                    
            """Check simple point/segment cases.
            
            This case is an opposite slant segment.
            All points should be about 0.707 units from the segment.
            """

            seg1 = (-1,1)
            seg2 = (1,-1)
            points = [(1,0),(0,-1),(-1,0),(0,1)]
            expected = 0.707106781187**2

            for point in points:
                dist = TestFunc(point, seg1, seg2)
                msg = ('Segment [%s,%s], point %s distance should be %s, got %s'
                        % (str(seg1), str(seg2), str(point),
                            str(expected), str(dist)))

                self.assertAlmostEqual(dist, expected, places=NumPlaces, msg=msg)

            # reverse segment, test again
            (seg1, seg2) = (seg2, seg1)
            for point in points:
                dist = TestFunc(point, seg1, seg2)
                msg = ('Segment [%s,%s], point %s distance should be %s, got %s'
                        % (str(seg1), str(seg2), str(point),
                            str(expected), str(dist)))

                self.assertAlmostEqual(dist, expected, places=NumPlaces, msg=msg)

        def test_simple5(self):                                                    
            """Check simple point/segment cases.
            
            This case is a horizontal segment.
            All points should be on the line, ie distance is 0.0.
            """

            seg1 = (-1,0)
            seg2 = (1,0)
            points = [seg1, (0,0), seg2]
            expected = 0.0**2

            for point in points:
                dist = TestFunc(point, seg1, seg2)
                msg = ('Segment [%s,%s], point %s distance should be %s, got %s'
                        % (str(seg1), str(seg2), str(point),
                            str(expected), str(dist)))

                self.assertAlmostEqual(dist, expected, places=NumPlaces, msg=msg)

            # reverse segment, test again
            (seg1, seg2) = (seg2, seg1)
            for point in points:
                dist = TestFunc(point, seg1, seg2)
                msg = ('Segment [%s,%s], point %s distance should be %s, got %s'
                        % (str(seg1), str(seg2), str(point),
                            str(expected), str(dist)))

                self.assertAlmostEqual(dist, expected, places=NumPlaces, msg=msg)

        def test_simple6(self):                                                    
            """Check simple point/segment cases.
            
            This case is a vertical segment.
            All points should be on the line, ie distance is 0.0.
            """

            seg1 = (0,1)
            seg2 = (0,-1)
            points = [seg1, (0,0), seg2]
            expected = 0.0**2

            for point in points:
                dist = TestFunc(point, seg1, seg2)
                msg = ('Segment [%s,%s], point %s distance should be %s, got %s'
                        % (str(seg1), str(seg2), str(point),
                            str(expected), str(dist)))

                self.assertAlmostEqual(dist, expected, places=NumPlaces, msg=msg)

            # reverse segment, test again
            (seg1, seg2) = (seg2, seg1)
            for point in points:
                dist = TestFunc(point, seg1, seg2)
                msg = ('Segment [%s,%s], point %s distance should be %s, got %s'
                        % (str(seg1), str(seg2), str(point),
                            str(expected), str(dist)))

                self.assertAlmostEqual(dist, expected, places=NumPlaces, msg=msg)

        def test_simple7(self):                                                    
            """Check simple point/segment cases.
            
            This case is a slant segment.
            All points should be on the line, ie distance is 0.0.
            """

            seg1 = (1,1)
            seg2 = (-1,-1)
            points = [seg1, (0,0), seg2]
            expected = 0.0**2

            for point in points:
                dist = TestFunc(point, seg1, seg2)
                msg = ('Segment [%s,%s], point %s distance should be %s, got %s'
                        % (str(seg1), str(seg2), str(point),
                            str(expected), str(dist)))

                self.assertAlmostEqual(dist, expected, places=NumPlaces, msg=msg)

            # reverse segment, test again
            (seg1, seg2) = (seg2, seg1)
            for point in points:
                dist = TestFunc(point, seg1, seg2)
                msg = ('Segment [%s,%s], point %s distance should be %s, got %s'
                        % (str(seg1), str(seg2), str(point),
                            str(expected), str(dist)))

                self.assertAlmostEqual(dist, expected, places=NumPlaces, msg=msg)

        def test_simple8(self):                                                    
            """Check simple point/segment cases.  Not straddling axes.
            NE quadrant.  Test horizontal, vertical and slant cases.
            """

            seg1 = (2,2)
            seg2 = (3,2)
            points = [(1,2),(2,3),(2.5,3),(3,3),(4,2),(3,1),(2.3,1),(2,1)]
            expected = 1.0**2

            for point in points:
                dist = TestFunc(point, seg1, seg2)
                msg = ('Segment [%s,%s], point %s distance should be %s, got %s'
                        % (str(seg1), str(seg2), str(point),
                            str(expected), str(dist)))

                self.assertAlmostEqual(dist, expected, places=NumPlaces, msg=msg)

            # reverse segment, test again
            (seg1, seg2) = (seg2, seg1)
            for point in points:
                dist = TestFunc(point, seg1, seg2)
                msg = ('Segment [%s,%s], point %s distance should be %s, got %s'
                        % (str(seg1), str(seg2), str(point),
                            str(expected), str(dist)))

                self.assertAlmostEqual(dist, expected, places=NumPlaces, msg=msg)


    suite = unittest.makeSuite(TestAssumptions,'test')                           
    runner = unittest.TextTestRunner()                                           
    runner.run(suite)
