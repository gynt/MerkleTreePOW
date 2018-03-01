import sys
import time


class Measurement(object):

    def __init__(self, obj, validation=False):
        self.obj = obj
        if not validation:
            self.func = obj.build_proof
        else:
            self.func = obj.validate_proof
        self.validation=validation

    def _build_size_string(self, size):
        if size//1000000000==0:
            if size//1000000==0:
                if size//1000==0:
                    return "{} B".format(size)
                return "{} KB".format(size/1000)
            return "{} MB".format(size/1000000)
        return "{} GB".format(size/1000000000)

    def _time(self, func):
        
        t1=time.time()
        if not func():
            raise Exception("Function returned falsy")
        t2=time.time()
        return (t2-t1)

    def measure(self):
        self.t=self._time(self.func)
        if self.validation:
            self.memproof = sys.getsizeof(self.obj.proof_copy)
        else:
            self.memproof = sys.getsizeof(self.obj.proof)
        self.memtree = sys.getsizeof(self.obj.param.selector.merkle_tree.nodes)
        print("{} took {} seconds.\nProof is of (allocated) size: {}.\nTree is of (allocated) size: {}".format("Validation" if self.validation else "Generation",self.t, self._build_size_string(self.memproof), self._build_size_string(self.memtree)))

    def compute_load(self, ram_in_bytes, cores):
        if self.validation:
            raise NotImplementedError("Not implented yet")
        messages=(ram_in_bytes/self.memtree)
        t=self.t/cores

        span = t*messages

        network = messages*self.memproof

        print("With RAM={} and cores={}, an attacker can send {} messages after {} seconds and bandwidth {} ".format(self._build_size_string(ram_in_bytes), cores, messages, span, self._build_size_string(network)))
