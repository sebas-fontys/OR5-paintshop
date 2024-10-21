# IMPORTS
from itertools import count
from math import inf
import random as rng
import numpy as np
from abc import ABC, abstractmethod
import time
from heuristics_constructive import ConstructiveHeuristic, Random
from move import GenerateNew, Move
from schedule import Schedule
from time import time
from moveSelectionStrategy import MoveSelectionStrategies, MoveSelectionStrategy
from text_decoration import GREEN, RED, TEXT_GREEN, TEXT_RED, YELLOW, ColorDecoration, DecorationTypes, decorate
# from heuristics_improvement import ImprovementHeuristic

# DATA CLASS FOR IMPROVEMENT RUN ITERATION
class HeuristicIterationData:
    def __init__(self, time: float, move: Move, cost: float):
        self.time = time # Time it took to determine the move
        self.move = move # The move made
        self.cost = cost # The cost after the move
                
        

# DATA CLASS FOR IMPROVEMENT RUN
class HeuristicRunData:
    def __init__(self, improver, initial: Schedule):
        self.improver                                 = improver # ImprovementHeuristic instance
        self.initial: Schedule                        = initial  # Initial schedule
        self.best: Schedule                           = initial  # Best schedule
        self.last: Schedule                           = initial  # Last schedule
        self.iterations: list[HeuristicIterationData] = [        # Iterations made
            HeuristicIterationData(0, None, initial.cost)
        ]
        self.time = 0



# ABSTRACT IMPROVEMENT HEURISTIC
class ImprovementHeuristic(ABC):
    
    name = 'abstract'
        
    # I think this method makes it so that the strategy field is exposed on the interface.
    @abstractmethod
    def __init__(self, strategy: MoveSelectionStrategy):
        self.strategy = strategy

    # 
    @abstractmethod
    def run(self, run_data: HeuristicRunData, verbosity: 0|1|2 = 2) -> HeuristicRunData:
        """Determine the move to make according to the heuristic.

        Returns:
            tuple[Move, Schedule]: The move and the moved schedule. 
            If the move is None, the heuristic reached termination. 
            Schedule can never be None - in the case of termination, it will be the original schedule.
        """
        pass
        
    @abstractmethod
    def __str__(self) -> str:
        pass
    
    @abstractmethod
    def run_timed(self, run_data: HeuristicRunData, t0, t_max, verbosity: 0|1|2 = 2) -> HeuristicRunData:
        pass
    
    @staticmethod
    def print_iteration(base_message: str, iteration: int, time: float, last_cost: int, best_cost: int, verbosity: int, move: Move, schedule: Schedule):
        # Print if verbose
        if verbosity > 0:
            if verbosity > 1:
                print("")
            improvement = (last_cost is not None) and (last_cost > schedule.cost)
            change_color = (YELLOW if schedule.cost < best_cost else GREEN) if improvement else RED
            print(f"""[{
                    base_message
                }] [{time:.1f}] {
                    iteration
                }: [{
                    decorate(f'{schedule.cost:.0f}', [ColorDecoration(DecorationTypes.TEXT, change_color)])
                }] {
                    move
                }""")
            if verbosity > 1:
                print(f'{schedule}\n')
    


