import os
import pandas as pd
import logging
import re
import joblib
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import argparse
import configparser

# Download necessary NLTK resources
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Lemmatizer and stopwords
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

def load_data(file_path):
    """Load and validate the dataset."""
    try:
        data = pd.read_csv(file_path)
        if 'text' not in data.columns or 'label' not in data.columns:
            logging.error("Dataset must contain 'text' and 'label' columns.")
            return None
        logging.info("Dataset loaded successfully.")
        return data
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}. Please provide a valid file path.")
    except Exception as e:
        logging.error(f"An error occurred while loading the dataset: {e}")
    return None

def clean_text(text):
    """Preprocess the text by removing noise, lemmatizing, and filtering stopwords."""
    text = text.lower()
    text = re.sub(r'\d+', '', text)  # Remove numbers
    text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
    text = re.sub(r'\W', ' ', text)  # Remove special characters
    text = ' '.join([lemmatizer.lemmatize(word) for word in text.split() if word not in stop_words])
    return text

def train_model(emails):
    """Train a logistic regression model with TF-IDF vectorization."""
    emails['text'] = emails['text'].apply(clean_text)
    X = emails['text']
    y = emails['label']

    vectorizer = TfidfVectorizer(max_features=5000)
    X_vec = vectorizer.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(X_vec, y, test_size=0.2, random_state=42)

    model = LogisticRegression(max_iter=1000)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    logging.info(f"Training completed. Model Accuracy: {accuracy_score(y_test, y_pred):.2f}")
    logging.info("\n" + classification_report(y_test, y_pred))

    joblib.dump(model, 'phishing_model.pkl')
    joblib.dump(vectorizer, 'vectorizer.pkl')

    return model, vectorizer

def load_model():
    """Load the trained model and vectorizer."""
    try:
        model = joblib.load('phishing_model.pkl')
        vectorizer = joblib.load('vectorizer.pkl')
        logging.info("Model and vectorizer loaded successfully.")
        return model, vectorizer
    except FileNotFoundError:
        logging.warning("Model or vectorizer file not found. A new model will be trained.")
    except Exception as e:
        logging.error(f"An error occurred during model loading: {e}")
    return None, None

def predict_email(model, vectorizer, email_text):
    """Predict whether an email is phishing or normal."""
    email_text_clean = clean_text(email_text)
    email_vec = vectorizer.transform([email_text_clean])
    prediction = model.predict(email_vec)
    return "Phishing" if prediction[0] == 1 else "Normal"

def generate_report(predictions, file_path, output_format="txt"):
    """Generate a prediction report in the specified format."""
    try:
        if output_format == "txt":
            with open(file_path, 'w') as file:
                for i, pred in enumerate(predictions):
                    file.write(f"Email {i+1}: {pred}\n")
        elif output_format == "csv":
            pd.DataFrame({"Email": range(1, len(predictions) + 1), "Prediction": predictions}).to_csv(file_path, index=False)
        logging.info(f"Report saved at {file_path}")
    except Exception as e:
        logging.error(f"Failed to save report: {e}")

def get_config(config_file):
    """Retrieve configuration from the file."""
    config = configparser.ConfigParser()
    try:
        config.read(config_file)
        file_path = config.get('DEFAULT', 'FilePath', fallback='emails.csv')
        logging.info(f"Dataset path loaded from configuration: {file_path}")
        return file_path
    except Exception as e:
        logging.error(f"Error reading configuration file: {e}")
    return 'emails.csv'

def check_emails(model, vectorizer):
    """Check user-provided emails for phishing."""
    try:
        num_emails = int(input("How many emails would you like to check? "))
        if num_emails <= 0:
            raise ValueError("Number of emails must be a positive integer.")
    except ValueError as e:
        logging.error(f"Invalid input: {e}")
        return

    predictions = []
    for i in range(num_emails):
        email_text = input(f"Enter the content of email {i + 1}: ")
        result = predict_email(model, vectorizer, email_text)
        predictions.append(result)
        logging.info(f"Email {i+1}: {result}")

    report_path = input("Enter the path to save the prediction report (e.g., report.txt): ")
    output_format = input("Enter the report format (txt or csv): ").strip().lower()
    generate_report(predictions, report_path, output_format)

def main():
    """Main function to drive the program."""
    parser = argparse.ArgumentParser(description="Phishing Email Detection Program")
    parser.add_argument('--config', type=str, help='Path to configuration file', default='config.ini')
    args = parser.parse_args()

    # Load configuration
    file_path = get_config(args.config)

    logging.info("Starting Phishing Email Detection Program...")

    emails = load_data(file_path)
    if emails is None:
        return

    model, vectorizer = load_model()
    if model is None or vectorizer is None:
        model, vectorizer = train_model(emails)

    while True:
        user_choice = input("\nChoose an option:\n1. Check emails for phishing\n2. Exit\nYour choice: ")
        if user_choice == '2':
            logging.info("Exiting the program. Goodbye!")
            break
        elif user_choice == '1':
            check_emails(model, vectorizer)
        else:
            logging.warning("Invalid choice. Please select option 1 or 2.")

if __name__ == "__main__":
    main()
