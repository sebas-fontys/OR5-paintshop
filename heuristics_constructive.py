# IMPORTS
from abc import ABC, abstractmethod
import copy

from paintshop import PaintShop
from schedule import Schedule
import random as rng

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
    
    # Static cached result
    _schedule: Schedule = None
    
    @staticmethod
    def get_schedule(verbosity: 0|1 = 0) -> Schedule:
        
        # Use cached schedule if available
        if Simple._schedule is None:
        
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
            
            # Cache finished schedule
            Greedy._schedule = schedule
            
        # Return finished schedule
        return Greedy._schedule
   

# GREEDY
class Greedy(ConstructiveHeuristic):
    
    name = "Greedy"
    
    # Static cached result
    _schedule: Schedule = None
    
    @staticmethod
    def get_schedule(verbosity: 0|1 = 0) -> Schedule:
        
        # Use cached schedule if available
        if Greedy._schedule is None:
        
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
            
            # Cache finished schedule
            Greedy._schedule_basic = schedule
            
        # Return finished schedule
        return Greedy._schedule
    

# RANDOM
class Random(ConstructiveHeuristic):
    
    name = "Random"
    
    @staticmethod
    def get_schedule(verbosity: 0|1 = 0) -> Schedule:
        
        # Construct an empty solution dictionary.
        schedule = Schedule()
        
        # Create list of shuffled order ID's
        unassigned_orders = copy.copy(PS.order_ids)
        rng.shuffle(unassigned_orders)
        
        # While any order is unassigned
        while len(unassigned_orders) > 0:
            
            # Choose random unassigned order
            oi = rng.choice(range(len(unassigned_orders)))
            
            # Add order to random machine queue
            machine = rng.choice(PS.machine_ids)
            queue_len = len(schedule[machine, :])
            schedule[machine, queue_len:queue_len] = [unassigned_orders[oi]]
            
            # Delete assinged order from list of unassigned orders
            del unassigned_orders[oi]     
        
        # Calculate penalties
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