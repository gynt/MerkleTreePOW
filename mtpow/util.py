

class ByteFunctions(object):

    def int_to_bytes(self, x):
        return x.to_bytes((x.bit_length() + 7) // 8, 'big')

    def int_from_bytes(self, xbytes):
        return int.from_bytes(xbytes, 'big')
