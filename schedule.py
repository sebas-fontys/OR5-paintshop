# IMPORTS
import copy
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.patches as mpatches


# Initialize PaintShop
from paintshop import PaintShop
PS = PaintShop()


# Utility funcions
def to_red(string: str) -> str:
    return f"\x1b[31m{string}\x1b[0m"

def to_green(string: str) -> str:
    return f"\x1b[32m{string}\x1b[0m"

def to_yellow(string: str) -> str:
    return f"\x1b[33m{string}\x1b[0m"


# SCHEDULE CLASS:
# Represents a solution to the paintshop problem.
# This class internally stores the solution as a 2-level list.
# This outer list represents the machines and each inner list represents the order queues for a particular machine.
# This class contains many function related to a schedule such as draw() and get_copy().
# This class also has implements 2D indexers to get, set and delete.
class Schedule:
    """
    This class represents a solution to the paintshop-problem in the form of an order queue for each machine to be processed in-order.
    This class supports indexing and has many usefull functions such as draw(), get_cost() and get_copy().
    """
    
    # CONSTRUCTOR
    def __init__(self):
        """Constructs an empty schedule."""
        self.__queues: list[list[int]] = [
            [] for _ in PS.machine_ids
        ]
        
        # The time at which the orders are completed by their queue-index.
        self.__completion_times: dict[tuple[int, int], float] = {
            (mi, -1): 0 for mi in PS.machine_ids
        }
        
        # The penalty of the orders by their queue-index.
        self.__cumulative_penalties: dict[tuple[int, int], float] = {
            (mi, -1): 0 for mi in PS.machine_ids
        }
        
        # Penalties by queue
        self.queue_costs: list[float] = [
            0 for _ in PS.machine_ids
        ]
        
    # EQUALITY OPERATOR
    def __eq__(self, other) -> bool:
        
        # Two schedules are equal if (and only if) their queues are equal
        return self.__queues == other.__queues
    
    # HASHING (needed for creating a set of schedules during validation)
    def __hash__(self) -> int:
        
        # Lists cannot be hashed, tuples can however.
        return hash(
            '|'.join([
                '-'.join([
                    str(order) for order in queue
                ])
            for queue in self.__queues
            ])
        )
    
    # INDEX GETTER (supports slicing)
    def __getitem__(self, index: tuple[int, int]) -> list[int] | int:
        """Gets the order index at the specified queue index for the specified machine index.

        Args:
            index tuple[int, int]: A tuple containing the machine index at position 0 and the queue index at position 1.

        Returns:
            list[int] or int: The order index at the specified position in the schedule or the queue for the specified machine if the second index is a slice.
        """        
        return self.__queues[index[0]][index[1]]
    
    # INDEX SETTER (supports slicing for the second index)
    # TODO: Fix -> doesnt work when using two slices like: schedule[:,:] = [[],[],[]]
    def __setitem__(self, index: tuple[int, int], order: int | list[int] | list[list[int]]) -> None:
        
        # If index[0] is a slice, loop over slice indices
        if isinstance(index[0], slice):
            for i in index[0].indices(len(order)):
                self.__queues[i][index[1]] = order[i]
            return
        
        self.__queues[index[0]][index[1]] = order
    
    # INDEX DELETION (can use slice, but not using negative number)
    def __delitem__(self, index: tuple[int, int]):
        del self.__queues[index[0]][index[1]]
        
    # STRING CONVERSION
    def __str__(self) -> str:
        
        # Determine machine strings
        machine_strings = [f'M{machine_id + 1}: ' for machine_id in PS.machine_ids]
        longest_ms = max([len(ms) for ms in machine_strings])
        machine_strings_justed = [
            f'{ms.ljust(longest_ms)}' for ms in machine_strings
        ]
        
        # Determine queue strings
        longest_order_id = len(str(max(PS.order_ids)))
        longest_queue = max([len(queue) for queue in self.__queues])
        queue_strings_basic = [[str(id).rjust(longest_order_id) for id in queue] for queue in self.__queues]
        queue_string_lengths = [len('  '.join(qs)) for qs in queue_strings_basic]
        
        queue_strings_colored = [
            '  '.join([
                (
                    to_red(str)
                    if (
                        # (qi > 0) &
                        (self.__cumulative_penalties[(mi,qi)] > self.__cumulative_penalties[(mi,qi - 1)])
                    ) else 
                    to_green(str)
                ) for qi, str in enumerate(queue)
            ]) for mi, queue in enumerate(queue_strings_basic)
        ]
        # longest_qs = max([len(qs) for qs in queue_strings])
        longest_queue_string_len = max(queue_string_lengths)
        
        queue_strings_justed = [
            f'| {qs + " "*(longest_queue_string_len - queue_string_lengths[mi])}  |' for mi, qs in enumerate(queue_strings_colored)
        ]
        
        # Determine cost strings
        cost_strings = [
            f' {self.queue_costs[machine_id]:.2f}' for machine_id in PS.machine_ids
        ]
        longest_cs = max([len(cs) for cs in cost_strings])
        cost_strings_justed = [
            f'{cs.ljust(longest_cs)}' for cs in cost_strings
        ]
        
        # Determine cost % strings
        cost_fracs = [
            (f' ({(self.queue_costs[machine_id] / self.cost * 100):.0f}%)' if self.cost > 0 else '') for machine_id in PS.machine_ids
        ]
        
        # Determine header
        longest_queue = max([len(q) for q in self.__queues])    
        header = f'{" "*longest_ms}| {"  ".join([str(i).rjust(longest_order_id) for i in range(longest_queue)])}  | {to_yellow(f"{self.cost:.2f}")} {"✔" if self.is_feasible() else "✘"}'
        # footer = f'{"Total cost:".ljust(longest_ms + longest_qs + 4)} {self.get_cost():.2f}'
        
        return '\n'.join([
            header,
            '\n'.join([machine_strings_justed[i] + queue_strings_justed[i] + cost_strings_justed[i] + cost_fracs[i] for i in PS.machine_ids]),
            # footer
        ])

    
    # COST CALCULATION
    def calc_cost(self):
        for mi in PS.machine_ids:
            self.calc_queue_cost_from(mi, 0)
    
    # OPTIMISED COST CALCULATION
    def calc_queue_cost_from(self, machine, first_change_index):
        
        # Get chached starting time   
        t_start = self.__completion_times[(machine, first_change_index - 1)]
        
        # Get order before current index. (Can optimize since we only need the color)
        order_prev = self.__queues[machine][first_change_index - 1] if first_change_index > 0 else None
        
        # Get current cumulative penalty for this queue
        cumulative_penalty_prev = 0 if (order_prev is None) else self.__cumulative_penalties[(machine, first_change_index - 1)]
        
        # For each order at index change_index or higher:
        for qi in range(first_change_index, len(self.__queues[machine])):
           
            # Localize order 
            order = self.__queues[machine][qi]
            
            # Get and set completion time
            t_done = t_start + PS.get_processing_time(order, machine) + PS.get_setup_time(order_prev, order)
            self.__completion_times[(machine, qi)] = t_done
            
            # Calculate and set cumulative penalty
            cumulative_penalty = cumulative_penalty_prev + PS.get_penalty(order, t_done)
            self.__cumulative_penalties[(machine, qi)] = cumulative_penalty
            cumulative_penalty_prev = cumulative_penalty
            
            # Update previous order & t_start
            order_prev = order
            t_start = t_done
            
        # Set queue penalty to be the last cumulative penalty
        self.queue_costs[machine] = self.__cumulative_penalties[(machine, len(self.__queues[machine]) - 1)]
    
        # Calc total cose
        self.cost = sum(self.queue_costs)
            
    # FEASABILITY CHECK
    def is_feasible(self) -> bool:
        return set(PS.order_ids) == set(oi for queue in self[:,:] for oi in queue)
    
    
    # PLOT USING PYPLOT
    def plot(self) -> None:
        
        # Get machine order execution start times and durations
        # machine_schedules = self.get_machine_schedules()
        
        # Determine schedule end-time
        schedule_completion_time = max([self.get_completion_time(mi) for mi in PS.machine_ids])
        
        # Declaring a figure "gnt"
        fig = plt.figure(figsize = (20,5))
        
        # Iterate over machines
        for mi in PS.machine_ids[::-1]:
            
            # Plot dividing line above current machine schedule
            if mi != 0:
                plt.plot(
                    (0, schedule_completion_time), 
                    (mi - 0.5, mi - 0.5),
                    "black"
                )
            
            # Plot order processing
            oi: int
            for qi, oi in enumerate(self[mi, :]):
                
                processing_time = PS.get_processing_time(oi, mi)
                
                # Add rectangle representing the job
                plt.gca().add_patch(
                    patches.Rectangle(
                        (
                            self.__completion_times[(mi, qi)] - processing_time, 
                            mi - 0.4
                        ), 
                        processing_time, 
                        0.8,
                        fill = True, 
                        facecolor = PS.get_order_color_name(oi),
                        # edgecolor = 'red' if (job["cost"] > 0) else 'black',
                        edgecolor = 'black'
                        # linewith = 1
                    )
                )
                
                # Add text to center of rectangle
                plt.text(
                    self.__completion_times[(mi, qi)] - processing_time / 2, 
                    mi,
                    f"O{oi + 1}",
                    # f"O{job['order'] + 1}\n\n{job['cost']:.0f}",
                    horizontalalignment = "center",
                    verticalalignment = "center",
                ) 
        
        # Graph decoration
        plt.title(f"Schedule. Duration: {schedule_completion_time:.0f}. Cost: {self.cost:.0f}")
        plt.ylim(-0.5, len(PS.machine_ids) - 0.5)
        plt.xlim(0, schedule_completion_time)
        plt.yticks(PS.machine_ids, [f"M{id+1}" for id in PS.machine_ids])
        plt.xlabel(f"Elapsed time units since start of schedule execution.")
        
        # Compose custom legend
        colors_patches = [
            mpatches.Patch(color=c, label=c) for c in PS.get_color_names()
        ]
        plt.legend(
            handles = colors_patches,
            title = "Paint colors"
        )
        # plt.grid()
        
        # Show graph
        plt.show()
        
    # GET QUEUE COMPLETION TIME
    def get_completion_time(self, machine_id: int) -> float:
        return self.__completion_times[(machine_id, len(self[machine_id, :]) - 1)]
    
    # CHECK IF INDEX IS LAST IN QUEUE
    def is_last_in_queue(self, index: tuple[int, int]):
        return index[1] == (len(self[index[0], :]) - 1)
    
    # GET COPY
    def get_copy(self):
        return copy.deepcopy(self)