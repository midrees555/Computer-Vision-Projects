# haar_face_live.py
# Live face detection using Haar Cascade and webcam
# This script is separate from haar_face_detect.py (image file detection)

# Import the OpenCV library for computer vision tasks
import cv2

# CASCADE_PATH is a variable that stores the full path to the Haar Cascade XML file for face detection.
# cv2.data.haarcascades gives the directory where OpenCV stores its pre-trained Haar Cascade files.
# 'haarcascade_frontalface_default.xml' is a pre-trained model for detecting front-facing human faces.
CASCADE_PATH = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'

# face_cascade is a variable that holds the loaded Haar Cascade classifier object.
# cv2.CascadeClassifier loads the XML file so it can be used to detect faces in images.
face_cascade = cv2.CascadeClassifier(CASCADE_PATH)

def detect_faces_live():
    """
    Detect faces in real-time from webcam using Haar Cascade.
    Press 'q' to quit the live window.
    """
    # Open the default webcam (0 is usually the built-in camera, 1 for external)
    cap = cv2.VideoCapture(0)
    # Check if the webcam opened successfully
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return
    print("Webcam opened successfully. Press 'q' to quit.")
    while True:
        # Read a frame from the webcam
        ret, frame = cap.read()
        # ret is True if frame is read correctly, frame is the image from webcam
        if not ret:
            print("Error: Failed to capture frame.")
            break
        # Convert the frame to grayscale (face detection works better on grayscale images)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Detect faces in the grayscale frame using the loaded Haar Cascade classifier
        # detectMultiScale returns a list of rectangles, each representing a detected face
        # scaleFactor=1.1 means the image is reduced by 10% at each scale
        # minNeighbors=5 means each candidate rectangle should have at least 5 neighbors to be retained
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
        # For each detected face, draw a blue rectangle (BGR: 255,0,0) around it
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
        # Show the frame with rectangles in a window titled 'Live Face Detection (Press q to quit)'
        cv2.imshow('Live Face Detection (Press q to quit)', frame)
        # Wait for 1 millisecond for a key press; if 'q' is pressed, exit the loop
        # cv2.waitKey returns a 32-bit integer; & 0xFF gets the last 8 bits (the key code)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("'q' pressed. Exiting...")
            break
    # Release the webcam resource
    cap.release()
    # Close all OpenCV windows
    cv2.destroyAllWindows()
    print("Webcam released and windows closed.")

# This block runs only if the script is executed directly (not imported as a module)
if __name__ == "__main__":
    # Call the live face detection function
    detect_faces_live()
