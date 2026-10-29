# Operations Dashboard (System Control)

## 1. Executive Summary
The Operations Dashboard serves as the primary landing page and central command center for the entire RailMind AI application. Designed for high-level controllers, administrators, and department heads, it provides a real-time, consolidated view of the railway network's operational status without requiring users to navigate through complex sub-menus.

## 2. Core Functionality & Features
The dashboard acts as an aggregator of telemetry data from all other modules. Its core features include:
- **Live Corridor Telemetry**: A visual representation of the active track corridor (e.g., Central Main Line Corridor from CSMT to KALYAN). It shows live train positions and highlights track segments that are currently under active maintenance blocks.
- **Key Performance Indicators (KPIs)**:
  - **Active Blocks**: The number of currently active maintenance blocks that have been verified by the system.
  - **Safety Events**: A counter tracking how many potential conflicts or safety hazards were detected and auto-mitigated by the AI.
  - **Critical Tasks**: The total count of maintenance tasks flagged as "CRITICAL" priority that require immediate scheduling action.
  - **Network Health**: A real-time percentage score indicating the overall efficiency and safety of the corridor.
- **Quick Access Panels**: Mini-registers providing immediate access to recently approved Block Plans and highly critical infrastructure tasks, acting as shortcuts to the `BlockPlans` and `Maintenance Board` modules.

## 3. User Flow & Practical Use Case
**Who uses it:** Chief Controllers, Operations Managers.
**How it is used:**
1. A Chief Controller logs into RailMind AI at the start of their shift.
2. They instantly view the **Network Health** score. If it is below a certain threshold (e.g., 70%), they know the network is under stress.
3. They check the **Critical Tasks** alert. Seeing "20 Action Required", they can click directly on this widget to be routed to the Maintenance Board, pre-filtered for critical tasks.
4. They monitor the live corridor map to maintain spatial awareness of where active work is happening relative to running trains.

## 4. In-Depth AI Integration
While the dashboard itself is primarily a visualization layer, it relies heavily on the AI engines running in the background:
- **Dynamic Risk Aggregation**: The "Network Health" percentage is not a static number. It is dynamically calculated by aggregating the individual **AI Risk Scores** of all pending tasks (calculated via Random Forest/XGBoost models) and cross-referencing them with live IoT sensor data from the Asset Health module.
- **Auto-Mitigation Reporting**: When the LLM (NVIDIA Nemotron) inside the Safety & Conflicts module successfully resolves a scheduling clash in the background, it increments the "Safety Events Auto-Mitigated" counter. This provides transparency to the administration that the AI is actively preventing human error without requiring constant human oversight.
- **Predictive System Health**: The "Core Online / Checking / Uplink Lost" status indicator constantly polls the backend AI inference engine's health endpoints to ensure the neural networks and solvers are actively listening and ready to process requests.
