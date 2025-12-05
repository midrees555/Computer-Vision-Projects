import pyttsx3  # Import the library for text-to-speech conversion.
import winsound  # Import winsound for playing WAV files natively on Windows (no external dependencies).
import os  # Import os to check if files exist.
import threading  # Import threading to play sounds in the background without freezing the main program.

class AudioNotifier:  # Defines the class responsible for all audio notifications.
    def __init__(self, alert_sound_path=None):  # The constructor method.
        """Initializes the text-to-speech engine, sets a female voice, and loads the alert sound."""
        self.engine = pyttsx3.init()  # Initialize the text-to-speech engine.

        # --- Set a more attractive, female voice ---
        try:  # Use a try-except block in case voice settings are not supported on the OS.
            voices = self.engine.getProperty('voices')  # Get a list of all available voices on the system.
            female_voice = next((voice for voice in voices if voice.gender == 'female'), None)  # Find the first voice in the list that is identified as female.
            if female_voice:  # If a female voice was found...
                self.engine.setProperty('voice', female_voice.id)  # ...set it as the active voice.
                print(f"Audio: Female voice '{female_voice.name}' selected.")  # Log which voice was selected.
            else:  # If no female voice was found...
                print("Audio: No female voice found, using default.")  # ...log that the default voice will be used.
        except Exception as e:  # If any error occurs during this process...
            print(f"Audio: Could not set female voice: {e}")  # ...print the error.

        # --- Determine the alert sound path relative to this script's location ---
        if alert_sound_path is None:  # If no path was provided...
            script_dir = os.path.dirname(os.path.abspath(__file__))  # Get the directory where this audio_alerts.py file is located.
            alert_sound_path = os.path.join(script_dir, 'assets', 'siren-alert.wav')  # Build the path to the alert sound.

        self.alert_sound_path = None  # Initialize the alert sound path variable to None.
        if os.path.exists(alert_sound_path):  # Check if the specified alert sound file exists.
            self.alert_sound_path = alert_sound_path  # Store the path for later use.
            print(f"Audio: Alert sound loaded from '{alert_sound_path}'")  # Log success.
        else:  # If the file does not exist...
            print(f"Warning: Alert sound file not found at '{alert_sound_path}'")  # ...print a warning.

    def _play_wav_in_background(self, wav_path):  # A helper method for playing WAV sound.
        """Plays a WAV file using winsound in a separate thread to avoid blocking the main program."""
        def play_sound():
            winsound.PlaySound(wav_path, winsound.SND_FILENAME)  # Play the WAV file.
        threading.Thread(target=play_sound, daemon=True).start()  # Create and start a new thread to play the sound.

    def welcome(self, name):  # Method to welcome a known person.
        """Speaks a welcome message for a known person in a non-blocking background thread."""
        # --- Prettify the name for speech ---
        spoken_name = name.replace('_', ' ')  # Replace underscores with spaces for a natural sound.
        message = f"Welcome, {spoken_name}"  # Create the welcome message string with the cleaned name.
        print(f"AUDIO: Playing welcome message for {name} (as '{spoken_name}')")  # Log the action to the console.
        
        # --- Run TTS in a separate thread to avoid blocking the main recognition loop ---
        def speak():
            self.engine.say(message)
            self.engine.runAndWait()
        threading.Thread(target=speak, daemon=True).start()

    def unknown_alert(self):  # Method to alert for an unknown person.
        """Plays the alert sound, or uses text-to-speech as a fallback."""
        if self.alert_sound_path:  # If a custom alert sound was successfully loaded...
            print("AUDIO: Playing unknown person alert sound.")  # ...log the action.
            self._play_wav_in_background(self.alert_sound_path)  # ...play it in the background.
        else:  # If no custom sound is available...
            # ...fallback to using text-to-speech.
            print("AUDIO: Playing fallback text-to-speech alert.")  # Log the fallback action.
            self.engine.say("Alert. Unknown person detected.")  # Queue the verbal alert message.
            self.engine.runAndWait()  # Block until the alert has been spoken.