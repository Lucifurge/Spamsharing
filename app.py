from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import threading
import requests
import time

# Initialize Flask app
app = Flask(__name__)

# Enable CORS for the frontend URL
CORS(app, resources={r"/submit": {"origins": "https://frontend-253d.onrender.com"}})

# Store fbstate data in memory
fbstate_storage = []

# Function to send share requests to Facebook
def share_post(fbstate, post_id, amount, interval):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        # Build the cookies from fbstate as a string
        cookies = {}
        cookie_string = ""
        for cookie in fbstate:
            # Assuming the fbstate is now a string, concatenate key-value pairs
            cookie_string += f"{cookie['key']}={cookie['value']}; "

        # Clean up the trailing semicolon and space
        cookie_string = cookie_string.strip("; ")

        for i in range(amount):
            try:
                # Ensure the URL and cookies are correctly handled
                share_url = f"https://www.facebook.com/{post_id}/share"
                print(f"Attempting to share post: {share_url} with cookies: {cookie_string}")
                response = requests.post(
                    share_url,
                    headers=headers,
                    cookies={cookie_string: cookie_string},  # Pass cookies as a string
                )
                if response.status_code == 200:
                    print(f"[{i + 1}] Successfully shared post ID: {post_id}")
                else:
                    print(f"[{i + 1}] Failed to share post ID: {post_id}. Status code: {response.status_code}")
            except Exception as e:
                print(f"[{i + 1}] Error sharing post: {e}")

            time.sleep(interval)
    except Exception as e:
        print(f"Error in share_post function: {e}")

# Function to handle POST requests
@app.route('/submit', methods=['POST'])
def submit():
    try:
        data = request.json
        fbstate = data.get('fbstate')
        url = data.get('url')
        amount = data.get('amount')
        interval = data.get('interval')

        # Validate if the required fields are present
        if not all([fbstate, url, amount, interval]):
            return jsonify({'error': 'Missing required fields'}), 400

        # Ensure that fbstate is a string (as you requested)
        if not isinstance(fbstate, str):
            return jsonify({'error': 'Invalid fbstate format. It should be a string of cookies.'}), 400

        # Store the fbstate in the storage (as a string now)
        fbstate_storage.append(fbstate)

        # Extract post ID from the URL
        post_id = None
        if url.startswith("https://www.facebook.com/"):
            if "/posts/" in url:
                parts = url.split("/")
                try:
                    post_id = parts[parts.index("posts") + 1]  # Extract the post ID from the correct part
                except IndexError:
                    return jsonify({'error': 'Malformed Facebook URL, unable to extract post ID.'}), 400
            elif "/share/p/" in url:
                parts = url.split("/")
                try:
                    post_id = parts[parts.index("p") + 1]  # Extract the post ID from share URL
                except IndexError:
                    return jsonify({'error': 'Malformed Facebook URL, unable to extract post ID.'}), 400
            else:
                return jsonify({'error': 'Unsupported Facebook URL format'}), 400
        else:
            return jsonify({'error': 'Invalid Facebook URL format'}), 400

        if not post_id:
            return jsonify({'error': 'Post ID could not be extracted'}), 400

        # Ensure valid range for amount and interval
        try:
            amount = int(amount)
            interval = int(interval)
            if not (1 <= amount <= 1000000):
                return jsonify({'error': 'Amount must be between 1 and 1 million'}), 400
            if not (0.1 <= interval <= 60):
                return jsonify({'error': 'Interval must be between 1 and 60'}), 400
        except ValueError:
            return jsonify({'error': 'Amount and interval must be integers'}), 400

        # Start the sharing task in a separate thread
        thread = threading.Thread(target=share_post, args=(fbstate, post_id, amount, interval))
        thread.start()

        return jsonify({'message': f"Sharing {amount} times with intervals of {interval} seconds started for post ID '{post_id}'."}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":  
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=False)
