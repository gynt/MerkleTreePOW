
from mtpow import *
import sys


if __name__=="__main__":
    desc="testaccount@example.com:1239128310:001"
    depth=18
    amount=16

    
    gen = default_generator(desc, depth, amount)
    
    print("\n\tGeneration")
    mea=measurement.Measurement(gen)
    mea.measure()
    

    validator=default_validator(desc, depth, amount, gen.proof)
    
    print("\n\tValidation")
    measurement.Measurement(validator, True).measure()


    print("\nAttack parameters:")
    mea.compute_load(2*1000*1000*1000, 4)
