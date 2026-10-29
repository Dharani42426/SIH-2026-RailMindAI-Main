# Safety & Conflicts (Conflict Resolver)

## 1. Executive Summary
The Safety & Conflicts module is the ultimate fail-safe mechanism of RailMind AI. It acts as an aggressive, real-time clash detection engine that physically prevents human operators from making catastrophic scheduling errors. It is where advanced AI logic meets hard safety protocols.

## 2. Core Functionality & Features
This sandbox interface allows for the manual testing of proposed track blocks:
- **Live Perturbation Injection**: A user can manually input a proposed maintenance block (e.g., "I want to block KM 10 to 20 from 14:00 to 16:00 on Line 2").
- **Real-Time Clash Detection**: The system instantly cross-references this proposal against the live Train Dispatch timetable.
- **Visual Alerting**: If a train is scheduled to pass through that exact KM range during that exact time window, the system flashes a critical "UNSAFE VECTOR DETECTED" alert and lists the specific trains involved in the crash scenario.
- **Hard Lockout**: The system will not allow a block to be pushed to `APPROVED` status if an unmitigated conflict exists.

## 3. User Flow & Practical Use Case
**Who uses it:** Chief Safety Officers and Controllers.
**How it is used:**
1. In an emergency (e.g., a sudden rail fracture), a controller bypasses the normal AI Planner and manually tries to force an immediate block on the track.
2. They input the parameters into the Safety Simulator.
3. The simulator flags that a Premium Express train is 15 minutes away from that zone.
4. The controller is blocked from issuing the order blindly. They must now rely on the AI to generate a mitigation strategy before proceeding.

## 4. In-Depth AI Integration
This module showcases the most advanced use of Generative AI in the application:
- **LLM-Based Mitigation Strategies**: When a physical clash is detected, standard software can only say "Error: Clash." RailMind goes further. It takes the clash data (Train #, priority, block location, duration) and feeds it into an advanced Large Language Model (e.g., NVIDIA Nemotron 3 Ultra) acting via a customized LangChain pipeline.
- **System Prompting**: The LLM is instructed to act as a "Senior Railway Safety Controller." It analyzes the conflict and generates a concise, operational directive.
- **Intelligent Output**: The LLM will output a natural-language mitigation plan. For example: *"Conflict Detected with Premium Express 12124. Do not approve block. Strategy: Delay train 12124 at previous station (Thane) by 15 minutes, and compress maintenance block duration to 45 minutes to clear the vector."* This provides actionable intelligence rather than just an error code.
