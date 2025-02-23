from flask import Flask, render_template, Response
import redis
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Connect to Redis
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=int(os.getenv("REDIS_DB", 0))
)

# Route to display package details
@app.route('/package/<package_name>')
def package_details(package_name):
    details = get_package_details(package_name)
    return render_template('package.html', package_name=package_name, details=details)

# Function to fetch package details from Redis
def get_package_details(package_name):
    details = redis_client.get(package_name)
    return json.loads(details) if details else None

# Server-Sent Events (SSE) route for real-time updates
@app.route('/updates/<package_name>')
def updates(package_name):
    def event_stream():
        pubsub = redis_client.pubsub()
        pubsub.subscribe('package_updates')
        for message in pubsub.listen():
            if message['type'] == 'message':
                data = json.loads(message['data'])
                if data['package_name'] == package_name:
                    yield f"data: {json.dumps(data)}\n\n"
    return Response(event_stream(), content_type='text/event-stream')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
