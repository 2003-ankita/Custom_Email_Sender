from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO
from google.oauth2 import service_account
from googleapiclient.discovery import build
import groq
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import os
import re
import pandas as pd

app = Flask(__name__)
socketio = SocketIO(app)

# Load configuration (keeping your existing config)
app.config.update(
    SMTP_SERVER="smtp.gmail.com",
    SMTP_PORT=587,
    SMTP_USERNAME="atyadav403@gmail.com",
    SMTP_PASSWORD="qofh ebre kzlo nfmf",
    SMTP_SENDER_NAME="Ankita Yadav",
    GROQ_API_KEY="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",
    SERVICE_ACCOUNT_FILE='E:/Self_Learning/Custom Email Sender/email_app/credentials.json',
    SPREADSHEET_ID='1xbClJFH07cJT_q8W6ldvVNs4b-t1nOb6AW-E5NVjBIU',
    SHEETS_SCOPE=['https://www.googleapis.com/auth/spreadsheets.readonly']
)

# Global variables for analytics
email_analytics = {
    'total_sent': 0,
    'pending': 0,
    'scheduled': 0,
    'failed': 0
}
email_status = []

class GoogleSheetsService:
    def __init__(self):
        self.creds = None
        self.service = None
        self.setup_credentials()

    def setup_credentials(self):
        self.creds = service_account.Credentials.from_service_account_file(
            app.config['SERVICE_ACCOUNT_FILE'],
            scopes=app.config['SHEETS_SCOPE']
        )
        self.service = build('sheets', 'v4', credentials=self.creds)

    def get_sheet_data(self, sheet_range):
        sheet = self.service.spreadsheets()
        result = sheet.values().get(
            spreadsheetId=app.config['SPREADSHEET_ID'],
            range=sheet_range
        ).execute()
        
        values = result.get('values', [])
        if not values:
            return []
        
        # Clean up column headers (remove spaces and special characters)
        headers = [re.sub(r'[^a-zA-Z0-9]', '', header) for header in values[0]]
        
        # Create a list of dictionaries with cleaned data
        data = []
        for row in values[1:]:
            # Pad row with empty strings if it's shorter than headers
            padded_row = row + [''] * (len(headers) - len(row))
            row_dict = dict(zip(headers, padded_row))
            data.append(row_dict)
            
        return data

class EmailService:
    def __init__(self):
        self.smtp_config = {
            'server': app.config['SMTP_SERVER'],
            'port': app.config['SMTP_PORT'],
            'username': app.config['SMTP_USERNAME'],
            'password': app.config['SMTP_PASSWORD'],
            'sender_name': app.config['SMTP_SENDER_NAME']
        }
        self.groq_client = groq.Client(api_key=app.config['GROQ_API_KEY'])

    def generate_email_content(self, template, data):
        # Add sender name to data
        data['SenderName'] = self.smtp_config['sender_name']
        
        try:
            # Replace placeholders in template
            content = template
            for key, value in data.items():
                placeholder = f"{{{key}}}"
                content = content.replace(placeholder, str(value))

            # Create enhanced prompt for AI
            system_prompt = """You are an expert email writer who specializes in creating professional, personalized business communications. Enhance this email while preserving all specific information and maintaining professionalism."""

            user_prompt = f"""Please enhance this business email while keeping all specific information intact:

{content}

Make it engaging and professional while preserving all company details and product information."""

            # Generate enhanced content
            chat_completion = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model="mixtral-8x7b-32768",
                temperature=0.7,
                max_tokens=1000
            )

            enhanced_content = chat_completion.choices[0].message.content.strip()
            return enhanced_content

        except Exception as e:
            print(f"Error generating content: {str(e)}")
            return content

    def send_email(self, to_email, subject, content):
        msg = MIMEMultipart()
        msg['From'] = f"{self.smtp_config['sender_name']} <{self.smtp_config['username']}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(content, 'plain'))

        try:
            with smtplib.SMTP(self.smtp_config['server'], self.smtp_config['port']) as server:
                server.starttls()
                server.login(self.smtp_config['username'], self.smtp_config['password'])
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return False

@app.route('/')
def index():
    return render_template('input_form.html')

@app.route('/schedule_emails', methods=['POST'])
def schedule_emails():
    sheet_range = request.form.get('sheet_range', 'Sheet1!A1:D100')  # Updated range to include all columns
    delay_minutes = int(request.form.get('delay_minutes', 0))
    throttle_rate = int(request.form.get('throttle_rate', 10))
    prompt_template = request.form.get('prompt_template', '')
    
    # Get sheet data
    sheets_service = GoogleSheetsService()
    data = sheets_service.get_sheet_data(sheet_range)
    
    if not data:
        return "No data found", 400
    
    # Initialize scheduler and email service
    scheduler = BackgroundScheduler()
    email_service = EmailService()
    
    # Schedule emails
    for index, row in enumerate(data):
        email = row.get('Email')
        if not email:
            continue
        
        # Add to status tracking
        email_status.append({
            'email': email,
            'status': 'Scheduled',
            'delivery': 'Pending',
            'company': row.get('CompanyName', 'Unknown Company')
        })
        email_analytics['scheduled'] += 1
        
        # Calculate send time with throttling
        send_time = datetime.now() + timedelta(
            minutes=delay_minutes,
            seconds=(index // throttle_rate) * 60
        )
        
        # Schedule the email
        scheduler.add_job(
            process_email,
            'date',
            run_date=send_time,
            args=[email_service, email, row, prompt_template]
        )
    
    scheduler.start()
    return redirect(url_for('dashboard'))

def process_email(email_service, recipient, data, prompt):
    global email_analytics
    
    try:
        # Generate personalized content
        content = email_service.generate_email_content(prompt, data)
        
        # Create subject line using company name
        subject = f"Important Information for {data.get('CompanyName', 'Your Company')}"
        
        # Send email
        success = email_service.send_email(recipient, subject, content)
        
        # Update analytics and status
        if success:
            email_analytics['total_sent'] += 1
            status = 'Sent'
            delivery = 'Delivered'
        else:
            email_analytics['failed'] += 1
            status = 'Failed'
            delivery = 'Failed'
        
        # Update status tracking
        for email in email_status:
            if email['email'] == recipient:
                email['status'] = status
                email['delivery'] = delivery
        
        # Notify frontend
        socketio.emit('update_status', {
            'email': recipient,
            'status': status,
            'delivery': delivery,
            'analytics': email_analytics,
            'company': data.get('CompanyName', 'Unknown Company')
        })
        
    except Exception as e:
        print(f"Error processing email: {str(e)}")
        email_analytics['failed'] += 1
        socketio.emit('update_status', {
            'email': recipient,
            'status': 'Failed',
            'delivery': 'Error',
            'analytics': email_analytics,
            'company': data.get('CompanyName', 'Unknown Company')
        })

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html',
                         analytics=email_analytics,
                         email_status=email_status)

@socketio.on('connect')
def handle_connect():
    socketio.emit('initial_data', {
        'email_status': email_status,
        'analytics': email_analytics
    })

if __name__ == '__main__':
    socketio.run(app, debug=True)