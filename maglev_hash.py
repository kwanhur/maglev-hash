# /usr/bin/env python
# _*_ coding:utf-8 _*_
import math

import mmhash

VERSION = '0.0.1'


class MaglevHash(object):
    """
    maghash implements Google's load balance solution - Maglev's consistent hashing algorithm.
    ref: http://static.googleusercontent.com/media/research.google.com/zh-CN//pubs/archive/44824.pdf
    """

    def __init__(self, m):
        self.__m = m or 65537  # prime number for modular
        if not self.__is_prime(self.__m):
            raise Exception('invalid prime number')

        self.__permutation = []  # 2 division array
        self.__b_index = {}  # backend number
        self.__backends = []  # backend element list
        self.__n = 0  # backend number
        # result of backend selection for each possible hash value entry -- lookup table
        self.__entry = [None] * self.__m

    @staticmethod
    def __is_prime(m):
        if m < 2:
            return False

        for i in range(2, int(math.sqrt(m))):
            if m % i == 0:
                return False

        return True

    def backend_num(self):
        return self.__n

    def m(self):
        return self.__m

    def get_backend(self, flow):
        hash_gen = HashGenerator('mrmr')
        fhash = hash_gen.sum(str(flow))
        m = self.__m
        if len(self.__entry) != m:
            raise Exception('internal index inconsistent')

        bIdx = self.__entry[int(fhash % m)]
        return str(self.__backends[bIdx])

    def add_backend(self, backends):
        if not isinstance(backends, list):
            raise Exception('invalid type,must be list')

        for b in backends:
            if self.__b_index.get(b):
                continue
            self.__backends.append(b)
            self.__b_index[b] = self.__n
            self.__n += 1

        # should re-calculate permutation array asynchronize
        self.__spawn_permutation(0)
        self.__populate()

    def remove_backend(self, backends):
        if not isinstance(backends, list):
            raise Exception('invalid type,must be list')

        del_list = []
        for b in backends:
            idx = self.__b_index[b]
            if idx:
                del_list.append(idx)

        if len(del_list) == 0:
            return

        del_list.sort()

        bbuf = []
        pbuf = []
        start = 0
        for i, d in enumerate(del_list):
            if d > start:
                bbuf.extend(self.__backends[start:d])
                pbuf.extend(self.__permutation[start:d])
            start = d + 1

        self.__backends = bbuf
        self.__permutation = pbuf
        # renew data
        self.__n = len(self.__backends)
        self.__b_index = {}
        for i, b in enumerate(self.__backends):
            self.__b_index[b] = i

        self.__populate()

    def __populate(self):
        """
        populate lookup table base on permutation table
        """
        n = self.__n
        m = self.__m

        nexts = [None] * n
        for i in range(n):
            nexts[i] = 0
        for i in range(m):
            self.__entry[i] = -1

        j = 0
        while True:
            for i in range(n):
                c = self.__permutation[i][nexts[i]]
                while self.__entry[c] >= 0:
                    nexts[i] += 1
                    c = self.__permutation[i][nexts[i]]
                self.__entry[c] = i
                nexts[i] += 1
                j += 1
                if j == m:
                    return

    def __spawn_permutation(self, m):
        n = self.__n
        if m == 0:
            m = self.__m
        else:
            self.__m = int(m)

        if int(n) != len(self.__backends):
            raise Exception('backend number inconsistent, something wrong.')

        calced = len(self.__permutation)
        i = calced
        while i < n:
            buf = [None] * m
            for j in range(m):
                offset = self.__offset(i)
                skip = self.__skip(i)
                buf[j] = (offset + j * skip) % m
            self.__permutation.append(buf)
            i += 1

    def lookup_table(self):
        lookup = [None] * len(self.__entry)
        for i, b_idx in enumerate(self.__entry):
            lookup[i] = str(self.__backends[b_idx])
        return lookup

    def __offset(self, backend_idx):
        hash_gen = HashGenerator('BKDR')
        h1 = self.__get_hash(backend_idx, hash_gen)
        m = self.__m
        return h1 % m

    def __skip(self, backend_idx):
        hash_gen = HashGenerator('MRMR')
        h2 = self.__get_hash(backend_idx, hash_gen)
        m = self.__m
        return h2 % (m - 1) + 1

    def __get_hash(self, backend_idx, hash_gen):
        n = self.__n
        if backend_idx >= n:
            raise Exception('invalid index')

        if backend_idx < len(self.__backends):
            backend = self.__backends[backend_idx]
        else:
            raise Exception('invalid index')
        return hash_gen.sum(backend)


class HashGenerator(object):
    def __init__(self, algo):
        self.algo = str(algo).upper()

    def sum(self, content):
        if self.algo == 'BKDR':
            return self.__BKDRHash(content)
        elif self.algo == 'MRMR':
            return mmhash.get_hash(content)
        else:
            return str(content).__hash__()

    @staticmethod
    def __BKDRHash(key):
        seed = 131  # 31 131 1313 13131 131313 etc..
        value = 0
        for i in range(len(key)):
            value = (value * seed) + ord(key[i])
        return value & 0x7FFFFFFF


if __name__ == '__main__':
    mh = MaglevHash(7)
    mh.add_backend(['b0', 'b1', 'b2'])
    print(mh.lookup_table())
    mh.remove_backend(['b2'])
    print(mh.lookup_table())
