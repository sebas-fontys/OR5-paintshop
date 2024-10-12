import os
import pandas as pd

from enum import Enum
class Source(Enum):
    SEPTEMBER = "PaintShop - September 2024.xlsx"
    NOVEMBER  = "PaintShop - November 2024.xlsx"

# PAINTSHOP CLASS: holds problem parameters
class PaintShop:
    
    # STATIC
    __source_folder = "resources"
    __sheet_names_by_table_name = {
        "orders": "Orders", 
        "machines": "Machines", 
        "setups": "Setups"
    }
    
    # CONSTRUCTOR
    def __init__(self, source_file: Source):
        
        # Keep track of the source file name.
        self.source_id = source_file.name
        
        # Set source tables
        # We keep the source data in a dictionary in order to prevent confusion about what tables are source and what are derived.
        self.source = os.path.join(PaintShop.__source_folder, source_file.value)
        
        source_file = {
            table_name: pd.read_excel(self.source, sheet_name) 
            for table_name, sheet_name in self.__sheet_names_by_table_name.items()
        }
        print(f"[PaintShop] Loaded '{self.source}'")
        
        
        # Give each machine an ID (index in source table)
        self.machine_ids: list[int] = source_file["machines"].index.tolist()
        self.machine_count = len(self.machine_ids)
        
        # Create dictionary of machine speeds (by ID)
        self.machine_speeds = {
            id: speed
            for id, speed 
            in zip(source_file["machines"].index, source_file["machines"]["Speed"])
        }
        
        
        # Encode color names with ID's, create dict to get names by ID.
        unique_colors = source_file["setups"]["From colour"].unique()
        self.__color_names_by_id = {
            index: name for index, name in enumerate(unique_colors)
        }
        color_ids_by_name = {
            name: index for index, name in enumerate(unique_colors)
        }
        
        # Encode color names in setups
        setups = pd.DataFrame({
            "c1":   source_file["setups"]["From colour"].apply(lambda color_prev: color_ids_by_name[color_prev]),
            "c2":   source_file["setups"]["To colour"  ].apply(lambda color_next: color_ids_by_name[color_next]),
            "time": source_file["setups"]["Setup time" ]
        })
        
        
        # Fix orders table: encode colors and set index as order ID
        self.order_ids: list[int] = source_file["orders"].index.tolist()
        self.order_count = len(self.order_ids)
        self.orders = pd.DataFrame(
            {
                "surface":  source_file["orders"]["Surface" ].values,
                "color":    source_file["orders"]["Colour"  ].apply(lambda c: color_ids_by_name[c]),
                "deadline": source_file["orders"]["Deadline"].values,
                "penalty":  source_file["orders"]["Penalty" ].values,
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