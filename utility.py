# -*- coding: utf-8 -*-

import hashlib
import yaml
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

def read(filename):
    with open(filename, 'r') as f:
        ds = yaml.load(f.read(), Loader=Loader)
        i = 0
        while i < len(ds):
            d = ds[i]
            if not d:
                del ds[i]
                continue
            if 'is_post' in d:
                if d['is_post'] == u'是':
                    d['is_post'] = True
                else:
                    d['is_post'] = False
            if 'longitude' in d and d['longitude']:
                d['longitude'] = float(d['longitude'])
            else:
                d['longitude'] = 0.0
            if 'latitude' in d and d['latitude']:
                d['latitude'] = float(d['latitude'])
            else:
                d['latitude'] = 0.0
            if 'contact_one' in d and len(d['contact_one']) >0:
                d['contacts'] = list()
                if 'contact_one_phone' in d:
                    d['contacts'].append({'name': d['contact_one'], 'phone': d['contact_one_phone']})
                else:
                    d['contacts'].append({'name': d['contact_one'], 'phone': ''})
            if 'contact_two' in d and len(d['contact_two']) >0:
                if 'contacts' not in d:
                    d['contacts'] = list()
                if 'contact_two_phone' in d:
                    d['contacts'].append({'name': d['contact_two'], 'phone': d['contact_two_phone']})
                else:
                    d['contacts'].append({'name': d['contact_two'], 'phone': ''})
            i += 1
        return ds

def uuid(d):
    if 'province' in d:
        if 'district' not in d or d['district'] == None:
            d['district'] = ''
        if 'address' not in d or d['address'] == None:
            d['address'] = ''
        print d['province'], d['city'], d['district'], d['name'], d['address']
        target = (d['province'] + d['city'] + d['district'] + d['name'] + d['address']).encode("utf-8")
    else:
        target = (d['brand'] + d['model']).encode('utf-8')
    m = hashlib.md5()
    m.update(target)
    return m.digest()
