from sha3 import keccak_256


SNARK_SCALAR_FIELD = 0x30644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000001


def H(*args):
	data = b''.join(_.to_bytes(32, 'big') for _ in args)
	hashed = keccak_256(data).digest()
	return int.from_bytes(hashed, 'big')

assert H(123) == 38632140595220392354280998614525578145353818029287874088356304829962854601866


def round_constants(seed, p, R):
    for _ in range(R):
        seed = H(seed)
        yield seed


def mimc(x, k, seed, p, e, R):
    assert R > 2
    for c_i in [0] + list(round_constants(seed, p, R - 2)):
        a = (x + k + c_i) % p
        x = (a ** e) % p
    return (x + k) % p


def mimc_mp(x, k, seed, p, e, R):
    for x_i in x:
        k = (k + x_i + mimc(x_i, k, seed, p, e, R)) % p
    return k


if __name__ == "__main__":
	assert mimc(1, 1, 1, SNARK_SCALAR_FIELD, 7, 46) == 1300849129775089134466232670907109030853384837097186821504541142364641413437
	assert mimc(1, 1, 1, SNARK_SCALAR_FIELD, 5, 55) == 16451571189888683738166037749717624326602724070424662292143094644958444275424
	assert mimc_mp([1,2,3], 1, 1, SNARK_SCALAR_FIELD, 7, 10) == 15772580913570834494018056247779681195847786982073538652842589502561187453858
	assert mimc_mp([1,2,3], 1, 1, SNARK_SCALAR_FIELD, 5, 10) == 7476463565497645457767833111745932024909125653222220161832120383300453034759
