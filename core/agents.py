"""
Soft ReAct Pattern Agent Implementation
Flexible reasoning without strict format requirements using direct Ollama API calls
"""
import aiohttp
import json
import re
from typing import Dict, Any, List, Optional
from envi.environment import EscapeGrid


class SoftReActAgent:
    """
    Soft ReAct Pattern Agent - Flexible reasoning without strict format requirements.
    Uses regex-based parsing to extract tool calls from natural language LLM responses.
    Calls Ollama directly via HTTP API, bypassing BeeAI Framework entirely.
    """
    
    def __init__(self, agent_id: int, grid: EscapeGrid, strategy: str, model: str = "llama3.2:1b"):
        self.agent_id = agent_id
        self.grid = grid
        self.strategy = strategy.lower()
        self.model = model
        self.conversation_history: List[Dict[str, str]] = []
        self.move_count = 0
        self.ollama_url = "http://localhost:11434/api/chat"
        self.system_prompt = self._get_system_prompt()
        
    def _get_system_prompt(self) -> str:
        """Get strategy-specific system prompt."""
        base_prompt = f"""You are Agent {self.agent_id} escaping to exit at (9,9).

GRID: 10x10, (0,0)=top-left, (9,9)=bottom-right
- 0=Empty, 1=Wall, 3=Exit, 5=Fire, 10-12=Agents

COMMANDS (use ONLY these):
- vision
- move north
- move south
- move east
- move west

STRICT OUTPUT RULES:
1. Your response MUST contain exactly ONE command from above
2. DO NOT mention coordinates or positions
3. DO NOT say "I'm at" or "current position" or "moving to"
4. DO NOT make up locations
5. Keep response SHORT - just state the command with brief reasoning

CORRECT examples:
- "vision"
- "move east"
- "I'll move north to avoid the wall"
- "Let me use vision first"

WRONG examples (DO NOT DO THIS):
- "I'm at position (5,3)" ❌
- "Moving to (8,9)" ❌
- "Current position: (1,1)" ❌
- "I'll move 3 steps east" ❌

The system will tell you your actual position after each action. Trust the system, not your memory.

IF YOU GET HIT BY FIRE, SAY "AHHH" AND STAY STILL FOR THE REST OF THE SIMULATION!!

"""
        
        if self.strategy == 'safe':
            return base_prompt + """STRATEGY: SAFE
- Always use vision before moving
- Avoid fire at all costs
- Take the safest path even if slower
- Check surroundings frequently"""
        
        elif self.strategy == 'fast':
            return base_prompt + """STRATEGY: FAST
- Move quickly toward (9,9)
- Use vision sparingly
- Take direct routes
- Accept some risk for speed"""
        
        else:  # efficient
            return base_prompt + """STRATEGY: EFFICIENT
- Balance speed and safety
- Use vision when needed
- Find optimal paths
- Minimize total moves"""
    
    async def _call_ollama(self, messages: List[Dict[str, str]]) -> str:
        """Call Ollama API directly via HTTP."""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.ollama_url, json=payload) as response:
                if response.status != 200:
                    raise Exception(f"Ollama API error: {response.status}")
                
                result = await response.json()
                return result['message']['content']
    
    def _parse_response(self, text: str) -> Dict[str, Any]:
        """Parse LLM response using flexible regex patterns."""
        text_lower = text.lower()
        
        # Check for completion/escape - but ONLY if agent is actually at (9,9)
        if any(phrase in text_lower for phrase in ['escaped', 'reached exit', 'at (9,9)', 'i win']):
            # Verify agent is actually at exit before allowing completion
            pos = self.grid.get_agent_pos(self.agent_id)
            if pos == (9, 9):
                return {
                    'action': 'complete',
                    'thought': text,
                    'final_answer': 'Agent has escaped!'
                }
            # If not at exit, ignore the claim and continue with vision
            return {
                'action': 'vision',
                'thought': f"Agent claims escape but is at {pos}, not (9,9). Continuing...",
                'action_input': {}
            }
        
        # Check for vision tool
        if 'vision' in text_lower or 'look' in text_lower or 'see' in text_lower:
            return {
                'action': 'vision',
                'thought': text,
                'action_input': {}
            }
        
        # Check for move actions - flexible pattern to catch variations
        # Matches: "move north", "moving south", "I'll move east", "move 1 step west", etc.
        move_pattern = r'mov(?:e|ing)?\s+(?:\d+\s+)?(?:step\s+)?(?:to\s+)?(?:the\s+)?(north|south|east|west)'
        move_match = re.search(move_pattern, text_lower)
        if move_match:
            direction = move_match.group(1)
            return {
                'action': 'move',
                'thought': text,
                'action_input': {'direction': direction}
            }
        
        # Default: ask for vision if unclear
        return {
            'action': 'vision',
            'thought': text,
            'action_input': {}
        }
    
    async def _execute_action(self, action: str, action_input: Dict[str, Any]) -> str:
        """Execute vision or move action and return result string."""
        if action == 'vision':
            # Get surroundings from grid
            surroundings = self.grid.get_surroundings(self.agent_id)
            if surroundings is None:
                return "Error: Agent not found on grid"
            
            # Format vision result
            result = "Vision:\n"
            for direction, content in surroundings.items():
                if direction in ['north', 'south', 'east', 'west']:
                    result += f"  {direction.capitalize()}: {content}\n"
            
            return result
        
        elif action == 'move':
            direction = action_input.get('direction', '').lower()
            
            # Get current position
            pos = self.grid.get_agent_pos(self.agent_id)
            if pos is None:
                return "Error: Agent not found"
            
            y, x = pos
            
            # Calculate new position (only 1 tile movement allowed)
            new_y, new_x = y, x
            if direction == 'north':
                new_y -= 1
            elif direction == 'south':
                new_y += 1
            elif direction == 'east':
                new_x += 1
            elif direction == 'west':
                new_x -= 1
            else:
                return f"Error: Invalid direction '{direction}'. Must be north, south, east, or west."
            
            # STRICT VALIDATION: Ensure only 1-tile movement
            distance = abs(new_x - x) + abs(new_y - y)
            if distance != 1:
                return f"Error: Teleportation attempt detected! Can only move 1 tile. Staying at ({y}, {x})."
            
            # Attempt move
            success = self.grid.move_agent(self.agent_id, new_x, new_y)
            
            if success:
                # Verify the move was actually only 1 tile
                new_pos = self.grid.get_agent_pos(self.agent_id)
                
                # Check if reached exit (agent removed from grid)
                if new_pos is None:
                    self.move_count += 1
                    return f"SUCCESS! Moved {direction} and reached EXIT at (9,9)! Total moves: {self.move_count}"
                
                # Verify movement distance (safety check)
                actual_distance = abs(new_pos[1] - x) + abs(new_pos[0] - y)
                if actual_distance > 1:
                    return f"Error: Invalid move detected (moved {actual_distance} tiles). Staying at ({y}, {x})."
                
                self.move_count += 1
                
                # Get new surroundings
                surroundings = self.grid.get_surroundings(self.agent_id)
                result = f"Moved {direction} to ({new_pos[0]},{new_pos[1]}). Move #{self.move_count}\n"
                result += "Surroundings:\n"
                if surroundings:
                    for dir_name, content in surroundings.items():
                        if dir_name in ['north', 'south', 'east', 'west']:
                            result += f"  {dir_name.capitalize()}: {content}\n"
                return result
            else:
                return f"Failed to move {direction} - blocked or out of bounds. Staying at ({y}, {x})."
        
        return "Unknown action"
    
    async def step(self, prompt: str) -> Dict[str, Any]:
        """
        Execute one reasoning step.
        
        Returns:
            Dict with keys: 'escaped' (bool), 'message' (str), 'error' (bool)
        """
        try:
            # Check if already escaped
            pos = self.grid.get_agent_pos(self.agent_id)
            if pos is None:
                return {
                    'escaped': True,
                    'message': f'Agent {self.agent_id} has already escaped!',
                    'error': False
                }
            
            # Add user prompt to conversation
            self.conversation_history.append({
                'role': 'user',
                'content': prompt
            })
            
            # Build messages for LLM
            messages = [
                {'role': 'system', 'content': self.system_prompt}
            ] + self.conversation_history
            
            # Call LLM
            response_text = await self._call_ollama(messages)
            
            # Add assistant response to history
            self.conversation_history.append({
                'role': 'assistant',
                'content': response_text
            })
            
            # Parse response
            parsed = self._parse_response(response_text)
            
            # Check for completion
            if parsed['action'] == 'complete':
                return {
                    'escaped': True,
                    'message': parsed.get('final_answer', 'Escaped!'),
                    'error': False
                }
            
            # Execute action
            action_result = await self._execute_action(
                parsed['action'],
                parsed.get('action_input', {})
            )
            
            # Add action result to conversation
            self.conversation_history.append({
                'role': 'user',
                'content': f"Action result: {action_result}"
            })
            
            # Check if escaped after move
            pos_after = self.grid.get_agent_pos(self.agent_id)
            if pos_after is None:
                return {
                    'escaped': True,
                    'message': f'Agent {self.agent_id} escaped in {self.move_count} moves!',
                    'error': False
                }
            
            return {
                'escaped': False,
                'message': f"{response_text[:100]}... | {action_result[:100]}...",
                'error': False
            }
            
        except Exception as e:
            return {
                'escaped': False,
                'message': f'Error: {str(e)}',
                'error': True
            }


def create_agent_by_type(agent_id: int, grid: EscapeGrid, agent_type: str, model: str = "llama3.2:1b") -> SoftReActAgent:
    """
    Factory function to create agents by type.
    
    Args:
        agent_id: Agent identifier (10, 11, or 12)
        grid: EscapeGrid instance
        agent_type: Strategy type ('safe', 'fast', or 'efficient')
        model: Ollama model name
        
    Returns:
        SoftReActAgent instance
    """
    # Debug: Print parameter types
    print(f"DEBUG create_agent_by_type: agent_id={agent_id} (type={type(agent_id).__name__}), agent_type={agent_type} (type={type(agent_type).__name__}), model={model}")
    
    # SoftReActAgent expects: (agent_id, grid, strategy, model)
    return SoftReActAgent(agent_id=agent_id, grid=grid, strategy=agent_type, model=model)


# Made with Bob
