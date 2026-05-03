"""
Streamlit Dashboard for Storm Simulation: AI Escape
Real-time visualization of AI agents navigating the grid
"""
import streamlit as st
import sys
import os
import asyncio
import traceback
from typing import Dict, List
import importlib

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Force reload modules to avoid cache issues
import envi.environment
import core.agents
importlib.reload(envi.environment)
importlib.reload(core.agents)

from envi.environment import EscapeGrid
from core.agents import create_agent_by_type


def map_cell_to_emoji(cell_value: int) -> str:
    """
    Map grid cell values to emoji representations.
    
    Args:
        cell_value: Integer value from the grid
        
    Returns:
        Emoji string representing the cell
    """
    emoji_map = {
        0: '⬜',   # Empty
        1: '🧱',   # Wall
        3: '🚪',   # Exit
        5: '🔥',   # Fire
        10: '🏃',  # Agent 10 (Safe)
        11: '⚡',  # Agent 11 (Fast)
        12: '🎯',  # Agent 12 (Efficient)
    }
    return emoji_map.get(cell_value, '❓')


def display_grid(grid):
    """
    Display the grid as a clean table with emojis.
    
    Args:
        grid: NumPy array representing the escape grid
    """
    rows, cols = grid.shape
    
    # Create HTML table
    html = '<div style="font-size: 32px; line-height: 1.2;">'
    html += '<table style="border-collapse: collapse; margin: auto;">'
    
    for i in range(rows):
        html += '<tr>'
        for j in range(cols):
            emoji = map_cell_to_emoji(grid[i, j])
            # Highlight exit cell
            bg_color = '#90EE90' if grid[i, j] == 3 else 'transparent'
            html += f'<td style="padding: 5px; text-align: center; border: 1px solid #ddd; background-color: {bg_color};">{emoji}</td>'
        html += '</tr>'
    
    html += '</table></div>'
    
    st.markdown(html, unsafe_allow_html=True)


async def run_agent_step(agent, agent_id: int, grid) -> Dict:
    """
    Run a single step for an agent using Soft ReAct pattern.
    
    Args:
        agent: SoftReActAgent instance
        agent_id: Agent identifier
        grid: EscapeGrid instance
        
    Returns:
        Dictionary with step result: {'escaped': bool, 'message': str, 'error': bool}
    """
    try:
        # Check if agent has escaped
        pos = grid.get_agent_pos(agent_id)
        if pos is None:
            return {'escaped': True, 'message': f'Agent {agent_id} has escaped!', 'error': False}
        
        # Simple, direct prompt for Soft ReAct
        prompt = f"Move 1 step toward exit at (9,9). Your agent_id is {agent_id}."
        
        # Use the new Soft ReAct step() method - returns Dict directly
        result = await agent.step(prompt)
        
        return result
    except Exception as e:
        error_msg = str(e)
        # Print full traceback for debugging
        print(f"\n{'='*60}")
        print(f"ERROR in Agent {agent_id}:")
        print(f"{'='*60}")
        traceback.print_exc()
        print(f"{'='*60}\n")
        
        # Check if it's a schema error
        if "schema" in error_msg.lower() or "json" in error_msg.lower():
            return {
                'escaped': False,
                'message': f'⚠️ Model struggling with tool format. Retrying...',
                'error': True
            }
        
        # Check for timeout error
        if "timeout" in error_msg.lower():
            return {
                'escaped': False,
                'message': f'⏱️ Timeout - model too slow. Try smaller model.',
                'error': True
            }
        
        # Check for emitter error
        if "emitter" in error_msg.lower():
            return {
                'escaped': False,
                'message': f'Emitter error: {error_msg[:200]}',
                'error': True
            }
        
        return {
            'escaped': False,
            'message': f'Error: {error_msg[:200]}',
            'error': True
        }


def initialize_simulation():
    """Initialize the simulation with grid and agents."""
    # Create grid
    grid = EscapeGrid()
    
    # Add obstacles - challenging maze
    obstacles = [
        (2, 2, 1), (3, 2, 1), (4, 2, 1),  # Wall line
        (2, 5, 1), (3, 5, 1), (4, 5, 1),  # Wall line
        (6, 3, 1), (6, 4, 1), (6, 5, 1),  # Wall line
        (5, 5, 5), (6, 6, 5), (7, 5, 5),  # Fire hazards
        (5, 8, 5), (3, 4, 5), (8, 6, 5),  # Fire hazards
    ]
    
    for x, y, obstacle_type in obstacles:
        grid.add_obstacle(x, y, obstacle_type)
    
    # Mark exit at (9, 9)
    grid.add_obstacle(9, 9, 3)
    
    # Spawn agents
    agent_configs = [
        (10, 'safe', (1, 1)),       # Safe agent
        (11, 'fast', (1, 8)),       # Fast agent
        (12, 'efficient', (5, 1)),  # Efficient agent
    ]
    
    agents = {}
    # Use llama3.2:1b for Soft ReAct pattern
    model = "llama3.2:1b"  # Fast, lightweight model
    
    for agent_id, agent_type, (spawn_x, spawn_y) in agent_configs:
        grid.spawn_agent(agent_id, spawn_x, spawn_y)
        # Create Soft ReAct agent with correct parameter order: (agent_id, grid, agent_type, model)
        try:
            agent = create_agent_by_type(agent_id, grid, agent_type, model)
        except Exception as e:
            print(f"Failed to create agent {agent_id} with {model}: {e}")
            # Fallback
            try:
                agent = create_agent_by_type(agent_id, grid, agent_type, "llama3.2:1b")
            except Exception:
                agent = create_agent_by_type(agent_id, grid, agent_type, "llama3.2")
        
        agents[agent_id] = {
            'agent': agent,
            'type': agent_type,
            'steps': 0,
            'escaped': False,
            'grid': grid,  # Store grid reference with agent
            'errors': 0  # Track consecutive errors
        }
    
    return grid, agents


