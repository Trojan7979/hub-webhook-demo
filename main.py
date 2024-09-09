from flask import Flask, jsonify, request
import json
from datetime import datetime, timezone
import traceback

# Create a Flask instance
app = Flask(__name__)

# Helper function to add day suffix (st, nd, rd, th).................
def format_day_with_suffix(day):
    """Returns the day of the month with the appropriate suffix (st, nd, rd, th)"""
    if 4 <= day <= 20 or 24 <= day <= 30:
        suffix = "th"
    else:
        suffix = ["st", "nd", "rd"][day % 10 - 1]
    return f"{day}{suffix}"

# Function to format the timestamp...............
def format_timestamp(timestamp):
    """Formats the datetime object to the desired string format"""""
    day = format_day_with_suffix(timestamp.day)
    #formatted_time = timestamp.strftime(f"{day} %B %Y - %I:%M %p UTC")
    return timestamp.strftime(f"{day} %B %Y - %I:%M %p UTC")

# Define a route
@app.route('/', methods=['GET'])
def hello_world():
    return jsonify(message="Hello, World!")

@app.route('/webhook', methods=['POST'])
def submit_data():
    try:  
        event_type = request.headers.get('X-GitHub-Event')

        data = request.get_json()  #Get the JSON data from the request body

        # Get the current UTC timestamp (timezone-aware)
        timestamp = datetime.now(timezone.utc)
        formatted_timestamp = format_timestamp(timestamp)

        # Handling different GitHub event types
        if event_type == "push":
            author = data['pusher']['name']
            to_branch = data['ref'].split('/')[-1]
            event_message = f'{author} pushed to {to_branch} on {formatted_timestamp}'
            print(event_message)  #Print for debugging

        elif event_type == "pull_request":
            author = data['pull_request']['user']['login']
            from_branch = data['pull_request']['head']['ref']
            to_branch = data['pull_request']['base']['ref']
            event = {
                "author": author,
                "event": "pull_request",
                "from_branch": from_branch,
                "to_branch": to_branch,
                "timestamp": formatted_timestamp
            }
            print(event)

    except Exception as e:
        traceback.print_exc()
        print(e)
    # print(json.dumps(data))
    # Extract the names from different sections
    # repository_name = data['repository']['name']
    # pusher_name = data['pusher']['id']['name']
    # commits = data['commits']
    # for commit in commits:
    #     print (commit['timestamp'])
    
    # user_mail = data['head_commit']['committer']['email']
    

    # print("Repository Name:", repository_name)
    # print("Pusher Name:", pusher_name)


    # Create a response with the received data
    return "success", 200

# Run the app
if __name__ == '__main__':
    app.run(debug=True)