from hashlib import sha256
from math import log, ceil
try:
	from math import gcd
except ImportError:
	from fractions import gcd
from mimc import mimc, mimc_mp, round_constants
from jarvis import jarvis, friday
from mimcsponge import MiMCFeistel, MiMCsponge
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


PRIME_QUALITIES = {
	'gcd(3,p-1)==1': lambda p: gcd(3, p-1) == 1,
	'gcd(5,p-1)==1': lambda p: gcd(5, p-1) == 1,	
	'gcd(7,p-1)==1': lambda p: gcd(7, p-1) == 1,
}

ALGORITHMS = {
	# Example of uniformly random distribution
	'random_oracle': fn_random_oracle,

	'inversion': lambda k, m, p: (pow(m, p-2, p) + k) % p,

	'jarvis': lambda k, m, p: jarvis(m, k, round_constants(0, p, 5), p),
	'friday': lambda k, m, p: friday([m], k, round_constants(0, p, 5), p),

	'mimc_e3': lambda k, m, p: mimc(m, k, 0, p, 3, 3),
	'mimc_e5': lambda k, m, p: mimc(m, k, 0, p, 5, 3),	
	'mimc_e7': lambda k, m, p: mimc(m, k, 0, p, 7, 3),

	'mimc_mp_e3': lambda k, m, p: mimc_mp([m], k, 0, p, 3, 3),
	'mimc_mp_e5': lambda k, m, p: mimc_mp([m], k, 0, p, 5, 3),
	'mimc_mp_e7': lambda k, m, p: mimc_mp([m], k, 0, p, 7, 3),

	'mimcsponge_e5': lambda k, m, p: list(MiMCsponge([m], 0, k, p=p, R=3, e=5))[0],
	'mimcsponge_e5_m': lambda k, m, p: list(MiMCsponge([m], m, k, p=p, R=3, e=5))[0],
	'mimcsponge_e5_mm': lambda k, m, p: list(MiMCsponge([m, m], 0, k, p=p, R=3, e=5))[0],
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

	def display(self):
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


properties_alg_stats = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

primes = dict()

with open('first-mil-primes.txt', 'r') as handle:
	for i, p in enumerate(handle):
		p = int(p.strip())
		if p < 5:
			continue
		quals = {name: quality(p) for name, quality in PRIME_QUALITIES.items()}
		primes[p] = quals

		for alg_name, alg_fn in ALGORITHMS.items():
			alg_quals = dict()
			#print('Prime', p)
			#print('Alg', alg_name)
			x = FunctionSquare(p, alg_fn)			
			#x.display()
			#print()

			b = x.bijectivity()
			alg_quals['latin_square'] = (b[0] == p-1 and b[1] == p-1)
			alg_quals['bijective_m_each_key'] = b[0] == p-1
			alg_quals['bijective_k_each_msg'] = b[1] == p-1 
			#print("STDEV per row", statistics.mean([statistics.stdev(_) for _ in x.rows()]))
			#print("STDEV per col", statistics.mean([statistics.stdev(_) for _ in x.cols()]))
			try:
				freqs_rows = [statistics.stdev(list(observe_frequencies(_, p))) for _ in x.rows()]
				freqs_cols = [statistics.stdev(list(observe_frequencies(_, p))) for _ in x.cols()]
				freq_dev_rows = statistics.median(freqs_rows)
				freq_dev_cols = statistics.median(freqs_cols)
				"""
				if freq_dev_rows == 0.0:
					print(p, alg_name, quals, freqs_rows, freqs_cols)
					x.display()
					print()
					print()
					print()
				"""

				#print("Frequency Deviance Rows", freq_dev_rows)
				#print("Frequency Deviance Cols", freq_dev_cols)
			except Exception:
				pass
			for pq_name, pq_val in quals.items():
				if pq_val is not True:
					continue
				properties_alg_stats[alg_name][pq_name]['deviance_rows'].append(freq_dev_rows)
				properties_alg_stats[alg_name][pq_name]['deviance_cols'].append(freq_dev_cols)
				for alg_qual_name, alg_qual_value in alg_quals.items():
					if alg_qual_value:
						properties_alg_stats[alg_name][alg_qual_name]['deviance_rows'].append(freq_dev_rows)
						properties_alg_stats[alg_name][alg_qual_name]['deviance_cols'].append(freq_dev_cols)
			#print(alg_quals)
			#print()
		if i != 0 and i % 50 == 0:
			for alg_name in sorted(properties_alg_stats.keys()):
				alg_quals = properties_alg_stats[alg_name]
				print(alg_name)
				for qual_name in sorted(alg_quals.keys()):
					stats = alg_quals[qual_name]
					print("\t", qual_name, len(stats['deviance_rows']))
					print("\t\tRD: %.2f %.2f %.2f" % (statistics.median(stats['deviance_rows']), min(stats['deviance_rows']), max(stats['deviance_rows'])))
					print("\t\tCD: %.2f %.2f %.2f" % (statistics.median(stats['deviance_cols']), min(stats['deviance_cols']), max(stats['deviance_cols'])))
					#print(stats['deviance_rows'])
			break

			#print(properties_alg_stats)
		#print()
		#print()