def main():
    """Main Streamlit application."""
    # Page config
    st.set_page_config(
        page_title="Purgatory Protocol",
        page_icon="🔥",
        layout="wide"
    )
    
    # Title
    st.title("Purgatory Protocol")
    st.markdown("**Watch AI agents navigate to escape in real-time!**")
    st.markdown("---")
    
    # Initialize session state
    if 'grid' not in st.session_state:
        st.session_state.grid, st.session_state.agents = initialize_simulation()
        st.session_state.step_count = 0
        st.session_state.simulation_running = False
    
    # Sidebar controls
    with st.sidebar:
        st.header("🎮 Controls")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("▶️ Start", use_container_width=True, disabled=st.session_state.simulation_running):
                st.session_state.simulation_running = True
                st.rerun()
        
        with col2:
            if st.button("⏸️ Pause", use_container_width=True, disabled=not st.session_state.simulation_running):
                st.session_state.simulation_running = False
                st.rerun()
        
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.grid, st.session_state.agents = initialize_simulation()
            st.session_state.step_count = 0
            st.session_state.simulation_running = False
            st.rerun()
        
        if st.button("⏭️ Step Once", use_container_width=True, disabled=st.session_state.simulation_running):
            # Run one step for all agents
            for agent_id, agent_data in st.session_state.agents.items():
                if not agent_data['escaped']:
                    # Use the main grid from session state (all agents share this)
                    result = asyncio.run(run_agent_step(
                        agent_data['agent'],
                        agent_id,
                        st.session_state.grid
                    ))
                    
                    # Track errors
                    if result.get('error', False):
                        agent_data['errors'] = agent_data.get('errors', 0) + 1
                    else:
                        agent_data['errors'] = 0
                        agent_data['steps'] += 1
                    
                    agent_data['escaped'] = result['escaped']
                    agent_data['last_message'] = result['message']
            
            # Spread fire after all agents have moved
            new_fire_cells = st.session_state.grid.spread_fire()
            if new_fire_cells > 0:
                st.info(f"🔥 Fire spread to {new_fire_cells} new cell(s)!")
            
            st.session_state.step_count += 1
            st.rerun()
        
        st.markdown("---")
        st.header("📊 Statistics")
        st.metric("Total Steps", st.session_state.step_count)
        
        for agent_id, agent_data in st.session_state.agents.items():
            status = "✅ Escaped" if agent_data['escaped'] else "🏃 Running"
            st.metric(
                f"Agent {agent_id} ({agent_data['type'].title()})",
                f"{agent_data['steps']} steps",
                status
            )
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🗺️ Grid View")
        # Force refresh by creating a copy of the grid array
        import numpy as np
        current_grid = np.copy(st.session_state.grid.grid)
        display_grid(current_grid)
    
    with col2:
        st.subheader("📝 Agent Status")
        
        for agent_id, agent_data in st.session_state.agents.items():
            with st.expander(f"Agent {agent_id} - {agent_data['type'].upper()}", expanded=True):
                if agent_data['escaped']:
                    st.success(f"✅ Escaped in {agent_data['steps']} steps!")
                else:
                    pos = st.session_state.grid.get_agent_pos(agent_id)
                    if pos:
                        st.info(f"📍 Position: ({pos[1]}, {pos[0]})")
                    st.write(f"**Steps:** {agent_data['steps']}")
                    if 'last_message' in agent_data:
                        st.caption(f"💭 {agent_data['last_message']}")
    
    # Legend
    st.markdown("---")
    st.subheader("🔑 Legend")
    cols = st.columns(7)
    cols[0].markdown("⬜ Empty")
    cols[1].markdown("🧱 Wall")
    cols[2].markdown("🔥 Fire")
    cols[3].markdown("🚪 Exit")
    cols[4].markdown("🏃 Safe Agent")
    cols[5].markdown("⚡ Fast Agent")
    cols[6].markdown("🎯 Efficient Agent")
    
    # Auto-step if simulation is running
    if st.session_state.simulation_running:
        # Check if all agents have escaped
        all_escaped = all(agent_data['escaped'] for agent_data in st.session_state.agents.values())
        
        if all_escaped:
            st.session_state.simulation_running = False
            st.balloons()
            st.success("🎉 All agents have escaped!")
        else:
            # Run one step for all agents
            for agent_id, agent_data in st.session_state.agents.items():
                if not agent_data['escaped']:
                    # Use the grid stored with the agent to ensure consistency
                    result = asyncio.run(run_agent_step(
                        agent_data['agent'],
                        agent_id,
                        agent_data['grid']
                    ))
                    
                    # Track errors
                    if result.get('error', False):
                        agent_data['errors'] = agent_data.get('errors', 0) + 1
                        # Skip incrementing steps on error
                    else:
                        agent_data['errors'] = 0
                        agent_data['steps'] += 1
                    
                    agent_data['escaped'] = result['escaped']
                    agent_data['last_message'] = result['message']
            
            st.session_state.step_count += 1
            
            # Auto-refresh with reduced delay
            import time
            time.sleep(0.5)  # 0.5 second delay (50% faster)
            st.rerun()


if __name__ == "__main__":
    main()

# Made with Bob
