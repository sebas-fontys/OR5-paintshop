import math
import pandas as pd
from sterling import count_part_empty_allowed


# PAINTSHOP CLASS: holds problem parameters
class PaintShop:
    
    # STATIC
    __data_filepath = "PaintShop - September 2024.xlsx"
    __sheet_names_by_table_name = {
        "orders": "Orders", 
        "machines": "Machines", 
        "setups": "Setups"
    }
    
    # CONSTRUCTOR
    def __init__(self):
        
        # Set source tables
        # We keep the source data in a dictionary in order to prevent confusion about what tables are source and what are derived.
        source = {
            table_name: pd.read_excel(self.__data_filepath, sheet_name) 
            for table_name, sheet_name in self.__sheet_names_by_table_name.items()
        }
        
        
        # Give each machine an ID (index in source table)
        self.machine_ids: list[int] = source["machines"].index.tolist()
        
        # Create dictionary of machine speeds (by ID)
        self.machine_speeds = {
            id: speed
            for id, speed 
            in zip(source["machines"].index, source["machines"]["Speed"])
        }
        
        
        # Encode color names with ID's, create dict to get names by ID.
        unique_colors = source["setups"]["From colour"].unique()
        self.__color_names_by_id = {
            index: name for index, name in enumerate(unique_colors)
        }
        color_ids_by_name = {
            name: index for index, name in enumerate(unique_colors)
        }
        
        # Encode color names in setups
        setups = pd.DataFrame({
            "c1":   source["setups"]["From colour"].apply(lambda color_prev: color_ids_by_name[color_prev]),
            "c2":   source["setups"]["To colour"  ].apply(lambda color_next: color_ids_by_name[color_next]),
            "time": source["setups"]["Setup time" ]
        })
        
        
        # Fix orders table: encode colors and set index as order ID
        self.order_ids: list[int] = source["orders"].index.tolist()
        self.orders = pd.DataFrame(
            {
                "surface":  source["orders"]["Surface" ].values,
                "color":    source["orders"]["Colour"  ].apply(lambda c: color_ids_by_name[c]),
                "deadline": source["orders"]["Deadline"].values,
                "penalty":  source["orders"]["Penalty" ].values,
            },
            index = self.order_ids
        )
        
        # Helper function
        def first_or_0(list):
            if len(list) == 0:
                return 0
            return list[0] 

        # Create table of order-to-order setup times (by ID's).
        self.__setup_times = pd.DataFrame({ 
            order1_id: pd.Series([
                0 if (order1_id == order2_id) else
                first_or_0(setups.loc[
                    (setups["c1"] == self.orders.loc[order1_id, "color"]) &
                    (setups["c2"] == self.orders.loc[order2_id, "color"]),
                    "time"
                ].values) for order2_id in self.orders.index.values
            ], dtype="Int64") for order1_id in self.orders.index.values 
        }).transpose()
        
        
        # Process times for any order on any machine. Ex: process_times.loc[0,1]
        self.__process_times = pd.DataFrame({
            machine_id: [
                order_surface / machine_speed for order_surface in self.orders["surface"].values
            ] for machine_id, machine_speed in self.machine_speeds.items()
        })
        
        
        # Calculate solution space size
        # The amount of ways to permute the order of a linear list of the orders.
        permutations = math.factorial(len(self.order_ids))
        # The amount of ways to partition a linear list of the orders in m ways (m being the amount of machines)
        # Allowing empty partitions. (m-1 is the ways to do it with one machine being assigned 0 orders, etc.)
        # That why we sum the sterling numbers over {1,...,m}
        self.solution_space_partitions = count_part_empty_allowed(self.orders.shape[0], len(self.machine_ids))
        self.solution_space_size = permutations * self.solution_space_partitions
        
    
    def get_processing_time(self, order: int, machine: int) -> float:
        return self.__process_times.loc[order, machine]
    
    def get_setup_time(self, order_old, order_new) -> float:
        
        if (order_old == None):
            return 0
        
        return self.__setup_times.loc[order_old, order_new]
    
    def get_penalty(self, order, t_done) -> float:
        
        return self.orders.loc[order, 'penalty'] * max(
            0, 
            t_done - self.orders.loc[order, 'deadline']
        )
    
    def get_color_names(self) -> list[str]:
        return self.__color_names_by_id.values()
    
    def get_color_name(self, color) -> str:
        return self.__color_names_by_id[color]
    
    def get_order_color_name(self, order) -> str:
        return self.get_color_name(self.orders.loc[order, "color"])