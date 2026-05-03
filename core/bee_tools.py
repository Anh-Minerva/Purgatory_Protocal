"""
Bee Agent Framework Tools for Storm Simulation
Provides VisionTool and MoveTool for agent interaction with EscapeGrid
"""
from beeai_framework.tools.tool import Tool
from beeai_framework.emitter import Emitter
from pydantic import BaseModel, Field
from typing import Dict, Any

# 1. Define the schema outside the class to be clean
class VisionInput(BaseModel):
    agent_id: int = Field(description="Your agent identifier (10, 11, or 12)")

class VisionTool(Tool):
    @property
    def name(self) -> str:
        return "vision"

    @property
    def description(self) -> str:
        return "Get information about your 8 surrounding tiles."

    @property
    def input_schema(self) -> type[VisionInput]:
        return VisionInput

    def __init__(self, grid):
        self.grid = grid
        super().__init__()

    def _create_emitter(self) -> Emitter:
        """Create emitter for vision tool events."""
        return Emitter.root().child(
            namespace=["tool", "vision"],
            creator=self,
        )

    # 2. BeeAI expects '_run' (with underscore) and it usually wants it to be async
    async def _run(self, input: VisionInput, options: Any = None, context: Any = None) -> Any:
        agent_id = input.agent_id
        pos = self.grid.get_agent_pos(agent_id)
        if not pos: return {"error": "Agent missing"}
        
        y, x = pos
        view = {}
        
        # Directions to check: (dy, dx, name)
        checks = [(-1, 0, 'N'), (1, 0, 'S'), (0, 1, 'E'), (0, -1, 'W')]
        
        for dy, dx, name in checks:
            # 1. Check immediate tile
            ny, nx = y + dy, x + dx
            first_tile = self.grid.get_tile(ny, nx)
            view[name] = first_tile
            
            # 2. Line of Sight: Only check the 2nd tile if the 1st isn't a Wall
            # This gives agent their "6th" tile (and others) realistically
            if first_tile != 1: # 1 = Wall
                nny, nnx = y + (dy * 2), x + (dx * 2)
                view[f"{name}_far"] = self.grid.get_tile(nny, nnx)
            else:
                view[f"{name}_far"] = "blocked"

        return {
            "observation": "You look in four directions. Walls block your vision.",
            "surroundings": view
        }

class MoveInput(BaseModel):
    agent_id: int = Field(description="Your agent identifier (10, 11, or 12)")
    x: int = Field(description="Target X coordinate (0-9)")
    y: int = Field(description="Target Y coordinate (0-9)")

class MoveTool(Tool):
    """
    Tool for agents to move on the grid.
    IMPORTANT: Only move 1 tile at a time in cardinal directions.
    """
    @property
    def name(self) -> str:
        return "move"

    @property
    def description(self) -> str:
        return """
        Move your agent to a new position on the grid.
    
    CRITICAL RULES:
    - Only move 1 tile at a time (not 2, 3, or more)
    - Valid moves: 1 tile North, South, East, or West
    - Cannot move diagonally
    - Cannot move through walls (blocked)
    - Cannot move through fire (blocked)
    - Cannot move through other agents (blocked)
    - Moving to an Exit tile means you escape successfully
    
    Input: 
        - agent_id (int): Your agent identifier (10, 11, or 12)
        - x (int): Target X coordinate (column, 0-9)
        - y (int): Target Y coordinate (row, 0-9)
    
    Output: 
        - True if move succeeded
        - False if move was blocked or invalid
    
    Example: To move 1 tile right from (2,3), call move(agent_id, 3, 3)
    """

    @property
    def input_schema(self) -> type[MoveInput]:
        return MoveInput

    def __init__(self, grid):
        """
        Initialize MoveTool with grid reference.
        
        Args:
            grid: EscapeGrid instance
        """
        self.grid = grid
        super().__init__()
    
    def _create_emitter(self) -> Emitter:
        """Create emitter for move tool events."""
        return Emitter.root().child(
            namespace=["tool", "move"],
            creator=self,
        )
    
    async def _run(self, input: MoveInput, options: Any = None, context: Any = None) -> Any:
        # 1. Map input variables to your local logic
        agent_id = input.agent_id
        x, y = input.x, input.y
        
        # 2. Your existing logic for getting position
        current_pos = self.grid.get_agent_pos(agent_id)
        if current_pos is None:
            return {"success": False, "message": f"Agent {agent_id} not found"}
        
        current_y, current_x = current_pos
        
        # 3. Your existing 1-tile validation
        dx = abs(x - current_x)
        dy = abs(y - current_y)
        
        if dx + dy != 1:
            return {
                "success": False,
                "message": f"Invalid move: Must move exactly 1 tile. (Tried {dx+dy})"
            }
        
        # 4. Execute move and return response
        success = self.grid.move_agent(agent_id, x, y)
        
        if success:
            # Check for escape
            new_pos = self.grid.get_agent_pos(agent_id)
            if new_pos is None:
                return {
                    "success": True,
                    "message": f"Agent {agent_id} ESCAPED!",
                    "escaped": True
                }
            
            # Get 3x3 surroundings automatically after successful move
            surroundings = self.grid.get_surroundings(agent_id)
            
            return {
                "success": True,
                "message": f"Agent {agent_id} moved to ({x}, {y})",
                "new_position": {"x": x, "y": y},
                "surroundings": surroundings,
                "vision_included": True
            }
            
        return {"success": False, "message": "Move blocked by obstacle or fire."}


# Made with Bob
