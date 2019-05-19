import time

LOOP = 1000000

def tile_cycle(num, maxnum, start=0):
    while num > 0:
        yield start
        start += 1
        if start >= maxnum:
            start = 0
        num -= 1

tile_cycle_c1 = list(tile_cycle(20, 10))
#print('list(tile_cycle(20, 10))=%s' % str(tile_cycle_c1))

start = time.time()
for _ in range(LOOP):
    c = list(tile_cycle(20, 10))
delta = time.time() - start
print('%d times, list(tile_cycle(20, 10)) took %.2fs' % (LOOP, delta))

tile_cycle_c2 = list(tile_cycle(20, 10, 3))
#print('list(tile_cycle(20, 10, 3))=%s' % str(tile_cycle_c2))

start = time.time()
for _ in range(LOOP):
    c = list(tile_cycle(20, 10, 3))
delta = time.time() - start
print('%d times, list(tile_cycle(20, 10, 3)) took %.2fs' % (LOOP, delta))

###################

def tile_cycle_list(num, maxnum, start=0):
    result = []
    while num > 0:
        result.append(start)
        start += 1
        if start >= maxnum:
            start = 0
        num -= 1
    return result

tile_cycle_list_c1 = tile_cycle_list(20, 10)
#print('tile_cycle_list(20, 10)=%s' % str(tile_cycle_list_c1))

start = time.time()
for _ in range(LOOP):
    c = tile_cycle_list(20, 10)
delta = time.time() - start
print('%d times, tile_cycle_list(20, 10) took %.2fs' % (LOOP, delta))

tile_cycle_list_c2 = tile_cycle_list(20, 10, 3)
#print('tile_cycle_list(20, 10, 3)=%s' % str(tile_cycle_list_c2))

start = time.time()
for _ in range(LOOP):
    c = tile_cycle_list(20, 10, 3)
delta = time.time() - start
print('%d times, tile_cycle_list(20, 10, 3) took %.2fs' % (LOOP, delta))

###################

def tile_cycle_list2(num, maxnum, start=0):
    result = []
    while num > 0:
        result.append(start)
        start = (start + 1) % maxnum
        num -= 1
    return result

tile_cycle_list2_c1 = tile_cycle_list2(20, 10)
#print('tile_cycle_list2(20, 10)=%s' % str(tile_cycle_list2_c1))

start = time.time()
for _ in range(LOOP):
    c = tile_cycle_list2(20, 10)
delta = time.time() - start
print('%d times, tile_cycle_list2(20, 10) took %.2fs' % (LOOP, delta))

tile_cycle_list2_c2 = tile_cycle_list2(20, 10, 3)
#print('tile_cycle_list2(20, 10, 3)=%s' % str(tile_cycle_list2_c2))

start = time.time()
for _ in range(LOOP):
    c = tile_cycle_list2(20, 10, 3)
delta = time.time() - start
print('%d times, tile_cycle_list2(20, 10, 3) took %.2fs' % (LOOP, delta))

###################

from itertools import cycle, dropwhile, islice

def tile_iter_list(L, maxnum, start=0):
    cycled = cycle(L)
    skipped = dropwhile(lambda x: x != start, cycled)
    sliced = islice(skipped, None, maxnum)
    return list(sliced)

L = range(10)

tile_iter_list_c1 = tile_iter_list(L, 20)
#print('tile_iter_list(L, 20)=%s' % str(tile_iter_list_c1))

start = time.time()
for _ in range(LOOP):
    c = tile_iter_list(L, 20)
delta = time.time() - start
print('%d times, tile_iter_list(L, 20) took %.2fs' % (LOOP, delta))

tile_iter_list_c2 = tile_iter_list(L, 20, 3)
#print('tile_iter_list(L, 20, 3)=%s' % str(tile_iter_list_c2))

start = time.time()
for _ in range(LOOP):
    c = tile_iter_list(L, 20, 3)
delta = time.time() - start
print('%d times, tile_iter_list(L, 20, 3) took %.2fs' % (LOOP, delta))

###################
# sanity check

if tile_cycle_list_c1 != tile_cycle_c1:
    print('tile_cycle_list: bad result, tile_cycle_list_c1=%s, expected %s' % (str(tile_cycle_list_c1), str(tile_cycle_c1)))
if tile_cycle_list_c2 != tile_cycle_c2:
    print('tile_cycle_list: bad result, tile_cycle_list_c2=%s, expected %s' % (str(tile_cycle_list_c2), str(tile_cycle_c2)))

if tile_cycle_list2_c1 != tile_cycle_c1:
    print('tile_iter_list: bad result, tile_cycle_list2_c1=%s, expected %s' % (str(tile_cycle_list2_c1), str(tile_cycle_c1)))
if tile_cycle_list2_c2 != tile_cycle_c2:
    print('tile_iter_list: bad result, tile_cycle_list2_c2=%s, expected %s' % (str(tile_cycle_list2_c2), str(tile_cycle_c2)))

if tile_iter_list_c1 != tile_cycle_c1:
    print('tile_iter_list: bad result, tile_iter_list_c1=%s, expected %s' % (str(tile_iter_list_c1), str(tile_cycle_c1)))
