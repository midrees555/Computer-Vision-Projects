# --- Import Necessary Libraries ---
import cv2  # Import OpenCV for video capture, image processing, and drawing on the screen.
import os  # Import os to check if files and directories exist.
import argparse  # Import argparse to parse command-line arguments when running the script directly.
import pickle  # Import pickle to load the saved embeddings file.
import numpy as np  # Import numpy for numerical operations (not directly used here but good practice with OpenCV).
from collections import deque, Counter  # Import deque for efficient fixed-size lists and Counter for majority voting.
import time  # Import time for calculating FPS and handling time-based events.
from notifications import send_alert_email  # Import our custom function for sending email alerts.
from logger import SecurityLogger  # Import our custom class for logging events to a CSV file.
from audio_alerts import AudioNotifier  # Import our custom class for playing audio alerts.

def recognize_faces_live(embeddings_path='models/embeddings.pkl', camera_index=0, confidence_threshold=0.8):  # Main function for live recognition.
    """Captures video, detects faces, tracks them, and performs recognition with alerts and logging."""
    # --- Argument Explanations ---
    # embeddings_path (str): The file path of the saved embeddings pickle file.
    # camera_index (int or str): The number for the webcam (e.g., 0) or a URL for a video stream.
    # confidence_threshold (float): The threshold for recognition. Higher is stricter (0.0 to 1.0).

    # --- Initial Checks ---
    if not os.path.exists(embeddings_path):  # Check if the embeddings file exists.
        print(f"Error: Embeddings file not found at '{embeddings_path}'. Please run the training script first.")  # Print an error if not found.
        return  # Exit the function.

    # --- Load Deep Learning Models ---
    models_dir = os.path.dirname(embeddings_path)  # Get the directory where models are stored.
    # Load the DNN face detector model (YuNet).
    detector_path = os.path.join(models_dir, 'face_detection_yunet_2023mar.onnx')  # Path to the detector model.
    if not os.path.exists(detector_path):  # Check if the model file exists.
        print(f"Error: Face detector model not found at '{detector_path}'")  # Print an error.
        return  # Exit.
    face_detector = cv2.FaceDetectorYN.create(detector_path, "", (0, 0))  # Create the face detector object.

    # Load the DNN face recognizer model (SFace).
    recognizer_path = os.path.join(models_dir, 'face_recognition_sface_2021dec.onnx')  # Path to the recognizer model.
    if not os.path.exists(recognizer_path):  # Check if the model file exists.
        print(f"Error: Face recognizer model not found at '{recognizer_path}'")  # Print an error.
        return  # Exit.
    face_recognizer = cv2.FaceRecognizerSF.create(recognizer_path, "")  # Create the face recognizer object.
    
    # --- Load the Trained Data ---
    with open(embeddings_path, 'rb') as f:  # Open the embeddings file in read-binary mode ('rb').
        data = pickle.load(f)  # Load the data from the pickle file.
    known_embeddings = data["embeddings"]  # Get the list of face embeddings.
    known_names = data["names"]  # Get the corresponding list of names.

    # --- Face Tracking and Smoothing Logic ---
    # We will track faces across frames to make the recognition more stable.
    
    # `tracked_faces` is a dictionary that will store information about each face being tracked.
    # The key is a unique `tracker_id`, and the value is another dictionary containing that tracker's info.
    tracked_faces = {}  # Initialize an empty dictionary for active trackers.
    next_tracker_id = 0  # Initialize a counter to assign unique IDs to new trackers.
    
    def get_iou(boxA, boxB):  # Helper function to calculate "Intersection over Union" (IoU) of two bounding boxes.
        """Calculates the IoU to determine if a new detection is the same face as an existing tracker."""
        xA = max(boxA[0], boxB[0])  # Get the largest x-coordinate of the top-left corners.
        yA = max(boxA[1], boxB[1])  # Get the largest y-coordinate of the top-left corners.
        xB = min(boxA[2], boxB[2])  # Get the smallest x-coordinate of the bottom-right corners.
        yB = min(boxA[3], boxB[3])  # Get the smallest y-coordinate of the bottom-right corners.
        interArea = max(0, xB - xA) * max(0, yB - yA)  # Calculate the area of the intersection rectangle.
        boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])  # Calculate the area of the first box.
        boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])  # Calculate the area of the second box.
        iou = interArea / float(boxAArea + boxBArea - interArea)  # Calculate the IoU score.
        return iou  # Return the score.

    # --- Configuration Parameters ---
    PREDICTION_HISTORY_SIZE = 10  # How many of the last predictions to store for smoothing.
    TRACKER_TTL = 5  # Time To Live: How many frames a tracker can exist without being re-detected before it's deleted.
    CONFIRMATION_THRESHOLD = 3  # How many times a name must be seen consecutively to be "confirmed".
    UNKNOWN_ALERT_DURATION = 5.0  # How long (in seconds) an unknown person must be visible to trigger an alert.
    UNKNOWN_COOLDOWN_SECONDS = 300  # 5 minutes: How long to remember an unknown face to prevent sending duplicate alerts.

    os.makedirs('data/alerts', exist_ok=True)  # Create a directory to store snapshot images for alerts.

    # --- Initialize Modules ---
    logger = SecurityLogger()  # Create an instance of our logger class.
    audio_notifier = AudioNotifier()  # Create an instance of our audio notifier class.
    # This list will store features of unknown faces for which we've recently sent an alert.
    # It acts as a short-term memory to prevent spamming alerts for the same person.
    recent_unknowns = []  # Initialize an empty list.

    # --- Start Video Capture ---
    cap = cv2.VideoCapture(camera_index)  # Initialize video capture from the specified camera index or URL.
    if not cap.isOpened():  # Check if the camera was opened successfully.
        print(f"Error: Could not open camera with index '{camera_index}'.")  # Print an error if not.
        return  # Exit the function.

    print("Camera opened successfully. Press 'q' in the video window to quit.")  # Inform the user.

    last_frame_time = time.time()  # Initialize a variable to store the time of the last frame for FPS calculation.
    while True:  # Start the main loop to process video frames.
        ret, frame = cap.read()  # Read a single frame from the camera.
        if not ret:  # If the frame was not captured successfully (e.g., camera disconnected)...
            print("Error: Failed to capture frame.")  # ...print an error...
            break  # ...and exit the loop.

        # --- FPS Calculation ---
        current_time = time.time()  # Get the current time.
        fps = 1 / (current_time - last_frame_time)  # Calculate Frames Per Second.
        last_frame_time = current_time  # Update the last frame time for the next iteration.

        # --- Performance Optimization: Resize frame before detection ---
        # High-resolution frames are great, but detection is much faster on smaller images.
        orig_h, orig_w, _ = frame.shape  # Get the original frame dimensions.
        target_width = 640  # Define a standard width for detection.
        scale = target_width / orig_w  # Calculate the scaling factor to maintain aspect ratio.
        detection_frame = cv2.resize(frame, (target_width, int(orig_h * scale)))  # Resize the frame.

        # --- Face Detection ---
        h, w, _ = detection_frame.shape  # Get the dimensions of the resized detection frame.
        face_detector.setInputSize((w, h))  # Set the input size for the detector.
        _, faces = face_detector.detect(detection_frame)  # Run face detection.
        current_detections = faces if faces is not None else []  # Ensure `current_detections` is always a list.
        
        # --- Match current detections with existing trackers ---
        matched_tracker_ids = set()  # Create a set to keep track of trackers that have been matched in this frame.
        for face in current_detections:  # Loop through each face detected in the current frame.
            box = list(map(int, face[:4]))  # Get the bounding box coordinates [x, y, width, height].
            x, y, w, h = box  # Unpack the coordinates.
            current_box = [x, y, x + w, y + h]  # Convert to [x1, y1, x2, y2] format, relative to the small detection_frame.

            # Find the best matching existing tracker for the current detected face.
            best_iou = 0  # Initialize the best IoU score.
            best_tracker_id = None  # Initialize the ID of the best matching tracker.
            for tracker_id, tracker_data in tracked_faces.items():  # Loop through all active trackers.
                iou = get_iou(current_box, tracker_data['box'])  # Calculate the IoU between the current face and the tracker.
                if iou > best_iou:  # If this IoU is better than the previous best...
                    best_iou = iou  # ...update the best score...
                    best_tracker_id = tracker_id  # ...and store the tracker's ID.

            # If a good match is found (IoU > 0.5), update the existing tracker.
            if best_iou > 0.5 and best_tracker_id not in matched_tracker_ids:  # Check for a good overlap and that the tracker hasn't been matched already.
                tracker = tracked_faces[best_tracker_id]  # Get the matched tracker.
                matched_tracker_ids.add(best_tracker_id)  # Add its ID to the set of matched trackers for this frame.
            else:  # Otherwise, if no good match is found, create a new tracker for this new face.
                tracker = {  # Create a new dictionary to hold the new tracker's information.
                    'id': next_tracker_id,  # Assign a unique ID.
                    'predictions': deque(maxlen=PREDICTION_HISTORY_SIZE),  # A deque to store recent name predictions.
                    'confirmed_name': "Unknown",  # The stable, confirmed name for this person.
                    'confirmation_streak': 0,  # A counter for consecutive same-name predictions.
                    'first_seen': time.time(),  # Timestamp of when this tracker was created.
                    'alert_sent': False,  # A flag to ensure we only send one alert per unknown person.
                    'log_and_audio_triggered': False  # A flag to ensure we only log/welcome a person once.
                }
                tracked_faces[next_tracker_id] = tracker  # Add the new tracker to our main dictionary.
                matched_tracker_ids.add(next_tracker_id)  # Add its ID to the set of matched trackers.
                next_tracker_id += 1  # Increment the ID counter for the next new face.

            # --- Perform Recognition ---
            aligned_face = face_recognizer.alignCrop(detection_frame, face)  # Align and crop the detected face.
            feature = face_recognizer.feature(aligned_face)  # Extract the 128-d feature vector (embedding).
            
            # Compare the current face's feature against all known embeddings.
            best_score = -1  # Initialize the best score.
            current_name = "Unknown"  # Initialize the current prediction.
            for i, emb in enumerate(known_embeddings):  # Loop through all known embeddings.
                score = face_recognizer.match(feature, emb, cv2.FaceRecognizerSF_FR_COSINE)  # Calculate the cosine similarity score.
                if score > best_score:  # If this score is the best so far...
                    best_score = score  # ...update the best score...
                    current_name = known_names[i]  # ...and store the corresponding name.
            
            # Add the current prediction to this tracker's history for smoothing.
            if best_score > confidence_threshold:  # If the score is above our confidence threshold...
                tracker['predictions'].append(current_name)  # ...add the recognized name to the history.
            else:  # Otherwise...
                tracker['predictions'].append("Unknown")  # ...add "Unknown" to the history.

            # --- Get Smoothed & Confirmed Name ---
            name = "Unknown"  # Default name is "Unknown".
            if tracker['predictions']:  # If there are any predictions in the history...
                most_common = Counter(tracker['predictions']).most_common(1)[0]  # Find the most common name in the history.
                candidate_name = most_common[0]  # This is our best guess for the name.

                # --- Stronger Confirmation Logic to "lock in" a name ---
                if tracker['confirmed_name'] != "Unknown":  # If this tracker is already confirmed as a known person...
                    name = tracker['confirmed_name']  # ...use that locked-in name.
                elif candidate_name != "Unknown":  # Otherwise, if the current candidate is a known person...
                    tracker['confirmation_streak'] += 1  # ...increment the confirmation streak.
                    if tracker['confirmation_streak'] >= CONFIRMATION_THRESHOLD:  # If the streak reaches the threshold...
                        tracker['confirmed_name'] = candidate_name  # ...lock in the name.
                        name = candidate_name  # And use it for display.

                        # --- Trigger Welcome Message and Log Entry ONCE per confirmation ---
                        if not tracker['log_and_audio_triggered']:  # Check if we haven't already welcomed this person.
                            logger.log_event('KNOWN_PERSON_ENTRY', name)  # Log the entry event.
                            audio_notifier.welcome(name)  # Play the welcome message.
                            tracker['log_and_audio_triggered'] = True  # Set the flag to prevent re-triggering.

            # --- Intelligent Alerting Logic ---
            if name == "Unknown" and not tracker['alert_sent']:  # If the person is Unknown and we haven't sent an alert for this tracker yet...
                time_visible = time.time() - tracker['first_seen']  # ...calculate how long they've been visible.
                if time_visible > UNKNOWN_ALERT_DURATION:  # If they've been visible longer than our alert duration...
                    is_new_unknown = True  # ...assume it's a new unknown person by default.
                    # Clean up old entries from our recent unknowns list to keep it from growing indefinitely.
                    recent_unknowns = [u for u in recent_unknowns if time.time() - u['timestamp'] < UNKNOWN_COOLDOWN_SECONDS]
                    
                    for unknown in recent_unknowns:  # Loop through the faces of recently alerted unknown people.
                        score = face_recognizer.match(feature, unknown['feature'], cv2.FaceRecognizerSF_FR_COSINE)  # Compare the current face to the stored one.
                        if score > confidence_threshold:  # If they are very similar...
                            is_new_unknown = False  # ...it's not a new unknown person.
                            print(f"INFO: Re-detected a recent unknown person. Suppressing new alert.")  # Log this.
                            break  # Stop checking.

                    if is_new_unknown:  # If it is genuinely a new unknown person...
                        print(f"ALERT: New unknown person detected for over {UNKNOWN_ALERT_DURATION} seconds.")  # ...print an alert.
                        snapshot_path = f"data/alerts/alert_{int(time.time())}.jpg"  # ...create a path for the snapshot.
                        cv2.imwrite(snapshot_path, frame)  # ...save the current frame as an image.
                        logger.log_event('UNKNOWN_PERSON_ALERT', details=f"Snapshot saved to {snapshot_path}")  # ...log the event.
                        send_alert_email(snapshot_path)  # ...send the email alert.
                        audio_notifier.unknown_alert()  # ...play the audio alert.
                        # Add this new unknown person's feature to our short-term memory.
                        recent_unknowns.append({'feature': feature, 'timestamp': time.time()})

                    tracker['alert_sent'] = True  # Mark the alert as sent for this specific tracker to prevent it from re-triggering immediately.

            # --- Update Tracker State ---
            tracker['box'] = current_box  # Update the tracker's last known position.
            tracker['ttl'] = TRACKER_TTL  # Reset the tracker's Time To Live since it was just seen.

            # --- Draw on Original Frame ---
            # We need to scale the bounding box coordinates from the small `detection_frame` back to the large original `frame`.
            orig_x = int(current_box[0] / scale)  # Scale the x-coordinate.
            orig_y = int(current_box[1] / scale)  # Scale the y-coordinate.
            orig_w_box = int((current_box[2] - current_box[0]) / scale)  # Scale the width.
            orig_h_box = int((current_box[3] - current_box[1]) / scale)  # Scale the height.
            color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)  # Green for known, red for unknown.
            text = f"{name} ({best_score:.2f})"  # Create the text to display (Name and Score).
            cv2.putText(frame, f"FPS: {fps:.1f}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)  # Draw the FPS counter.
            cv2.rectangle(frame, (orig_x, orig_y), (orig_x + orig_w_box, orig_y + orig_h_box), color, 2)  # Draw the bounding box.
            cv2.putText(frame, text, (orig_x, orig_y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)  # Draw the name text above the box.

        # --- Clean up old trackers ---
        dead_trackers = []  # Create a list to hold IDs of trackers to be deleted.
        for tracker_id, tracker in tracked_faces.items():  # Loop through all active trackers.
            if tracker_id not in matched_tracker_ids:  # If a tracker was NOT matched in the current frame...
                tracker['ttl'] -= 1  # ...decrement its Time To Live.
            if tracker['ttl'] <= 0:  # If its TTL has reached zero...
                dead_trackers.append(tracker_id)  # ...mark it for deletion.
        
        for tracker_id in dead_trackers:  # Loop through the trackers marked for deletion.
            del tracked_faces[tracker_id]  # Remove them from the active trackers dictionary.

        cv2.imshow('Live Face Recognition (Press q to quit)', frame)  # Display the final frame in a window.

        if cv2.waitKey(1) & 0xFF == ord('q'):  # Wait for 1ms for a key press; if it's 'q'...
            print("'q' pressed. Exiting...")  # ...log the exit...
            break  # ...and break the main loop.

    # --- Final Cleanup ---
    cap.release()  # Release the camera resource.
    cv2.destroyAllWindows()  # Close all OpenCV windows.
    print("Camera released and windows closed.")  # Print a final message.

if __name__ == '__main__':  # This block runs only when this script is executed directly from the command line.
    parser = argparse.ArgumentParser(description="Live face recognition using a trained model.")  # Create an argument parser.
    parser.add_argument('--camera', type=str, default='0',  # Add an argument for the camera source.
                        help="Camera index or video stream URL. Default is 0.")
    parser.add_argument('--confidence', type=float, default=0.8,  # Add an argument for the confidence threshold.
                        help="Confidence threshold for recognition (0.0 to 1.0). Default is 0.8.")
    
    args = parser.parse_args()  # Parse the provided arguments.

    try:  # Try to convert the camera argument to an integer.
        camera_source = int(args.camera)
    except ValueError:  # If it fails (e.g., it's a URL), use it as a string.
        camera_source = args.camera

    recognize_faces_live(camera_index=camera_source, confidence_threshold=args.confidence)  # Call the main function with the parsed arguments.