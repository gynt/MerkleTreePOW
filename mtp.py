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
        leaves=self.choose_leaves()
        necessaries=self.add_necessaries(leaves)
        ptree=self.compile_tree(leaves, necessaries)
        #self.append_root(ptree)
        self.proof=ptree
        return self.proof

    def choose_leaves(self):
        leaves=[]
        while self.param.selector.has_next():
            leaves.append(self.param.selector.next())
        return leaves

    def add_necessaries(self, leaves):
        necs=[]
        necs.extend(self.param.selector.logic.trace_givens(leaves))
        necs=list(set(necs))
        return necs

    def compile_tree(self, leaves, necessaries):
        allnodes={}
        for leaf in leaves:
            allnodes[leaf]=self.param.selector.merkle_tree.node(leaf)

        for node in necessaries:
            allnodes[node]=self.param.selector.merkle_tree.node(node)

        return allnodes

    def get_root(self):
        return self.param.selector.merkle_tree.node(0)

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
            child1=(2*i)+1
            child2=(2*i)+2
            if not child1 in self.nodes and not child2 in self.nodes:
                raise Exception("Tree does not contain: {}, and it cannot be computed.".format(i))
            else:
                return self.inner(i, self.node((2*i)+1), self.node((2*i)+2))
        
        return self.nodes[i]

    def leaf(self, i):
        raise Exception("Tree does not contain leaf: {}, and it should not be computed.".format(i))

class ProofValidator(ProofGenerator):

    def __init__(self, parameters, proof):
        super().__init__(parameters)
        self.proof_copy = proof.copy()
        self.param.selector.merkle_tree.nodes = self.proof_copy.copy()
        #self.param.selector.merkle_tree.cacher = FullCache()#ValidationCache(self.proof_copy)

    def sanitize_proof(self):
        if 0 in self.param.selector.merkle_tree.nodes:
            del self.param.selector.merkle_tree.nodes[0]
        return True

    def check_layer(self, leaf):
        layer=self.param.selector.logic.find_layer(leaf)-1
        if layer > self.param.selector.merkle_tree.parameters.depth or layer < 0:
            raise Exception("Invalid layer: {} for leaf: {}".format(layer, leaf))
        return True

    def check_leave_hashes(self):
        leaves = [node for node in self.param.selector.merkle_tree.nodes if node >= self.param.selector.merkle_tree.N-1]
        if len(leaves)==0:
            raise Exception("No leaves specified!")
        
        while len(leaves) > 0:
            leaf = leaves[0]

            if not self.check_layer(leaf):
                return False

            del leaves[0]
            if self.param.selector.merkle_tree.parameters.merkle_hasher.leaf(leaf) != self.proof_copy[leaf]:
                raise Exception("Proof contains invalid leaf: {}".format(leaf))
                return False
        return True

    def rebuild(self):
        leaves = [node for node in self.param.selector.merkle_tree.nodes if node >= self.param.selector.merkle_tree.N-1]
        if len(leaves)==0:
            raise Exception("No leaves specified!")
        layer=leaves
        while len(layer)>0:
            node=layer[0]
            if node == 0:
                self.root_copy = self.param.selector.merkle_tree.node(0)
                break
            parent = self.param.selector.logic.trace_parent(node)
            layer.append(parent)
            sibling = self.param.selector.logic.trace_sibling(node)
            if sibling in self.param.selector.merkle_tree.nodes:
                self.param.selector.merkle_tree.node(parent)
            else:
                raise Exception("Sibling not found for: {}, sibling: {}".format(node, sibling))
                return False
            del layer[0]
        return True
            

    def check_leave_choice(self):
        
        choice = self.choose_leaves()
        for c in choice:
            if c not in self.proof_copy:
                raise Exception("Proof does not contain correct leaves: {}".format(c))
                return False

        necs = self.add_necessaries(choice)
        for n in necs:
            if n not in self.proof_copy:
                raise Exception("Proof does not contain correct supplementary nodes: {}".format(n))
                return False

        comb = choice+necs

        erroneous=[]
        
        for n in self.proof_copy.keys():
            if n == 0:
                continue
            
            if n not in comb:
                raise Exception("Proof contains incorrect nodes: {}. comb: {}".format(n, comb))
                erroneous.append(n)
                return False

        for n in erroneous:
            del self.param.selector.merkle_tree.nodes[n]
        
        return True

    def build_proof(self):
        raise NotImplementedError()

    def validate_proof(self):
        return self.sanitize_proof() and self.check_leave_hashes() and self.rebuild() and self.check_leave_choice()

def time(func):
    import time
    t1=time.time()
    if not func():
        raise Exception("Function returned falsy")
    t2=time.time()
    return (t2-t1)

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

    def compute_dos(self, ram_in_bytes, cores):
        messages=(ram_in_bytes/self.memtree)
        t=self.t/cores

        span = t*messages

        network = messages*self.memproof

        print("With RAM={} and cores={}, an attacker can send {} messages after {} seconds and bandwidth {} ".format(self._build_size_string(ram_in_bytes), cores, messages, span, self._build_size_string(network)))

        

def gen_proof(desc, depth, amount):
    gen=ProofGenerator(
        ProofParameters(
            TreeBasedSelector(
                MerkleTree(
                    MerkleTreeParameters(
                        depth, MerkleHasher(
                            desc, SHA256Hash(), ByteFunctions()
                            )
                        ), InnerCache(pow(2, depth))#LayerCache(list(range(0,23,2)))#pow(2,21))
                    ),amount,MerkleTreeLogic()
                )
            )
        )
    took=time(gen.build_proof)
    print("Generation of proof took: {} seconds".format(took))
    return gen

def fill_memory(desc, depth, amount):
    c=0
    interval=100
    global gens
    gens=[]
    while True:
        if interval < 0:
            interval=100
            print(c)
        gens.append(gen_proof(desc, depth, amount))
        c+=1
        interval-=1
    return gens



import sys

if __name__=="__main__":
    desc="testaccount@example.com:1239128310:001"
    depth=18
    amount=16
    
    gen=ProofGenerator(
        ProofParameters(
            TreeBasedSelector(
                MerkleTree(
                    MerkleTreeParameters(
                        depth, MerkleHasher(
                            desc, SHA256Hash(), ByteFunctions()
                            )
                        ), InnerCache(pow(2, depth))
                    ),amount,MerkleTreeLogic()
                )
            )
        )
    print("\n\tGeneration")
    mea=Measurement(gen)
    mea.measure()
    
    proof=gen.proof
    #gen.reset()

    validator=ProofValidator(
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
            ),proof.copy()
        )
    print("\n\tValidation")
    Measurement(validator, True).measure()

    print("\nAttack parameters:")
    mea.compute_dos(2*1000*1000*1000, 4)
