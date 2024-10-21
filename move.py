# IMPORTS
from abc import ABC, abstractmethod
import itertools as iter

from heuristics_constructive import ConstructiveHeuristic
from schedule import Schedule
from paintshop import PaintShop
from typing import Type


# CONSTANTS
# PS = PaintShop()

# Move (Abstract Base Class) (https://docs.python.org/3/library/abc.html)
class Move(ABC):
    
    # As I'm still testing out abstract base classes, I'm raising an exception.
    # Apparantly, abstact methods can only be called by subclasses calling super.func()
    @abstractmethod
    def __init__(self, queue_indices: tuple[tuple[int, int], tuple[int, int]]):
        pass
        
    # STR
    @abstractmethod
    def __str__(self):
        pass
    
    @abstractmethod
    def get_moved(self, schedule_old: Schedule) -> Schedule:
        pass
    
    @staticmethod
    @abstractmethod
    def get_moves(schedule: Schedule) -> list:
        pass
    
    @abstractmethod
    def is_moved(mi, qi) -> bool:
        pass

# Swap two orders by queue index.
class SwapMove(Move):
    
    # Constructor
    def __init__(self, queue_indices: tuple[tuple[int, int], tuple[int, int]]):
        self.a = queue_indices[0]
        self.b = queue_indices[1]
        
    # STR
    def __str__(self):
        return f'swap: {self.a} <=> {self.b}'
    
    # Returns a swapped copy of the specified schedule.
    def get_moved(self, old: Schedule) -> Schedule:
        
        # Create copy of schedule
        new = old.get_copy()
        
        # Apply swap to new
        new[self.b] = old[self.a]
        new[self.a] = old[self.b]
        
        # Recalc penalties
        if self.a[0] == self.b[0]:
            new.calc_queue_cost_from(self.a[0], min(self.a[1], self.b[1]))
        else:
            new.calc_queue_cost_from(self.a[0], self.a[1])
            new.calc_queue_cost_from(self.b[0], self.b[1])
        
        # Return swapped copy
        new.move = self # This may be controversial
        return new
    
    @staticmethod
    def get_moves(schedule: Schedule):
        
        # Get all queue-indices of the orders.
        order_indices = [
            (machine_id, queue_index) 
            for machine_id in schedule.ps.machine_ids for queue_index in range(len(schedule[machine_id, :]))
        ]
        
        # Return all combinations of length 2.
        return [
            SwapMove(swap) for swap in list(iter.combinations(order_indices, 2))
        ]
    
    def is_moved(self, mi, qi):
        return (mi, qi) in [self.a, self.b]
    

