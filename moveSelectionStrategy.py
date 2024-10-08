# IMPORTS
from abc import ABC, abstractmethod
import copy
from typing import Callable

import numpy as np
from move import Move, get_moves
from paintshop import PaintShop
from schedule import Schedule
import random as rng

# CONSTANTS
# PS = PaintShop()
SEED = 420


# SETUP
rng.seed(SEED)


# ABSTRACT IMPROVEMENT HEURISTIC
class MoveSelectionStrategy(ABC):
    
    name: str
    name_display: str

    @abstractmethod
    def try_get_move(schedule: Schedule, solution_allow_criteria: Callable[[Schedule], bool] = None) -> tuple[Move, Schedule]:
        """Determine the move to make according to the heuristic.

        Returns:
            tuple[Move, Schedule]: The move and the moved schedule. 
            If the move is None, the heuristic reached termination. 
            Schedule can never be None - in the case of termination, it will be the original schedule.
        """
        pass
    

# FIRST
class First(MoveSelectionStrategy):
    
    name: str = 'first'
    name_display = 'First move'

    @staticmethod
    def try_get_move(schedule: Schedule, solution_allow_criteria: Callable[[Schedule], bool] = None) -> tuple[Move, Schedule]:
        
        # Get list of moves
        moves = get_moves(schedule)
        
        # If no criteria, return first move
        if solution_allow_criteria is None:
            move: Move = moves[0]
            return (move, move.get_moved(schedule))
        
        # Loop over the moves to find the first allowed move
        for move in moves:
            
            # Get the moved schedule.
            moved_schedule = move.get_moved(schedule)
            
            # Return move if allowed
            if solution_allow_criteria(moved_schedule):
                return (move, moved_schedule)
            
        # No allowed solution found
        return (None, None)


# RANDOM
class Random(MoveSelectionStrategy):
    
    name: str = 'random'
    name_display = 'Random move'

    @staticmethod
    def try_get_move(schedule: Schedule, solution_allow_criteria: Callable[[Schedule], bool] = None) -> tuple[Move, Schedule]:
        
        # Get shuffled list of moves
        moves: list[Move] = get_moves(schedule)
        rng.shuffle(moves)
        
        # DEBUG
        # print(moves[0])
        
        # If no criteria, return first move
        if solution_allow_criteria is None:
            move: Move = moves[0]
            return (move, move.get_moved(schedule))
        
        # Loop over the moves to find the first allowed move
        for move in moves:
            
            # Get the moved schedule.
            moved_schedule = move.get_moved(schedule)
            
            # Return move if allowed
            if solution_allow_criteria(moved_schedule):
                return (move, moved_schedule)
            
        # No allowed solution found
        return (None, None)


# BEST
class Best(MoveSelectionStrategy):
    
    name: str = 'best'
    name_display = 'Best move'

    @staticmethod
    def try_get_move(schedule: Schedule, solution_allow_criteria: Callable[[Schedule], bool] = None) -> tuple[Move, Schedule]:
        
        # Get list of moves & their moved schedules
        moves = [(move, move.get_moved(schedule)) for move in get_moves(schedule)]
        
        # Filter list by criteria
        if solution_allow_criteria is not None:
            moves = [move for move in moves if solution_allow_criteria(move[1])]
        
        # Return best allowed move (first by cost ascending)
        return sorted(
            moves,
            key = lambda move: move[1].cost
        )[0]
    
# Not sure if and why this is neccessary
MoveSelectionStrategy.register(First)
MoveSelectionStrategy.register(Best)
MoveSelectionStrategy.register(Random)


class MoveSelectionStrategies:
    first  = First
    best   = Best
    random = Random
    all: list[MoveSelectionStrategy] = [first, best, random]