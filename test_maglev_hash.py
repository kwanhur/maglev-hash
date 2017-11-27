# /usr/bin/env python
# _*_ coding:utf-8 _*_
from maglev_hash import MaglevHash


class TestMagHash(object):
    def test_add_backend(self):
        mag_hash = MaglevHash(7)
        mag_hash.add_backends(['B0', 'B1', 'B2'])
        assert mag_hash.backend_num() == 3
        assert mag_hash.lookup_table().count('B0') >= 2
        assert mag_hash.lookup_table().count('B1') >= 2
        assert mag_hash.lookup_table().count('B2') >= 2

    def test_remove_backend(self):
        mag_hash = MaglevHash(7)
        mag_hash.add_backends(['B0', 'B1', 'B2'])
        mag_hash.remove_backend('B2')
        assert mag_hash.lookup_table().count('B0') >= 3
        assert mag_hash.lookup_table().count('B1') >= 3
        assert mag_hash.lookup_table().count('B2') == 0
