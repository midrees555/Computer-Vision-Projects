import smtplib  # Import the library for sending emails using SMTP.
from email.mime.multipart import MIMEMultipart  # Import for creating a multi-part message (text and image).
from email.mime.text import MIMEText  # Import for creating the text part of the email.
from email.mime.image import MIMEImage  # Import for creating the image attachment part of the email.
import os  # Import os to get the filename from a path.

# --- Email Configuration ---
# IMPORTANT: Use a Gmail "App Password" here, not your regular password.
# See: https://support.google.com/accounts/answer/185833
SENDER_EMAIL = "earnmoney4v@gmail.com"  # The email address that will send the alerts.
SENDER_PASSWORD = "xjke fjms mnbs ytby"  # The 16-digit App Password generated from your Google account.
RECIPIENT_EMAILS = ["midrees4040@gmail.com", "alamgirkhani0987@gmail.com", "mrshahisagher@gmail.com", "kashiiking112@gmail.com", "kmusaddiq836@gmail.com"]  # A list of email addresses that will receive the alerts.

def send_alert_email(image_path):  # The main function to send an alert email.
    """Sends an email with an attached image of the detected unknown person."""
    # --- Configuration Validation ---
    if not SENDER_EMAIL or "your_email" in SENDER_EMAIL:  # A simple check to see if the configuration has been updated.
        print("Notification Error: Please configure sender and recipient emails in 'notifications.py'")  # Print an error if not configured.
        return  # Exit the function.

    try:  # Use a try-except block to handle potential network errors or file reading errors.
        # --- Read the Image Data ---
        with open(image_path, 'rb') as f:  # Open the snapshot image file in binary read mode ('rb').
            img_data = f.read()  # Read the entire content of the image file.

        # --- Construct the Email Message ---
        msg = MIMEMultipart()  # Create a multi-part message object.
        msg['Subject'] = "Security Alert: Unknown Person Detected"  # Set the email subject.
        msg['From'] = SENDER_EMAIL  # Set the sender's email address.
        msg['To'] = ", ".join(RECIPIENT_EMAILS)  # Set the recipient email addresses, joined by commas.

        text = MIMEText("An unknown person was detected in your room. See attached image.")  # Create the plain text body of the email.
        msg.attach(text)  # Attach the text body to the message.

        image = MIMEImage(img_data, name=os.path.basename(image_path))  # Create an image attachment from the image data.
        msg.attach(image)  # Attach the image to the message.

        # --- Send the Email via Gmail's SMTP Server ---
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:  # Connect to Gmail's secure SMTP server on port 465.
            smtp_server.login(SENDER_EMAIL, SENDER_PASSWORD)  # Log in to the server using your credentials.
            smtp_server.sendmail(SENDER_EMAIL, RECIPIENT_EMAILS, msg.as_string())  # Send the complete message.
        print(f"Alert email sent successfully to {', '.join(RECIPIENT_EMAILS)}")  # Print a success confirmation.
    except Exception as e:  # If any error occurred during the process...
        print(f"Failed to send email: {e}")  # ...print the error message.