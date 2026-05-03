"""
Main execution loop for BeeAI Escape Simulation
Runs multiple agents asynchronously to escape from a 10x10 grid
Uses Soft ReAct Pattern for flexible LLM reasoning
"""
import asyncio
from envi.environment import EscapeGrid
from core.agents import create_agent_by_type
from typing import Dict, List, Tuple


async def run_agent(agent, agent_id: int, agent_type: str, grid, max_steps: int = 50) -> Dict:
    """
    Run a single agent until it escapes or reaches max steps.
    
    Args:
        agent: SoftReActAgent instance
        agent_id: Agent identifier (10, 11, or 12)
        agent_type: Type of agent ('safe', 'fast', or 'efficient')
        grid: EscapeGrid instance to check agent position
        max_steps: Maximum number of steps before timeout
        
    Returns:
        Dictionary with agent results (steps, escaped, agent_id, type)
    """
    print(f"\n🤖 Agent {agent_id} ({agent_type.upper()}) starting...")
    
    steps = 0
    escaped = False
    
    for step in range(max_steps):
        steps = step + 1
        
        # Check if agent has escaped (no longer on grid)
        pos = grid.get_agent_pos(agent_id)
        if pos is None:
            escaped = True
            print(f"✅ Agent {agent_id} ESCAPED in {steps} steps!")
            break
        
        # Run one step with Soft ReAct agent
        try:
            prompt = f"You are at step {steps}. Find the exit at (9,9) and escape!"
            result = await agent.step(prompt)
            
            # Check if escaped
            if result['escaped']:
                escaped = True
                print(f"✅ Agent {agent_id} ESCAPED in {steps} steps!")
                break
            
            # Print agent's action
            if not result['error']:
                print(f"  Step {steps}: {result['message'][:100]}...")
            else:
                print(f"❌ Agent {agent_id} error at step {steps}: {result['message']}")
                break
                
        except Exception as e:
            print(f"❌ Agent {agent_id} error at step {steps}: {str(e)}")
            break
    
    if not escaped:
        print(f"⏱️ Agent {agent_id} timed out after {steps} steps")
    
    return {
        'agent_id': agent_id,
        'type': agent_type,
        'steps': steps,
        'escaped': escaped
    }


async def run_simulation(
    agent_configs: List[Tuple[int, str, Tuple[int, int]]],
    model: str = "llama3.2:1b",
    max_steps: int = 50
) -> List[Dict]:
    """
    Run multiple agents concurrently in the escape simulation.
    
    Args:
        agent_configs: List of (agent_id, agent_type, spawn_position) tuples
        model: Ollama model name
        max_steps: Maximum steps per agent
        
    Returns:
        List of result dictionaries for each agent
    """
    # Initialize grid
    grid = EscapeGrid()
    
    # Add obstacles
    print("🌪️ Setting up Storm Simulation environment...")
    
    # Create a challenging maze
    obstacles = [
        (2, 2, 1), (3, 2, 1), (4, 2, 1),  # Wall line
        (2, 5, 1), (3, 5, 1), (4, 5, 1),  # Wall line
        (6, 3, 1), (6, 4, 1), (6, 5, 1),  # Wall line
        (5, 5, 5), (6, 6, 5), (7, 5, 5),  # Fire hazards
    ]
    
    for x, y, obstacle_type in obstacles:
        grid.add_obstacle(x, y, obstacle_type)
    
    # Mark exit at (9, 9)
    grid.add_obstacle(9, 9, 3)  # 3 = Exit
    
    # Spawn agents and create agent instances
    agents = []
    tasks = []
    
    for agent_id, agent_type, (spawn_x, spawn_y) in agent_configs:
        grid.spawn_agent(agent_id, spawn_x, spawn_y)
        agent = create_agent_by_type(agent_id, grid, agent_type, model)
        agents.append(agent)
        
        # Create async task for each agent
        task = run_agent(agent, agent_id, agent_type, grid, max_steps)
        tasks.append(task)
        
        print(f"  Agent {agent_id} ({agent_type}) spawned at ({spawn_x}, {spawn_y})")
    
    print("\n🏁 Starting simulation...\n")
    
    # Run all agents concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out exceptions and return valid results
    valid_results = [r for r in results if isinstance(r, dict)]
    
    return valid_results


def print_results(results: List[Dict]):
    """
    Print simulation results in a formatted table.
    
    Args:
        results: List of result dictionaries
    """
    print("\n" + "="*60)
    print("📊 SIMULATION RESULTS")
    print("="*60)
    
    # Sort by steps (winners first)
    sorted_results = sorted(results, key=lambda x: (not x['escaped'], x['steps']))
    
    for i, result in enumerate(sorted_results, 1):
        status = "✅ ESCAPED" if result['escaped'] else "❌ FAILED"
        print(f"{i}. Agent {result['agent_id']} ({result['type'].upper()}): "
              f"{status} - {result['steps']} steps")
    
    print("="*60)
    
    # Calculate statistics
    escaped_count = sum(1 for r in results if r['escaped'])
    avg_steps = sum(r['steps'] for r in results if r['escaped']) / max(escaped_count, 1)
    
    print(f"\n📈 Statistics:")
    print(f"  Escaped: {escaped_count}/{len(results)}")
    if escaped_count > 0:
        print(f"  Average steps (escaped): {avg_steps:.1f}")
    print()


async def main():
    """Main entry point for the simulation."""
    print("🌪️ BeeAI Escape Simulation - Soft ReAct Pattern")
    print("="*60)
    
    # Configure agents: (agent_id, type, spawn_position)
    agent_configs = [
        (10, 'safe', (1, 1)),       # Safe agent at top-left
        (11, 'fast', (1, 8)),       # Fast agent at top-right
        (12, 'efficient', (5, 1)),  # Efficient agent at middle-left
    ]
    
    # Run simulation
    results = await run_simulation(
        agent_configs=agent_configs,
        model="llama3.2:1b",
        max_steps=50
    )
    
    # Print results
    print_results(results)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Simulation interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Simulation error: {str(e)}")
        import traceback
        traceback.print_exc()


# Made with Bob