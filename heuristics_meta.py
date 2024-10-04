# IMPORTS
from abc import ABC, abstractmethod
import copy
import math

import numpy as np
from heuristics_improvement import ImprovementStrategy
from move import Move
from paintshop import PaintShop
from schedule import Schedule
import random as rng

# CONSTANTS
PS = PaintShop()
SEED = 420


# SETUP
rng.seed(SEED)


# ABSTRACT META HEURISTIC

# Meta heuristics are instantiated, as opposed to the others.

class MetaHeuristic(ABC):
    
    name: str = 'abstract_meta'
    name_display: str = 'Abstract Metaheuristic'
    
    @abstractmethod
    def get_move() -> tuple[Move, Schedule]:
        """Determine the move to make according to the heuristic.

        Returns:
            tuple[Move, Schedule]: The move and the moved schedule. 
            If the move is None, the heuristic reached termination. 
            Schedule can never be None - in the case of termination, it will be the original schedule.
        """
        pass
   

# TABOO SEARCH
class Tabu(MetaHeuristic):


    # Static    
    name: str = 'tabu'
    name_display = 'Tabu search'

    def __init__(self, initial: Schedule, tabu_list_len: int, improvement_strategy: ImprovementStrategy):
        self.list_len = tabu_list_len
        self.strategy = improvement_strategy
        
        self.incumbent = initial
        self.incumbent_cost = initial.get_cost()
        
        self.current = initial
        self.cur_iter = 0
        
        # Initialise tabu list (hashes of previous schedules)
        self.tabu: list[str] = []
    
    # TODO: Optimize by not copying schedule so much
    def get_move(self) -> tuple[Move, Schedule]:
        
        # # Calculate current cost
        # current_cost = self.current.get_cost()
        
        # best_move: Move
        # best_moved: Schedule
        # best_cost = -math.inf
        
        all_moves: list[Move] = Move.get_moves(self.current)
        
        # Get list of all allowed moves
        moves = [
            (move, moved_schedule)
            for move, moved_schedule in [
                (move, move.get_moved(self.current)) for move in all_moves
            ] if (hash(moved_schedule) not in self.tabu)
        ]
        
        # Get move according to strategy
        return self.strategy.get_move(moves, math.inf)
        
        
        # Loop over all possible moves
        # move: Move # Cannot do type hints in a for loop: https://peps.python.org/pep-0526/#id11
        # for move in Move.get_moves(self.current):
            
        #     # Get the moved schedule.
        #     moved_schedule = move.get_moved(self.current)
        #     moved_penalty = moved_schedule.get_cost()
            
        #     # Get schedule hash
        #     moved_hash = hash(moved_schedule)
            
        #     # If tabu does not contain the schedule:        
        #     if (not moved_hash in self.tabu) & (moved_penalty < best_cost):
                
        #         # Keep track of best move
        #         best_move = move
        #         best_moved = moved_schedule
        #         best_cost = moved_penalty
                
        
        # Return none because no improving feasible solution found
        # return (best_move, best_moved)
    

# Register subclasses
MetaHeuristic.register(Tabu)