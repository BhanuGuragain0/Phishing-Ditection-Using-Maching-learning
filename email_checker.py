import pandas as pd
import logging
import re
import joblib
import nltk
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import argparse
import configparser

nltk.download('stopwords')
nltk.download('wordnet')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Lemmatizer and stopwords
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

def load_data(file_path):
    """Load data from a CSV file."""
    try:
        data = pd.read_csv(file_path)
        return data
    except FileNotFoundError:
        logging.error(f"File not found at {file_path}. Please provide a valid file path.")
    except Exception as e:
        logging.error(f"An error occurred during data loading: {e}")
    return None

def clean_text(text):
    """Clean the text data."""
    text = text.lower()
    text = re.sub(r'\d+', '', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\W', ' ', text)
    text = ' '.join([lemmatizer.lemmatize(word) for word in text.split() if word not in stop_words])
    return text

def train_model(emails):
    """Train and return a logistic regression model and vectorizer."""
    emails['text'] = emails['text'].apply(clean_text)
    X = emails['text']
    y = emails['label']

    vectorizer = CountVectorizer()
    X_vec = vectorizer.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(X_vec, y, test_size=0.2, random_state=42)

    model = LogisticRegression(max_iter=1000)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    logging.info(f"Model Accuracy: {accuracy:.2f}")

    joblib.dump(model, 'phishing_model.pkl')
    joblib.dump(vectorizer, 'vectorizer.pkl')

    return model, vectorizer

def load_model():
    """Load the trained model and vectorizer."""
    try:
        model = joblib.load('phishing_model.pkl')
        vectorizer = joblib.load('vectorizer.pkl')
        return model, vectorizer
    except FileNotFoundError:
        logging.error("Model or vectorizer file not found. Please train the model first.")
    except Exception as e:
        logging.error(f"An error occurred during model loading: {e}")
    return None, None

def predict_email(model, vectorizer, email_text):
    """Predict if the given email text is phishing or not."""
    email_text_clean = clean_text(email_text)
    email_vec = vectorizer.transform([email_text_clean])
    prediction = model.predict(email_vec)
    return prediction[0]

def generate_report(predictions, file_path):
    """Generate a report with the predictions."""
    with open(file_path, 'w') as file:
        for i, pred in enumerate(predictions):
            file.write(f"Email {i+1}: {'Phishing' if pred == 1 else 'Normal'}\n")
    logging.info(f"Report generated at {file_path}")

def get_config(config_file):
    """Get configuration from file."""
    config = configparser.ConfigParser()
    config.read(config_file)
    file_path = config.get('DEFAULT', 'FilePath', fallback='/home/bhanu/Desktop/email_data.csv')
    return file_path

def main():
    # Argument parser for command line interface
    parser = argparse.ArgumentParser(description="Phishing Email Detection Program")
    parser.add_argument('--config', type=str, help='Path to configuration file', default='config.ini')
    args = parser.parse_args()

    # Load configuration
    file_path = get_config(args.config)

    logging.info("Welcome to the Phishing Email Detection Program!")
    logging.info("Ensure you have a phishing email dataset to prepare the machine learning model.")
    logging.info("Program is running, please wait...")

    emails = load_data(file_path)
    if emails is None:
        return

    model, vectorizer = load_model()
    if model is None or vectorizer is None:
        logging.info("Training a new model...")
        model, vectorizer = train_model(emails)

    while True:
        user_choice = input("Choose an option:\n1. Check emails for phishing\n2. Exit\nYour choice: ")
        if user_choice == '2':
            break
        elif user_choice == '1':
            try:
                num_emails = int(input("Enter the number of email texts you want to check for phishing: "))
                if num_emails <= 0:
                    raise ValueError("Number of emails must be a positive integer.")
            except ValueError as ve:
                logging.error(f"Error: {ve}")
                continue

            predictions = []
            for i in range(num_emails):
                user_input = input(f"Enter email text {i + 1}: ")
                prediction = predict_email(model, vectorizer, user_input)
                predictions.append(prediction)
                logging.info("Phishing Email Detected!" if prediction == 1 else "Normal Email")

            report_path = input("Enter the path to save the report: ")
            generate_report(predictions, report_path)
        else:
            logging.error("Invalid choice. Please choose 1 or 2.")

if __name__ == "__main__":
    main()
