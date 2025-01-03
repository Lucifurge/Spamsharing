from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
from flask_cors import CORS  # Import CORS
import time
import os

# Initialize Flask app
app = Flask(__name__)

# Enable CORS for the frontend URL
CORS(app, resources={r"/submit": {"origins": "https://frontend-253d.onrender.com"}})

# Store fbstate data in memory (this could be saved to a database or file in a real-world scenario)
fbstate_storage = []

# Helper function to load cookies into the browser session
def load_facebook_cookies(page, cookies):
    for cookie in cookies:
        cookie_dict = {
            "name": cookie["key"],
            "value": cookie["value"],
            "domain": cookie["domain"],
            "path": cookie["path"],
            "secure": False,
            "httpOnly": False
        }
        page.context.add_cookies([cookie_dict])

# Function to perform the sharing action on Facebook
def share_post(page, post_id):
    page.goto(f"https://www.facebook.com/{post_id}")
    time.sleep(2)  # Wait for page to load

    # Find the share button and click it (this may vary depending on the Facebook layout)
    share_button = page.locator("div[aria-label='Share']")
    share_button.click()
    time.sleep(2)  # Wait for the modal to appear

    # Find the "Post" button and click it to share
    post_button = page.locator("button[aria-label='Post']")
    post_button.click()
    time.sleep(5)  # Wait for the post to be shared

# Define the route to handle the submission from the frontend
@app.route('/submit', methods=['POST'])
def submit():
    try:
        data = request.json
        fbstate = data.get('fbstate')
        url = data.get('url')
        amount = data.get('amount')
        interval = data.get('interval')

        # Check if all required fields are present
        if not all([fbstate, url, amount, interval]):
            return jsonify({'error': 'Missing required fields'}), 400

        # Store the fbstate in the storage (this is just an example; you can save it as needed)
        fbstate_storage.append(fbstate)

        # Extract post ID from the URL
        post_id = None
        if url.startswith("https://www.facebook.com/"):
            if "/posts/" in url:
                parts = url.split("/")
                try:
                    post_id = parts[5]  # Extract the post ID
                except IndexError:
                    return jsonify({'error': 'Malformed Facebook post URL'}), 400
            elif "/share/p/" in url:
                parts = url.split("/")
                try:
                    post_id = parts[5]  # Extract the post ID
                except IndexError:
                    return jsonify({'error': 'Malformed Facebook share URL'}), 400
            else:
                return jsonify({'error': 'Unsupported Facebook URL format'}), 400
        else:
            return jsonify({'error': 'Invalid Facebook URL'}), 400

        if not post_id:
            return jsonify({'error': 'Post ID could not be extracted'}), 400

        # Ensure valid range for amount and interval
        if not (1 <= amount <= 1000000):
            return jsonify({'error': 'Amount must be between 1 and 1 million'}), 400
        if not (1 <= interval <= 60):
            return jsonify({'error': 'Interval must be between 1 and 60'}), 400

        # Start Playwright session and browser
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Open Facebook and load cookies into the browser session
            page.goto("https://www.facebook.com")
            time.sleep(3)  # Allow time for the page to load
            load_facebook_cookies(page, fbstate)
            page.reload()
            time.sleep(5)  # Wait for the session to be established

            # Simulate the share action multiple times with the specified interval
            for i in range(amount):
                share_post(page, post_id)
                time.sleep(interval)

            browser.close()

        return jsonify({'message': f"{amount} shares of post ID '{post_id}' completed in intervals of {interval} seconds"})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=False)
