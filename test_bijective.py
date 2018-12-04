from hashlib import sha256
from math import gcd, log, ceil
from mimc import mimc, mimc_mp, round_constants
import statistics
from collections import defaultdict


def observe_frequencies(x, p):
	expected = 1/p
	hist = defaultdict(int)
	for x_i in x:
		hist[x_i] += 1
	for k in sorted(hist.keys()):
		frequency = hist[k] / p
		deviance =  frequency / expected
		yield deviance


def fn_random_oracle(k, m, p):
	data = b"%d.%d" % (k, m)
	return int.from_bytes(sha256(data).digest(), 'big') % p


def fn_inversion_many(k, m, p):
	for c in [0] + list(round_constants(12343, p, 10)):
		m = (pow(m, p-2, p) + k + c) % p
	return m


def fn_inversion_many_mp(k, m, p):
	return (k + m + fn_inversion_many(k, m, p)) % p


def fn_inversion_mp(k, m, p):
	return (pow(m, p-2, p) + k + m) % p


PRIME_QUALITIES = {
	'odd': lambda p: p % 2 != 0,
	'gcd3_eq1': lambda p: gcd(3, p-1) == 1,
	'gcd4_eq1': lambda p: gcd(4, p-1) == 1,
	'gcd5_eq1': lambda p: gcd(5, p-1) == 1,	
	'gcd6_eq1': lambda p: gcd(6, p-1) == 1,
	'gcd7_eq1': lambda p: gcd(7, p-1) == 1,

	'gcd3': lambda p: gcd(3, p-1),
	'gcd4': lambda p: gcd(4, p-1),
	'gcd5': lambda p: gcd(5, p-1),	
	'gcd6': lambda p: gcd(6, p-1),
	'gcd7': lambda p: gcd(7, p-1),
}

ALGORITHMS = {
	# Example of uniformly random distribution
	'random_oracle': fn_random_oracle,

	'inversion': lambda k, m, p: (pow(m, p-2, p) + k) % p,
	'inversion_many': fn_inversion_many,
	'inversion_mp': fn_inversion_mp,
	'inversion_many_mp': fn_inversion_many_mp,

	'mimc_e3': lambda k, m, p: mimc(m, k, 0, p, 3, 3),
	'mimc_e5': lambda k, m, p: mimc(m, k, 0, p, 5, 3),
	'mimc_e7': lambda k, m, p: mimc(m, k, 0, p, 7, 3),

	'mimc_mp_e3': lambda k, m, p: mimc_mp([m], k, 0, p, 3, 3),
	'mimc_mp_e5': lambda k, m, p: mimc_mp([m], k, 0, p, 5, 3),
	'mimc_mp_e7': lambda k, m, p: mimc_mp([m], k, 0, p, 7, 3),
}


class FunctionSquare(object):
	def __init__(self, p, fn):
		self._p = p
		self._fn = fn
		self._data = dict()
		for k in range(0, p-1):		
			self._data[k] = [fn(k, m, p) for m in range(0, p-1)]

	def rows(self):
		return [self.row(k) for k in range(0, self._p - 1)]

	def cols(self):
		return [self.col(m) for m in range(0, self._p - 1)]

	def row(self, k):
		return self._data[k]

	def col(self, m):
		return [self._data[k][m] for k in range(0, self._p - 1)]

	def print(self):
		ndigits = int(ceil(log(self._p, 10))) + 1
		fmt = '%-' + str(ndigits) + 's'
		header = [' ' * ndigits] + [fmt % i for i in range(0, p-1)]
		print(''.join(header))
		for k in range(0, self._p - 1):
			row = [fmt % k] + [fmt % _ for _ in self.row(k)]
			print(''.join(row))

	def bijectivity(self):
		n_rows_bijective = 0
		for row in self.rows():
			if len(set(row)) == len(row):
				n_rows_bijective += 1

		n_cols_bijective = 0 
		for col in self.cols():
			if len(set(col)) == len(col):
				n_cols_bijective += 1

		return (n_rows_bijective, n_cols_bijective)


primes = dict()
with open('first-mil-primes.txt', 'r') as handle:
	for p in handle:		
		p = int(p.strip())
		if p < 5:
			continue
		quals = {name: quality(p) for name, quality in PRIME_QUALITIES.items()}
		primes[p] = quals

		for alg_name, alg_fn in ALGORITHMS.items():
			alg_quals = dict()
			print('Prime', p)
			print('Alg', alg_name)
			x = FunctionSquare(p, alg_fn)			
			#x.print()

			b = x.bijectivity()
			alg_quals['latin_square'] = (b[0] == p-1 and b[1] == p-1)
			alg_quals['bijective_m_each_key'] = b[0] == p-1
			alg_quals['bijective_k_each_msg'] = b[1] == p-1 
			print("STDEV per row", statistics.mean([statistics.stdev(_) for _ in x.rows()]))
			print("STDEV per col", statistics.mean([statistics.stdev(_) for _ in x.cols()]))
			try:
				print("Frequency Deviance Rows", statistics.median([statistics.stdev(list(observe_frequencies(_, p))) for _ in x.rows()]))
				print("Frequency Deviance Cols", statistics.median([statistics.stdev(list(observe_frequencies(_, p))) for _ in x.cols()]))
			except Exception:
				pass
			print(alg_quals)
			print()
		print()
		print()

