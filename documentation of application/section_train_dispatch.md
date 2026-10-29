# Train Dispatch

## 1. Executive Summary
The Train Dispatch module is the live operational timetable of the railway network. While RailMind is focused on maintenance, maintenance cannot happen without a perfect understanding of train movements. This module provides the baseline temporal map that the entire AI scheduling system must navigate around.

## 2. Core Functionality & Features
The Dispatch board provides a comprehensive view of all rolling stock:
- **Live Tracking**: Displays all active trains, their unique Train Numbers, origins, destinations, and current status.
- **Priority Categorization**: Visually distinguishes between high-priority traffic (e.g., Premium Express, Rajdhani, Shatabdi) and lower-priority traffic (Local, Freight).
- **Temporal Station Mapping**: Shows the exact predicted arrival and departure timestamps for a train at every single station along the corridor.
- **Delay Monitoring**: Highlights trains that are currently running behind schedule, cascading the delay projections down the line.

## 3. User Flow & Practical Use Case
**Who uses it:** Dispatchers, Controllers, and Planning Algorithms (via API).
**How it is used:**
1. A Dispatcher monitors the board to ensure train flow is smooth.
2. If a major freight train is delayed by 2 hours, the dispatcher updates the timetable.
3. This update is instantly broadcast to the backend. The AI Planner, which might have scheduled a maintenance block based on the *original* timetable, now knows the temporal landscape has shifted.

## 4. In-Depth AI Integration
The AI's relationship with the Train Dispatch module is continuous and predictive:
- **Dynamic Constraint Mapping**: The AI Planner does not use a static timetable. It continuously polls the Dispatch database. The arrival/departure times of these trains serve as strict, immutable "Shadow Constraints" in the CP-SAT solver. The solver is mathematically forbidden from allocating a maintenance block that overlaps with a train's temporal footprint at a specific kilometer mark.
- **Predictive Delay Propagation**: Using historical data, Machine Learning models can predict how a 10-minute delay at Station A will compound into a 30-minute delay at Station D due to network congestion, allowing the AI Planner to proactively shift maintenance blocks before the delay even happens.
