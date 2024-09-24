# IMPORTS
import copy
import matplotlib.pyplot as plt
import itertools as iter
import matplotlib.patches as patches
import matplotlib.patches as mpatches
from abc import ABC, abstractmethod


# Initialize PaintShop
from paintshop import PaintShop
PS = PaintShop()


# Private funcs
def to_red(string: str) -> str:
    return f"\x1b[31m{string}\x1b[0m"

def to_green(string: str) -> str:
    return f"\x1b[32m{string}\x1b[0m"

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
        self.queues = [
            [] for _ in PS.machine_ids
        ]
        
        # Order penalty by index in queue
        self.penalties: dict[tuple[int, int], float] = {}
        
    
    # EQUALITY OPERATOR
    def __eq__(self, other):
        
        # Two schedules are equal if (and only if) their queues are equal
        return self.queues == other.queues
    
    
    # HASHING (needed for creating a set of schedules during validation)
    def __hash__(self):
        
        # Lists cannot be hashed, tuples can however.
        return hash(
            '|'.join([
                '-'.join([
                    str(order) for order in queue
                ])
            for queue in self.queues
            ])
        )
    
        
    # INDEX GETTER
    def __getitem__(self, index: tuple[int, int]) -> list[int] | int:
        """Gets the order index at the specified queue index for the specified machine index.

        Args:
            index tuple[int, int]: A tuple containing the machine index at position 0 and the queue index at position 1.

        Returns:
            list[int] or int: The order index at the specified position in the schedule or the queue for the specified machine if the second index is a slice.
        """
        return self.queues[index[0]][index[1]]
    
    
    # INDEX SETTER
    def __setitem__(self, index: tuple[int, int], queue: list[int] | int):
        """Sets the queue for the machine with the specified machine-number

        Args:
            machine_id (int): The index of the machine.
            queue (list[int]): The queue for the specified machine.
        """
        self.queues[index[0]][index[1]] = queue
    
    
    # INDEX DELETION
    def __delitem__(self, index: tuple[int, int]):
        
        # Set queue as two contatenated slices where the item at index is skipped.
        self[index[0], :] = self[index[0], :index[1]] + self[index[0], (index[1]+1):]
    
    
    # STRING CONVERSION
    def __str__(self) -> str:
        
        self.calculate_penalties()
        
        # Determine machine strings
        machine_strings = [f'M{machine_id + 1}: ' for machine_id in PS.machine_ids]
        longest_ms = max([len(ms) for ms in machine_strings])
        machine_strings_justed = [
            f'{ms.ljust(longest_ms)}' for ms in machine_strings
        ]
        
        # Determine queue strings
        longest_order_id = len(str(max(PS.order_ids)))
        longest_queue = max([len(queue) for queue in self.queues])
        queue_strings_basic = [[str(id).rjust(longest_order_id) for id in queue] for queue in self.queues]
        queue_string_lengths = [len('  '.join(qs)) for qs in queue_strings_basic]
        
        queue_strings_colored = [
            '  '.join([(to_red(str) if (self.penalties[(mi,qi)] > 0) else to_green(str)) for qi, str in enumerate(queue)]) for mi, queue in enumerate(queue_strings_basic)
        ]
        # longest_qs = max([len(qs) for qs in queue_strings])
        longest_queue_string_len = max(queue_string_lengths)
        
        queue_strings_justed = [
            f'[ {qs + " "*(longest_queue_string_len - queue_string_lengths[mi])} ]' for mi, qs in enumerate(queue_strings_colored)
        ]
        
        # Determine cost strings
        cost_strings = [
            f' {self.get_cost_machine(machine_id):.2f}' for machine_id in PS.machine_ids
        ]
        longest_cs = max([len(cs) for cs in cost_strings])
        cost_strings_justed = [
            f'{cs.ljust(longest_cs)}' for cs in cost_strings
        ]
        
        # Determine cost % strings
        cost_fracs = [
            f' ({(self.get_cost_machine(machine_id) / self.get_cost() * 100):.0f}%)' for machine_id in PS.machine_ids
        ]
        
        # Determine header
        longest_queue = max([len(q) for q in self.queues])    
        header = f'{" "*longest_ms}  {"  ".join([str(i).rjust(longest_order_id) for i in range(longest_queue)])}   {self.get_cost():.2f}'
        # footer = f'{"Total cost:".ljust(longest_ms + longest_qs + 4)} {self.get_cost():.2f}'
        
        return '\n'.join([
            header,
            '\n'.join([machine_strings_justed[i] + queue_strings_justed[i] + cost_strings_justed[i] + cost_fracs[i] for i in PS.machine_ids]),
            # footer
        ])

    
    # # Returns the solution in pandas.DataFrame form
    # def to_dataframe(self) -> pd.DataFrame:
    #     """Returns the Solution converted to a pandas.DataFrame.

    #     Returns:
    #         pd.DataFrame: The Solution in dataframe form.
    #     """
        
    #     return pd.DataFrame.from_dict(
    #         self.order_queue,
    #     ).rename(columns ={
    #         machine_id: f"M{machine_id + 1}" 
    #         for machine_id in machine_ids
    #     })
    
    # Returns information about the current machine schedules on the order level.
    def get_machine_schedules(self) -> list[list[dict[str, float]]]:
        """Returns information about the current machine schedules on the order level such as order-processing starting- and ending-times

        Returns:
            list[list[dict[str, float]]]: A list (index: machine ID) containing lists (index: order queue index) of dictionaries containing the following data on the order execution:
            - "start": start time in time units since schedule start, 
            - "duration": processing duration in time units, 
            - "end": order processing completion time in time units since schedule start, 
            - "order": the order ID,
            - "cost": the penalty related to the deadline of the order.
        """
        
        machine_schedules = [[] for _ in self.machine_ids]
        
        for machine_id in self.machine_ids:
            
            t_current = 0
            last_order_id = None
        
            for order_id in self.queues[machine_id]:
                
                if (last_order_id != None):
                    t_current += PS.get_setup_time(last_order_id, order_id)
                
                processing_time = PS.orders.loc[order_id, "surface"] / PS.machine_speeds[machine_id]
                machine_schedules[machine_id] += [{
                    "start": t_current, 
                    "duration": processing_time, 
                    "end": t_current + processing_time, 
                    "order": order_id,
                    "cost": 0 
                        if ((t_current + processing_time) > self.orders.loc[order_id, "deadline"]) 
                        else (t_current + processing_time) * self.orders.loc[order_id, "penalty"]
                }]
                
                t_current += processing_time
                last_order_id = order_id
                
        return machine_schedules
    
    # Draws the schedule using matplotlib.pyplot
    def draw(self) -> None:
        
        # Get machine order execution start times and durations
        machine_schedules = self.get_machine_schedules()
        
        # Determine schedule end-time
        schedule_completion_time = max([machine_schedule[-1]["end"] for machine_schedule in machine_schedules])
        
        # Declaring a figure "gnt"
        fig = plt.figure(figsize= (20,5))
        
        # Iterate over machines
        for machine_id in PS.machine_ids:
            
            # Plot dividing line above current machine schedule
            if machine_id != 0:
                plt.plot(
                    (0, schedule_completion_time), 
                    (machine_id - 0.5, machine_id - 0.5),
                    "black"
                )
            
            # Plot order processing
            for job in machine_schedules[machine_id]:
                
                # Add rectangle representing the job
                plt.gca().add_patch(
                    patches.Rectangle(
                        (
                            job["start"], 
                            machine_id - 0.4
                        ), 
                        job["duration"], 
                        0.8,
                        fill = True, 
                        facecolor = PS.get_order_color_name(job["order"]),
                        # edgecolor = 'red' if (job["cost"] > 0) else 'black',
                        edgecolor = 'black'
                        # linewith = 1
                    )
                )
                
                # Add text to center of rectangle
                plt.text(
                    job["start"] + job["duration"] / 2, 
                    machine_id,
                    f"O{job['order'] + 1}",
                    # f"O{job['order'] + 1}\n\n{job['cost']:.0f}",
                    horizontalalignment = "center",
                    verticalalignment = "center",
                ) 
        
        # Graph decoration
        plt.title(f"Schedule. Duration: {schedule_completion_time:.0f}. Cost: {self.get_cost():.0f}")
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
        
        
    # Return the time at which the machine with the specified ID finishes it's order queue
    def get_finish_time(self, machine_id: int) -> float:
        
        # Processing time when starting on the current order
        t = 0
        last_order_id = None
        
        # Iterate over orders in queue
        for order_id in self.queues[machine_id]:
            
            # Add processing time to current time
            t += PS.get_processing_time(order_id, machine_id)
            
            # Add setup time
            if (last_order_id != None):
                t += PS.get_setup_time(last_order_id, order_id)
            
            # Update last order ID
            last_order_id = order_id
            
        return t
    
    
    # TODO improve this
    def calculate_penalties(self) -> None:
        self.get_cost()
    
    
    
    # Get the cost for the machine with the given machine_id
    def get_cost_machine(self, machine_id):
        # Processing time when starting on the current order
        t = 0
        last_order_id = None
            
        # Initialize penalty
        total_penalty = 0
            
        # Iterate over orders in queue
        for queue_index, order_id in enumerate(self.queues[machine_id]):
            
            # Add processing time to current time
            t += PS.get_processing_time(order_id, machine_id)
            
            # Add setup time
            t += PS.get_setup_time(last_order_id, order_id)
            
            # Calculate penalty
            penalty = PS.get_penalty(order_id, t)
            
            # Add penalty to total_cost
            total_penalty += penalty
            
            # Save penalty
            self.penalties[(machine_id, queue_index)] = penalty
            
            # Update last order ID
            last_order_id = order_id
        
        return total_penalty
    
    
    # Returns the total cost of the solution
    def get_cost(self) -> float:
        """Returns the total penalty for this schedule.

        Returns:
            float: The total penalty
        """
        
        # Initialize penalty
        total_penalty = 0
        
        # Iterate over machines in schedule
        for machine_id in PS.machine_ids:
            
            total_penalty += self.get_cost_machine(machine_id)
        
        # Return total penalty
        return total_penalty
    
    
    # # Returns a list of all possible moves.
    # def get_moves(self) -> list[Move]:
        
    #     # Get all indices of the orders.
    #     order_indices = [(machine_id, queue_index) for machine_id in PS.machine_ids for queue_index in range(len(self.queues[machine_id]))]
        
    #     # Return all combinations of length 2.
    #     return list(iter.combinations(order_indices, 2))
    
    
    def is_last_in_queue(self, index: tuple[int, int]):
        return index[1] == (len(self[index[0], :]) - 1)
    
    # Return a copy of self
    def get_copy(self):
        return copy.deepcopy(self)




# # DEBUG
# Construct an empty solution dictionary.
schedule = Schedule()

import random as rng
import numpy as np

# Create list of shuffled order ID's
order_ids_remaining = PS.order_ids
rng.shuffle(order_ids_remaining)

while len(order_ids_remaining) > 0:
    
    next_order_id_index = rng.choice(range(len(order_ids_remaining)))
    
    schedule[rng.choice(PS.machine_ids), :] += [order_ids_remaining[next_order_id_index]]
    
    order_ids_remaining = np.delete(order_ids_remaining, next_order_id_index)
    
    schedule.calculate_penalties()
    
    
    
print(schedule)