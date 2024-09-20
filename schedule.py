# IMPORTS
import copy
import matplotlib.pyplot as plt
import itertools as iter
import matplotlib.patches as patches
import matplotlib.patches as mpatches
from abc import ABC, abstractmethod
import copy


# Initialize PaintShop
from paintshop import PaintShop
PS = PaintShop()



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
        
        return f"""Cost: \t{
            self.get_cost():.2f
        }\n""" + '\n'.join([
            f'M{machine_id + 1}: {self[machine_id, :]} ({self.get_cost_machine(machine_id):.2f}) ({len(self[machine_id, :])})' 
            for machine_id in PS.machine_ids
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
    
    # Get the cost for the machine with the given machine_id
    def get_cost_machine(self, machine_id):
        # Processing time when starting on the current order
        t = 0
        last_order_id = None
            
        # Initialize penalty
        total_penalty = 0
            
        # Iterate over orders in queue
        for order_id in self.queues[machine_id]:
            
            # Add processing time to current time
            t += PS.get_processing_time(order_id, machine_id)
            
            # Add setup time
            t += PS.get_setup_time(last_order_id, order_id)
            
            # Add penalty to total_cost
            total_penalty += PS.get_penalty(order_id, t)
            
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
    
    
    # Returns a list of tuples containing the swaps
    def get_swaps(self) -> list[(tuple[int, int], tuple[int, int])]:
        
        # Get all indices of the orders.
        order_indices = [(machine_id, queue_index) for machine_id in PS.machine_ids for queue_index in range(len(self.queues[machine_id]))]
        
        # Return all combinations of length 2.
        return list(iter.combinations(order_indices, 2))
    
    
    # Get item
    def get_item(self, index: tuple[int, int]):
        
        return self.queues[index[0]][index[1]]
    
    
    # Set item
    def set_item(self, index, value):
        self.queues[index[0]][index[1]] = value
    
    # Return a swapped copy of self
    def get_copy(self):
        return copy.deepcopy(self)
    


# Move (Abstract Base Class) (https://docs.python.org/3/library/abc.html)
class Move(ABC):
    
    # As I'm still testing out abstract base classes, I'm raising an exception.
    # Apparantly, this method can only be called by subclasses calling super.func()
    @abstractmethod
    def get_moved(self, schedule_old: Schedule) -> Schedule:
        raise Exception("Abstract method used.")

    # @abstractmethod
    # def get_gain(self) -> float:
    #     raise Exception("Abstract method used.")

# Swap two orders by queue index.
class SwapOrders(Move):
    
    def __init__(self, queue_index_1: tuple[int, int], queue_index_2: tuple[int, int]):
        self.a = queue_index_1
        self.b = queue_index_2
    
    # Returns a swapped copy of the specified schedule.
    def get_moved(self, old: Schedule) -> Schedule:
        
        # Create copy of schedule
        new = copy.deepcopy(self)
        
        # Apply swap to new
        new[self.b] = old[self.a]
        new[self.a] = old[self.b]
        
        # Return swapped copy
        return new
    
    # # Get the change in cost resulting from this swap in a optimised way.
    # def get_gain(self, s: Schedule):
        
    #     return 

# Swap two orders by queue index.
class MoveOrder(Move):
    
    def __init__(self, old_index: tuple[int, int], new_index: tuple[int, int]):
        self.old_index = old_index
        self.new_index = new_index
    
    # Returns a swapped copy of the specified schedule.
    def get_moved(self, schedule_old: Schedule) -> Schedule:
        
        # Create copy of schedule
        new = copy.deepcopy(schedule_old)
        
        # Apply move (little something i leared called 'slice assignment' and the 'del keyword')
        new[self.new_index[0], self.new_index[1]:self.new_index[1]] = [schedule_old[self.old_index]]
        del new[self.old_index]
        
        # Return swapped copy
        return new

# Swaps the queue of two machines.
class SwapQueues(Move):
    
    def __init__(self, machine_index_a: int, machine_index_b: int):
        self.machine_a = machine_index_a
        self.machine_b = machine_index_b
    
    def get_moved(self, schedule_old: Schedule) -> Schedule:
        
        # Create copy of schedule
        schedule_new = copy.deepcopy(schedule_old)
        
        # Apply move (swap two queues)
        schedule_new[self.machine_a, :] = schedule_old[self.machine_b, :]
        schedule_new[self.machine_b, :] = schedule_old[self.machine_a, :]
        
        # Return swapped copy
        return schedule_new
    
    
# class ShuffleEach(Move):
    
#     def get_moved(self, schedule_old: Schedule) -> Schedule:
        
#         # Create copy of schedule
#         new = copy.deepcopy(schedule_old)
        
#         # Apply move (shuffle each queue)
#         new[self.new_index[0], self.new_index[1]:self.new_index[1]] = [schedule_old[self.old_index]]
#         del new[self.old_index]
        
#         # Return swapped copy
#         return new
        

# ???
Move.register(SwapOrders)
Move.register(MoveOrder)
Move.register(SwapQueues)



