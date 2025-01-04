import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import threading
import requests
import time

# Initialize Flask app
app = Flask(__name__)

# Enable CORS for the specific frontend URL
CORS(app, resources={r"/submit": {"origins": "https://frontend-253d.onrender.com"}})

# Configure logging for detailed debugging
logging.basicConfig(level=logging.DEBUG)

# Facebook credentials (Access token and App details)
ACCESS_TOKEN = "EAAOJZBiWW8UUBO8x7QEXkM6j0LlhM57pMhbHfBMsCnJcg6Pnqqi9GdKBpjWI8ZAhADM20lzS8UQLLTBTtOqMw2qmnHy9W0oeAFMJZCIhPRDhhHwZBkwZAud7H5Fql2GyZA4il7FpL0ZC9py8tTOxumZCQPm2nzmyh8aZAQyDt3agPl6XOowlvHV4NFh3c5p0a9WHg1hNguPHF6SyweA7jGptXtfz1pN4ZD"

# Function to send share requests to Facebook
def share_post(fbstate, post_id, amount, interval):
    try:
        logging.debug(f"Starting to share post {post_id} {amount} times with interval {interval} seconds.")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        # Build cookies from fbstate
        cookie_string = "; ".join([f"{cookie['key']}={cookie['value']}" for cookie in fbstate])
        logging.debug(f"Generated cookie string: {cookie_string}")

        for i in range(amount):
            try:
                share_url = f"https://graph.facebook.com/v14.0/{post_id}/shares"
                params = {'access_token': ACCESS_TOKEN}
                logging.debug(f"Requesting URL: {share_url} with params: {params} and cookies: {cookie_string}")

                response = requests.post(
                    share_url,
                    headers=headers,
                    cookies={"cookie": cookie_string},
                    params=params
                )

                logging.debug(f"Response status code: {response.status_code}")
                logging.debug(f"Response body: {response.text}")

                if response.status_code == 200:
                    logging.info(f"[{i + 1}] Successfully shared post ID: {post_id}")
                else:
                    logging.warning(f"[{i + 1}] Failed to share post ID: {post_id}. Status code: {response.status_code}")
            except Exception as e:
                logging.error(f"[{i + 1}] Error sharing post: {e}")

            time.sleep(interval)

    except Exception as e:
        logging.error(f"Error in share_post function: {e}")

# Route to handle POST requests
@app.route('/submit', methods=['POST'])
def submit():
    try:
        data = request.json
        logging.debug(f"Received data from frontend: {data}")

        fbstate = data.get('fbstate')
        url = data.get('url')
        amount = data.get('amount')
        interval = data.get('interval')

        # Validate required fields
        if not all([fbstate, url, amount, interval]):
            return jsonify({'error': 'Missing required fields'}), 400

        # Validate fbstate format
        if not isinstance(fbstate, list) or not all(isinstance(cookie, dict) for cookie in fbstate):
            return jsonify({'error': 'Invalid fbstate format. It should be a list of cookies.'}), 400

        # Extract post ID from the URL
        post_id = None
        if url.startswith("https://www.facebook.com/"):
            if "/posts/" in url:
                parts = url.split("/")
                try:
                    post_id = parts[parts.index("posts") + 1]
                except IndexError:
                    return jsonify({'error': 'Malformed Facebook URL, unable to extract post ID.'}), 400
            elif "/share/p/" in url:
                parts = url.split("/")
                try:
                    post_id = parts[parts.index("p") + 1]
                except IndexError:
                    return jsonify({'error': 'Malformed Facebook URL, unable to extract post ID.'}), 400
            else:
                return jsonify({'error': 'Unsupported Facebook URL format'}), 400
        else:
            return jsonify({'error': 'Invalid Facebook URL format'}), 400

        if not post_id:
            return jsonify({'error': 'Post ID could not be extracted'}), 400

        logging.debug(f"Extracted post ID: {post_id}")

        # Validate amount and interval
        try:
            amount = int(amount)
            interval = float(interval)
            if not (1 <= amount <= 1000000):
                return jsonify({'error': 'Amount must be between 1 and 1 million'}), 400
            if not (0.1 <= interval <= 60):
                return jsonify({'error': 'Interval must be between 0.1 and 60 seconds'}), 400
        except ValueError:
            return jsonify({'error': 'Amount must be an integer and interval a number'}), 400

        # Start the sharing task in a separate thread
        thread = threading.Thread(target=share_post, args=(fbstate, post_id, amount, interval))
        thread.start()

        return jsonify({'message': f"Sharing {amount} times with intervals of {interval} seconds started for post ID '{post_id}'."}), 200

    except Exception as e:
        logging.error(f"Error in submit function: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=True)
