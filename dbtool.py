#! /usr/bin/env python2
# -*- coding: utf-8 -*-
import argparse
import array
import bintrees
import cdb
import hashlib
import json
import RC6
import struct
import yaml
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

seckey = 'smallspanner-kachebang-android'

mask32 = 2**32 - 1
mask64 = 2**64 - 1
blocksize = 8 + 16

def load(filename):
    with open(filename, 'r') as f:
        ds = yaml.load(f.read(), Loader=Loader)
        i = 0
        while i < len(ds):
            d = ds[i]
            if not d:
                del ds[i]
                continue
            if 'is_post' in d:
                del d['is_post']
                # if d['is_post'] == u'是':
                #     d['is_post'] = True
                # else:
                #     d['is_post'] = False
            if 'province' in d:
                print d['province'], d['city'], d['district'], d['address'], d['name'], d['latitude'], d['longitude']
            if 'longitude' in d and d['longitude']:
                d['longitude'] = float(d['longitude'])
            else:
                d['longitude'] = 0.0
            if 'latitude' in d and d['latitude']:
                d['latitude'] = float(d['latitude'])
            else:
                d['latitude'] = 0.0
            if 'partner' not in d:
                d['partner'] = False
            i += 1
        return ds

def uuid(d):
    if 'id' in d:
        return d['id']
    if 'province' in d:
        if 'district' not in d or d['district'] == None:
            d['district'] = ''
        if 'address' not in d or d['address'] == None:
            d['address'] = ''
        target = (d['province'] + d['city'] + d['district'] + d['name'] + d['address']).encode("utf-8")
    else:
        target = (d['brand'] + d['model']).encode('utf-8')
    m = hashlib.md5()
    m.update(target)
    return m.digest()

def calcgt(latitude, longitude):
    la = max(0, long((latitude + 90) * 1000000) & mask32)
    lo = max(0, long((longitude + 180) * 1000000) & mask32)
    l = 0
    for i in range(32):
        mask = 1 << i
        a = (la & mask) >> i
        o = (lo & mask) >> i
        l |= ((a | (o << 1)) & mask64) << (i * 2)
    return l & mask64

def buildtree(ds):
    bst = bintrees.AVLTree()
    for d in ds:
        if 'latitude' not in d or not d['latitude'] or 'longitude' not in d or not d['longitude']:
            continue
        k = calcgt(d['latitude'], d['longitude'])
        v = uuid(d)
        bst.insert(k, v)
    return bst

def walk(node, idx, rowstart, depth, output):
    offset = rowstart + idx * blocksize
    output.seek(offset)
    key = node.key
    value = node.value
    output.write(struct.pack('>Q', key))
    output.write(value)
    left = node.left
    right = node.right
    if left:
        walk(left, (idx << 1), rowstart + 2 ** depth * blocksize, depth + 1, output)
    if right:
        walk(right, (idx << 1) | 0x01, rowstart + 2 ** depth * blocksize, depth + 1, output)

def dodb(ds, dst):
    db = cdb.cdbmake(dst, dst + 'tmp')
    for d in ds:
        k = d['id']
        del d['id']
        j = json.dumps(d)
        d['id'] = k
        e = RC6.encrypt(bytearray(j, 'utf-8'), bytearray(seckey, 'ascii'))
        v = array.array('B')
        v.fromlist(e)
        db.add(k, v)
    db.finish()

def dogt(ds, dst):
    bst = buildtree(ds)
    s = 0
    for i in range(bst._root.balance + 1):
        s += 2 ** i
    with open(dst, 'wb') as output:
        output.truncate(8 + s * blocksize)
        output.seek(0)
        output.write(struct.pack('>BBB', 0x87, 0x72, 0xee)) # magic key 'gttree'
        output.write(struct.pack('>B', 0x03))   # version
        output.write(struct.pack('>BBH', bst._root.balance + 1, 8, 16)) # depth, key size, value size
        walk(bst._root, 0, 8, 0, output)

