from hashlib import sha256


def hash(i):
    m=sha256()
    m.update(i.to_bytes(4, 'big'))
    return m.digest()


def y(x, mod):
    return int.from_bytes(hash(x),'big') % mod


def counts(iterable):
    result = {}
    for i in iterable:
        if not i in result:
            result[i]=0
        result[i]+=1
    return result

sample=counts([y(x, 19) for x in range(0,100000)])
print(min(sample.values()))
print(max(sample.values()))
