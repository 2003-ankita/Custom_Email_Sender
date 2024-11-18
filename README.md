# Custom Email Sender 
A Flask-based application that allows users to send personalized emails using data from Google Sheets, with real-time tracking and analytics.

# Features:
- Google Sheets integration for email data source
- Gmail SMTP integration for sending emails
- Groq API integration for email content customization
- Email scheduling and throttling capabilities
- Real-time analytics dashboard
- Live email status tracking

# Set-up
## 1. Create and activate a virtual environment
   ```bash
   python -m venv env
   .\env\Scripts\activate
   ```
## 2. Install Dependencies
  ```bash
  pip install -r requirements.txt
  ```
## 3. API Keys and Credentials Setup
### Gmail Configuration
1) Enable 2-Step Verification in your Gmail account
2) Generate an App Password:
    - Go to Google Account Settings > Security
    - Under "Signing in to Google," select App Passwords
    - Generate a new app password for "Mail"
    - Copy the 16-character password

### Google Sheets API Setup
1) Create a new project in **[Google Cloud Console](https://cloud.google.com)**
2) Enable Google Sheets API
3) Create Service Account:
   - Go to APIs & Services > Credentials
   - Click "Create Credentials" > Service Account
   - Download the JSON credentials file
   - Rename it to credentials.json and place it in the project root
4) Share your Google Sheet with the service account email

## Groq API Setup
1) Sign up for a Groq account at **[Groq API Key](https://console.groq.com/keys)**. 
2) Generate and copy an API key

## Configuration
Update config.py with your credentials:
 ```bash
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "your-email@gmail.com"
SMTP_PASSWORD = "your-app-password"
SMTP_SENDER_NAME = "Your Name"
GROQ_API_KEY = "your-groq-api-key"
SERVICE_ACCOUNT_FILE = 'path/to/credentials.json'
SPREADSHEET_ID = 'your-spreadsheet-id'
 ```
## Running the Application
 ```bash
python app.py
 ```
