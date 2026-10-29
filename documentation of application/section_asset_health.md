# Asset Health

## 1. Executive Summary
The Asset Health module shifts the railway's maintenance philosophy from *reactive* (fixing things when they break and stop trains) to *predictive* (fixing things right before they are about to break). It acts as the IoT (Internet of Things) sensor monitoring hub for physical railway infrastructure.

## 2. Core Functionality & Features
This dashboard provides live streams of data from physical hardware out on the tracks:
- **Live Telemetry Feeds**: Displays real-time metrics such as vibration frequencies of track points, temperature of axle counters, and voltage sag on overhead traction wires.
- **Asset Status Mapping**: Color-codes every major asset on the network (Green = Healthy, Yellow = Degrading, Red = Critical Failure Imminent).
- **Automated Request Generation**: If an asset crosses a critical threshold, the system can bypass the human-driven "Request Inbox" and automatically generate a `CRITICAL` maintenance ticket directly onto the Maintenance Board.

## 3. User Flow & Practical Use Case
**Who uses it:** Field Engineers and Diagnostic Analysts.
**How it is used:**
1. An analyst monitors the Asset Health dashboard during a heatwave.
2. They notice that the temperature sensor on Point Motor #34 at Dadar station is steadily climbing into the "Yellow" zone.
3. Instead of waiting for the motor to burn out (which would halt the mainline for 4 hours), they preemptively file a 30-minute inspection request to lubricate the motor during a quiet night block.

## 4. In-Depth AI Integration
The Asset Health module relies heavily on continuous Machine Learning algorithms to make sense of massive data streams:
- **Time-Series Anomaly Detection**: Simple threshold alarms (e.g., "Alert if Temp > 80C") are flawed because they trigger false positives during summer. Instead, RailMind uses advanced time-series AI models (like LSTMs or Autoencoders) that understand the *normal* baseline of an asset given the current time of day and season.
- **Predictive Failure Modeling**: By analyzing historical data of past failures, the AI can recognize the subtle data "signatures" that precede a breakdown. If it detects a specific pattern of micro-vibrations in a track point that historically resulted in a failure 3 days later, it will flag the asset as "Degrading" and calculate a precise "Remaining Useful Life" (RUL) score.
