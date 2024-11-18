import os

class Config:
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    SMTP_USERNAME = "your-email@gmail.com"
    SMTP_PASSWORD = "your-app-password"
    SMTP_SENDER_NAME = "Your Name"
    GROQ_API_KEY = "your-groq-api-key"
    SERVICE_ACCOUNT_FILE = 'path/to/credentials.json'
    SPREADSHEET_ID = 'your-spreadsheet-id'
    SHEETS_SCOPE = ['https://www.googleapis.com/auth/spreadsheets.readonly']