# Based on https://github.com/kobigurk/circomlib/blob/feature/mimcsponge/circuits/mimcsponge.circom

from sha3 import keccak_256


SNARK_SCALAR_FIELD = 0x30644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000001
DEFAULT_SEED = b"mimcsponge"
DEFAULT_ROUNDS = 220
DEFAULT_p = SNARK_SCALAR_FIELD


"""
this is for mimcjs.hash(1,2,3): 
{ xL:
   6708731823698495319568907590961715813245439042144756682443964812580711632283n,
  xR:
   18444058245820418255538785847032978363886102372504864086197416499869253008979n }

which is the feistel (https://github.com/kobigurk/circomlib/blob/feature/mimcsponge/src/mimcsponge.js#L35)

----

this is for mimcjs.multiHash([1,2],0,3):
[ 6432874992294674054175660886639983161951588679049969118759985614991668008078n,
  16107962609518944685115501428726677783815662389783053514525145863770337651276n,
  18596824120637634257707596359183267387824043670063531573294490754003339453501n ]

which is a hash of [1,2], 0 key and 3 outputs (https://github.com/kobigurk/circomlib/blob/feature/mimcsponge/src/mimcsponge.js#L52)
"""


def to_bytes(*args):
    for i, _ in enumerate(args):
        if isinstance(_, str):
            yield _.encode('ascii')
        elif isinstance(_, bytes):
            yield _
        elif isinstance(_, int):
            yield int(_).to_bytes(32, 'big')
        else:
            raise TypeError('Cannot convert unknown type to bytes: %r, %r' % (type(_), _))


def H(*args):
    data = b''.join(to_bytes(*args))
    hashed = keccak_256(data).digest()
    return int.from_bytes(hashed, 'big')

assert H(123) == 38632140595220392354280998614525578145353818029287874088356304829962854601866


def round_constants(p=DEFAULT_p, R=DEFAULT_ROUNDS, seed=DEFAULT_SEED):
    for i, _ in enumerate(range(R)):
        seed = H(seed)
        yield seed % p if i != 0 else 0


def MiMCFeistel(xL, xR, k, p=DEFAULT_p, R=DEFAULT_ROUNDS, seed=DEFAULT_SEED, e=5):
    for c in round_constants(p, R, seed):
        te = pow(k + xL + c, e, p)
        xL, xR = (xR + te) % p, xL
    return (xL, xR)


def MiMCsponge(inputs, k, nOutputs, p=DEFAULT_p, R=DEFAULT_ROUNDS, seed=DEFAULT_SEED, e=5):
    xL, xR = 0, 0
    for x_i in inputs:
        xL, xR = MiMCFeistel(xL + x_i, xR, k, p, R, seed, e)
    yield xL
    for i in range(nOutputs - 1):
        xL, xR = MiMCFeistel(xL, xR, k, p, R, seed, e)
        yield xL


if __name__ == "__main__":
    constants = list(round_constants(SNARK_SCALAR_FIELD, 220))
    assert constants[-1] == 12785816057369026966653780180257549951796705239580629452502836335892168319323
    assert constants[0] == 0

    xL, xR = MiMCFeistel(1, 2, 3, SNARK_SCALAR_FIELD, 220)
    assert xL == 6708731823698495319568907590961715813245439042144756682443964812580711632283
    assert xR == 18444058245820418255538785847032978363886102372504864086197416499869253008979

    results = list(MiMCsponge([1,2], 0, 3))
    assert results == [
        6432874992294674054175660886639983161951588679049969118759985614991668008078,
        16107962609518944685115501428726677783815662389783053514525145863770337651276,
        18596824120637634257707596359183267387824043670063531573294490754003339453501 ]
    