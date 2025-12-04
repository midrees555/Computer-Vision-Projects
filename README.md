# Advanced Face Recognition Security System

This project is a complete, professional face recognition security system built with Python. It uses state-of-the-art deep learning models for accurate face detection (YuNet) and recognition (SFace). The system is managed through a user-friendly graphical interface (GUI) and includes advanced features like intelligent alerting, audio notifications, and security logging.

## Features

- **High-Accuracy Recognition**: Utilizes deep learning models (`YuNet` for detection, `SFace` for recognition) for robust performance.
- **Professional GUI**: A polished and attractive dark-themed interface to start/stop the system, manage users, and view system status.
- **Intelligent Email Alerts**: Sends an email with a snapshot when a new, unknown person is detected. Prevents spamming alerts for the same person.
- **Attractive Audio Alerts**: Provides spoken welcome messages for known users and a distinct alert for unknown individuals, with a pleasant female voice.
- **Automated Security Log**: Logs all confirmed entries and unknown person alerts to a daily CSV file with timestamps.
- **Easy User Management via Upload**: Add new people by uploading existing high-quality photos. The application handles file management and model retraining automatically.
- **Robust Face Tracking**: Implements tracking logic (IoU) to maintain a stable identity for people moving in the camera's view, reducing flickering.
- **Dynamic Data Augmentation**: Automatically creates more training data for users with fewer photos, improving model balance and performance.

## Directory Structure

- `src/` — Source code for face detection and recognition
- `assets/` — Contains static assets, such as the alert sound file.
- `data/` — Datasets, raw images, and processed data
  - `train/` — Stores training images, organized in subfolders named after each person.
  - `alerts/` — Stores snapshot images of unknown individuals who triggered an alert.
- `models/` — Pre-trained deep learning models (`.onnx`) and the custom-trained embeddings file (`.pkl`).
- `logs/` — Contains the daily security log CSV files.
- `_practice_and_utilities/` — Contains helper scripts and utilities for practice or alternative workflows (e.g., command-line data collection).

## Installation

1.  **Clone the Repository**
    ```bash
    git clone <https://github.com/midrees555/Computer-Vision-Projects>
    cd Face-Recognition
    ```

2.  **Set Up Environment and Install Dependencies**
    You can use a virtual environment (recommended) or install the packages globally.

    **Method 1: Using a Conda Environment (Recommended)**
    This method isolates project dependencies and is what the `hostel_room_security.ps1` launcher script is designed to use.
    - Ensure you have Anaconda or Miniconda installed.
    - Create and activate the `cv_env` environment:
      ```powershell
      conda create --name cv_env python=3.9 -y
      conda activate cv_env
      pip install -r requirements.txt
      ```

    **Method 2: Using a Standard Python Environment**
    If you prefer not to use Conda, you can install the packages directly using `pip`. It's still highly recommended to do this inside a Python virtual environment (`venv`).
    ```powershell
    pip install -r requirements.txt
    ```
3.  **Download Models**
    You need to download the pre-trained `.onnx` models and place them in the `models/` folder:
    - face_detection_yunet_2023mar.onnx (for detection)
    - face_recognition_sface_2021dec.onnx (for recognition)

4.  **(Optional) Add an Alert Sound**
    Place a sound file (e.g., `alert.wav` or `alert.mp3`) inside the `assets/` folder. If not found, the system will use a spoken voice alert as a fallback.

## How to Use

1.  **Configure Email Alerts**
    - Open `src/notifications.py`.
    - Update `SENDER_EMAIL`, `SENDER_PASSWORD` (with a Gmail App Password), and `RECIPIENT_EMAILS`.

2.  **Launch the Application**
    - **If you used Conda (Method 1):**
      The easiest way to start is by using the provided PowerShell launcher script. Simply double-click `hostel_room_security.ps1` or run it from a PowerShell terminal:
      ```powershell
      .\hostel_room_security.ps1
      ```
      This script automatically finds the `cv_env` Conda environment and launches the GUI.

    - **If you used `pip` directly (Method 2):**
      You will need to run the application's GUI script manually from your terminal:
      ```powershell
      python src/app_gui.py
      ```
3.  **Add Users**
    - Click the "**＋ Add Person via Upload**" button.
    - Enter the person's name in the dialog box.
    - A file dialog will open. Select one or more high-quality pictures of the person.
    - The application will copy the files and automatically retrain the model, providing status updates along the way.

4.  **Start the Security System**
    - Click the "**▶ Start System**" button to begin live recognition.
    - A window will show the live camera feed with bounding boxes and names.
    - Click "**■ Stop System**" or press **`q`** in the camera window to stop.

## Core Components Explained

- **`app_gui.py`**: The main entry point. Provides the Tkinter-based graphical user interface.
- **`recognize_face.py`**: The core engine. Handles video capture, face tracking, recognition, and triggering alerts/logs.
- **`train_model.py`**: The training script. Processes images, applies data augmentation, and creates the `embeddings.pkl` file.
- **`collect_data.py`**: (In `_practice_and_utilities/`) A helper script for command-line based data collection.
- **`notifications.py`**: Manages the construction and sending of email alerts via SMTP.
- **`audio_alerts.py`**: Manages all audio output, including text-to-speech welcome messages and alert sounds.
- **`logger.py`**: Manages writing events to the daily CSV log file.

## Requirements
- Python 3.8+
- OpenCV
- `pyttsx3`
- `pydub`
- `PyYAML`
