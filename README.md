# Drishti (दृष्टि): Real-Time AI-Driven Motor Insurance Risk Assessment

## 1. Project Overview

Drishti is an AI-based solution that assesses motor insurance risks in real time. By leveraging telematics, IoT devices, and machine learning algorithms, Drishti monitors driver behavior, predicts potential risks, and provides personalized feedback to policyholders. This promotes safer driving habits, reducing the likelihood of road accidents and insurance claims.

**Objectives**
- **Real-Time Risk Assessment:** Continuously analyze driver behavior using telematics and sensor data.  
- **Safer Driving Promotion:** Provide actionable, real-time feedback and suggestions to drivers.  
- **Claims Reduction:** Identify risky behaviors early on to minimize insurance claims.

**Core Technologies**
- **Machine Learning:** Predictive models for drowsiness detection, alcohol consumption, and rash driving analysis.  
- **IoT & Telematics:** Collect real-time data from cameras, sensors (MQ-3), and On-Board Diagnostics (OBD).  
- **Cloud Infrastructure:** Store and process sensor data on a virtual machine (VM) server.

---

## 2. Features

### Drowsiness & Yawning Detection
- A USB camera is dedicated to monitoring the driver’s eyes and mouth.
- Alerts are generated if signs of drowsiness or yawning are detected.

### Alcohol Level Monitoring
- An MQ-3 sensor connected to an Arduino checks for alcohol in the driver’s breath.
- The system raises an incident if abnormal alcohol levels are recorded.

### Front-View Visibility Analysis
- A Raspberry Pi camera captures real-time images of the road ahead, taken from the driver’s perspective.
- Visibility percentage is calculated to help determine safe driving speeds.

### OBD-II Data Processing
- Key vehicle metrics such as speed, bearing, engine load, throttle position, and acceleration are captured.
- Risky driving events (aggressive acceleration, harsh braking, speeding, or abrupt turns) are identified.

### Incident Reporting
- All flagged events (alcohol detection, drowsiness, low visibility, rash driving) are consolidated into a final CSV on our server.
- The Drishti website displays these events in real time for continuous monitoring.

---

## 3. System Architecture

Drishti’s system architecture is designed around capturing and processing critical driving data in real time. Four main hardware components work together:

1. **Raspberry Pi (Front Camera)**
   - A Raspberry Pi camera module, mounted to capture the driver’s front view at ~3-second intervals.
   - These images are transferred to a virtual machine (VM) server, where they are processed for visibility analysis.

2. **Driver-Side USB Camera**
   - A USB camera continuously streams video at 30 frames per second (fps).
   - The Raspberry Pi processes these frames locally to detect eye closure or yawning, indicating drowsiness.

3. **Arduino with MQ-3 Sensor**
   - An MQ-3 sensor measures alcohol levels every 2 seconds.
   - The Arduino relays this data to the Raspberry Pi via serial communication.

4. **OBD-II Sensor**
   - Connected to the vehicle’s OBD port, it captures vital telemetry (speed, bearing, RPM, etc.) at around 10 samples per second.
   - This data is forwarded to the VM server to detect events indicative of rash driving.

Together, these components provide a holistic view of the driver’s condition and the vehicle’s performance. The raw data (sensor readings, images, OBD logs) is continuously pushed to a VM server for further processing and archival.

---

## 4. Hardware Setup

- **Raspberry Pi**
  - Connect the official Pi Camera Module for front-view imaging.
  - Ensure the Pi has a stable power supply (5V, 2.5A or higher).

- **USB Camera**
  - Attach the USB camera to the Raspberry Pi for driver-facing footage.
  - Verify that the camera is recognized (`ls /dev/video*` on most Linux systems).

- **Arduino + MQ-3 Alcohol Sensor**
  - MQ-3 sensor’s analog output goes to the Arduino’s analog pin.
  - The Arduino sends data to the Raspberry Pi through a USB serial connection.

- **OBD-II Adapter**
  - Plug the adapter into your vehicle’s OBD port.
  - Connect it to the Raspberry Pi (via USB or Bluetooth, depending on the adapter model) to stream live vehicle metrics.

---

## 5. Communication Flow

1. **Alcohol Sensor Data (MQ-3) → Arduino → Raspberry Pi → VM Server**
   - Every 2 seconds, the Arduino reads the MQ-3 sensor’s analog values.
   - It sends these readings via serial to the Raspberry Pi.
   - The Pi logs them in a CSV file and then uploads this CSV to the VM server.
   - If any abnormal values are detected (above set thresholds), an incident is noted in the final consolidated CSV.

2. **Front Camera (Raspberry Pi) → VM Server**
   - The Raspberry Pi camera snaps an image roughly every 3 seconds.
   - Each image is uploaded immediately to a dedicated folder on the VM server.
   - A watch process on the server detects new images, calculates the visibility percentage, and logs the result.
   - This visibility metric is compared with the current speed from the OBD data. If the speed is too high for poor visibility, an “unsafe” incident is logged.

