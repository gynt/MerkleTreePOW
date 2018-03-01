import mtpow.cache
import mtpow.tree
import mtpow.hash
import mtpow.util
import mtpow.proof
import mtpow.validation
import mtpow.selection
import mtpow.measurement


def default_generator(desc, depth, leaves):
    gen=proof.ProofGenerator(
        proof.ProofParameters(
            selection.TreeBasedSelector(
                tree.MerkleTree(
                    tree.MerkleTreeParameters(
                        depth, hash.MerkleHasher(
                            desc, hash.SHA256Hash(), util.ByteFunctions()
                            )
                        ), cache.InnerCache(pow(2, depth))
                    ),leaves,tree.MerkleTreeLogic()
                )
            )
        )
    return gen


def default_validator(desc, depth, leaves, the_proof):
    validator=validation.ProofValidator(
        proof.ProofParameters(
            selection.TreeBasedSelector(
                tree.MerkleTree(
                    tree.MerkleTreeParameters(
                        depth, hash.MerkleHasher(
                            desc, hash.SHA256Hash(), util.ByteFunctions()
                            )
                        ), cache.FullCache()
                    ),leaves,tree.MerkleTreeLogic()
                )
            ),the_proof.copy()
        )
    return validator
