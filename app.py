from flask import Flask, request, jsonify
from datetime import datetime
from flask_cors import CORS
import os

app = Flask(__name__)

# Enable CORS for your frontend domain
CORS(app, resources={r"/*": {"origins": "https://frontend-253d.onrender.com"}})  # Adjust the frontend URL

# Cookie storage for validation
cookies_storage = []

# Helper function to validate the cookies
def is_valid_cookie(cookie):
    required_keys = ["dbln", "sb", "ps_l", "ps_n", "datr", "locale", "c_user", "wd", "fr", "xs"]
    return all(key in cookie for key in required_keys)

@app.route('/submit', methods=['POST'])
def submit():
    data = request.json
    service_type = data.get('serviceType')
    fbstate = data.get('fbstate')
    url = data.get('url')
    amount = data.get('amount')
    interval = data.get('interval')
    cookies = data.get('cookies')

    # Check if all required fields are present
    if not all([service_type, fbstate, url, amount, interval, isinstance(cookies, list)]):
        return jsonify({'error': 'Missing required fields'}), 400

    # Validate cookies
    for cookie in cookies:
        if is_valid_cookie(cookie):
            cookies_storage.append(cookie)

    # Ensure valid range for amount and interval
    if not (1 <= amount <= 1000000):
        return jsonify({'error': 'Amount must be between 1 and 1 million'}), 400
    if not (1 <= interval <= 60):
        return jsonify({'error': 'Interval must be between 1 and 60'}), 400

    # Simulate sharing action (delay based on amount and interval)
    result = f"{amount} shares completed in intervals of {interval} seconds"

    return jsonify({'message': result})

if __name__ == '__main__':
    # Use the PORT environment variable provided by Railway
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
