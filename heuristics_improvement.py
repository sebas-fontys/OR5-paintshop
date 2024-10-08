# IMPORTS
from abc import ABC, abstractmethod
import time
from move import Move
from schedule import Schedule
from moveSelectionStrategy import MoveSelectionStrategy




# Utility funcions
def colored(s: str, c: str):
    match c:
        case "red":
            return f"\x1b[31m{s}\x1b[0m"
        case "green":
            return f"\x1b[32m{s}\x1b[0m"
        case "yellow":
            return f"\x1b[33m{s}\x1b[0m"


# Data classes for improvement runs
class HeuristicIterationData:
    def __init__(self, index: int, time: float, move: Move, result: Schedule):
        self.index = index
        self.time = time
        self.move = move
        self.result = result

class HeuristicRunData:
    def __init__(self, initial: Schedule):
        self.initial = initial
        self.best = initial
        self.move_count = 0
        self.total_time = 0
        self.iterations: list[HeuristicIterationData] = []



# ABSTRACT IMPROVEMENT HEURISTIC
class ImprovementHeuristic(ABC):
    
    # I think this method makes it so that the strategy field is exposed on the interface.
    @abstractmethod
    def __init__(self, strategy: MoveSelectionStrategy):
        self.strategy = strategy

    # 
    @abstractmethod
    def run(initial: Schedule, verbosity: 0|1|2 = 2) -> HeuristicRunData:
        """Determine the move to make according to the heuristic.

        Returns:
            tuple[Move, Schedule]: The move and the moved schedule. 
            If the move is None, the heuristic reached termination. 
            Schedule can never be None - in the case of termination, it will be the original schedule.
        """
        pass


# BASIC DISCRETE IMPROVEMENT (run to local optimum according to given strategy)
class Basic(ImprovementHeuristic):
        
    def __init__(self, strategy: MoveSelectionStrategy):
        self.strategy = strategy
        
    def run(self, schedule: Schedule, verbosity: 0|1|2 = 2) -> HeuristicRunData:
        
        # Record starting time
        t_total_0 = time.time()
        
        # Create run data object
        data = HeuristicRunData(schedule)
        
        # Loop until termination
        while True:
            
            # Define criteria
            def criteria(s: Schedule):
                return s.cost < schedule.cost
            
            # Record starting time
            t0 = time.time()
            
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
            data.iterations.append(HeuristicIterationData(
                len(data.iterations),
                time.time() - t0,
                move,
                schedule
            ))
            
            # Print if verbose
            if verbosity > 0:
                print(f'\n{len(data.iterations)}: [{schedule.cost}] {move}')
                if verbosity > 1:
                    print(f'{schedule}')
            
        # Return none because no improving feasible solution found
        data.best = data.iterations[-1].result
        data.move_count = len(data.iterations)
        data.total_time = time.time() - t_total_0
        return data


# TABOO SEARCH (allow non-improving moves but keep a blacklist of previous solutions)
class Taboo(ImprovementHeuristic):

    run_cache = 'taboo'

    # 
    def __init__(self, improvement_strategy: MoveSelectionStrategy, non_improvement_strategy: MoveSelectionStrategy, tabu_list_len: int, max_iterations: int):
        self.taboo_count = tabu_list_len
        self.improvement_strategy = improvement_strategy
        self.non_improvement_strategy = non_improvement_strategy
        self.max_iterations = max_iterations
    
    #
    def run(self, schedule: Schedule, verbosity: 0|1|2 = 2, cached: HeuristicRunData = None) -> HeuristicRunData:
        
        # Record time
        t_total_0 = time.time()
        
        # Create run data object
        history: list[str]
        data: HeuristicRunData
        if cached is None:
            data = HeuristicRunData(schedule)
            history = []
        else:
            data = cached
            history = [hash(i.result) for i in data.iterations]
        
        
        
        # Loop until termination
        iterations = 0
        while iterations < self.max_iterations:
            
            iterations += 1
            
            # Record starting time
            t0 = time.time()
            
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
                if self.taboo_count is None:
                    def criteria_nontaboo(schedule: Schedule) -> bool:
                        return hash(schedule) not in history
                else:
                    def criteria_nontaboo(schedule: Schedule) -> bool:
                        return hash(schedule) not in history[-self.taboo_count::] # Dayum... [1,2,3,4,5][-3::] => [3,4,5]

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
            data.iterations.append(
                HeuristicIterationData(
                    len(data.iterations),
                    time.time() - t0,
                    move,
                    schedule
                )
            )
            
            # Print if verbose
            if verbosity > 0:
                if verbosity > 1:
                    print("")
                improvement = len(data.iterations) > 1 and data.iterations[-2].result.cost > schedule.cost
                change_color = ('yellow' if schedule.cost < data.best.cost else 'green') if improvement else 'red'
                print(f"""{
                        len(data.iterations)
                    }: [{colored(f'{data.iterations[-1].result.cost:.0f}', change_color)}] {
                        move
                    }""")
                if verbosity > 1:
                    print(f'{schedule}')
            
            # Update best if best
            if schedule.cost < data.best.cost:
                data.best = schedule
            
            # Add move to history
            history.append(hash(schedule))
            
            
            
        # Return none because no improving feasible solution found
        data.total_time = time.time() - t_total_0
        return data

    
# Not sure if and why this is neccessary
ImprovementHeuristic.register(Basic)
ImprovementHeuristic.register(Taboo)


class ImprovementHeuristics:
    
    simple = Basic
    greedy = Taboo
    all: list[ImprovementHeuristic] = [simple, greedy]