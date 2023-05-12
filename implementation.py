#!/usr/bin/python
import random
from bloom_filter2 import BloomFilter
from pympler import asizeof
import time
import bbhash
from bbhash_table import BBHashTable
import sys

def random_key(length):
	letters = 'abcdefghijklmnopqrstuvwxyz'
	return ''.join(random.choice(letters) for i in range(length))

print(random_key(10))

class Bloom:
	def __init__(self, max_elements, error_rate):
		self.bloom = BloomFilter(max_elements=max_elements, error_rate=error_rate)

	def build_filter(self, keys):
		for key in keys:
			self.bloom.add(key)
	
	def query_filter(self, key):
		return key in self.bloom
	
	def size(self):
		return asizeof.asizeof(self.bloom)

class MPHF:
	def __init__(self):
		pass
	
	def build_table(self, keys):
		num_threads = 1
		gamma = 1.0
		hashed_keys = [abs(hash(key)) for key in keys]
		self.hashes = bbhash.PyMPHF(hashed_keys, len(keys), num_threads, gamma)
	
	def query_table(self, key):
		# print("index is", self.hashes.lookup(abs(hash(key))))
		return self.hashes.lookup(abs(hash(key))) is not None
	
	def size(self):
		# return asizeof.asizeof(self.hashes)
		return self.hashes.get_mem()

def get_last_n_bits(num, n):
	mask = (1 << n) - 1
	last_n_bits = num & mask
	return last_n_bits

class AugMPHF:
	def __init__(self, num_elements, fingerprint_size):
		self.num_elements = num_elements
		self.fingerprints = [None] * num_elements
		self.fingerprint_size = fingerprint_size
	
	def build_table(self, keys):
		num_threads = 1
		gamma = 1.0
		hashed_keys = [abs(hash(key)) for key in keys]
		self.hashes = bbhash.PyMPHF(hashed_keys, len(keys), num_threads, gamma)
		for key in keys:
			self.fingerprints[self.hashes.lookup(abs(hash(key)))] = get_last_n_bits(abs(hash("." + key)), self.fingerprint_size)
	
	def query_table(self, key):
		# print("index is", self.hashes.lookup(abs(hash(key))))
		in_table = self.hashes.lookup(abs(hash(key))) is not None
		if in_table:
			prints_match = self.fingerprints[self.hashes.lookup(abs(hash(key)))] == get_last_n_bits(abs(hash("." + key)), self.fingerprint_size)
		return in_table and prints_match
	
	def size(self):
		# return asizeof.asizeof(self.hashes)
		# print(asizeof.asizeof(self.fingerprints), sys.getsizeof(self.fingerprints))
		return (self.num_elements * self.fingerprint_size) / 8

def run_bloom_tests():
	# 3 sizes: 1000, 10000, 100000
	# 3 positive/negative mixtures: 50%, 5%, 0.5%
	# 3 filters: 1/128, 1/256, 1/1024
	fp_rates = [1/128, 1/256, 1/1024]
	sizes = [1000, 10000, 100000]
	props = [.5, .05, .005]

	for fp_rate in fp_rates:
		for size in sizes:
			keys = [random_key(31) for i in range (size)]
			for prop in props:
				num_matches = int(1000 * prop)
				num_original = 1000 - num_matches
				keysp = random.sample(keys, num_matches)
				keysp += [random_key(31) for i in range (num_original)]
				
				bf = Bloom(size, fp_rate)
				bf.build_filter(keys)

				recorded_matches = 0
				start = time.perf_counter()
				for key in keysp:
					if (bf.query_filter(key)):
						recorded_matches += 1
				end = time.perf_counter()
				print(fp_rate, size, prop, (recorded_matches - num_matches) / size, f"{end - start:0.4f}", bf.size())

def run_mphf_tests():
	# 3 sizes: 1000, 10000, 100000
	# 3 positive/negative mixtures: 50%, 5%, 0.5%
	# 3 filters: 1/128, 1/256, 1/1024
	sizes = [1000, 10000, 100000]
	props = [.5, .05, .005]

	for size in sizes:
		keys = [random_key(31) for i in range (size)]
		for prop in props:
			num_matches = int(1000 * prop)
			num_original = 1000 - num_matches
			keysp = random.sample(keys, num_matches)
			keysp += [random_key(31) for i in range (num_original)]
			
			mph = MPHF()
			mph.build_table(keys)

			recorded_matches = 0
			start = time.perf_counter()
			for key in keysp:
				if mph.query_table(key):
					recorded_matches += 1
				# if not mph.query_table(key):
				# 	print("what (1)")
			# for key in keysn:
			# 	if mph.query_table(key):
			# 		print("what")
			end = time.perf_counter()
			print(size, prop, (recorded_matches - num_matches) / size, f"{end - start:0.6f}")


def run_amphf_tests():
	# 3 sizes: 1000, 10000, 100000
	# 3 positive/negative mixtures: 50%, 5%, 0.5%
	# 3 filters: 1/128, 1/256, 1/1024
	print_sizes = [7, 8, 10]
	sizes = [1000, 10000, 100000]
	props = [.5, .05, .005]

	for fp_size in print_sizes:
		for size in sizes:
			keys = [random_key(31) for i in range (size)]
			for prop in props:
				num_matches = int(1000 * prop)
				num_original = 1000 - num_matches
				keysp = random.sample(keys, num_matches)
				keysp += [random_key(31) for i in range (num_original)]
				
				amph = AugMPHF(size, fp_size)
				amph.build_table(keys)

				recorded_matches = 0
				start = time.perf_counter()
				for key in keysp:
					if (amph.query_table(key)):
						recorded_matches += 1
				end = time.perf_counter()
				print(fp_size, size, prop, (recorded_matches - num_matches) / size, f"{end - start:0.4f}", amph.size())

run_amphf_tests()