# Swap two orders by queue index.
class MoveMove(Move):
    
    def __init__(self, queue_indices: tuple[tuple[int, int], tuple[int, int]]):
        self.a = queue_indices[0]
        self.b = queue_indices[1]
    
    # STR
    def __str__(self):
        return f'move: {self.a} => {self.b}'
    
    # Returns a swapped copy of the specified schedule.
    def get_moved(self, old: Schedule) -> Schedule:
        
        # Create copy of schedule
        new = old.get_copy()
        
        # Apply move (little something i leared called 'slice assignment' and the 'del keyword')
        new[self.b[0], self.b[1]:self.b[1]] = [old[self.a]]
        
        # If an item moves to a position in from of its old position,
        # it's old position will move up by one. (we found out the hard way)
        if (self.a[0] == self.b[0]) and (self.b[1] < self.a[1]):
            del new[(self.a[0], self.a[1] + 1)]
        else:
            del new[self.a]
        
        # Recalc penalties
        if self.a[0] == self.b[0]:
            new.calc_queue_cost_from(self.a[0], min(self.a[1], self.b[1]))
        else:
            new.calc_queue_cost_from(self.a[0], self.a[1])
            new.calc_queue_cost_from(self.b[0], self.b[1])
            
        # Return swapped copy
        new.move = self # This may be controversial
        return new
    
    # Return all possible move-moves
    @staticmethod
    def get_moves(schedule: Schedule):
        
        # Get all queue-indices of the orders. [(0,0), (0,1), (0,2), ...]
        order_indices = [
            (machine_id, queue_index) 
            for machine_id in schedule.ps.machine_ids for queue_index in range(len(schedule[machine_id, :]))
        ]
        
        # Create list of all moves where item 1 is put in front of item 2 (this excludes cases where an item would be put in front of itself)
        all_possible_swaps = list(iter.combinations(order_indices, 2))
        
        moves = all_possible_swaps + [(b, a) for a, b in all_possible_swaps]
        
        # Add the moves where it is added to the end of a queue (slice assigment will add it to the end. It will not throw AOB)
        for order_index in order_indices:
            
            # If not last in queue
            if not schedule.is_last_in_queue(order_index):
                
                # Add move where it is added to the end of the queue
                moves += [
                    (
                        order_index, 
                        (machine_id, len(schedule[machine_id, :]))
                    )
                    for machine_id in schedule.ps.machine_ids
                ]
        
        # Remove moves where it would be inserted behind itself. (this would do nothing, since the source is deleted afterwards)
        # Note: Since swapping index n with index n+1 is the same as moving n in front of n+2, these are exluded also.
        # swap: (0, 13) <=> (0, 14) is equal to move: (0, 14) => (0, 13)
        moves = [
            move for move in moves if not # if NOT
            (
                (move[0][0] == move[1][0]) and             # On the same machine AND
                (
                    (move[1][1] == (move[0][1] - 1)) or    # Target is n-1 (same as swapping with n-1)
                    (move[1][1] == (move[0][1] + 1)) or    # Target is n+1 (does nothing)
                    (move[1][1] == (move[0][1] + 2))       # Target is n+2 (same as swapping)
                )
            )
        ]
        
        # Return instances
        return [MoveMove(move) for move in moves]

    # IS MOVED
    def is_moved(self, mi, qi):
        # Only the desination
        return (mi, qi) == self.b
    

# Swaps the queue of two machines.
class SwapQueuesMove(Move):
    
    def __init__(self, move: tuple[int, int]):
        self.machine_a = move[0]
        self.machine_b = move[1]
    
    
    # STR
    def __str__(self):
        return f'qswp: {self.machine_a} => {self.machine_b}'
    
    
    def get_moved(self, old: Schedule) -> Schedule:
        
        # Create copy of schedule
        new = old.get_copy()
        
        # Apply move (swap two queues)
        new[self.machine_a, :] = old[self.machine_b, :]
        new[self.machine_b, :] = old[self.machine_a, :]
        
        # Recalc penalties
        new.calc_queue_cost_from(self.machine_a, 0)
        new.calc_queue_cost_from(self.machine_b, 0)
        
        # Return swapped copy
        new.move = self # This may be controversial
        return new
    
    
    @staticmethod
    def get_moves(schedule: Schedule):
        
        # Return all 2-item combinations of the machine ID's
        return [SwapQueuesMove(move) for move in list(iter.combinations(schedule.ps.machine_ids, 2))]
    
    # IS MOVED
    def is_moved(self, mi, _):
        # All orders in any of the two queues in question
        return mi in [self.machine_a, self.machine_b]
    
