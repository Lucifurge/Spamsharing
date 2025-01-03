import json
import logging
import threading
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

# Function to simulate sharing a post
def share_post(fbstate, post_id, amount, interval):
    logging.debug(f"Started sharing post ID {post_id} {amount} times with an interval of {interval} seconds.")

    # Facebook sharing endpoint (Reverse-engineered; subject to change by Facebook)
    share_url = f"https://www.facebook.com/api/graphql/"

    # Common headers for Facebook requests
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "*/*",
        "Origin": "https://www.facebook.com",
        "Referer": "https://www.facebook.com/",
    }

    # Attach cookies from fbstate
    cookies = {item["key"]: item["value"] for item in fbstate}

    for i in range(amount):
        try:
            # Payload for sharing (Reverse-engineered payload structure)
            payload = {
                "av": cookies.get("c_user"),
                "fb_dtsg": cookies.get("fb_dtsg"),
                "action": "share",
                "object_id": post_id,
                "source": "timeline",  # Example source
            }

            response = requests.post(share_url, data=payload, headers=headers, cookies=cookies)
            if response.status_code == 200:
                logging.debug(f"Successfully shared post {post_id}: Attempt {i + 1}/{amount}")
            else:
                logging.error(f"Failed to share post {post_id}: {response.text}")

            time.sleep(interval)

        except Exception as e:
            logging.error(f"Error while sharing post {post_id}: {e}")
            break

@app.route('/submit', methods=['POST'])
def submit():
    try:
        data = request.json
        logging.debug(f"Received data: {data}")

        fbstate = data.get('fbstate')
        url = data.get('postLink')
        amount = data.get('shares')
        interval = data.get('interval')

        if not all([fbstate, url, amount, interval]):
            return jsonify({'error': 'Missing required fields'}), 400

        try:
            fbstate = json.loads(fbstate)
        except Exception as e:
            return jsonify({'error': 'Invalid fbstate format.'}), 400

        try:
            amount = int(amount)
            interval = float(interval)

            # Interval validation: Allow 0.1 - 0.10 and 1 - 60
            if not ((0.1 <= interval <= 0.10) or (1 <= interval <= 60)):
                return jsonify({'error': 'Interval must be between 0.1 and 0.10 or between 1 and 60 seconds'}), 400

            if not (1 <= amount <= 1000000):
                return jsonify({'error': 'Amount must be between 1 and 1 million'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid amount or interval format'}), 400

        post_id = None
        if "/posts/" in url:
            post_id = url.split("/posts/")[1].split("?")[0]
        elif "/share/p/" in url:
            post_id = url.split("/p/")[1].split("?")[0]
        else:
            return jsonify({'error': 'Unsupported URL format'}), 400

        if not post_id:
            return jsonify({'error': 'Post ID extraction failed'}), 400

        logging.debug(f"Post ID extracted: {post_id}")

        # Make a POST request to the frontend for the submission
        frontend_url = "https://frontend-253d.onrender.com/submit"
        frontend_data = {
            "fbstate": fbstate,
            "postLink": url,
            "shares": amount,
            "interval": interval
        }
        try:
            frontend_response = requests.post(frontend_url, json=frontend_data)
            if frontend_response.status_code == 200:
                logging.debug(f"Successfully sent data to frontend: {frontend_response.json()}")
            else:
                logging.error(f"Failed to communicate with frontend: {frontend_response.text}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Error communicating with frontend: {e}")

        thread = threading.Thread(target=share_post, args=(fbstate, post_id, amount, interval))
        thread.start()

        return jsonify({'message': f"Sharing started for post ID {post_id} with {amount} shares."}), 200

    except Exception as e:
        logging.error(f"Error in submit: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
