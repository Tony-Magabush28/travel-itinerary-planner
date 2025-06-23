from flask import Flask, render_template, request, make_response
from datetime import datetime, timedelta
import os
import json
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from xhtml2pdf import pisa
from io import BytesIO

app = Flask(__name__)

# Load credentials from .env
load_dotenv()
SCOPES = ['https://www.googleapis.com/auth/calendar']
creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")

# Convert the JSON string to a dictionary
creds_dict = json.loads(creds_json)
creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=SCOPES)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        destination = request.form['destination']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        activities_raw = request.form['activities']
        activities = [a.strip() for a in activities_raw.split(',') if a.strip()]

        itinerary = generate_itinerary(destination, start_date, end_date, activities)
        add_to_google_calendar(itinerary)

        return render_template('itinerary.html', itinerary=itinerary)

    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    itinerary = request.json.get('itinerary')
    html = render_template('pdf_template.html', itinerary=itinerary)

    pdf = BytesIO()
    pisa.CreatePDF(html, dest=pdf)

    response = make_response(pdf.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=itinerary.pdf'
    return response

def generate_itinerary(destination, start_date, end_date, activities):
    itinerary = []
    current_date = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    activity_index = 0
    while current_date <= end:
        if activity_index < len(activities):
            itinerary.append({
                'date': current_date.strftime("%Y-%m-%d"),
                'activity': activities[activity_index],
                'destination': destination
            })
            activity_index += 1
        current_date += timedelta(days=1)
    return itinerary

def add_to_google_calendar(itinerary):
    service = build('calendar', 'v3', credentials=creds)
    calendar_id = "87fc7b3233cbf7bcc0b93dba01067e41de1cf29a5e6a6236d1373c31082be394@group.calendar.google.com"

    for item in itinerary:
        event = {
            'summary': f"{item['activity']} in {item['destination']}",
            'start': {'date': item['date'], 'timeZone': 'UTC'},
            'end': {'date': item['date'], 'timeZone': 'UTC'},
        }
        service.events().insert(calendarId=calendar_id, body=event).execute()

if __name__ == '__main__':
    app.run(debug=True)