# BASIC DISCRETE IMPROVEMENT (run to local optimum according to given strategy)
class Basic(ImprovementHeuristic):
     
    name = 'basic'
     
    #   
    def __init__(self, strategy: MoveSelectionStrategy):
        self.strategy = strategy
        
    #
    def __str__(self):
        return "_".join([
            Basic.name,
            self.strategy.name,
        ])   
        
        
    def run_timed(self, run_data: HeuristicRunData, t0, t_max, verbosity: 0|1|2 = 2):
        
        # Generator in the case that a local optimum is found but time is not up
        generator = GenerateNew(Random)
        
        # Loop until termination
        while True:
            
            # Define criteria
            def must_improve(s: Schedule):
                return s.cost < run_data.last.cost
                        
            # Get move according to the move selection strategy and the criteria
            move, moved = self.strategy.try_get_move(
                run_data.last, 
                must_improve
            )
            
            # If no improving move found: generate new start
            if move is None:
                move, moved = (generator, generator.get_moved(run_data.last))
            
            # Break if time limit exceeded
            move_time = time() - t0
            if move_time > t_max:
                if verbosity > 0:
                    print(decorate("Time limit reached.", [TEXT_RED]))
                break
            
            # Make move
            run_data.last = moved
            
            # Print if verbose
            ImprovementHeuristic.print_iteration(
                str(self),
                len(run_data.iterations), 
                move_time,
                run_data.iterations[-1].cost, 
                run_data.best.cost, 
                verbosity, 
                move, 
                run_data.last
            )
            
            # Log
            iteration_data = HeuristicIterationData(
                move_time,
                move,
                run_data.last.cost
            )
            run_data.iterations.append(iteration_data)
            
            # If improving move found:
            if run_data.last.cost < run_data.best.cost:
                run_data.best = run_data.last
        
        # Return
        run_data.time = time() - t0
        return run_data 
    
    #
    def run(self, run_data: HeuristicRunData, verbosity: 0|1|2 = 2) -> HeuristicRunData:
        
        t0 = time()
        
        # Loop until termination
        while True:
            
            # Define criteria
            def must_improve(s: Schedule):
                return s.cost < run_data.last.cost
                        
            # Get move according to the move selection strategy and the criteria
            move, moved_schedule = self.strategy.try_get_move(
                run_data.last, 
                must_improve
            )
            
            move_time = time() - t0
            
            # Break if optimum reached
            if move is None:
                if verbosity > 0:
                    print(decorate("Optimum reached.", [TEXT_GREEN]))
                break
            else:
                run_data.last = moved_schedule
                        
            # Print log
            ImprovementHeuristic.print_iteration(
                str(self),
                len(run_data.iterations), 
                move_time,
                run_data.iterations[-1].cost, 
                run_data.best.cost, 
                verbosity, 
                move, 
                run_data.last
            )
            
            # Add iteration data
            run_data.iterations.append(HeuristicIterationData(
                move_time,
                move,
                run_data.last.cost
            ))
            
            run_data.best = run_data.last
        
        run_data.time = time() - t0
        return run_data

