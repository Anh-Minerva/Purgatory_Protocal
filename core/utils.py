"""
Utility functions for Storm Simulation
Provides math and direction logic for agent navigation
"""
import math
from typing import Tuple, Optional


def manhattan_distance(pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
    """
    Calculate Manhattan distance between two positions.
    
    Args:
        pos1: First position as (y, x) tuple
        pos2: Second position as (y, x) tuple
        
    Returns:
        Manhattan distance (sum of absolute differences)
    """
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


def euclidean_distance(pos1: Tuple[int, int], pos2: Tuple[int, int]) -> float:
    """
    Calculate Euclidean distance between two positions.
    
    Args:
        pos1: First position as (y, x) tuple
        pos2: Second position as (y, x) tuple
        
    Returns:
        Euclidean distance (straight-line distance)
    """
    return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)


def get_direction_to_target(current: Tuple[int, int], target: Tuple[int, int]) -> Optional[str]:
    """
    Determine the best cardinal direction to move toward a target.
    
    Args:
        current: Current position as (y, x) tuple
        target: Target position as (y, x) tuple
        
    Returns:
        Direction string ('north', 'south', 'east', 'west') or None if already at target
    """
    cy, cx = current
    ty, tx = target
    
    dy = ty - cy
    dx = tx - cx
    
    # Already at target
    if dy == 0 and dx == 0:
        return None
    
    # Prioritize larger difference (greedy approach)
    if abs(dy) > abs(dx):
        return 'south' if dy > 0 else 'north'
    elif abs(dx) > abs(dy):
        return 'east' if dx > 0 else 'west'
    else:
        # Equal distance - prioritize horizontal movement
        return 'east' if dx > 0 else 'west'


def direction_to_coords(direction: str, current: Tuple[int, int]) -> Tuple[int, int]:
    """
    Convert a direction string to target coordinates.
    
    Args:
        direction: Direction string ('north', 'south', 'east', 'west')
        current: Current position as (y, x) tuple
        
    Returns:
        Target position as (y, x) tuple
    """
    y, x = current
    
    direction_map = {
        'north': (y - 1, x),
        'south': (y + 1, x),
        'east': (y, x + 1),
        'west': (y, x - 1)
    }
    
    return direction_map.get(direction.upper(), current)


def is_valid_move(current: Tuple[int, int], target: Tuple[int, int]) -> bool:
    """
    Check if a move is valid (exactly 1 tile in a cardinal direction).
    
    Args:
        current: Current position as (y, x) tuple
        target: Target position as (y, x) tuple
        
    Returns:
        True if move is valid, False otherwise
    """
    dy = abs(target[0] - current[0])
    dx = abs(target[1] - current[1])
    
    # Must move exactly 1 tile in one direction
    return (dy == 1 and dx == 0) or (dy == 0 and dx == 1)


def get_safe_directions(surroundings: dict) -> list:
    """
    Get list of safe directions from vision surroundings.
    
    Args:
        surroundings: Dictionary from VisionTool with direction keys
        
    Returns:
        List of safe direction strings
    """
    safe = []
    
    for direction in ['north', 'sound', 'east', 'west']:
        tile = surroundings.get(direction)
        # Safe if empty (0) or exit (9)
        if tile == 0 or tile == 9:
            safe.append(direction)
    
    return safe


def coords_to_move_params(agent_id: int, target: Tuple[int, int]) -> dict:
    """
    Convert coordinates to MoveTool parameters.
    
    Args:
        agent_id: Agent identifier (10, 11, or 12)
        target: Target position as (y, x) tuple
        
    Returns:
        Dictionary with agent_id, x, y for MoveTool
    """
    y, x = target
    return {
        'agent_id': agent_id,
        'x': x,
        'y': y
    }


# Made with Bob