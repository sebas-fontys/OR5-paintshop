# # Function to calculate a Sterling number of the second order for n and k.
# # AKA, the amount of ways to k-way partition a set of n elements (excluding empty sets).
# # Used to calculate to size of the solution space.
# # Modified from https://rosettacode.org/wiki/Stirling_numbers_of_the_second_kind#Python
# sterling2_cache = {}
# def sterling2(n, k):
    
#     # Cache key
# 	key = f"{n},{k}"

#     # Check for cached
# 	if key in sterling2_cache.keys():
# 		return sterling2_cache[key]

#     # Trivial cases
# 	if n == k == 0:
# 		return 1
# 	if (n > 0 and k == 0) or (n == 0 and k > 0):
# 		return 0
# 	if n == k:
# 		return 1
# 	if k > n:
# 		return 0

#     # Compute
# 	result = k * sterling2(n - 1, k) + sterling2(n - 1, k - 1)
# 	sterling2_cache[key] = result
# 	return result


### Above code discarded in favor of the code below.


# Functions to find i-th k-way partitioning of a set if n elements
# Modified from https://stackoverflow.com/questions/45829748/python-finding-random-k-subset-partition-for-a-given-list
fact = [1]
def nCr(n: int, k: int) -> int:
    """Return number of ways of choosing k elements from n"""
    while len(fact)<=n:
        fact.append(fact[-1]*len(fact))
    return fact[n]//(fact[k]*fact[n-k])

cache = {}
def count_part(n: int, k: int) -> int:
    """Return number of ways of partitioning n items into k non-empty subsets"""
    if k==1:
        return 1
    key = n,k
    if key in cache:
        return cache[key]
    # The first element goes into the next partition
    # We can have up to y additional elements from the n-1 remaining
    # There will be n-1-y left over to partition into k-1 non-empty subsets
    # so n-1-y>=k-1
    # y<=n-k
    t = 0
    for y in range(0,n-k+1):
        t += count_part(n-1-y,k-1) * nCr(n-1,y)
    cache[key] = t
    return t

def ith_subset(A: list, k: int, i: int) -> list:
    """Returns the first subset from the ith k-subset partition of A"""
    # Choose first element x
    n = len(A)
    if n==k:
        return A
    if k==0:
        return []
    for x in range(n):
        # Find how many cases are possible with the first element being x
        # There will be n-x-1 left over, from which we choose k-1
        extra = nCr(n-x-1,k-1)
        if i<extra:
            break
        i -= extra
    return [A[x]] + ith_subset(A[x+1:],k-1,i)

def gen_part(A: list, k: int, i: int) -> list[list]:
    """Return i^th k-partition of elements in A (zero-indexed) as list of lists"""
    if k==1:
        return [A]
    n=len(A)
    # First find appropriate value for y - the extra amount in this subset
    for y in range(0,n-k+1):
        extra = count_part(n-1-y,k-1) * nCr(n-1,y)
        if i<extra:
            break
        i -= extra
    # We count through the subsets, and for each subset we count through the partitions
    # Split i into a count for subsets and a count for the remaining partitions
    count_partition,count_subset = divmod(i,nCr(n-1,y))
    # Now find the i^th appropriate subset
    subset = [A[0]] + ith_subset(A[1:],y,count_subset)
    S=set(subset)
    return  [subset] + gen_part([a for a in A if a not in S],k-1,count_partition)