# TABOO SEARCH (allow non-improving moves but keep a blacklist of previous solutions)
class Taboo(ImprovementHeuristic):

    name = 'taboo'

    # 
    def __init__(self, improvement_strategy: MoveSelectionStrategy, non_improvement_strategy: MoveSelectionStrategy, max_iterations: int = inf, taboo_len: int = None):
        self.taboo_len = taboo_len
        self.improvement_strategy = improvement_strategy
        self.non_improvement_strategy = non_improvement_strategy
        self.max_iterations = max_iterations
    
    #
    def __str__(self):
        return "_".join([str(x) for x in [
            Taboo.name,
            self.improvement_strategy.name,
            self.non_improvement_strategy.name,
            self.taboo_len,
            self.max_iterations
        ]])
    
    #
    def run(self, schedule: Schedule, verbosity: 0|1|2 = 2, taboo_set: set[str] = set(), t0 = time(), t_max = None) -> HeuristicRunData:
                
        # Create run data object
        run_data = HeuristicRunData(self, schedule)
        
        # Add initial to 
        
        # Loop until termination
        while len(run_data.iterations) < self.max_iterations:
            
            
            # Add current schedule to taboo set
            taboo_set.add(hash(schedule))
                        
            # (Re)define criteria (should arguably be a lambda)
            def criteria_improve(s: Schedule) -> bool:
                return s.cost < schedule.cost # Dayum... [1,2,3,4,5][-3::] => [3,4,5]
            
            # Try to get an improving move
            move, moved_schedule = self.improvement_strategy.try_get_move(
                schedule, 
                criteria_improve
            )
            
            # No improving move found: Do a non improving move that is not taboo
            if move is None:
                
                # (Re)define criteria (should arguably be a lambda)
                if self.taboo_len is None:
                    def criteria_nontaboo(schedule: Schedule) -> bool:
                        return hash(schedule) not in taboo_set
                else:
                    def criteria_nontaboo(schedule: Schedule) -> bool:
                        return hash(schedule) not in taboo_set[-self.taboo_len::] # Dayum... [1,2,3,4,5][-3::] => [3,4,5]

                # Get best move accoring to strategy & taboo list
                move, moved_schedule = self.non_improvement_strategy.try_get_move(
                    schedule, 
                    criteria_nontaboo
                )
            
            # Break if optimum reached
            if move is None:
                if verbosity > 0:
                    if verbosity > 1:
                        print("")
                    print(decorate("Optimum reached.", [TEXT_GREEN]))
                break
            
            # Break if time limit exceeded
            if (t_max is not None) and ((time() - t0) > t_max):
                if verbosity > 0:
                    print(decorate("Time limit reached.", [TEXT_RED]))
                break
            
            # Set schedule to new schedule
            schedule = moved_schedule
            
            # Print if verbose
            ImprovementHeuristic.print_iteration(
                len(run_data.iterations), 
                time() - t0,
                run_data.iterations[-1].cost, 
                run_data.best.cost, 
                verbosity, 
                move, 
                schedule
            )
            
            # Append iteration data
            run_data.iterations.append(
                HeuristicIterationData(
                    time() - t0,
                    move,
                    schedule.cost
                )
            )
                        
            # Update best if best
            if schedule.cost < run_data.best.cost:
                run_data.best = schedule
            
            
            
        # Return none because no improving feasible solution found
        run_data.last = schedule
        return run_data
    
    def run_timed(self, run_data: HeuristicRunData, t0, t_max, verbosity: 0|1|2 = 2) -> HeuristicRunData:
        
        taboo_set: set[str] = set()
        
        # Loop until termination
        while run_data.iterations[-1].time < t_max:
            
            # Add current schedule to taboo set
            taboo_set.add(hash(run_data.last))
                        
            # (Re)define criteria (should arguably be a lambda)
            def criteria_improve(s: Schedule) -> bool:
                return s.cost < run_data.last.cost
            
            # Try to get an improving move
            move, moved = self.improvement_strategy.try_get_move(
                run_data.last, 
                criteria_improve
            )
            
            # No improving move found: Do a non improving move that is not taboo
            if move is None:
                
                # (Re)define criteria (should arguably be a lambda)
                def criteria_nontaboo(schedule: Schedule) -> bool:
                    return hash(schedule) not in taboo_set

                # Get best move accoring to strategy & taboo list
                move, moved = self.non_improvement_strategy.try_get_move(
                    run_data.last, 
                    criteria_nontaboo
                )
            
            # Break if no moved left
            if move is None:
                if verbosity > 0:
                    if verbosity > 1:
                        print("")
                    print(decorate("Optimum reached.", [TEXT_GREEN]))
                break
            
            move_time = time() - t0
            
            # Break if time limit exceeded
            if move_time > t_max:
                if verbosity > 0:
                    print(decorate("Time limit reached.", [TEXT_RED]))
                break
            
            # Set schedule to new schedule
            run_data.last = moved
            
            # Print if verbose
            ImprovementHeuristic.print_iteration(
                str(self),
                len(run_data.iterations), 
                move_time,
                run_data.iterations[-1].cost, 
                run_data.best.cost, 
                verbosity, 
                move, 
                run_data.last
            )
            
            # Append iteration data
            run_data.iterations.append(
                HeuristicIterationData(
                    move_time,
                    move,
                    run_data.last.cost
                )
            )
                        
            # Update best if best
            if run_data.last.cost < run_data.best.cost:
                run_data.best = run_data.last
            
            
            
        # Return none because no improving feasible solution found
        run_data.time = time() - t0
        return run_data
   

