

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
