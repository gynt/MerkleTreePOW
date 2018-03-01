from mtpow import proof


class ProofValidator(proof.ProofGenerator):

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
