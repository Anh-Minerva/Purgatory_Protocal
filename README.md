# Purgatory Protocol

A multi-agent AI escape simulation using the BeeAI Framework and Ollama. Three AI agents with different strategies (Safe, Fast, Efficient) navigate a 10x10 grid to escape from obstacles and fire hazards.

## 🎯 Project Overview

This simulation demonstrates autonomous AI agents using the BeeAI Framework to navigate a challenging environment. Each agent has a unique strategy and must use vision and movement tools to find the exit at position (9,9).

## 📁 Project Structure

```
storm-simulation/
├── core/                      # Core agent logic
│   ├── __init__.py           # Package initializer
│   ├── agents.py             # Agent factory (Safe, Fast, Efficient)
│   ├── bee_tools.py          # VisionTool and MoveTool
│   └── utils.py              # Math and direction utilities
├── envi/                      # Environment management
│   ├── __init__.py           # Package initializer
│   └── environment.py        # EscapeGrid (10x10 grid)
├── ui/                        # User interface
│   ├── __init__.py           # Package initializer
│   └── dashboard.py          # Streamlit visualization
├── main.py                    # Main simulation entry point
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## 🚀 Setup Instructions

### Prerequisites

- Python 3.10 or higher
- Ollama installed with `ibm/granite4.1:3b` model
- Virtual environment (recommended)

### Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd storm-simulation
   ```

2. **Create and activate virtual environment:**
   ```bash
   # Windows
   python -m venv stormSimulation
   .\stormSimulation\Scripts\activate

   # Linux/Mac
   python3 -m venv stormSimulation
   source stormSimulation/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Ensure Ollama is running with the model:**
   ```bash
   ollama pull ibm/granite4.1:3b
   ollama serve
   ```

## 🎮 Usage

### Option 1: Terminal-based AI Simulation

Run the autonomous AI agent simulation in the terminal:

```bash
python main.py
```

This will:
- Spawn 3 AI agents (Safe, Fast, Efficient) at different positions
- Run them concurrently to escape the grid
- Display progress and results in the terminal

**Expected Output:**
```
🌪️ BeeAI Escape Simulation
============================================================
🌪️ Setting up Storm Simulation environment...
  Agent 10 (safe) spawned at (1, 1)
  Agent 11 (fast) spawned at (1, 8)
  Agent 12 (efficient) spawned at (5, 1)

🏁 Starting simulation...

🤖 Agent 10 (SAFE) starting...
  Step 1: Using vision to check surroundings...
  ...
✅ Agent 10 ESCAPED in 23 steps!
```

### Option 2: Streamlit Visual Dashboard

Launch the interactive visual dashboard:

```bash
# Windows
.\stormSimulation\Scripts\streamlit.exe run ui/dashboard.py

# Linux/Mac
streamlit run ui/dashboard.py
```

Then open your browser to: **http://localhost:8501**

The dashboard provides:
- Visual 10x10 grid with emoji representations
- Manual agent movement controls
- Grid reset functionality
- Real-time grid state display

## 🤖 Agent Strategies

### 1. Safe Agent (Conservative)
- **Strategy:** Safety-first approach
- **Behavior:** Always checks surroundings, avoids fire at all costs
- **Best for:** Guaranteed escape, avoiding hazards

### 2. Fast Agent (Aggressive)
- **Strategy:** Speed-first approach
- **Behavior:** Takes direct paths, accepts calculated risks
- **Best for:** Quick escapes, time-critical scenarios

### 3. Efficient Agent (Balanced)
- **Strategy:** Optimal pathfinding
- **Behavior:** Uses Manhattan distance, balances safety and speed
- **Best for:** Optimal performance, resource efficiency

## 🛠️ Technical Details

### Grid System

- **Size:** 10x10 grid (100 cells)
- **Coordinates:** (x, y) where x=column (0-9), y=row (0-9)
- **Exit:** Located at (9, 9)

### Cell Values

| Value | Type | Description |
|-------|------|-------------|
| 0 | Empty | Safe to move |
| 1 | Wall | Blocks movement |
| 3 | Exit | Goal at (9,9) |
| 5 | Fire | Hazard to avoid |
| 10-12 | Agents | Agent identifiers |

### Tools Available to Agents

1. **VisionTool**
   - Provides line-of-sight in 4 cardinal directions (N, S, E, W)
   - Shows immediate tile and far tile (if not blocked)
   - Returns tile values for decision-making

2. **MoveTool**
   - Moves agent exactly 1 tile in cardinal directions
   - Validates moves (no diagonal, no teleporting)
   - Checks for obstacles and collisions

## 🔧 Configuration

### Changing the Model

Edit `main.py` or agent creation functions:

```python
model = "ibm/granite4.1:3b"  # Change to your preferred Ollama model
```

### Adjusting Max Steps

In `main.py`:

```python
max_steps = 50  # Increase for more complex mazes
```

### Customizing the Grid

In `main.py`, modify the obstacles:

```python
obstacles = [
    (2, 2, 1),  # Wall at (2,2)
    (5, 5, 5),  # Fire at (5,5)
    # Add more obstacles...
]
```

## 📊 Performance Metrics

The simulation tracks:
- **Steps taken:** Number of moves to reach exit
- **Escape status:** Whether agent successfully escaped
- **Average steps:** Mean steps for successful escapes
- **Success rate:** Percentage of agents that escaped

## 🐛 Troubleshooting

### "Pydantic race condition" error
- The code includes automatic fixes for this
- If it persists, restart Python and try again

### "Model not found" error
- Ensure Ollama is running: `ollama serve`
- Pull the model: `ollama pull ibm/granite4.1:3b`

### Streamlit shows blank screen
- Check browser console for errors
- Refresh the page at http://localhost:8501
- Ensure all dependencies are installed

### Agents not moving
- Check Ollama is running and responding
- Verify the model is loaded correctly
- Check terminal output for error messages

## 🤝 Contributing

This project was created with Bob (AI coding assistant). Feel free to:
- Add new agent strategies
- Implement more complex grid layouts
- Integrate the dashboard with live AI agent simulation
- Add performance analytics and visualizations
- Add collision mechanism between each agent
- Add health threshold for each agent
- Add new disasters with different effects


## 📝 License

MIT License - Feel free to use and modify as needed.

## 🙏 Acknowledgments

- **BeeAI Framework** - For the agent framework
- **Ollama** - For local LLM inference
- **Streamlit** - For the visualization dashboard
- **Bob** - For development assistance

---

**Made with Bob** 🤖

For questions or issues, please check the troubleshooting section or review the code comments.
