import tkinter as tk  # Import the standard GUI library for Python.
from tkinter import simpledialog, messagebox, PhotoImage, filedialog  # Import specific dialogs, message boxes, image handling, and file dialogs from tkinter.
import subprocess  # Import subprocess to run other Python scripts from this one.
import threading  # Import threading to run processes in the background without freezing the GUI.
import os  # Import os for operating system interactions, like creating directories.
import shutil  # Import shutil for high-level file operations like copying.
import time  # Import time for creating unique filenames.

class FaceRecApp:  # Defines the main class for our GUI application.
    def __init__(self, root):  # The constructor method, called when a new FaceRecApp object is created.
        self.root = root  # Store the main Tkinter window object.
        self.root.title("Face Recognition Security System")  # Set the title of the window.
        self.root.geometry("500x380")  # Set the initial size of the window.
        self.root.configure(bg="#212121")  # Set the background color of the main window to a dark grey.

        # --- Icon (Optional) ---
        # You can uncomment the line below and provide a path to a .png file to set a custom window icon.
        # self.root.iconphoto(False, PhotoImage(file='assets/icon.png')) 

        self.recognition_process = None  # A variable to hold the running recognition script process.
        
        # --- Professional Style Configuration for a Modern Dark Theme ---
        self.dark_bg = "#212121"  # Define the dark background color.
        self.medium_bg = "#333333"  # A slightly lighter grey for button backgrounds.
        self.light_fg = "#FFFFFF"  # Define the light foreground (text) color.
        self.accent_color = "#00BFFF"  # Define an accent color (Deep Sky Blue) for highlights.
        self.hover_color = "#454545"  # Color for when the mouse hovers over a button.
        self.success_green = "#2E7D32"  # Green for the start button.
        self.stop_white = "#FFFFFF"  # White for the stop button.
        self.error_red = "#C62828"  # Red for the stop button and exit button.
        self.title_font = ("Segoe UI", 18, "bold")  # Define the font for the main title.
        self.button_font = ("Segoe UI", 11, "bold")  # Define the font for the buttons.
        self.status_font = ("Segoe UI", 9)  # Font for the status bar.

        # --- Main Frame to hold all widgets ---
        main_frame = tk.Frame(root, padx=20, pady=20, bg=self.dark_bg)  # Create a frame with padding and dark background.
        main_frame.pack(expand=True, fill=tk.BOTH)  # Make the frame fill the entire window.

        # --- Title Label ---
        title_label = tk.Label(main_frame, text="Security System Control", font=self.title_font, bg=self.dark_bg, fg=self.accent_color)  # Create the title text.
        title_label.pack(pady=(0, 25))  # Add it to the frame with vertical padding at the bottom.

        # --- Camera Source Flag (Checkbox) ---
        self.use_mobile_var = tk.BooleanVar()  # A special tkinter variable to hold the checkbox state (True/False).
        self.camera_frame = tk.Frame(main_frame, bg=self.dark_bg)  # Create a frame for the camera input widgets.
        self.camera_frame.pack(pady=10, fill=tk.X, anchor='w')  # Add the frame, aligned to the west (left).

        # Create the checkbox that acts as our "flag".
        mobile_camera_check = tk.Checkbutton(self.camera_frame, text="Use Mobile Camera", variable=self.use_mobile_var,
                                             command=self.toggle_mobile_url_entry, bg=self.dark_bg, fg=self.light_fg, relief=tk.FLAT, borderwidth=1,
                                             selectcolor=self.medium_bg, activebackground=self.dark_bg, activeforeground=self.light_fg,
                                             font=("Segoe UI", 10))
        mobile_camera_check.pack(side=tk.LEFT)  # Place the checkbox on the left of its frame.

        # Create an entry box for the mobile URL, which will be hidden by default.
        self.mobile_url_entry = tk.Entry(self.camera_frame, font=("Segoe UI", 10), width=30, bg=self.medium_bg, fg=self.light_fg, relief=tk.SOLID, borderwidth=1, insertbackground=self.light_fg)
        self.mobile_url_entry.insert(0, "http://192.168.1.14:8080/video")  # Pre-fill with an example URL.

        # --- Frame to hold the main action buttons (Start/Stop) ---
        action_button_frame = tk.Frame(main_frame, bg=self.dark_bg)  # Create a new frame for these buttons.
        action_button_frame.pack(pady=25, fill=tk.X)  # Add it to the main frame.

        # --- Start Button ---
        self.start_button = self.create_styled_button(action_button_frame, "▶ Start System", self.start_recognition, self.success_green)  # Create the styled "Start" button.
        self.start_button.pack(side=tk.LEFT, expand=True, padx=5)  # Place it on the left, allowing it to expand.

        # --- Stop Button ---
        self.stop_button = self.create_styled_button(action_button_frame, "■ Stop System", self.stop_recognition, self.stop_white, text_color=self.dark_bg)  # Create the styled "Stop" button.
        self.stop_button.config(state=tk.DISABLED)  # Initially disabled.
        self.stop_button.pack(side=tk.LEFT, expand=True, padx=5)  # Place it next to the start button.

        # --- Add New Person Button ---
        self.add_person_button = self.create_styled_button(main_frame, "＋ Add Person via Upload", self.add_new_person_by_upload, self.accent_color, text_color=self.dark_bg)  # Create the "Add Person" button.
        self.add_person_button.pack(fill=tk.X, pady=5)  # Add it to the main frame, filling horizontal space.

        # --- Exit Button ---
        exit_button = self.create_styled_button(main_frame, "Exit Application", self.on_closing, self.error_red)  # Create the "Exit" button.
        exit_button.pack(fill=tk.X, pady=(15, 0))  # Add it to the main frame with extra padding on top.

        # --- Status Bar ---
        self.status_label = tk.Label(root, text="System Idle.", font=self.status_font, bg=self.accent_color, fg=self.dark_bg, bd=1, relief=tk.SUNKEN, anchor=tk.W)  # Create a label for the status bar.
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)  # Dock it to the bottom of the window.

        # --- Graceful Exit Handling ---
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)  # Bind the window's 'X' button to our custom on_closing method.

    def create_styled_button(self, parent, text, command, bg_color, text_color=None):  # A helper function to create buttons with a consistent style.
        """Helper function to create a consistently styled button with hover effects."""
        fg_color = text_color if text_color else self.light_fg  # Use provided text color, or default to light_fg.
        button = tk.Button(parent, text=text, command=command, bg=bg_color, fg=fg_color,  # Create the button.
                           font=self.button_font, relief=tk.SOLID, borderwidth=1, padx=10, pady=10,  # Set font, relief, border, and padding.
                           activebackground=bg_color, activeforeground=fg_color)  # Set colors for when the button is clicked.
        
        # Bind mouse hover events to change button color.
        button.bind("<Enter>", lambda e, b=button: b.config(bg=self.hover_color, fg=self.light_fg))  # On hover, change to hover color.
        button.bind("<Leave>", lambda e, b=button, bg=bg_color, fg=fg_color: b.config(bg=bg, fg=fg))  # On leave, revert to original colors.
        return button  # Return the created button object.

    def run_in_thread(self, command):  # A helper method to run a command.
        """Runs a command in a separate process to keep the GUI responsive."""
        self.recognition_process = subprocess.Popen(command)  # Start the command as a new process and store it.
        self.recognition_process.wait()  # Wait here until the subprocess finishes (e.g., user presses 'q').
        # This code runs AFTER the recognition process has stopped.
        self.root.after(0, self.on_recognition_stop)  # Schedule the UI update to run on the main GUI thread.

    def on_recognition_stop(self):  # This method is called after the recognition process has ended.
        """Updates the UI after the recognition process has naturally stopped (e.g., user pressed 'q')."""
        if self.recognition_process:  # This check handles cases where the GUI stop button was used.
            self.recognition_process = None  # Reset the process variable.
        print("GUI: Recognition process finished.")  # Log the event.
        self.update_status("System Idle.", self.accent_color)  # Update the status bar.
        self.start_button.config(state=tk.NORMAL)  # Re-enable the "Start" button.
        self.stop_button.config(state=tk.DISABLED)  # Disable the "Stop" button.
        self.add_person_button.config(state=tk.NORMAL)  # Re-enable the "Add Person" button.

    def toggle_mobile_url_entry(self):  # This method is called when the checkbox is clicked.
        """Shows or hides the mobile URL entry box based on the checkbox state."""
        if self.use_mobile_var.get():  # If the checkbox is checked...
            self.mobile_url_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(10, 0))  # ...show the entry box.
        else:  # If the checkbox is unchecked...
            self.mobile_url_entry.pack_forget()  # ...hide the entry box.

    def update_status(self, text, color):  # A helper method to update the status bar.
        """Updates the text and color of the status bar."""
        self.status_label.config(text=f" {text}", bg=color)  # Set the new text and background color.

    def start_recognition(self):  # This method is called when the "Start System" button is clicked.
        """Starts the live recognition script in a background thread."""
        print("GUI: Starting recognition system...")  # Log the action to the console.
        
        # Determine the camera source based on the checkbox "flag".
        if self.use_mobile_var.get():  # If the mobile camera flag is set...
            camera_source = self.mobile_url_entry.get().strip()  # ...get the URL from the entry box.
            if not camera_source:  # Basic validation to ensure the URL is not empty.
                messagebox.showerror("Error", "Mobile camera URL cannot be empty when the box is checked.")  # Show an error.
                return  # Stop the function.
        else:  # If the flag is not set...
            camera_source = '0'  # ...default to the laptop webcam.
            
        command = ["python", "src/recognize_face.py", "--camera", camera_source]  # Define the command to run the recognition script with the camera argument.
        threading.Thread(target=self.run_in_thread, args=(command,), daemon=True).start()  # Run the command in a new thread so the GUI doesn't freeze.
        
        # --- Update UI to "Running" State ---
        self.update_status("System Running...", self.success_green)  # Update the status bar.
        self.start_button.config(state=tk.DISABLED)  # Disable the "Start" button to prevent multiple clicks.
        self.stop_button.config(state=tk.NORMAL)  # Enable the "Stop" button.
        self.add_person_button.config(state=tk.DISABLED)  # IMPORTANT: Disable adding users while the system is running to prevent conflicts.

    def stop_recognition(self):  # This method is called when the "Stop System" button is clicked.
        """Stops the live recognition script process."""
        if self.recognition_process:  # Check if a process is actually running.
            print("GUI: Stopping recognition system...")  # Log the action to the console.
            self.update_status("Stopping system...", self.error_red)  # Update the status bar.
            self.recognition_process.terminate()  # Send a signal to terminate the running script.
            # The UI update will be handled by on_recognition_stop once the process fully terminates.

    def add_new_person_by_upload(self):  # This method is called when the "Add Person via Upload" button is clicked.
        """Opens dialogs to get a name and upload image files, then retrains the model."""
        person_name = simpledialog.askstring("Add New Person", "Enter the person's name:", parent=self.root)  # Show a dialog asking for the person's name.
        
        # --- Validation Step 1: Check if a name was entered ---
        if person_name and person_name.strip():  # Check if the user entered a name and it's not just spaces.
            person_name = person_name.strip()  # Remove any leading/trailing whitespace.
            
            # --- Validation Step 2: Check for reserved names ---
            if person_name.lower() == "unknown":  # Check for the reserved keyword "unknown".
                messagebox.showerror("Invalid Name", "'Unknown' is a reserved name. Please choose another.")  # Show an error message.
                return  # Stop the function.

            # --- File Selection Dialog ---
            # Open a native OS file dialog to select multiple image files.
            filepaths = filedialog.askopenfilenames(
                title=f"Select pictures of {person_name}",
                filetypes=[("Image Files", "*.jpg *.jpeg *.png"), ("All files", "*.*")]
            )

            # --- Validation Step 3: Check if files were selected ---
            if not filepaths:
                messagebox.showwarning("Cancelled", "No images were selected. Operation cancelled.")  # Show a warning if no files were chosen.
                return  # Stop the function.
            
            # --- File Copying and Retraining ---
            try:  # Use a try-except block to catch any errors from the scripts.
                self.update_status(f"Copying {len(filepaths)} images...", self.accent_color)  # Update status bar.
                person_dir = os.path.join('data/train', person_name)  # Define the target directory for the new images.
                os.makedirs(person_dir, exist_ok=True)  # Create the person's training directory if it doesn't exist.
                for fpath in filepaths:  # Loop through each selected file path.
                    # Copy each selected file into the new directory with a unique name.
                    timestamp = int(time.time() * 1000)  # Create a unique timestamp.
                    _, extension = os.path.splitext(fpath)  # Get the file extension.
                    new_filename = f"{person_name}_{timestamp}{extension}"  # Create a new, unique filename.
                    shutil.copy(fpath, os.path.join(person_dir, new_filename))  # Copy the file.
                
                messagebox.showinfo("Training", f"{len(filepaths)} images copied successfully. Now retraining the model. This may take a moment.")  # Inform the user.
                self.update_status("Retraining model...", self.accent_color)  # Update status bar.
                subprocess.run(["python", "src/train_model.py"], check=True)  # Run the training script and wait for it to finish.
                messagebox.showinfo("Success", f"Model successfully retrained with {person_name}!")  # Announce success.
                self.update_status("System Idle.", self.accent_color)  # Reset status bar.
            except subprocess.CalledProcessError:  # If any of the scripts fail...
                messagebox.showerror("Error", "A script failed to execute. Check the console for details.")  # ...show an error message.
                self.update_status("Error during training.", self.error_red)  # Update status bar with error state.
            except Exception as e:  # Catch other potential errors, like file permission issues.
                messagebox.showerror("Error", f"An error occurred while copying files: {e}")  # Show the error.
                self.update_status("File copy error.", self.error_red)  # Update status bar.
        else:  # If the user cancelled the name dialog...
            messagebox.showwarning("Cancelled", "No name entered. Operation cancelled.")  # ...show a warning.

    def on_closing(self):  # This method is called when the user tries to close the window.
        """Handles the window close event to ensure graceful shutdown."""
        print("GUI: Close requested.")
        if self.recognition_process:  # If the recognition system is running...
            self.stop_recognition()  # ...stop it first.
        self.root.destroy()  # Then, safely close the GUI window.

if __name__ == "__main__":  # This block runs only when this script is executed directly.
    root = tk.Tk()  # Create the main application window.
    app = FaceRecApp(root)  # Create an instance of our FaceRecApp class.
    root.mainloop()  # Start the Tkinter event loop, which listens for user actions (like button clicks).
