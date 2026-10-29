# AI Planner (The Core Engine)

## 1. Executive Summary
The AI Planner is the "brain" of RailMind AI. It is an advanced mathematical scheduling engine designed to solve one of the most complex logistical challenges in railway operations: scheduling track maintenance without disrupting live train schedules. It entirely replaces the manual, error-prone process of drafting block plans on paper.

## 2. Core Functionality & Features
The Planner takes massive amounts of variables and outputs an optimized schedule:
- **Constraint Parsing**: It loads all approved tasks from the Maintenance Board, strict deadlines, live train timetables, and available maintenance slots.
- **Multi-Department Integration (Shadow Blocks)**: It actively looks for opportunities to combine tasks. If the Engineering department needs the track at KM 10, and the Signaling department needs the track at KM 12, the Planner will schedule them simultaneously in a single "Integrated Block" rather than closing the track twice.
- **Optimization Strategy Toggle**: Users can instruct the AI to optimize for different goals:
  - *Maximize Task Completion*: Schedule as many tasks as possible.
  - *Minimize Train Delay*: Ensure absolutely zero interference with passenger trains.
  - *Prioritize Critical Assets*: Focus strictly on tasks with the highest AI Risk Scores.
- **Interactive Generation**: Controllers can watch the solver in real-time as it evaluates thousands of permutations before arriving at the optimal schedule.

## 3. User Flow & Practical Use Case
**Who uses it:** Chief Controllers and Planning Engineers.
**How it is used:**
1. At the end of the week, a Controller opens the AI Planner to schedule next week's maintenance.
2. They select the target section (e.g., CSMT-KYN) and the date range.
3. They click "Initialize AI Optimizer".
4. The system crunches the constraints and generates a complete Block Plan containing dozens of scheduled time windows.
5. The Controller reviews the AI's explanation for the schedule, and if satisfied, publishes it to the official Block Plans register.

## 4. In-Depth AI Integration
The AI Planner uses a hybrid approach of Operations Research and Multi-Agent AI:
- **Constraint Programming (CP-SAT Solver)**: The backend utilizes Google OR-Tools (CP-SAT), a state-of-the-art constraint programming solver. The NP-hard scheduling problem is modeled using Boolean variables (e.g., `is_task_X_scheduled_in_slot_Y`). The solver applies hard constraints (e.g., `sum(tasks_in_slot) <= slot_duration`) and maximizes an objective function (e.g., `Maximize(completed_critical_tasks + integrated_block_bonus)`).
- **Multi-Agent Negotiation Framework**: Before feeding data to the CP-SAT solver, virtual agents representing each department negotiate. The TRD agent might "request" a 4-hour block, but the ENGG agent also requests time in the same zone. The negotiation algorithm finds the overlapping spatial-temporal windows (KM ranges and times) and bundles them into an "Integrated Proposal" to feed to the solver.
- **Heuristic Fallback**: If the problem is too complex to solve optimally within the 60-second timeout, the AI automatically falls back to a custom greedy heuristic algorithm, ensuring the user always receives a mathematically sound plan rather than a system timeout.
