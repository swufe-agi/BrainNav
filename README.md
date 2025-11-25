
# 📘 BrainNav

This project implements an autonomous navigation system based on **VLM**, a **visual perception module**, **navigation graph construction**, and **macro-action control**, designed for the **LIMO Pro mobile robot**.

We conduct experiments using the **LIMO Pro** mobile robot (dimensions: **322 × 220 × 251 mm**).
The robot is equipped with an **Orbbec DaBai RGB camera** for capturing the current visual observations.
Five macro-actions are implemented:

* **Move Forward**: the robot moves forward by **0.5 cm**
* **Move Backward**: the robot rotates **180°**, then moves **0.5 cm** backward
* **Turn Left**: the base rotates **90°** to the left
* **Turn Right**: the base rotates **90°** to the right
* **Stop**: the robot remains stationary

It is important to note that our experimental framework uses **only RGB images**.
No depth images, LiDAR, or additional sensing algorithms are required, making the system lightweight and easy to deploy in real-world environments.

The system integrates voice commands, environmental images, candidate paths, and backtracking navigation, achieving intelligent movement with **memory**, **reasoning ability**, and **reversible path tracing**.

---

# 📁 Project Structure

```
.
├── agent_main.py           # Main navigation logic (NavigationAgent)
├── agent_api.py            # GPT inference interface
├── agent_prompt_manager.py # Prompt generator
├── actions.py              # Robot action executor (move_car)
├── camera.py               # Four-direction image capture
├── nav_log.py              # Log management
├── Map_code/               # Map construction code
├── version1/               # Single-obstacle version
├── output/                 # Output files
├── Log/                    # Log directory
├── navigation_log.txt      # Default navigation log
├── item_list_storage.json  # Detected object list
├── history_data.json       # Historical viewpoint data
├── road_map_data.json      # Road network structure (graph)
└── README.md               # This documentation
```

---

# 🚀 1. Environment Setup

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Install LIMO SDK and Orbbec SDK (depth camera)

These are automatically integrated through the provided directories:

* `pylimo/`
* `pyorbbecsdk-main/`

### 3. Configure the OpenAI API Key

Edit `API_KEY.py`:

```python
OPENAI_API_KEY = "your_key_here"
```

---

# 🎮 2. Run the System

Execute the main program:

```bash
python agent_main.py
```

The system will then wait for the user to input a navigation instruction, e.g.:

```
Take me to the elevator entrance.
```

---

# ✨ 3. Backtracking Navigation

The system supports a complete backtracking mechanism, including:

* `start_road()`: Begin searching based on stored map files
* `backtrack_road()`: Reverse traversal according to current observations

The module outputs a final coordinate sequence and controls the robot along the computed route.

---

# 🗂 4. Output File Description

| File name                | Function                                  |
| ------------------------ | ----------------------------------------- |
| `item_list_storage.json` | All detected objects                      |
| `history_data.json`      | Coordinates and details of each viewpoint |
| `road_map_data.json`     | Constructed road network graph            |
| `navigation_log.txt`     | Complete navigation log                   |

---



