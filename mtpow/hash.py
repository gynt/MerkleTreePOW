

class Hash(object):

    def __init__(self):
        pass

    def hash(self, *args):
        raise NotImplementedError()


class SHA256Hash(Hash):

    def __init__(self):
        super().__init__()
        
        from hashlib import sha256
        self.func = sha256

    def hash(self, *args):
        m=self.func()
        for arg in args:
            m.update(arg)
        return m.digest()


class MerkleHasher(object):

    def __init__(self, service_descriptor, hasher, bytefunctions):
        self.hasher=hasher
        self.bytefunctions=bytefunctions
        self.hs = self.service_desc(service_descriptor.encode("UTF-8"))

    def service_desc(self, descriptor):
        return self.hasher.hash(descriptor)

    def leaf(self, i):
        return self.hasher.hash(self.hs, self.bytefunctions.int_to_bytes(i))

    def inner(self, i, n1, n2):
        return self.hasher.hash(self.hs, n1, n2, self.bytefunctions.int_to_bytes(i))
