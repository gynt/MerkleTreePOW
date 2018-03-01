

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