class Annealing(ImprovementHeuristic):
    
    name = 'annealing'
    
    def __init__(self, delta_factor: int):
        self.delta_factor = delta_factor

    def __str__(self):
        return "_".join([str(x) for x in [
            Annealing.name,
            self.delta_factor
        ]])
        
    def run_timed(self, run_data: HeuristicRunData, t0, t_max, verbosity: 0|1|2 = 2):
        
        # Iterate infinitely
        for i in count(start=0):
            
            # Generate a random neighbour
            move, moved = MoveSelectionStrategies.random.try_get_move(run_data.last)
            
            # Determine move time
            t_move = time() - t0
            
            # Calculate temperature
            temp = 1 - t_move/t_max
            
            # Break if temperature < 0
            if temp <= 0:
                break
            
            # Determine if move is accepted
            cost_delta = moved.cost - run_data.last.cost
            if (cost_delta < 0) or (rng.random() < np.exp(-cost_delta/(temp * self.delta_factor))):
                
                # Make move
                run_data.last = moved
                
                # Print move
                ImprovementHeuristic.print_iteration(
                    str(self),
                    i, 
                    t_move,
                    run_data.iterations[-1].cost, 
                    run_data.best.cost, 
                    verbosity, 
                    move, 
                    moved
                )
                
                # Log move
                run_data.iterations.append(HeuristicIterationData(
                    t_move,
                    move,
                    moved.cost
                ))
                
                # Update best
                if moved.cost < run_data.best.cost:
                    run_data.best = moved
                    
        # Return
        run_data.time = time() - t0
        return run_data
                
    def run(self, schedule: Schedule, iterations, verbosity: 0|1|2 = 2, t0 = time()) -> HeuristicRunData:
                
        # Initialize
        run_data = HeuristicRunData(self, schedule)
        
        # self.iterations may be "time",
        # in this case, the temperature will be time-based, ending at 0 when time() - t0 == t_max
        if self.iterations == "time":
            # temp_iterations = range(inf)
            temp_iterations = count(start=0)
        else:
            temp_iterations = range(self.iterations)
        
        # Run until cold
        for i in temp_iterations:
            
            
            # Generate a random neighbour
            move, moved = MoveSelectionStrategies.random.try_get_move(schedule)
            
            # Determine move time
            t_move = time() - t0
                
            # Break if time limit reached
            if (t_max is not None) and (t_move > t_max):
                break
            
            # Calculate temperature
            if self.iterations == "time":
                temp = 1 - (t_move+1)/t_max
            else:
                temp = 1 - (i+1)/self.iterations
            
            # If move is acceptable
            delta = moved.cost - schedule.cost
            if (delta < 0) or ((temp > 0) and (rng.random() < np.exp(-(delta / self.delta_factor)/temp))):
                
                # Make move
                schedule = moved
                
                # Print
                ImprovementHeuristic.print_iteration(
                    str(self),
                    i, 
                    t_move,
                    run_data.iterations[-1].cost, 
                    run_data.best.cost, 
                    verbosity, 
                    move, 
                    schedule
                )
                
                # Update best
                if schedule.cost < run_data.best.cost:
                    run_data.best = schedule
                
                # Log move
                run_data.iterations.append(HeuristicIterationData(
                    t_move,
                    move,
                    moved.cost
                ))
            
        # Return
        run_data.last = schedule
        return run_data
    
# Not sure if and why this is neccessary
ImprovementHeuristic.register(Basic)
ImprovementHeuristic.register(Taboo)
ImprovementHeuristic.register(Annealing)

class ImprovementHeuristics:
    
    basic = Basic
    taboo = Taboo
    annealing = Annealing
    all: list[ImprovementHeuristic] = [basic, taboo, annealing]