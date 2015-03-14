#! /usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import bintrees
import struct

def bstwalk(node, idx, rowstart, depth, blocksize, output):
    offset = rowstart + idx * blocksize
    output.seek(offset)
    key = node.key
    value = node.value
    if key == '':
        output.write(struct.pack('>HH', 0, 1))
    else:
        output.write(struct.pack('>HH', ord(key), value))
    left = node.left
    right = node.right
    if left:
        bstwalk(left, (idx << 1), rowstart + 2 ** depth * blocksize, depth + 1, blocksize, output)
    if right:
        bstwalk(right, (idx << 1) | 0x01, rowstart + 2 ** depth * blocksize, depth + 1, blocksize, output)

class Cell:
    base = 0
    check = 0

class Tail:
    suffix = None
    data = None

class DA:
    def __init__(self, am):
        self.am = am
        self.sak = sorted(am.keys())
        self.cells = [None] * 16
        self.tails = [Tail()]
        self.set_base(1, 1)
        self.set_check(1, 1)

    def dump(self):
        for i in range(len(self.cells)):
            print(i, self.get_base(i), self.get_check(i))
        for i in range(len(self.tails)):
            k = ''
            if self.get_tail(i) != None and self.get_tail(i).suffix != None:
                for j in self.get_tail(i).suffix:
                    if j == 1:
                        continue
                    k += self.sak[j - 1]
            print(i, k, self.get_tail(i).data)

    def get_root(self):
        return 1

    def get_base(self, s):
        while s >= len(self.cells):
            self.cells.extend([None] * len(self.cells))
        if self.cells[s] == None:
            self.cells[s] = Cell()
        return self.cells[s].base

    def set_base(self, s, v):
        while s >= len(self.cells):
            self.cells.extend([None] * len(self.cells))
        if self.cells[s] == None:
            self.cells[s] = Cell()
        self.cells[s].base = v

    def get_check(self, s):
        while s >= len(self.cells):
            self.cells.extend([None] * len(self.cells))
        if self.cells[s] == None:
            self.cells[s] = Cell()
        return self.cells[s].check

    def set_check(self, s, v):
        while s >= len(self.cells):
            self.cells.extend([None] * len(self.cells))
        if self.cells[s] == None:
            self.cells[s] = Cell()
        self.cells[s].check = v

    def get_tail_index(self, s):
        return -self.get_base(s)

    def set_tail_index(self, s, v):
        self.set_base(s, -v)

    def alpha_map_char(self, c):
        if c in self.am:
            return self.am[c]
        return None

    def alpha_map_str(self, str):
        ams = []
        for i in str:
            c = self.alpha_map_char(i)
            if c == None:
                return ams
            ams.append(c)
        return ams

    def get_tail(self, i):
        if len(self.tails) <= i:
            self.tails.append(Tail())
        return self.tails[i]

    def tail_add_suffix(self, suffix):
        t = Tail()
        t.suffix = suffix
        self.tails.append(t)
        return len(self.tails) - 1

    def tail_get_suffix(self, idx):
        if len(self.tails) <= idx:
            self.tails.append(Tail())
        return self.tails[idx].suffix

    def tail_set_suffix(self, idx, suffix):
        if len(self.tails) <= idx:
            self.tails.append(Tail())
        self.tails[idx].suffix = suffix

    def tail_get_data(self, idx):
        if len(self.tails) <= idx:
            self.tails.append(Tail())
        return self.tails[idx].data

    def tail_set_data(self, idx, data):
        if len(self.tails) <= idx:
            self.tails.append(Tail())
        self.tails[idx].data = data

    def find_common(self, s1, s2):
        c = []
        for i in range(min(len(s1), len(s2))):
            if s1[i] != s2[i]:
                return (c, s1[i:], s2[i:])
            c.append(s1[i])
        return (c, s1[i + 1:], s2[i + 1:])

    def x_check(self, lst):
        i = 0
        q = 1
        while i < len(lst):
            c = lst[i]
            i += 1
            n = self.get_check(q + c)
            if n > 0:
                i = 0
                q += 1
        return q

    def children(self, p):
        c = []
        for i in self.am.keys():
            if self.get_check(self.get_base(p) + self.am[i]) == p:
                c.append(self.am[i])
        return c

    def insert(self, k, v):
        s = self.get_root()
        ak = self.alpha_map_str(k) + [1]
        for i in range(len(ak)):
            c = ak[i]
            if c == None:
                exit(-1)
            n = self.get_base(s) + c
            if self.get_check(n) == 0: # empty slot
                sfx = ak[i + 1:]
                t = self.tail_add_suffix(sfx)
                self.tail_set_data(t, v)
                self.set_tail_index(n, t)
                self.set_check(n, s)
                return
            elif self.get_check(n) > 0 and self.get_check(n) != s: # found a slot collisio
                # solve the collision
                ch1 = self.children(self.get_check(n))
                ch2 = self.children(s) + [c]
                if len(ch1) < len(ch2):
                    ch0 = ch1
                    cad = self.get_check(n)
                    np = self.x_check(ch1)
                else:
                    cad = s
                    np = self.x_check(ch2)
                    ch0 = ch2[0: -1] # drop current input char, we will calculate it when inserting again later
                ob = self.get_base(cad)
                self.set_base(cad, np)
                for nn in ch0:
                    self.set_base(np + nn, self.get_base(ob + nn))
                    self.set_check(np + nn, self.get_check(ob + nn))
                    for ch in self.children(ob + nn):
                        self.set_check(self.get_base(ob + nn) + ch, np + nn)
                    self.set_base(ob + nn, 0)
                    self.set_check(ob + nn, 0)
                # insert the new value
                self.insert(k, v)
                return
            elif self.get_base(n) < 0: # found a tail slot
                sfx = ak[i + 1:]
                ot = self.get_tail_index(n)
                osfx = self.tail_get_suffix(ot)
                (pfx, ors, rs) = self.find_common(osfx, sfx)
                if len(ors) == 0 and len(rs) == 0:
                    # they are the same one?
                    self.tail_set_data(ot, v)
                else:
                    last = n
                    last_parent = s
                    for p in pfx:
                        self.set_check(last, last_parent)
                        pb = self.x_check([p])
                        self.set_base(last, pb)
                        last_parent = last
                        last = self.get_base(last) + p
                    orsh = ors[0]
                    orst = ors[1:]
                    rsh = rs[0]
                    rst = rs[1:]
                    self.set_check(last, last_parent)
                    ns = self.x_check([orsh, rsh])
                    self.set_base(last, ns)
                    sors = ns + orsh
                    self.tail_set_suffix(ot, orst)
                    self.set_tail_index(sors, ot)
                    self.set_check(sors, last)
                    srs = ns + rsh
                    nt = self.tail_add_suffix(rst)
                    self.tail_set_data(nt, v)
                    self.set_tail_index(srs, nt)
                    self.set_check(srs, last)
                return
            else:
                s = n

    def retrieval(self, k):
        s = self.get_root()
        ak = self.alpha_map_str(k) + [1]
        for c in ak:
            n = self.get_base(s) + c
            if self.get_base(n) < 0:
                return self.tail_get_data(self.get_tail_index(n))
            if self.get_check(n) != s:
                return None
            s = n

    def fwrite(self, path):
        with open(path, 'wb') as output:
            output.write(struct.pack('>BBB', 0xda, 0x72, 0x1e)) # magic key 'datrie'
            output.write(struct.pack('>B', 0x01)) # version
            offset = 4
            tail_start = offset
            tail_offsets = []
            for i in range(len(self.tails)):
                t = self.tails[i]
                if t != None and t.data != None:
                    tail_offsets.append(offset)
                    sfx = []
                    for ch in t.suffix:
                        sfx.append((ch & 0xFF00) >> 8)
                        sfx.append(ch & 0xFF)
                    suffix = bytes(sfx)
                    data = t.data
                    if len(suffix) == 0:
                        output.write(struct.pack('>HH%ds' % len(data), len(suffix), len(data), data))
                        offset += struct.calcsize('>HH%ds' % len(data))
                    else:
                        output.write(struct.pack('>H%dsH%ds' % (len(suffix), len(data)), len(suffix), suffix, len(data), data))
                        offset += struct.calcsize('>H%dsH%ds' % (len(suffix), len(data)))
                else:
                    tail_offsets.append(0)
            if offset % 4 != 0:
                offset += 4 - offset % 4
                output.seek(offset)
            da_start = offset
            da_end = len(self.cells) - 1
            for i in range(len(self.cells) - 1, 0, -1):
                if self.cells[i] != None and self.cells[i].check != 0:
                    da_end = i
                    break
            for i in range(da_end + 1):
                if self.cells[i] == None:
                    output.write(struct.pack('>ii', 0, 0))
                elif self.cells[i].base < 0:
                    output.write(struct.pack('>ii', -tail_offsets[-self.cells[i].base], self.cells[i].check))
                else:
                    output.write(struct.pack('>ii', self.cells[i].base, self.cells[i].check))
                offset += struct.calcsize('>ii')
            if offset % 4 != 0:
                offset += 4 - offset % 4
                output.seek(offset)
            am_start = offset
            bstsize = 0
            for i in range(self.am._root.balance + 1):
                bstsize += 2 ** i
            output.truncate(offset + 4 + bstsize * struct.calcsize('>HH'))
            output.seek(offset)
            output.write(struct.pack('>BBH', self.am._root.balance + 1, 2, 2)) # depth, key size, value size
            bstwalk(self.am._root, 0, offset + 4, 0, struct.calcsize('>HH'), output)
            offset += 4 + bstsize * struct.calcsize('>HH')
            if offset % 4 != 0:
                offset += 4 - offset % 4
                output.seek(offset)
            index_start = offset
            output.write(struct.pack('>IIII', tail_start, da_start, am_start, index_start))