3. **Driver-Side Camera (Raspberry Pi) → Local Processing → Final CSV**
   - This camera captures the driver’s face at 30 fps.
   - Real-time facial landmark detection (eyes and mouth) on the Raspberry Pi identifies signs of drowsiness or yawning.
   - Any detected drowsy event is logged directly into the final consolidated CSV.

4. **OBD-II Data → Raspberry Pi → VM Server → Analysis**
   - OBD sensor streams data at ~10 samples per second to the Raspberry Pi.
   - The Pi aggregates these readings and forwards them to the VM server.
   - On the server side, an API monitors for risky driving patterns like harsh braking, sharp turns, or speeding.
   - Incidents are tagged and recorded in the final CSV file.

5. **Final CSV Updates → Drishti Website**
   - All incidents are consolidated into a single CSV, continuously updated on the VM server.
   - The Drishti website fetches and displays real-time incident updates for monitoring and analytics.

---

## 6. Data Processing Pipeline

1. **Data Collection**
   - **Sensor Input:** Alcohol levels (MQ-3), driver images (USB camera), front-view images (Pi camera), OBD readings.
   - **Local Logging:** Intermediate CSV files are generated on the Raspberry Pi.

2. **Server-Side Transfer & Storage**
   - CSV files (alcohol, OBD, drowsiness logs) and front-view images are sent to the VM server.
   - Stored in dedicated directories, each monitored by a custom script or application.

3. **Real-Time Analysis & Event Detection**
   - **Visibility Analysis:** Each new front-view image is processed to calculate the road’s visible area.
   - **Driver Drowsiness:** Eye Aspect Ratio (EAR) and Lips Aspect Ratio (LAR) detect drowsiness or yawning in near real time.
   - **Rash Driving:** Vehicle telemetry from OBD (speed, acceleration, throttle, etc.) is fed into an ML or rule-based model to detect harsh braking, abrupt turns, or speeding.

4. **Incident Consolidation**
   - If any subsystem flags an abnormal or unsafe event, it is appended to the final, consolidated CSV.
   - This consolidated CSV becomes a single source of truth for all incidents.

5. **Presentation & Alerts**
   - The Drishti website displays incidents in real time.
   - Alerts (if configured) can be sent to insurance providers or driver’s mobile applications.

---
## 7. Getting Started

Below is a step-by-step guide to setting up and running **Drishti** for development or testing.

### 1. Install Dependencies
   1. On Raspberry Pi (assuming a Debian-based OS):
   ```bash
   sudo apt-get update
   sudo apt-get install python3-pip python3-opencv python3-numpy python3-pandas python3-serial
   ### Install any additional libraries required for camera support as needed.
   ```
   2. On Arduino:
      1. Install the Arduino IDE.
      2. Add any necessary libraries for reading from the MQ-3 sensor (optional, depending on your code).

### 2. Connect and Configure Hardware
   1. **Raspberry Pi Camera**: Enable the camera interface via `raspi-config`.
   2. **USB Camera**: Connect it to one of the Pi’s USB ports and verify it’s detected.
   3. **Arduino + MQ-3**: Plug in the Arduino via USB and check the serial port (e.g., `/dev/ttyACM0`).
   4. **OBD Adapter**: Ensure the Pi recognizes it (Bluetooth or USB).

### 3. Upload Arduino Code
   1. Open the Arduino IDE and load the `.ino` file for MQ-3 sensor reading.
   2. Adjust any thresholds as necessary.
   3. Upload the code to the Arduino.

### 4. Run the Raspberry Pi Scripts
   1. In the cloned repository folder, locate the main Python script (e.g., `main.py`) or separate scripts for each component.
   2. Launch them in separate terminals if needed:
      ```bash
      python3 camera_front.py
      python3 camera_driver.py
      python3 obd_processing.py
      python3 alcohol_sensor.py
      ```
   3. Confirm that logs and CSV files are generated as expected.

### 5. Server-Side Setup
   1. On your VM server, install a web server (e.g., Apache or Nginx) or set up your Python-based server.
   2. Configure watchers or scripts that monitor incoming CSVs and images for new data.
   3. Implement or enable a dashboard on the **Drishti** website to show real-time incidents.

### 6. Testing
   1. **Local Tests**: Simulate a drowsiness event by blinking slowly or yawning in front of the USB camera. Verify if an event is logged.
   2. **Alcohol Sensor**: Use a small amount of isopropyl alcohol or a controlled breath sample to trigger the MQ-3 sensor.
   3. **OBD Data**: Use a vehicle or an OBD simulator to generate speed, RPM, and other signals.
   4. **Visibility**: Block part of the camera’s view or run tests at night to see if the system correctly identifies reduced visibility.

By following these steps, you should have a functional setup of **Drishti**, capturing and processing data to provide real-time insights into driver performance and potential risk factors.

---

## Conclusion

Drishti aims to revolutionize motor insurance risk assessment by combining live sensor data, AI-driven analytics, and easy-to-understand feedback for drivers. Developed by **Team Fast & Furious**, our system seeks to foster safer roads and more reliable insurance underwriting. We encourage you to explore and adapt Drishti for your own use cases—whether it’s to enhance fleet management, conduct research on driver behavior, or simply gain deeper insights into on-road safety.
