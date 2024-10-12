# IMPORTS
import random as rng
import numpy as np
from abc import ABC, abstractmethod
import time
from move import Move
from schedule import Schedule
from time import time
from moveSelectionStrategy import MoveSelectionStrategies, MoveSelectionStrategy
from text_decoration import GREEN, RED, YELLOW, ColorDecoration, DecorationTypes, decorate
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
        self.total_time: int                          = 0        # Total processing time
        self.iterations: list[HeuristicIterationData] = []       # Iterations made



# ABSTRACT IMPROVEMENT HEURISTIC
class ImprovementHeuristic(ABC):
    
    name = 'abstract'
        
    # I think this method makes it so that the strategy field is exposed on the interface.
    @abstractmethod
    def __init__(self, strategy: MoveSelectionStrategy):
        self.strategy = strategy

    # 
    @abstractmethod
    def run(self, initial: Schedule, verbosity: 0|1|2 = 2) -> HeuristicRunData:
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
    
    #
    def run(self, schedule: Schedule, verbosity: 0|1|2 = 2) -> HeuristicRunData:
        
        # Record starting time
        t0_run = time.time()
        
        # Create run data object
        run_data = HeuristicRunData(self, schedule)
        
        # Loop until termination
        while True:
            
            # Define criteria
            def criteria(s: Schedule):
                return s.cost < schedule.cost
            
            # Record starting time
            t0_move = time()
            
            # Get move according to the move selection strategy and the criteria
            move, schedule = self.strategy.try_get_move(
                schedule, 
                criteria
            )
            
            # Break if optimum reached
            if move is None:
                if verbosity > 0:
                    print("Optimum reached.")
                break
            
            # Add iteration data
            run_data.iterations.append(HeuristicIterationData(
                time() - t0_move,
                move,
                schedule.cost
            ))
            
            # Print if verbose
            if verbosity > 0:
                print(f'{len(run_data.iterations)}: [{schedule.cost:.2f}] {move}')
                if verbosity > 1:
                    print(f'{schedule}\n')
            
        # Return last solution (will allways be best)
        run_data.best = schedule
        run_data.last = schedule
        run_data.total_time = time() - t0_run
        return run_data


# TABOO SEARCH (allow non-improving moves but keep a blacklist of previous solutions)
class Taboo(ImprovementHeuristic):

    name = 'taboo'

    # 
    def __init__(self, improvement_strategy: MoveSelectionStrategy, non_improvement_strategy: MoveSelectionStrategy, max_iterations: int, taboo_len: int = None):
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
    def run(self, schedule: Schedule, verbosity: 0|1|2 = 2, taboo_set: set[str] = set()) -> HeuristicRunData:
        
        # Record time
        t0_run = time()
        
        # Create run data object
        run_data = HeuristicRunData(self, schedule)
        
        # Add initial to 
        
        # Loop until termination
        cur_iteration = 0
        last_schedule_cost = schedule.cost
        while cur_iteration < self.max_iterations:
            
            
            # Add current schedule to taboo set
            cur_iteration += 1
            taboo_set.add(hash(schedule))
            
            # Record starting time
            t0_move = time()
            
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
                    print("\nOptimum reached.")
                break
            
            # Set schedule to new schedule
            schedule = moved_schedule
            
            # Append iteration data
            run_data.iterations.append(
                HeuristicIterationData(
                    time() - t0_move,
                    move,
                    schedule.cost
                )
            )
            
            # Print if verbose
            if verbosity > 0:
                if verbosity > 1:
                    print("")
                improvement = (last_schedule_cost is not None) and (last_schedule_cost > schedule.cost)
                change_color = (YELLOW if schedule.cost < run_data.best.cost else GREEN) if improvement else RED
                print(f"""{
                        len(run_data.iterations)
                    }: [{decorate(f'{schedule.cost:.0f}', [ColorDecoration(DecorationTypes.TEXT, change_color)])}] {
                        move
                    }""")
                if verbosity > 1:
                    print(f'{schedule}\n')
                    
            last_schedule_cost = schedule.cost
            
            # Update best if best
            if schedule.cost < run_data.best.cost:
                run_data.best = schedule
            
            
            
        # Return none because no improving feasible solution found
        run_data.last = schedule
        run_data.total_time = time() - t0_run
        return run_data

class Annealing(ImprovementHeuristic):
    def __init__(self, initial_temp,cool_rate,it_per_temp,end_temp):
        self.initial_temp=initial_temp
        self.cool_rate=cool_rate
        self.it_per_temp=it_per_temp
        self.end_temp=end_temp

    def run(self, schedule: Schedule, verbosity: 0|1|2 = 2, cached: HeuristicRunData = None) -> HeuristicRunData:
        
        # Log starting time
        t0_run = time()
        
        # Initialize
        temp=self.initial_temp
        run_data = HeuristicRunData(self, schedule)
        
        # Run until cold
        last_schedule_cost = schedule.cost
        while temp > self.end_temp:
            for _ in range(self.it_per_temp):
                
                t0_move = time()
                
                # Calculate move
                move, moved=MoveSelectionStrategies.random.try_get_move(schedule)
                delta=moved.cost-schedule.cost
                
                # If the move improves, or temperature allows non-inproving:
                if (delta < 0) or (rng.random() < np.exp(-delta/temp)):
                    
                    # Make move
                    schedule = moved
                    if schedule.cost < run_data.best.cost:
                        run_data.best = schedule
                    
                    # Log move
                    run_data.iterations.append(HeuristicIterationData(
                        time() - t0_move,
                        move,
                        moved.cost
                    ))
                    
                    # Print if verbose
                    if verbosity > 0:
                        if verbosity > 1:
                            print("")
                        improvement = (last_schedule_cost is not None) and (last_schedule_cost > schedule.cost)
                        change_color = ('yellow' if schedule.cost < run_data.best.cost else 'green') if improvement else 'red'
                        print(f"""{
                                len(run_data.iterations)
                            }: [{decorate(f'{schedule.cost:.0f}', change_color)}] {
                                move
                            }""")
                        if verbosity > 1:
                            print(f'{schedule}\n')
                    last_schedule_cost = schedule.cost
                            
            
            # Cool it down 
            temp*=self.cool_rate
            
        # Return
        run_data.last = schedule
        run_data.total_time = time() - t0_run
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