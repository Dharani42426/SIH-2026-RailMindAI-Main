# Request Inbox

## 1. Executive Summary
The Request Inbox is the centralized, intelligent ticketing system of RailMind AI. It bridges the gap between field engineers who identify track defects and the central AI Planner that schedules the repairs. It eliminates the chaos of phone calls, WhatsApp messages, and fragmented emails by forcing all maintenance requests through a single, parsable pipeline.

## 2. Core Functionality & Features
The Inbox is designed to handle both structured and unstructured data inputs from various railway departments:
- **Multi-Department Support**: Filters and categorizes requests originating from Engineering (ENGG), Signal & Telecom (SNT), and Traction (TRD).
- **Unstructured Text Processing**: Allows field engineers to simply type exactly what they see in natural language (e.g., "Found a crack in the rail near Dadar station, need 3 hours to weld it before tomorrow").
- **Automated Structuring**: Converts the natural language input into a strict JSON schema containing `department`, `km_from`, `km_to`, `severity`, and `estimated_duration`.
- **Status Tracking**: Tracks the lifecycle of a request from `NEW` -> `PROCESSING` -> `APPROVED` -> `SCHEDULED` (when the AI Planner picks it up) -> `COMPLETED`.

## 3. User Flow & Practical Use Case
**Who uses it:** Field Engineers (Submitters) and Department Heads/Controllers (Reviewers).
**How it is used:**
1. A Permanent Way Inspector (PWI) detects a track defect during a morning patrol.
2. They open the RailMind app and use the Request Inbox to submit a quick text description of the problem.
3. The AI instantly processes the text and generates a structured ticket.
4. A Department Head reviews the auto-generated ticket in the Inbox. If the AI correctly extracted the details, they click "Approve".
5. Once approved, the ticket is pushed to the master **Maintenance Board**, making it eligible for the AI Planner to schedule.

## 4. In-Depth AI Integration
The Request Inbox relies entirely on Natural Language Processing (NLP) to function:
- **LLM-Powered Entity Extraction**: The module uses a Large Language Model (specifically integrated via the NVIDIA Nim API or local equivalent) to perform Named Entity Recognition (NER) and intent classification.
- **Contextual Understanding**: Unlike basic regex scripts, the NLP engine understands railway jargon. If an engineer types "OHE snapping at KM 34", the AI knows "OHE" means Overhead Equipment, automatically categorizing it under the **TRD (Traction)** department and assigning it a **CRITICAL** severity because a snapped wire halts trains immediately.
- **Automated Validation**: If the user's text is too vague (e.g., "Fix track"), the AI rejects the input and prompts the user to specify the location and estimated time, ensuring that the central planner only receives mathematically complete data.
