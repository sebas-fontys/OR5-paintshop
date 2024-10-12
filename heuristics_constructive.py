# IMPORTS
from abc import ABC, abstractmethod
import copy
from itertools import permutations
from math import factorial

from paintshop import PaintShop
from schedule import Schedule
import random as rng

from solution_space import get_ith_solution, get_solution_space_size
from sterling import count_part, gen_part

# CONSTANTS
SEED = 420

# SETUP
rng.seed(SEED)


# 
class ConstructiveHeuristic(ABC):
    
    name: str
    
    @abstractmethod
    def generate(verbosity: 0|1 = 0) -> Schedule:
        pass

# BASIC
class Simple(ConstructiveHeuristic):
    
    def __init__(self, PS: PaintShop):
        self.PS = PS
    
    # STATIC
    name = "Simple"
    
    # @staticmethod
    def generate(self, verbosity: 0|1 = 0) -> Schedule:
        
        # Construct an empty schedule.
        schedule = Schedule()
        
        # For each order, ordered by their deadline
        for order_id in sorted(self.PS.order_ids, key = lambda order_id: self.PS.orders.loc[order_id, 'deadline']):
            
            # Add order to the queue of the machine with the lowest completion time.
            machine_id_next = sorted(
                self.PS.machine_ids, 
                key = lambda i: len(schedule[i, :]) + i / len(self.PS.machine_ids)
            )[0]
            
            # Add order to machine queue.
            queue_len = len(schedule[machine_id_next, :])
            schedule[machine_id_next, queue_len:queue_len] = [order_id]
            
            # Calculate penalties
            schedule.calc_queue_cost_from(machine_id_next, len(schedule[machine_id_next, :]) - 1)
            
            # Print if verbose
            if verbosity >= 1:
                print(f'\n{schedule}')
            
            # schedule.append(machine_id_next, order_id)
        
        # Return finished schedule
        return schedule
   

# GREEDY
class Greedy(ConstructiveHeuristic):
    
    def __init__(self, PS: PaintShop):
        self.PS = PS
    
    # STATIC
    name = "Greedy"
    
    # @staticmethod
    def generate(self, verbosity: 0|1 = 0) -> Schedule:
        
        # Construct an empty schedule.
        schedule = Schedule()
        
        # For each order, ordered by their deadline
        for order_id in sorted(self.PS.order_ids, key = lambda order_id: self.PS.orders.loc[order_id, 'deadline']):
            
            # Add order to the queue of the machine with the lowest completion time.
            machine_id_next = sorted(
                self.PS.machine_ids, 
                key = lambda i: schedule.get_completion_time(i)
            )[0]
            
            # Add order to machine queue.
            queue_len = len(schedule[machine_id_next, :])
            schedule[machine_id_next, queue_len:queue_len] = [order_id]
            
            # Calculate penalties
            schedule.calc_queue_cost_from(machine_id_next, len(schedule[machine_id_next, :]) - 1)
            # schedule.append(machine_id_next, order_id)
        
        # Return finished schedule
        return schedule
    

# RANDOM
class Random(ConstructiveHeuristic):    
    
    def __init__(self, PS: PaintShop):
        self.PS = PS
    
    # STATIC
    name = "Random"
    
    # @staticmethod
    def generate(self, verbosity: 0|1 = 0, i = 0) -> Schedule:
        """Generates a random schedule, with an equal probability for all possible schedules.

        Args:
            verbosity (0 | 1, optional): 0 => prints nothing, 1 => prints info about the constructive process. Defaults to 0.

        Returns:
            Schedule: The constructed schedule.
        """
        
        # Construct an empty solution dictionary.
        schedule = Schedule(self.PS)
        
        # Generate a number in the range [0, solution space size)
        i = rng.randint(0, get_solution_space_size(self.PS))
        
        # Set queues & calulate cost
        schedule[:,:] = get_ith_solution(self.PS, i)
        schedule.calc_cost()
        
        # Return
        return schedule


# Not sure if and why this is neccessary
ConstructiveHeuristic.register(Simple)
ConstructiveHeuristic.register(Greedy)
ConstructiveHeuristic.register(Random)


class ConstructiveHeuristics:
    
    def __init__(self, PS: PaintShop):
        self.PS = PS
    
        self.simple: Simple = Simple(self.PS)
        self.greedy: Greedy = Greedy(self.PS)
        self.random: Random = Random(self.PS)
        self.all: list[ConstructiveHeuristic] = [self.simple, self.greedy, self.random]