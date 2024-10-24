# IMPORTS
import copy
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.patches as mpatches
from text_decoration import BACKGROUND_BLACK, BOLD, TEXT_GREEN, TEXT_RED, TEXT_YELLOW, UNDERLINE, ColorDecoration, decorate

# To avoid circular imports
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from move import Move
else:
    class Move:
        pass


# Initialize PaintShop
from paintshop import PaintShop
# PS = PaintShop()





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
    def __init__(self, ps: PaintShop, move: Move = None):
        
        self.ps = ps
        self.move = move
        
        """Constructs an empty schedule."""
        self.__queues: list[list[int]] = [
            [] for _ in ps.machine_ids
        ]
        
        # The time at which the orders are completed by their queue-index.
        self.__completion_times: dict[tuple[int, int], float] = {
            (mi, -1): 0 for mi in ps.machine_ids
        }
        
        # The penalty of the orders by their queue-index.
        self.__cumulative_penalties: dict[tuple[int, int], float] = {
            (mi, -1): 0 for mi in ps.machine_ids
        }
        
        # Penalties by queue
        self.queue_costs: list[float] = [
            0 for _ in ps.machine_ids
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
            for i in range(*index[0].indices(len(order))):
                self.__queues[i][index[1]] = order[i]
            return
        
        self.__queues[index[0]][index[1]] = order
    
    # INDEX DELETION (can use slice, but not using negative number)
    def __delitem__(self, index: tuple[int, int]):
        del self.__queues[index[0]][index[1]]
        
    # STRING CONVERSION
    def __str__(self, show_move = True) -> str:
        
        # Determine machine strings
        machine_strings = [f'M{machine_id + 1}: ' for machine_id in self.ps.machine_ids]
        longest_ms = max([len(ms) for ms in machine_strings])
        machine_strings_justed = [
            f'{ms.ljust(longest_ms)}' for ms in machine_strings
        ]
        
        # Determine queue strings
        longest_order_id = len(str(max(self.ps.order_ids)))
        longest_queue = max([len(queue) for queue in self.__queues])
        queue_strings_basic = [[f" {str(id).rjust(longest_order_id)} " for id in queue] for queue in self.__queues]
        queue_string_lengths = [len(''.join(qs)) for qs in queue_strings_basic]
        
        # Function for decoration order
        def decorate_order(mi: int, qi: int, o: str) -> str:
            decorations: list[ColorDecoration] = []
            
            # Text red if penalty
            if (self.__cumulative_penalties[(mi,qi)] > self.__cumulative_penalties[(mi,qi - 1)]):
                decorations.append(TEXT_RED)
            else:
                decorations.append(TEXT_GREEN)
                
            # Backgroud gray if moved
            if show_move and (self.move is not None):
                if self.move.is_moved(mi, qi):
                    decorations += [BACKGROUND_BLACK]
            
            # Return with decorations applied
            return decorate(o, decorations)
        
        queue_strings_decorated = [
            ''.join([
                decorate_order(mi, qi, str) for qi, str in enumerate(queue)
            ]) for mi, queue in enumerate(queue_strings_basic)
        ]
        # longest_qs = max([len(qs) for qs in queue_strings])
        longest_queue_string_len = max(queue_string_lengths)
        
        queue_strings_justed = [
            f'|{qs + " "*(longest_queue_string_len - queue_string_lengths[mi])}|' for mi, qs in enumerate(queue_strings_decorated)
        ]
        
        # Determine cost strings
        cost_strings = [
            f' {self.queue_costs[machine_id]:.2f}' for machine_id in self.ps.machine_ids
        ]
        longest_cs = max([len(cs) for cs in cost_strings])
        cost_strings_justed = [
            f'{cs.ljust(longest_cs)}' for cs in cost_strings
        ]
        
        # Determine cost % strings
        cost_fracs = [
            (f' ({(self.queue_costs[machine_id] / self.cost * 100):.0f}%)' if self.cost > 0 else '') for machine_id in self.ps.machine_ids
        ]
        
        # Determine header
        longest_queue = max([len(q) for q in self.__queues])    
        header = f'{" "*longest_ms}| {"  ".join([str(i).rjust(longest_order_id) for i in range(longest_queue)])} | {decorate(f"{self.cost:.2f}", [TEXT_YELLOW])} {"✔" if self.is_feasible() else "✘"}'
        # footer = f'{"Total cost:".ljust(longest_ms + longest_qs + 4)} {self.get_cost():.2f}'
        
        return '\n'.join([
            header,
            '\n'.join([machine_strings_justed[i] + queue_strings_justed[i] + cost_strings_justed[i] + cost_fracs[i] for i in self.ps.machine_ids]),
            # footer
        ])

    # COST CALCULATION
    def calc_cost(self):
        for mi in self.ps.machine_ids:
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
            t_done = t_start + self.ps.get_processing_time(order, machine) + self.ps.get_setup_time(order_prev, order)
            self.__completion_times[(machine, qi)] = t_done
            
            # Calculate and set cumulative penalty
            cumulative_penalty = cumulative_penalty_prev + self.ps.get_penalty(order, t_done)
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
        return set(self.ps.order_ids) == set(oi for queue in self[:,:] for oi in queue)
    
    
    # PLOT USING PYPLOT
    def plot(self, legend = False) -> None:
        
        plt.rcParams["hatch.linewidth"] = 4
        # setup_hatch = r"||"
        setup_hatch = r"//"
        setup_c1 = (0,0,0,0.3)
        setup_c2 = 'white'
        
        # Get machine order execution start times and durations
        # machine_schedules = self.get_machine_schedules()
        
        # Determine schedule end-time
        schedule_completion_time = max([self.get_completion_time(mi) for mi in self.ps.machine_ids])
        
        # Declaring a figure "gnt"
        fig = plt.figure(figsize = (30,6))
        
        # Iterate over machines
        for mi in self.ps.machine_ids:
            
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
                
                processing_time = self.ps.get_processing_time(oi, mi)
                completion_time = self.__completion_times[(mi, qi)]
                
                # Optionally draw setup time
                if (qi > 0) and (self.ps.get_setup_time(self[mi, qi-1], oi) > 0):
                    plt.gca().add_patch(
                        patches.Rectangle(
                            (
                                self.__completion_times[(mi, qi-1)], 
                                mi - 0.3
                            ),
                            self.ps.get_setup_time(self[mi, qi-1], oi),
                            0.6,
                            fill = True, 
                            facecolor = setup_c1,
                            edgecolor = setup_c2,
                            # facecolor = self.ps.get_order_color_name(oi),
                            # edgecolor = self.ps.get_order_color_name(self[mi, qi-1]),
                            hatch=setup_hatch,
                            zorder = -1
                            # linewith = 1
                        )
                    )
                
                # Add rectangle representing the job
                plt.gca().add_patch(
                    patches.Rectangle(
                        (
                            completion_time - processing_time, 
                            mi - 0.4
                        ),
                        processing_time,
                        0.8,
                        fill = True, 
                        facecolor = self.ps.get_order_color_name(oi),
                        # edgecolor = 'red' if (job["cost"] > 0) else 'black',
                        edgecolor = 'black',
                        # alpha = 0.5
                        # linewith = 1
                    )
                )
                
                # Add text to center of rectangle
                plt.text(
                    completion_time - processing_time / 2, 
                    mi,
                    f"O{oi + 1}",
                    # f"O{job['order'] + 1}\n\n{job['cost']:.0f}",
                    horizontalalignment = "center",
                    verticalalignment = "center",
                ) 
        
        # Graph decoration
        plt.title(f"Schedule. Duration: {schedule_completion_time:.0f}. Cost: {self.cost:.0f}")
        plt.ylim(self.ps.machine_count - 0.5, -0.5)
        plt.xlim(0, schedule_completion_time)
        plt.yticks(self.ps.machine_ids, [f"M{id+1}" for id in self.ps.machine_ids])
        plt.xlabel(f"Elapsed time units since start of schedule execution.")
        
        # Compose custom legend
        colors_patches = [
            mpatches.Patch(color=c, label=c) for c in self.ps.get_color_names()
        ] + [
            mpatches.Patch(facecolor=setup_c1, edgecolor = setup_c2, hatch = setup_hatch, label='Setup')
        ]
        if legend:
            plt.legend(
                handles = colors_patches,
                title = "Tasks"
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