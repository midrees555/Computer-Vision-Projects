
# --- Import Necessary Libraries ---
import cv2  # Import OpenCV for image processing and deep learning model inference.
import os  # Import os to interact with the file system (e.g., reading file paths, creating directories).
import numpy as np  # Import numpy for numerical operations, especially with image arrays.
import yaml  # Import yaml to save a human-readable list of trained names.
import pickle  # Import pickle to serialize and save the Python object containing embeddings and names.
import random  # Import random for data augmentation choices.

def train_model(data_dir='data/train', embeddings_path='models/embeddings.pkl', labels_path='models/face_labels.yml'):  # Main function to train the model.
    """Goes through training images, detects faces, extracts deep learning embeddings, and saves them."""
    # --- Argument Explanations ---
    # data_dir (str): The folder where our training images are stored (e.g., 'data/train').
    # embeddings_path (str): The file path where the extracted embeddings will be saved.
    # labels_path (str): The file path where a human-readable list of names will be saved.

    # --- Initial Checks and Setup ---
    if not os.path.exists(data_dir):  # Check if the training data directory exists.
        print(f"Error: Data directory not found at '{data_dir}'")  # Print an error if it doesn't.
        return  # Exit the function.

    models_dir = os.path.dirname(embeddings_path)  # Get the directory path for the models (e.g., 'models/').
    if not os.path.exists(models_dir):  # Check if the models directory exists.
        os.makedirs(models_dir)  # Create it if it doesn't.

    # --- Load Deep Learning Models ---
    # Load the DNN face detector model (YuNet).
    detector_path = os.path.join(models_dir, 'face_detection_yunet_2023mar.onnx')  # Path to the detector model.
    if not os.path.exists(detector_path):  # Check if the model file exists.
        print(f"Error: Face detector model not found at '{detector_path}'")  # Print an error.
        print("Please download it and place it in the 'models' folder.")  # Provide instructions.
        return  # Exit.
    face_detector = cv2.FaceDetectorYN.create(detector_path, "", (0, 0))  # Create the face detector object.

    # Load the DNN face recognizer model (SFace).
    recognizer_path = os.path.join(models_dir, 'face_recognition_sface_2021dec.onnx')  # Path to the recognizer model.
    if not os.path.exists(recognizer_path):  # Check if the model file exists.
        print(f"Error: Face recognizer model not found at '{recognizer_path}'")  # Print an error.
        print("Please download it and place it in the 'models' folder.")  # Provide instructions.
        return  # Exit.
    face_recognizer = cv2.FaceRecognizerSF.create(recognizer_path, "")  # Create the face recognizer object.

    # Set a confidence threshold for face detection. We will only process faces detected with a score higher than this.
    DETECTION_CONF_THRESHOLD = 0.90  # A value of 0.9 means 90% confidence.

    # --- Data Augmentation: Create more training data from existing images ---
    # By creating slightly modified versions of our training images (e.g., brighter, flipped),
    # we teach the model to be more robust and recognize faces under different conditions.

    def augment_brightness_contrast(image):  # Function to randomly change brightness and contrast.
        """Creates a new version of an image with slightly different brightness and contrast."""
        brightness = random.randint(-30, 30)  # Choose a random integer for brightness adjustment.
        contrast = random.uniform(0.8, 1.2)  # Choose a random float for contrast adjustment.
        augmented = np.clip(image * contrast + brightness, 0, 255).astype(np.uint8)  # Apply changes and clip values to the valid 0-255 range.
        return augmented  # Return the modified image.

    def augment_flip(image):  # Function to horizontally flip an image.
        """Creates a mirror image of the face."""
        return cv2.flip(image, 1)  # Use OpenCV's flip function with code 1 for horizontal flip.

    def augment_rotation(image):  # Function to slightly rotate an image.
        """Creates a slightly rotated version of the face."""
        angle = random.uniform(-15, 15)  # Choose a random rotation angle between -15 and 15 degrees.
        h, w = image.shape[:2]  # Get the height and width of the image.
        center = (w // 2, h // 2)  # Calculate the center of the image.
        M = cv2.getRotationMatrix2D(center, angle, 1.0)  # Get the 2D rotation matrix.
        return cv2.warpAffine(image, M, (w, h))  # Apply the rotation to the image.

    # --- Dynamic Data Augmentation ---
    # We can create more "fake" images for people with fewer photos to balance the dataset.
    # This helps the model learn better from under-represented individuals.
    BASE_AUGMENTATIONS = 2  # Number of augmented images to create for people with enough photos.
    EXTRA_AUGMENTATIONS = 8  # Number of augmented images for people with few photos.
    FEW_IMAGES_THRESHOLD = 10  # The threshold to decide if a person has "few" photos.

    # --- Data Processing Loop ---
    known_embeddings = []  # Create an empty list to store all face embeddings (features).
    known_names = []  # Create an empty list to store the corresponding names for each embedding.
    
    print("Preparing data and extracting embeddings...")  # Print a status message.
    # Loop through each item in the main 'data/train' directory.
    for person_name in os.listdir(data_dir):  # 'person_name' will be the name of the subfolder.
        person_dir = os.path.join(data_dir, person_name)  # Construct the full path to the person's folder.
        if not os.path.isdir(person_dir):  # Check if it's actually a directory.
            continue  # If not, skip to the next item.

        print(f"Processing images for {person_name}...")  # Print the name of the person being processed.

        image_files = [f for f in os.listdir(person_dir) if os.path.isfile(os.path.join(person_dir, f))]  # Get a list of all files in the person's folder.

        # Decide how many augmentations to perform for this person based on the number of images they have.
        if len(image_files) < FEW_IMAGES_THRESHOLD:  # If the number of images is below the threshold...
            num_augmentations_for_person = EXTRA_AUGMENTATIONS  # ...use the higher number of augmentations.
            print(f"  -> Low image count ({len(image_files)}). Applying {EXTRA_AUGMENTATIONS} augmentations per image.")  # Inform the user.
        else:  # Otherwise...
            num_augmentations_for_person = BASE_AUGMENTATIONS  # ...use the base number.

        for image_name in image_files:  # Loop through each image file for the current person.
            image_path = os.path.join(person_dir, image_name)  # Construct the full path to the image.
            try:  # Use a try-except block to handle corrupted or unreadable files gracefully.
                image = cv2.imread(image_path)  # Read the image from the file.
                if image is None:  # If the image could not be read...
                    print(f"Skipping file {image_path}, could not read.")  # ...print a warning...
                    continue  # ...and skip to the next image.

                # --- Pre-processing: Resize image for more consistent detection ---
                target_width = 640  # Define a standard width.
                h, w, _ = image.shape  # Get the original image dimensions.
                scale = target_width / w  # Calculate the scaling factor.
                resized_image = cv2.resize(image, (target_width, int(h * scale)))  # Resize the image while maintaining aspect ratio.
                
                # Set the input size for the face detector.
                h_resized, w_resized, _ = resized_image.shape  # Get the new dimensions of the resized image.
                face_detector.setInputSize((w_resized, h_resized))  # Tell the detector the size of the image it will receive.

                # Detect faces in the resized image.
                _, faces = face_detector.detect(resized_image)  # Run detection.
                
                if faces is not None and len(faces) > 0:  # Check if at least one face was found.
                    # Find the face with the highest detection score in the image (most likely to be a real face).
                    best_face = max(faces, key=lambda face: face[-1])  # The score is the last element of each face array.
                    if best_face[-1] >= DETECTION_CONF_THRESHOLD:  # Check if the best face's score is above our threshold.
                        # Align the face (rotate and crop it to be upright and centered).
                        original_aligned_face = face_recognizer.alignCrop(resized_image, best_face)  # This is a crucial step for accurate recognition.
                        
                        # --- Process the original, non-augmented face first ---
                        feature = face_recognizer.feature(original_aligned_face)  # Extract the 128-d feature vector (embedding).
                        known_embeddings.append(feature)  # Add the embedding to our list.
                        known_names.append(person_name)  # Add the corresponding name to the other list.

                        # --- Create and process the "fake" augmented versions ---
                        for _ in range(num_augmentations_for_person):  # Loop to create multiple augmented versions.
                            augmented_image = original_aligned_face.copy()  # Start with a copy of the original aligned face.
                            # Randomly decide whether to apply each type of augmentation.
                            if random.choice([True, False]):  # 50% chance.
                                augmented_image = augment_brightness_contrast(augmented_image)  # Apply brightness/contrast change.
                            if random.choice([True, False]):  # 50% chance.
                                augmented_image = augment_flip(augmented_image)  # Apply horizontal flip.
                            if random.choice([True, False]):  # 50% chance.
                                augmented_image = augment_rotation(augmented_image)  # Apply rotation.
                            
                            # Get the feature embedding from our newly created augmented image.
                            aug_feature = face_recognizer.feature(augmented_image)  # Extract the feature.
                            known_embeddings.append(aug_feature)  # Add the new embedding to our list.
                            known_names.append(person_name)  # Add the corresponding name.
                    else:  # If the best face's confidence was too low...
                        print(f"  - Skipping {image_name}: face detection confidence too low ({best_face[-1]:.2f})")  # ...print a warning.
                else:  # If no faces were detected in the image...
                    print(f"  - Skipping {image_name}: no face detected.")  # ...print a warning.

            except Exception as e:  # If any other error occurred while processing the file...
                print(f"Skipping file {image_path}, could not open or read: {e}")  # ...print the error...
                continue  # ...and continue to the next file.

    # --- Finalization and Saving ---
    if not known_embeddings:  # After all loops, check if any embeddings were extracted.
        print("No faces processed. Please check the training data and image quality.")  # If not, print an error.
        return  # Exit the function.

    print(f"\nExtracted {len(known_embeddings)} total embeddings from the training data.")  # Print a summary.

    # Save the embeddings and names to a binary pickle file for fast loading.
    data = {"embeddings": known_embeddings, "names": known_names}  # Create a dictionary to hold our two lists.
    with open(embeddings_path, 'wb') as f:  # Open the output file in write-binary mode ('wb').
        pickle.dump(data, f)  # Use pickle to serialize and save the dictionary to the file.

    # Save a unique, sorted list of names to a human-readable YAML file (optional but good practice).
    unique_names = {i: name for i, name in enumerate(sorted(list(set(known_names))))}  # Create a dictionary mapping an index to each unique name.
    with open(labels_path, 'w') as f:  # Open the YAML file in write mode.
        yaml.dump(unique_names, f, default_flow_style=False)  # Save the dictionary in a clean, block style.
        
    print(f"Embeddings saved to '{embeddings_path}'")  # Print a final confirmation message.
    print(f"Label map saved to '{labels_path}'")  # Print a final confirmation message.

if __name__ == '__main__':  # This block runs only when this script is executed directly.
    train_model()  # Call the main function to start the training process.
