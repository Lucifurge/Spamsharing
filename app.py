import json
import logging
import threading
from flask import Flask, request, jsonify

app = Flask(__name__)

# Ensure that you have logging set up
logging.basicConfig(level=logging.DEBUG)

def share_post(fbstate, post_id, amount, interval):
    # Function to simulate the sharing task (you can replace this with actual sharing logic)
    logging.debug(f"Sharing post {post_id} with {amount} shares at an interval of {interval} seconds.")
    # Here, implement the logic to share the post using fbstate, post_id, and interval.
    pass

@app.route('/')
def home():
    return "Welcome to the Facebook sharing service!"

@app.route('/submit', methods=['POST'])
def submit():
    try:
        # Step 1: Extract the data from the request body
        data = request.json
        logging.debug(f"Received data from frontend: {data}")

        # Step 2: Extract individual fields
        fbstate = data.get('fbstate')  # fbstate provided by the user
        url = data.get('postLink')  # Fixed typo: "url" -> "postLink"
        amount = data.get('shares')  # Fixed typo: "amount" -> "shares"
        interval = data.get('interval')

        # Step 3: Validate that the required fields are present
        if not all([fbstate, url, amount, interval]):
            return jsonify({'error': 'Missing required fields'}), 400

        # Step 4: Ensure fbstate is parsed correctly
        try:
            fbstate = json.loads(fbstate)  # Convert string to JSON object if necessary
        except Exception as e:
            return jsonify({'error': 'Invalid fbstate format. It should be a valid JSON string.'}), 400

        # Step 5: Ensure valid range for amount and interval
        try:
            amount = int(amount)
            interval = float(interval)  # Convert interval to float for decimal support
            if not (1 <= amount <= 1000000):
                return jsonify({'error': 'Amount must be between 1 and 1 million'}), 400
            if not (0.1 <= interval <= 60):
                return jsonify({'error': 'Interval must be between 0.1 and 60 seconds'}), 400
        except ValueError:
            return jsonify({'error': 'Amount must be an integer and interval must be a float'}), 400

        # Step 6: Extract post ID from the URL
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

        # Step 7: Handle cases where no post ID is extracted
        if not post_id:
            return jsonify({'error': 'Post ID could not be extracted'}), 400

        logging.debug(f"Extracted post ID: {post_id}")

        # Step 8: Start the sharing task in a separate thread
        thread = threading.Thread(target=share_post, args=(fbstate, post_id, amount, interval))
        thread.start()

        # Step 9: Return a success response
        return jsonify({'message': f"Sharing {amount} times with intervals of {interval} seconds started for post ID '{post_id}'."}), 200

    except Exception as e:
        logging.error(f"Error in submit function: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