# Swaps two batches (sequences of orders of the same color).
class SwapBatchMove(Move):
    
    #
    def __init__(self, b1: tuple[int, slice], b2: tuple[int, slice]):
        # Batch-index: solution-specific
        self.m1, self.slice1 = b1
        self.m2, self.slice2 = b2
    
    # STR
    def __str__(self):
        return f'bswp: ({self.m1},[{self.slice1.start},{self.slice1.stop}]) => ({self.m2},[{self.slice2.start},{self.slice2.stop}])'
    
    #
    def get_moved(self, old: Schedule) -> Schedule:
        
        # Create copy of schedule
        new = old.get_copy()
        
        # Apply swap
        # If they are one the same machine, apply them back-to-front
        if self.m1 == self.m2:
            queue = old[self.m1,:]
            
            # If slice1 is after slice 2:
            if self.slice1.indices(len(queue))[0] > self.slice2.indices(len(queue))[0]:
                new[self.m1, self.slice1] = old[self.m1, self.slice2]
                new[self.m1, self.slice2] = old[self.m1, self.slice1]
                new.calc_queue_cost_from(self.m1, self.slice2.indices(len(queue))[0])
            # Other way around
            else:
                new[self.m1, self.slice2] = old[self.m1, self.slice1]
                new[self.m1, self.slice1] = old[self.m1, self.slice2]
                new.calc_queue_cost_from(self.m1, self.slice1.indices(len(queue))[0])
        else:
            new[self.m1, self.slice1] = old[self.m2, self.slice2]
            new[self.m2, self.slice2] = old[self.m1, self.slice1]
            new.calc_queue_cost_from(self.m1, self.slice1.indices(len(old[self.m1,:]))[0])
            new.calc_queue_cost_from(self.m2, self.slice2.indices(len(old[self.m2,:]))[0])
        
        # Return
        new.move = self # This may be controversial
        return new
                
    @staticmethod    
    def get_batches(s: Schedule) -> list[tuple[int, slice]]:
         
        batches = []
        for mi, queue in enumerate(s[:,:]): 
            # Determine start and end of batches
            # For each order in q1
            qi = 0
            bi = 0
            
            while (qi + 1) < len(queue):
                
                # Get size of this batch
                batch_len = 1
                # While next index in list and next index has no setup time from previous
                while ((qi + batch_len < len(queue)) and (s.ps.get_setup_time(queue[qi + batch_len - 1], queue[qi + batch_len]) == 0)):
                    batch_len += 1
                
                # Skip if single
                if batch_len == 1:
                    qi = qi + batch_len
                    continue
                
                # Add batch to list
                batches += [(mi, slice(qi, qi+batch_len))]
                
                # Skip to next batch
                bi += 1
                qi = qi + batch_len

        # Return
        return batches
                
    @staticmethod
    def get_moves(schedule: Schedule):
        
        batches = SwapBatchMove.get_batches(schedule)
        permed_batches = list(iter.combinations(batches, 2))
        
        # Return all 2-item combinations of the machine ID's
        
        
        return [SwapBatchMove(batches[0], batches[1]) for batches in permed_batches]    
    
    # IS MOVED
    def is_moved(self, mi, qi):
        
        # If on one of the affected queues:
        if mi in [self.m1, self.m2]:
            
            # Special case where m1 == m2
            if (self.m1 == self.m2):
                return (
                    ( # Between slice.start and slice1.start + slice2.lenght
                        (qi >= self.slice1.start) and 
                        (qi < (self.slice2.stop - self.slice2.start + self.slice1.start))
                    ) or
                    (
                        (qi >= self.slice2.start) and 
                        (qi < (self.slice1.stop - self.slice1.start + self.slice2.start))
                    )
                )
                
            # If mi is m1
            if mi == self.m1:
                return (
                    (qi >= self.slice1.start) and 
                    (qi < (self.slice2.stop - self.slice2.start + self.slice1.start))
                )
            
            # mi is m2
            return (
                (qi >= self.slice2.start) and 
                (qi < (self.slice1.stop - self.slice1.start + self.slice2.start))
            )

# Special move that generates an entirely new schedule
class GenerateNew(Move):
    
    def __init__(self, generator: Type[ConstructiveHeuristic]):
        self.generator = generator
        
    def __str__(self):
        return f'gnew: ({self.generator})'

    def get_moved(self, schedule: Schedule):
        return self.generator(schedule.ps).generate()
    
    def get_moves(schedule: Schedule):
        pass
    
    def is_moved(self):
        return True

move_cache = {}
def get_moves(schedule: Schedule) -> list[Move]: 
    
    cache_key = tuple(len(queue) for queue in schedule[:,:])
    if cache_key in move_cache:
        cache_moves = move_cache[cache_key]
    else:
        cache_moves = [
            *SwapMove.get_moves(schedule),
            *MoveMove.get_moves(schedule),
            *SwapQueuesMove.get_moves(schedule)
        ]
        
    return [
        *cache_moves,
        *SwapBatchMove.get_moves(schedule)
    ]

# ???
Move.register(SwapMove)
Move.register(MoveMove)
Move.register(SwapQueuesMove)
Move.register(SwapBatchMove)