def dotc(ds, dst):
    with open(dst, 'wb') as output:
        data = dict()
        for d in ds:
            if 'province' not in d or 'city' not in d:
                continue
            v = uuid(d) # must be called before accessing district
            province = d['province']
            city = d['city']
            district = d['district']
            if not data.has_key(province):
                data[province] = dict()
            if not data[province].has_key(city):
                data[province][city] = dict()
            if not data[province][city].has_key(district):
                data[province][city][district] = list()
            data[province][city][district].append(v)
        offsets = dict()
        output.write(struct.pack('>BBBB', 0x03, 0xca, 0x8c, 0xad)) # magic key '1cascad'
        output.write(struct.pack('>B', 0x01))   # version
        offset = 5
        for province in data.keys():
            offsets[province] = dict()
            for city in data[province].keys():
                offsets[province][city] = dict()
                for district in data[province][city].keys():
                    offsets[province][city][district] = offset
                    vs = data[province][city][district]
                    offset += 4 + len(vs) * 16
                    output.write(struct.pack('>I', len(vs) * 16))
                    for e in vs:
                        output.write(e)
        for province in offsets.keys():
            for city in offsets[province].keys():
                for district in offsets[province][city].keys():
                    key = (province + '/' + city + '/' + district).encode('utf-8')
                    output.write(struct.pack('>H', len(key)))
                    output.write(key)
                    output.write(struct.pack('>I', offsets[province][city][district]))
        output.write(struct.pack('>I', offset))

def domk(ds, dst):
    with open(dst, 'wb') as output:
        data = dict()
        for d in ds:
            if 'brand' not in d:
                continue
            brands = d['brand']
            if not brands:
                continue
            v = uuid(d)
            for brand in brands:
                if brand not in data:
                    data[brand] = []
                data[brand].append(v)
        offsets = dict()
        output.write(struct.pack('>BB', 0x3a, 0x4e)) # magic key 'make'
        output.write(struct.pack('>B', 0x01)) # version
        offset = 3
        for brand in data.keys():
            offsets[brand] = offset
            vs = data[brand]
            offset += 4 + len(vs) * 16
            output.write(struct.pack('>I', len(vs) * 16))
            for v in vs:
                output.write(v)
        for brand in offsets.keys():
            key = brand.encode('utf-8')
            output.write(struct.pack('>H', len(key)))
            output.write(key)
            output.write(struct.pack('>I', offsets[brand]))
        output.write(struct.pack('>I', offset))

def dooc(ds, dst):
    field = 'brand'
    with open(dst, 'wb') as output:
        data = dict()
        for d in ds:
            if field not in d:
                continue
            key = d[field]
            v = uuid(d)
            if not data.has_key(key):
                data[key] = list()
            data[key].append(v)
        offsets = dict()
        output.write(struct.pack('>BBBB', 0x01, 0xca, 0x8c, 0xad)) # magic key '1cascad'
        output.write(struct.pack('>B', 0x01)) # version
        offset = 5
        for key in data.keys():
            offsets[key] = offset
            vs = data[key]
            offset += 4 + len(vs) * 16
            output.write(struct.pack('>I', len(vs) * 16))
            for e in vs:
                output.write(e)
        for k in offsets.keys():
            key = k.encode('utf-8')
            output.write(struct.pack('>H', len(key)))
            output.write(key)
            output.write(struct.pack('>I', offsets[k]))
        output.write(struct.pack('>I', offset))

def main(src, dst, db, gt, tc, mk, oc):
    ds = load(src)
    for d in ds:
        d['id'] = uuid(d)
    if db:
        dodb(ds, dst + '.db')
    if gt:
        dogt(ds, dst + '.gt')
    if tc:
        dotc(ds, dst + '.3c')
    if mk:
        domk(ds, dst + '.mk')
    if oc:
        dooc(ds, dst + '.1c')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'A tool to generate db and indexs')
    parser.add_argument('-db', action = 'store_true', default = False, help = 'flag to generate cdb')
    parser.add_argument('-gt', action = 'store_true', default = False, help = 'flag to generate geo tree index')
    parser.add_argument('-3c', action = 'store_true', default = False, help = 'flag to generate 3-cascade index', dest = 'tc')
    parser.add_argument('-mk', action = 'store_true', default = False, help = 'flag to generate make index')
    parser.add_argument('-1c', action = 'store_true', default = False, help = 'flag to generate 1-cascade index', dest = 'oc')
    parser.add_argument('-android', action = 'store_true', default = False, help = 'flag to generate files to android')
    parser.add_argument('-ios', action = 'store_true', default = False, help = 'flag to generate files to ios')
    parser.add_argument('src', action = 'store', help = 'yaml source')
    parser.add_argument('dst', action = 'store', help = 'destination')
    args = parser.parse_args()
    if args.ios:
        seckey = 'smallspanner-kachebang-ios-1.0.0'
    else:
        seckey = 'smallspanner-kachebang-android'
    main(args.src, args.dst, args.db, args.gt, args.tc, args.mk, args.oc)
