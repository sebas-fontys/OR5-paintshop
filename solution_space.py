from math import factorial
from more_itertools import distinct_permutations
from paintshop import PaintShop
from sterling import count_part, gen_part


def get_distinct_permutation_count(n, n_dupes):
    return factorial(n) // factorial(n_dupes)


cache = {}
def update_cache(n,k):
    cumulative_count = 0
    
    # Initialize cache entry    
    key = n,k
    cache[key] = []
    n_distperms = []
    
    # For each (number of empty partitions)
    for e in range(0,k):
        
        # Number of ways to make the remaining k-e partitions.
        n_parts = count_part(n, k-e)
        
        # Number of ways to permute a partition with e duplicates
        n_perms = get_distinct_permutation_count(k, e)
        
        # Add values multiplied
        n_distperms += [n_parts * n_perms]
        
        # Add to cache
        cumulative_count += n_parts * n_perms
        cache[key] += [(cumulative_count, e, n_parts, n_perms)]


def get_solution_space_size(ps: PaintShop) -> int:
    """Return the size of the solution space to the given PaintShop instance."""
    
    # Localize variables
    n = ps.order_count
    k = ps.machine_count
    key = n,k
    
    # Ensure cache
    if key not in cache:
        update_cache(n,k)
    
    # Return last cumulative count
    return cache[key][-1][0]


def get_ith_solution(ps: PaintShop, i):
    """Returns the i'th solution to the given PaintShop instance."""
    
    n = ps.order_count
    k = ps.machine_count
    
    key = n,k
    if key not in cache:
        update_cache(n,k)
          
    #DEBUG
    
    last_s_count_cum = 0
    for s_count_cum, e, n_parts, n_perms in cache[n, k]:
        
        # Skip if higher
        if i >= s_count_cum:
            last_s_count_cum = s_count_cum
            continue
        
        # Get local solution index
        i_given_e = i - last_s_count_cum
        
        i_part, i_perm  = divmod(i_given_e, n_perms)
                
        # Empty parts
        e_parts: list[list[int]] = [[] for _ in range(e)]
        
        
        part = [*e_parts, *gen_part(ps.order_ids, k-e, i_part)]
        
        # Get i_perm'th partition
        # print(f"Getting permutation #{i_perm} of partition #{i_part} granted {e} empties.")
        perm = list(distinct_permutations(part))[i_perm]

        return perm