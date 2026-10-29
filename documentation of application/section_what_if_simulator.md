# What-If Simulator

## 1. Executive Summary
Railway operations are inherently chaotic; a perfect schedule can be ruined by a single delayed train or a sudden heavy storm. The What-If Simulator provides a secure, isolated sandbox environment where planners can intentionally "break" an approved schedule to see how resilient it is to real-world perturbations.

## 2. Core Functionality & Features
The simulator allows for stress-testing without risking live operations:
- **Base Plan Selection**: Users select an already `APPROVED` Block Plan from the registry to serve as the baseline.
- **Perturbation Injection**: Users can inject specific chaos parameters into the simulation:
  - *Add/Remove Task*: "What if we suddenly have to fix a fractured rail during this block?"
  - *Add/Remove Train*: "What if a special VIP train needs to pass through this sector at 2 PM?"
  - *Delay Train*: "What if the 12124 Express is running 45 minutes late?"
- **Variance Analysis Output**: The system outputs a side-by-side comparison of the Original Plan vs. the Modified Plan, showing exactly how many fewer tasks can be completed or how much utilization percentage drops due to the perturbation.

## 3. User Flow & Practical Use Case
**Who uses it:** Chief Controllers and Contingency Planners.
**How it is used:**
1. A major cyclone is predicted to hit the coastal section tomorrow, likely delaying all freight trains by at least an hour.
2. The Controller opens the Simulator, loads tomorrow's approved Block Plan, and injects a 60-minute delay perturbation into the schedule.
3. They hit "Initiate Scenario Simulator".
4. The simulator reveals that due to the delay, Block 4 will now crash with a freight train.
5. The Controller proactively goes back to the AI Planner to rebuild the schedule around the predicted delay before tomorrow actually arrives.

## 4. In-Depth AI Integration
This module leverages the core AI architecture but runs it in a highly aggressive, isolated manner:
- **Shadow Optimizer Instances**: When the user clicks "Simulate", the backend spins up an isolated, temporary instance of the CP-SAT Block Optimizer. It feeds it the modified constraints (the perturbations) and forces it to re-solve the entire NP-hard scheduling problem in real-time.
- **State Rollback Validation**: Crucially, the AI is executing on a shadowed database transaction. Once the CP-SAT solver generates the modified contingency plan and calculates the new efficiency metrics, the backend explicitly executes a `db.rollback()`. This ensures that the simulated AI decisions never accidentally overwrite the live, official operational database, keeping the sandbox entirely separated from production reality.
