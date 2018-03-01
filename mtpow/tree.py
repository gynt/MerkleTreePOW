import math


class MerkleTreeParameters(object):

    def __init__(self, depth, merkle_hasher):
        self.depth=depth
        self.N=pow(2, depth)
        self.merkle_hasher = merkle_hasher


class MerkleTree(object):

    def __init__(self, parameters, cacher):
        self.parameters=parameters
        self.cacher=cacher

        self.leaf = self.parameters.merkle_hasher.leaf
        self.inner = self.parameters.merkle_hasher.inner
        self.N=self.parameters.N

        self.nodes={}

    def clear(self):
        self.nodes.clear()

    def node(self, i):
        if i in self.nodes:
            return self.nodes[i]

        if self.cacher.should_cache(i):
            return self.node_stor(i)
        else:
            return self.node_nstor(i)

    def node_stor(self, i):
        if not i in self.nodes:
            if i >= self.N-1:
                #is leaf node
                self.nodes[i] = self.leaf(i)
            else:
                self.nodes[i] = self.inner(i, self.node((2*i)+1), self.node((2*i)+2))
        return self.nodes[i]

    def node_nstor(self, i):
        if i >= self.N-1:
            #is leaf node
            return self.leaf(i)
        return self.inner(i, self.node((2*i)+1), self.node((2*i)+2))

class MerkleTreeLogic(object):

    def __init__(self):
        pass

    def trace_parent(self, node):
        if node==0:
            return 0
        node-= 1 if node%2==1 else 2
        return node//2

    def trace_route(self, node):
        route=[]
        while node!=0:
            node=self.trace_parent(node)
            route.append(node)
        return route

    def trace_sibling(self, node):
        if node==0:
            raise Exception()
        if node%2==0:
            return node-1
        else:
            return node+1
        
##    def trace_necessaries(self, node, others):
##        necs=[]
##        
##        while node!=0:
##            sib=self.trace_sibling(node)
##            if sib not in others:
##                necs.append(sib)
##            else:
##                break
##            node=self.trace_parent(node)
##            
##        return necs

    def trace_givens(self, leaves):
        necs = {}

        for leaf in leaves:
            necs[leaf]="computed"
            
            node=leaf
            while node>0:
                parent=self.trace_parent(node)
                necs[parent]="computed"
                
                sib=self.trace_sibling(node)
                if sib not in necs:
                    necs[sib]="given"
                    
                node=parent
            
        return [key for key in necs.keys() if necs[key]=="given"]

    def find_layer(self, i):
        layer=-1
        
        if i==0:
            layer = 0
        elif i%2==0:
            layer = math.log2((i//2)+1)
        else:
            layer = math.log2(i+1)
            
        return math.ceil(layer)
