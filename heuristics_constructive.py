# IMPORTS
from abc import ABC, abstractmethod
import copy

from paintshop import PaintShop
from schedule import Schedule
import random as rng

from sterling import count_part, gen_part

# CONSTANTS
SEED = 420

# SETUP
rng.seed(SEED)


# 
class ConstructiveHeuristic(ABC):
    
    name: str
    
    @abstractmethod
    def get_schedule(verbosity: 0|1 = 0) -> Schedule:
        pass

# BASIC
class Simple(ConstructiveHeuristic):
    
    def __init__(self, PS: PaintShop):
        self.PS = PS
    
    # STATIC
    name = "Simple"
    
    # @staticmethod
    def get_schedule(self, verbosity: 0|1 = 0) -> Schedule:
        
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
    def get_schedule(self, verbosity: 0|1 = 0) -> Schedule:
        
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
    def get_schedule(self, verbosity: 0|1 = 0) -> Schedule:
        """Generates a random schedule, with an equal probability for all possible schedules.

        Args:
            verbosity (0 | 1, optional): 0 => prints nothing, 1 => prints info about the constructive process. Defaults to 0.

        Returns:
            Schedule: The constructed schedule.
        """
        
        # Construct an empty solution dictionary.
        schedule = Schedule(self.PS)
        
        # Create list of shuffled order ID's
        orders = copy.copy(self.PS.order_ids)
        rng.shuffle(orders)
        
        part_i = rng.randint(0, self.PS.solution_space_partitions)
        
        if verbosity > 0:
            print(f"Generating {part_i}th partitioning of shuffled orders: {orders}")
        
        # Assign to the schedule queue a random partitioning of the schuffled orders.
        # Assigning using two slices doesn't work.
        for i, part in enumerate(gen_part(list(range(len(self.PS.order_ids))), len(self.PS.machine_ids), part_i)):
            schedule[i, :] = part
        # schedule[:,:] = gen_part(list(range(30)), 3, part_i)
        
        # Calc cost
        schedule.calc_cost()
        
        # return
        return schedule


# Not sure if and why this is neccessary
ConstructiveHeuristic.register(Simple)
ConstructiveHeuristic.register(Greedy)
ConstructiveHeuristic.register(Random)


class ConstructiveHeuristics:
    
    def __init__(self, PS: PaintShop):
        self.PS = PS
    
        self.simple = Simple(self.PS)
        self.greedy = Greedy(self.PS)
        self.random = Random(self.PS)
        self.all: list[ConstructiveHeuristic] = [self.simple, self.greedy, self.random]