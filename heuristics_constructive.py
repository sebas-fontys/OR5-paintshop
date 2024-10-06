# IMPORTS
from abc import ABC, abstractmethod
import copy

from paintshop import PaintShop
from schedule import Schedule
import random as rng

from sterling import count_part, gen_part

# CONSTANTS
PS = PaintShop()
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
    
    name = "Simple"
    
    @staticmethod
    def get_schedule(verbosity: 0|1 = 0) -> Schedule:
        
        # Construct an empty schedule.
        schedule = Schedule()
        
        # For each order, ordered by their deadline
        for order_id in sorted(PS.order_ids, key = lambda order_id: PS.orders.loc[order_id, 'deadline']):
            
            # Add order to the queue of the machine with the lowest completion time.
            machine_id_next = sorted(
                PS.machine_ids, 
                key = lambda i: len(schedule[i, :]) + i / len(PS.machine_ids)
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
    
    name = "Greedy"
    
    @staticmethod
    def get_schedule(verbosity: 0|1 = 0) -> Schedule:
        
        # Construct an empty schedule.
        schedule = Schedule()
        
        # For each order, ordered by their deadline
        for order_id in sorted(PS.order_ids, key = lambda order_id: PS.orders.loc[order_id, 'deadline']):
            
            # Add order to the queue of the machine with the lowest completion time.
            machine_id_next = sorted(
                PS.machine_ids, 
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
    
    name = "Random"
    
    @staticmethod
    def get_schedule(verbosity: 0|1 = 0) -> Schedule:
        """Generates a random schedule, with an equal probability for all possible schedules.

        Args:
            verbosity (0 | 1, optional): 0 => prints nothing, 1 => prints info about the constructive process. Defaults to 0.

        Returns:
            Schedule: The constructed schedule.
        """
        
        # Construct an empty solution dictionary.
        schedule = Schedule()
        
        # Create list of shuffled order ID's
        orders = copy.copy(PS.order_ids)
        rng.shuffle(orders)
        
        part_i = rng.randint(0, count_part(30, 3))
        
        if verbosity > 0:
            print(f"Generating {part_i}th partitioning of shuffled orders: {orders}")
        
        # Assign to the schedule queue a random partitioning of the schuffled orders.
        # Assigning using two slices doesn't work.
        for i, part in enumerate(gen_part(list(range(30)), 3, part_i)):
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
    simple = Simple
    greedy = Greedy
    random = Random
    all: list[ConstructiveHeuristic] = [simple, greedy, random]