import cv2  # Import OpenCV for camera access and image processing.
import os  # Import os to create directories.
import time  # Import time to create unique filenames.
import argparse  # Import argparse to handle command-line arguments.

def collect_training_data(person_name, num_images=30, output_dir='data/train'):  # Main function for data collection.
    """A helper utility to collect face images for training."""
    # --- Argument Explanations ---
    # person_name (str): The name of the person for whom data is being collected.
    # num_images (int): The target number of images to collect.
    # output_dir (str): The root directory where training data will be saved.
    
    # --- Setup ---
    # Load the face detector model.
    detector_path = 'models/face_detection_yunet_2023mar.onnx'  # Path to the pre-trained face detector model.
    if not os.path.exists(detector_path):  # Check if the model file exists.
        print(f"Error: Face detector model not found at '{detector_path}'")  # Print an error if not found.
        return  # Exit the function.
    face_detector = cv2.FaceDetectorYN.create(detector_path, "", (0, 0))  # Create the face detector object.

    # Create the directory for the person's images if it doesn't already exist.
    person_dir = os.path.join(output_dir, person_name)  # Construct the full path to the person's folder.
    os.makedirs(person_dir, exist_ok=True)  # Create the directory.

    # --- Input Validation ---
    # Prevent using "Unknown" as a name, as it's a reserved keyword in the recognition logic.
    if person_name.lower() == "unknown":  # Check if the provided name is "unknown".
        print("Error: 'Unknown' is a reserved name. Please choose a different name.")  # Print an error.
        return  # Exit the function.
    print(f"Saving images to: {person_dir}")  # Inform the user where images will be saved.

    # --- Start Video Capture ---
    cap = cv2.VideoCapture(0)  # Initialize video capture from the default camera (index 0).
    if not cap.isOpened():  # Check if the camera was opened successfully.
        print("Error: Could not open camera.")  # Print an error if not.
        return  # Exit the function.

    # Set camera resolution to a higher quality.
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)  # Set the frame width.
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)  # Set the frame height.

    count = 0  # Initialize a counter for the number of saved images.
    while count < num_images:  # Loop until the target number of images is collected.
        ret, frame = cap.read()  # Read a single frame from the camera.
        if not ret:  # If the frame was not captured successfully...
            break  # ...exit the loop.

        display_frame = frame.copy()  # Create a copy of the frame to draw on, leaving the original clean.

        # --- Face Detection ---
        h, w, _ = frame.shape  # Get the height and width of the frame.
        face_detector.setInputSize((w, h))  # Set the input size for the detector to match the frame.
        _, faces = face_detector.detect(frame)  # Run face detection on the frame.

        # --- Find and Display the Largest Face ---
        if faces is not None and len(faces) > 0:  # Check if any faces were detected.
            largest_face = max(faces, key=lambda face: face[2] * face[3])  # Find the face with the largest area (width * height).
            box = list(map(int, largest_face[:4]))  # Convert the bounding box coordinates to integers.
            x, y, w, h = box  # Unpack the coordinates.

            # Draw a green rectangle around the largest face on the display frame.
            cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Display instructions and progress on the screen.
            text = f"Press 's' to save. Collected: {count}/{num_images}"  # Create the text string.
            cv2.putText(display_frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)  # Draw the text.

        cv2.imshow('Data Collection - Press "q" to quit', display_frame)  # Show the frame in a window.

        # --- Handle User Input ---
        key = cv2.waitKey(1) & 0xFF  # Wait for a key press for 1 millisecond.
        if key == ord('q'):  # If the 'q' key is pressed...
            break  # ...exit the loop.
        elif key == ord('s') and faces is not None:  # If 's' is pressed and a face is visible...
            # ...save the original, clean frame as an image.
            timestamp = int(time.time() * 1000)  # Create a unique timestamp for the filename.
            filename = os.path.join(person_dir, f"{person_name}_{timestamp}.jpg")  # Construct the full file path.
            cv2.imwrite(filename, frame)  # Save the image to the file.
            print(f"Saved {filename}")  # Print a confirmation message.
            count += 1  # Increment the saved image counter.

    # --- Cleanup ---
    cap.release()  # Release the camera resource.
    cv2.destroyAllWindows()  # Close all OpenCV windows.
    print(f"\nData collection finished. Collected {count} images for {person_name}.")  # Print a final summary.

if __name__ == '__main__':  # This block runs only when this script is executed directly.
    parser = argparse.ArgumentParser(description="Collect face images for training.")  # Create a command-line argument parser.
    parser.add_argument('name', type=str, help="The name of the person (use quotes for names with spaces, e.g., 'John Doe').")  # Add an argument for the person's name.
    parser.add_argument('--count', type=int, default=30, help="Target number of images to collect.")  # Add an optional argument for the number of images.
    
    args = parser.parse_args()  # Parse the arguments provided by the user.
    collect_training_data(person_name=args.name, num_images=args.count)  # Call the main function with the parsed arguments.