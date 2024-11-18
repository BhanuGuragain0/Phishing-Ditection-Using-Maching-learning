import csv
import random
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def generate_email_dataset(num_emails, phishing_texts, non_phishing_texts, file_path):
    """
    Generate a dataset of phishing and non-phishing emails and save it to a CSV file.

    Args:
        num_emails (int): Total number of emails to generate.
        phishing_texts (list): List of phishing email templates.
        non_phishing_texts (list): List of non-phishing email templates.
        file_path (str): File path for the output CSV.
    """
    # Generate phishing emails (label 1)
    phishing_emails = [{'text': text, 'label': 1} for text in phishing_texts]
    
    # Generate non-phishing emails (label 0)
    non_phishing_emails = [{'text': text, 'label': 0} for text in non_phishing_texts]

    # Calculate additional emails needed to balance the dataset
    additional_non_phishing_needed = max(0, num_emails - len(phishing_emails) - len(non_phishing_emails))
    additional_non_phishing_emails = [
        {'text': f"Normal email content {i}", 'label': 0} for i in range(additional_non_phishing_needed)
    ]

    # Combine and shuffle emails
    all_emails = phishing_emails + non_phishing_emails + additional_non_phishing_emails
    random.shuffle(all_emails)

    # Write to CSV
    try:
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open('w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['text', 'label']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_emails)
        logging.info(f"Successfully generated {len(all_emails)} emails and saved to '{file_path}'.")
    except Exception as e:
        logging.error(f"Error writing to file: {e}")

if __name__ == "__main__":
    # Example phishing and non-phishing texts
    phishing_texts = [
        "Your account has been compromised. Click here: https://example.com/secure-account",
        "URGENT: Verify your account to avoid suspension: https://example.com/verify",
        "Action required: Unusual activity detected. Secure your account: https://example.com/security-alert"
    ]
    non_phishing_texts = [
        "Thank you for your recent purchase!",
        "Your order has been confirmed.",
        "Reminder: Appointment tomorrow at 10 AM."
    ]

    # Parameters
    num_emails = 10000  # Total emails to generate
    file_path = '/home/bhanu/Desktop/email_data.csv'  # Output file path

    # Generate dataset
    generate_email_dataset(num_emails, phishing_texts, non_phishing_texts, file_path)
