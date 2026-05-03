"""
EscapeGrid - Multi-agent escape simulation environment
Manages a 10x10 grid with obstacles and agents
"""
import numpy as np


class EscapeGrid:
    """
    Manages a 10x10 grid environment for multi-agent escape simulation.
    
    Cell values:
    - 0: Empty cell
    - 1: Wall obstacle
    - 5: Fire hazard
    - 10-12: Agents (agent_id 10, 11, or 12)
    """
    
    def __init__(self):
        """Initialize the 10x10 escape grid environment."""
        self.grid = np.zeros((10, 10), dtype=int)
    
    def add_obstacle(self, x: int, y: int, type: int):
        """
        Add an obstacle at the specified position.
        
        Args:
            x: X coordinate (column)
            y: Y coordinate (row)
            type: Obstacle type (1 = Wall, 5 = Fire)
        """
        if 0 <= x < 10 and 0 <= y < 10:
            self.grid[y, x] = type
    
    def spawn_agent(self, agent_id: int, x: int, y: int):
        """
        Spawn an agent at the specified position.
        
        Args:
            agent_id: Agent identifier (10, 11, or 12)
            x: X coordinate (column)
            y: Y coordinate (row)
        """
        if 0 <= x < 10 and 0 <= y < 10:
            self.grid[y, x] = agent_id
    
    def display(self):
        """Print the grid to the terminal."""
        print(self.grid)
    
    def get_agent_pos(self, agent_id: int):
        """
        Find and return the (y, x) coordinates of a specific agent.
        
        Args:
            agent_id: Agent identifier (10, 11, or 12)
            
        Returns:
            Tuple of (y, x) coordinates if agent found, None otherwise
        """
        positions = np.where(self.grid == agent_id)
        if len(positions[0]) > 0:
            return (positions[0][0], positions[1][0])
        return None
    
    def move_agent(self, agent_id: int, new_x: int, new_y: int) -> bool:
        """
        Move an agent to a new position.
        
        Args:
            agent_id: Agent identifier (10, 11, or 12)
            new_x: Target X coordinate (column)
            new_y: Target Y coordinate (row)
            
        Returns:
            True if move successful, False if blocked or invalid
        """
        # Swap to internal y, x convention
        y, x = new_y, new_x
        
        # Check if move is within bounds
        if not (0 <= x < 10 and 0 <= y < 10):
            return False
        
        # Collision check: target must be empty (0) or Exit (3)
        target_cell = self.grid[y, x]
        if target_cell != 0 and target_cell != 3:
            return False  # Blocked by wall, fire, or another agent
        
        # Find current agent position
        current_pos = self.get_agent_pos(agent_id)
        if current_pos is None:
            return False  # Agent not found
        
        old_y, old_x = current_pos

        #Prevent LLMs from teleporting right to the end
        if abs(x - old_x) > 1 or abs(y - old_y) > 1:
            return False  # Invalid move: too far

        
        # Clear old position and set new position
        self.grid[old_y, old_x] = 0
            
        # Only place agent if not moving to exit
        if target_cell != 3:
            self.grid[y, x] = agent_id
        # If moving to exit (3), agent "escapes" and is removed from grid
    
        return True
    
    def spread_fire(self):
        """
        Spread fire to adjacent empty cells (4-directional: N, S, E, W).
        Fire spreads to empty cells (0) only, not through walls, agents, or exit.
        """
        # Find all current fire positions
        fire_positions = np.argwhere(self.grid == 5)
        
        # Track new fire positions to add after checking all current fires
        new_fires = []
        
        for fire_y, fire_x in fire_positions:
            # Check 4 cardinal directions
            directions = [
                (fire_y - 1, fire_x),  # North
                (fire_y + 1, fire_x),  # South
                (fire_y, fire_x - 1),  # West
                (fire_y, fire_x + 1),  # East
            ]
            
            for ny, nx in directions:
                # Check bounds
                if 0 <= ny < 10 and 0 <= nx < 10:
                    # Fire only spreads to empty cells
                    if self.grid[ny, nx] == 0:
                        new_fires.append((ny, nx))
        
        # Apply all new fires
        for ny, nx in new_fires:
            self.grid[ny, nx] = 5
        
        return len(new_fires)  # Return number of new fire cells

    
    def get_surroundings(self, agent_id: int):
        """
        Return a dictionary showing what's around the agent in all 8 directions.
        Uses np.pad to handle edges with -1 (out of bounds).
        
        Args:
            agent_id: Agent identifier (10, 11, or 12)
            
        Returns:
            Dictionary mapping directions to tile content descriptions
            Returns None if agent not found
        """
        pos = self.get_agent_pos(agent_id)
        if pos is None:
            return None
        
        y, x = pos
        
        # Pad the grid with -1 to handle edges
        padded_grid = np.pad(self.grid, pad_width=1, mode='constant', constant_values=-1)
        
        # Adjust coordinates for padded grid (add 1 to both y and x)
        py, px = y + 1, x + 1
        
        # Extract 3x3 slice centered on the agent
        slice_3x3 = padded_grid[py-1:py+2, px-1:px+2]
        
        # Helper function to convert cell value to description
        def cell_to_description(cell_value):
            if cell_value == -1:
                return 'Out of Bounds'
            elif cell_value == 0:
                return 'Empty'
            elif cell_value == 1:
                return 'Wall'
            elif cell_value == 3:
                return 'Exit'
            elif cell_value == 5:
                return 'Fire'
            elif cell_value in [10, 11, 12]:
                return f'Agent {cell_value}'
            else:
                return f'Unknown ({cell_value})'
        
        # Map directions to positions in the 3x3 slice
        # slice_3x3 layout:
        # [0,0] [0,1] [0,2]  =>  NW  N  NE
        # [1,0] [1,1] [1,2]  =>  W   C  E
        # [2,0] [2,1] [2,2]  =>  SW  S  SE
        
        surroundings = {
            'north': cell_to_description(slice_3x3[0, 1]),
            'south': cell_to_description(slice_3x3[2, 1]),
            'east': cell_to_description(slice_3x3[1, 2]),
            'west': cell_to_description(slice_3x3[1, 0]),
            'northeast': cell_to_description(slice_3x3[0, 2]),
            'northwest': cell_to_description(slice_3x3[0, 0]),
            'southeast': cell_to_description(slice_3x3[2, 2]),
            'southwest': cell_to_description(slice_3x3[2, 0]),
        }

        return surroundings

    def add_exit(self, x, y):
        if 0 <= x < 10 and 0 <= y < 10:
            self.grid[x, y] = 3  # Exit
        

# Made with Bob