def genval(hint, loc):
    hint = hint.encode('utf-8')
    if len(hint) == 0:
        return struct.pack('>Bff', len(hint), float(loc[1]), float(loc[0]))
    else:
        return struct.pack('>B%dsff' % len(hint), len(hint), hint, float(loc[1]), float(loc[0]))

def loadsrc(src):
    f = open(src)
    dat = {}
    for l in f:
        if len(l) > 1:
            i = l[:-1].split(',')
            d = (i[0], i[1], i[2], i[3], i[4])
            if i[2] in dat:
                tmp = dat[i[2]]
                if isinstance(tmp, list):
                    tmp.append(d)
                else:
                    dat[i[2]] = [tmp, d]
            else:
                dat[i[2]] = d
    lms = {}
    for d in dat.keys():
        if isinstance(dat[d], list):
            for i in dat[d]:
                loc = (i[3], i[4])
                if i[0] != i[1]:
                    if i[1] != i[2]:
                        lms[i[0] + i[1] + i[2]] = genval('', loc)
                        lms[i[1] + i[2]] = genval(i[0], loc)
                        lms[i[2] + '/' + i[0] + i[1]] = genval('', loc)
                    else:
                        lms[i[0] + i[1]] = genval('', loc)
                        lms[i[1] + '/' + i[0]] = genval('', loc)
                else:
                    if i[1] != i[2]:
                        lms[i[1] + i[2]] = genval('', loc)
                        lms[i[2] + '/' + i[1]] = genval('', loc)
                    else:
                        lms[i[0]] = genval('', loc)
        else:
            i = dat[d]
            loc = (i[3], i[4])
            if i[0] != i[1]:
                if i[1] != i[2]:
                    lms[i[0] + i[1] + i[2]] = genval('', loc)
                    lms[i[1] + i[2]] = genval(i[0], loc)
                    hint = i[0] + i[1]
                else:
                    lms[i[0] + i[1]] = genval('', loc)
                    hint = i[0]
            else:
                if i[1] != i[2]:
                    lms[i[1] + i[2]] = genval('', loc)
                    hint = i[1]
                else:
                    hint = ''
            lms[d] = genval(hint, loc)
            # dat.append((k, v))
    return lms

def calc_alpha_map(lst):
    m = {}
    for l in lst:
        for i in l:
            m[i] = 0
    bst = bintrees.AVLTree()
    bst.insert('\1', 1)
    sk = sorted(m.keys())
    for i in range(len(sk)):
        bst.insert(sk[i], i + 2)
    return bst

def main(src, dst):
    kvs = loadsrc(src)
    # print(sorted(kvs.keys()))
    am = calc_alpha_map(kvs.keys())
    print(am)
    da = DA(am)
    for (k, v) in kvs.items():
        da.insert(k, v)
    da.fwrite(dst)
    # da.dump()
    # for (k, v) in kvs.items():
    #     print(k, da.retrieval(k))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'A double array trie building tool')
    parser.add_argument('src', action = 'store', help = 'Source file')
    parser.add_argument('dst', action = 'store', help = 'Output file')
    args = parser.parse_args()
    main(args.src, args.dst)
