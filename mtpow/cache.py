import math

class Cache(object):

    def __init__(self):
        pass

    def should_cache(self, i):
        raise NotImplementedError()

    def _find_layer(self, i):
        layer=-1
        
        if i==0:
            layer = 0
        elif i%2==0:
            layer = math.log2((i//2)+1)
        else:
            layer = math.log2(i+1)
            
        return math.ceil(layer)

class NoCache(Cache):

    def should_cache(self, i):
        return i==0

class FullCache(Cache):

    def should_cache(self, i):
        return True

class InnerCache(Cache):

    def __init__(self, N):
        self.N=N

    def should_cache(self, i):
        return i < self.N-1

class LayerCache(Cache):

    def __init__(self, layers):
        super().__init__()
        self.layers=layers

    def should_cache(self, i):
        layer = self._find_layer(i)
        return layer in self.layers

class ValidationCache(NoCache):

    def __init__(self, nodes):
        super().__init__()
        self.nodes=nodes

    def should_cache(self, i):
        if not i in self.nodes:
            child1=(2*i)+1
            child2=(2*i)+2
            if not child1 in self.nodes and not child2 in self.nodes:
                raise Exception("Tree does not contain: {}, and it should not be computed.".format(i))        
        return super().should_cache(i)
