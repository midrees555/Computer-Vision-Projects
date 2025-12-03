
# Import the OpenCV library for computer vision tasks
import cv2

# CASCADE_PATH is a variable that stores the full path to the Haar Cascade XML file for face detection.
# cv2.data.haarcascades gives the directory where OpenCV stores its pre-trained Haar Cascade files.
# 'haarcascade_frontalface_default.xml' is a pre-trained model for detecting front-facing human faces.
CASCADE_PATH = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'

# face_cascade is a variable that holds the loaded Haar Cascade classifier object.
# cv2.CascadeClassifier loads the XML file so it can be used to detect faces in images.
face_cascade = cv2.CascadeClassifier(CASCADE_PATH)


def detect_faces(image_path, show_result=True):
    """
    Detect faces in an image using Haar Cascade.
    Args:
        image_path (str): Path to the input image file (e.g., 'photo.jpg').
        show_result (bool): If True, show the image with rectangles drawn around detected faces.
    Returns:
        faces (list): List of rectangles (x, y, w, h) for each detected face.
    """
    # Read the image from the given file path. img will be a numpy array representing the image.
    img = cv2.imread(image_path)
    # If the image could not be loaded (e.g., wrong path), raise an error.
    if img is None:
        raise FileNotFoundError(f"Image not found: {image_path}")
    # Convert the image to grayscale (face detection works better on grayscale images).
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Detect faces in the grayscale image using the loaded Haar Cascade classifier.
    # detectMultiScale returns a list of rectangles, each representing a detected face.
    # scaleFactor=1.1 means the image is reduced by 10% at each scale.
    # minNeighbors=5 means each candidate rectangle should have at least 5 neighbors to be retained.
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
    # If show_result is True, draw rectangles around detected faces and display the image.
    if show_result:
        for (x, y, w, h) in faces:
            # Draw a blue rectangle (BGR: 255,0,0) around each face.
            cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
        # Show the image in a window titled 'Detected Faces'.
        cv2.imshow('Detected Faces', img)
        # Wait for any key to be pressed before closing the window.
        cv2.waitKey(0)
        # Close all OpenCV windows.
        cv2.destroyAllWindows()
    # Return the list of detected faces (rectangles).
    return faces

# This block runs only if the script is executed directly (not imported as a module).
if __name__ == "__main__":
    # Import the sys module to access command-line arguments.
    import sys
    # If the user did not provide an image path, print usage instructions.
    if len(sys.argv) < 2:
        print("Usage: python haar_face_detect.py <image_path>")
    else:
        # Call the detect_faces function with the image path provided by the user.
        detect_faces(sys.argv[1])
