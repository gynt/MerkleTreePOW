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
        return False

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

class ByteFunctions(object):

    def int_to_bytes(self, x):
        return x.to_bytes((x.bit_length() + 7) // 8, 'big')

    def int_from_bytes(self, xbytes):
        return int.from_bytes(xbytes, 'big')

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
        
        if i==0:
            return self.node_stor(i)
        elif self.cacher.should_cache(i):
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
        
    def trace_necessaries(self, node, others):
        necs=[]
        
        while node!=0:
            sib=self.trace_sibling(node)
            if sib not in others:
                necs.append(sib)
            else:
                break
            node=self.trace_parent(node)
            
        return necs

class NodeSelector(object):

    def __init__(self, merkle_tree, amount, merkle_tree_logic):
        self.merkle_tree=merkle_tree
        self.amount=amount
        self.logic=merkle_tree_logic

    def next(self):
        raise NotImplementedError()

    def has_next(self):
        raise NotImplementedError()

class TreeBasedSelector(NodeSelector):

    def __init__(self, merkle_tree, amount, merkle_tree_logic):
        super().__init__(merkle_tree, amount, merkle_tree_logic)
        if self.merkle_tree.parameters.N % self.amount != 0:
            raise Exception()
        self.gap=self.merkle_tree.parameters.N//amount
        self.current=0
        self.seednode=0
        self.count=0
        self.bytefunctions=merkle_tree.parameters.merkle_hasher.bytefunctions

    def next(self):
        seed=self.merkle_tree.node(self.seednode)
        seedint=self.bytefunctions.int_from_bytes(seed)
        selint=(seedint%self.gap)+(self.count*self.gap)+self.merkle_tree.parameters.N
        
        treeseed = self.merkle_tree.node(selint)
        treesel=self.bytefunctions.int_from_bytes(treeseed)%(self.merkle_tree.parameters.depth-2)
        self.seednode=self.logic.trace_route(selint)[treesel]
        
        self.count+=1
        return selint

    def has_next(self):
        return self.count < self.amount
    
class ProofParameters(object):

    def __init__(self, selector):
        self.selector=selector

class ProofGenerator(object):

    def __init__(self, proof_parameters):
        self.param = proof_parameters
        self.proof=None

    def build_proof(self):
        leaves=[]
        while self.param.selector.has_next():
            leaves.append(self.param.selector.next())

        necs=[]
        for leaf in leaves:
            necs.extend(self.param.selector.logic.trace_necessaries(leaf, necs))
        necs=list(set(necs))

        allnodes={}
        for leaf in leaves:
            allnodes[leaf]=self.param.selector.merkle_tree.node(leaf)

        for node in necs:
            allnodes[node]=self.param.selector.merkle_tree.node(node)

        allnodes[0]=self.param.selector.merkle_tree.node(0)

        self.proof=allnodes

        return allnodes

    def clear_tree(self):
        self.param.selector.merkle_tree.clear()

    def reset(self):
        self.proof=None
        self.param.selector.merkle_tree.clear()

class ValidationTree(MerkleTree):

    def __init__(self, parameters, nodes):
        super().__init__(parameters, None)
        self.parameters=parameters
        self.nodes=nodes

    def node(self, i):
        
        if not i in self.nodes:
            raise Exception("Tree does not contain: {}".format(i))
        else:
            return self.nodes[i]

##class ProofValidator(object):
##
##    def __init__(self, proof, proof_parameters):
##        self.proof = proof
##        self.depth = depth
##        self.hasher = hasher
##        self.logic = logic
##        self.amount = amount
##        self.N = pow(2, depth)
##
##    def validate(self):
##        tree=ValidationTree(
##        leaves = [key for key in proof.keys() if key >= self.N-1]
##        necessaries = []
##        for leaf in leaves:
##            necessaries.extend(self.logic.trace_necessaries(leaf, necessaries))
##
##        self._tree_contains_all(necessaries)
##        self.reb
##        
##
##    def _tree_contains_all(self, necessaries):
##        givens=self.proof_parameters.selector.merkle_tree.nodes.keys()
##        for nec in necessaries:
##            if nec not in givens:
##                raise Exception("{} is missing in the proof".format(nec))
##        return True
            

def time(func):
    import time
    t1=time.time()
    func()
    t2=time.time()
    return (t2-t1)

if __name__=="__main__":
    desc="testaccount@example.com:1239128310:001"
    depth=8
    amount=8
    gen=ProofGenerator(
        ProofParameters(
            TreeBasedSelector(
                MerkleTree(
                    MerkleTreeParameters(
                        depth, MerkleHasher(
                            desc, SHA256Hash(), ByteFunctions()
                            )
                        ), FullCache()
                    ),amount,MerkleTreeLogic()
                )
            )
        )
    took=time(gen.build_proof)
    print("Generation of proof took: {}".format(took))
    proof=gen.proof
    gen.reset()

    validator=ProofGenerator(
        ProofParameters(
            TreeBasedSelector(
                ValidationTree(
                    MerkleTreeParameters(
                        depth, MerkleHasher(
                            desc, SHA256Hash(), ByteFunctions()
                            )
                        ), proof
                    ),amount,MerkleTreeLogic()
                )
            )
        )
    took=time(validator.build_proof)
    print("Validation of proof took: {}".format(took))
    
    
    
