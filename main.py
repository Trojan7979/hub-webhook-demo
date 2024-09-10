from flask import Flask, jsonify, request, render_template
import json
from datetime import datetime, timezone, timedelta
import traceback
from pymongo import MongoClient
from dotenv import load_dotenv
import os

#Load environment variables
load_dotenv()
MONGO_URI=os.getenv("MONGO_URI")

#Create a Flask instance
app = Flask(__name__)

#MongoDB setup
client = MongoClient(MONGO_URI)
db = client['github_events']
collection = db['events']

#Helper function to add day suffix (st, nd, rd, th)
def format_day_with_suffix(day):
    """Returns the day of the month with the appropriate suffix (st, nd, rd, th)"""
    if 4 <= day <= 20 or 24 <= day <= 30:
        suffix = "th"
    else:
        suffix = ["st", "nd", "rd"][day % 10 - 1]
    return f"{day}{suffix}"

# Function to format the timestamp
def format_timestamp(timestamp):

    #Convert UTC to IST by adding 5 hours and 30 minutes
    IST_offset = timedelta(hours=5, minutes=30)
    ist_time = timestamp + IST_offset

    #to format the IST time:....
    day = format_day_with_suffix(ist_time.day)
    formatted_time = ist_time.strftime(f"{day} %B %Y - %I:%M %p IST")
    return formatted_time

#Define a route
@app.route('/', methods=['GET'])
def hello_world():
    return jsonify(message="Healthy")

@app.route('/webhook', methods=['POST'])
def submit_data():
    try:
        data = request.get_json()  #Get the JSON data from the request body
        event_type = request.headers.get('X-GitHub-Event')

        #Get the current UTC timestamp (timezone-aware)
        timestamp = datetime.now(timezone.utc)
        formatted_timestamp = format_timestamp(timestamp)

        #Initialize event message
        event_message = ""


        """Handling different GitHub event types"""
        if event_type == "push":
            author = data['pusher']['name']
            to_branch = data['ref'].split('/')[-1]

            #To format the output:
            event_message = f'{author} pushed to {to_branch} on {formatted_timestamp}'
            event_data = {
                'request_id': data['head_commit']['id'], #use the Git commit hash directly
                'author': author,
                'action': "PUSH",
                'from_branch': to_branch,
                'to_branch': to_branch,
                'timestamp': formatted_timestamp
            }


        elif event_type == "pull_request":
            author = data['pull_request']['user']['login']
            from_branch = data['pull_request']['head']['ref']
            to_branch = data['pull_request']['base']['ref']

            #Check if the pull request has been merged
            if data['pull_request'].get('merged', False):
                #handle merge action
                event_message = f'{author} merged branch "{from_branch}" to "{to_branch}" on {formatted_timestamp}'
                action = "MERGE" 
            else:
                #handle pull request action
                event_message = f'{author} submitted a pull request from "{from_branch}" to "{to_branch}" on {formatted_timestamp}'
                action = "PULL_REQUEST"

            event_data = {
                'request_id': data['pull_request']['id'],  # Use the PR ID for pull requests
                'author': author,
                'action': action,
                'from_branch': from_branch,
                'to_branch': to_branch,
                'timestamp': formatted_timestamp
            }
            
        else:
            #If the event type is unsupported, return 400 Bad Request
            return jsonify({"error": "Unsupported event type"}), 400
        
        #store the event in MongoDB
        collection.insert_one(event_data)

        #return the latest event message as a response
        return jsonify({"message": event_message}), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "An error occurred", "details": str(e)}), 500
    
@app.route('/events', methods=['GET'])
def get_events():
    try:
        events = list(collection.find().sort('timestamp', -1))

        for event in events:
            event['_id'] = str(event['_id'])  #convert ObjectId to string for JSON serialization
            event['timestamp'] = str(event['timestamp'])  #ensure timestamp is in string format
        return jsonify(events), 200
    
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "An error occurred", "details": str(e)}), 500

@app.route('/UI')
def interface():
    return render_template('index.html')

# Run the app
if __name__ == '__main__':
    app.run(debug=True)