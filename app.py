from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import threading
import asyncio
from playwright.async_api import async_playwright

# Initialize Flask app
app = Flask(__name__)

# Enable CORS for the frontend URL
CORS(app, resources={r"/submit": {"origins": "https://frontend-253d.onrender.com"}})

# Store fbstate data in memory
fbstate_storage = []

# Async function to run the Playwright task
async def run_browser_task(fbstate, post_id, amount, interval):
    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context()

            # Add Facebook cookies
            for cookie in fbstate:
                await context.add_cookies([{
                    "name": cookie["key"],
                    "value": cookie["value"],
                    "domain": cookie["domain"],
                    "path": cookie["path"]
                }])

            page = await context.new_page()

            for _ in range(amount):
                await page.goto(f"https://www.facebook.com/{post_id}")
                await page.wait_for_selector('div[aria-label="Share"]')
                share_button = await page.query_selector('div[aria-label="Share"]')
                if share_button:
                    await share_button.click()
                    await page.wait_for_selector('button[aria-label="Post"]')
                    post_button = await page.query_selector('button[aria-label="Post"]')
                    if post_button:
                        await post_button.click()
                    else:
                        print("Post button not found.")
                else:
                    print("Share button not found.")
                await asyncio.sleep(interval)  # Wait for the interval before sharing again

            await browser.close()

    except Exception as e:
        print(f"Error in browser task: {e}")

# Async wrapper for running Playwright tasks
def start_playwright_task(fbstate, post_id, amount, interval):
    asyncio.run(run_browser_task(fbstate, post_id, amount, interval))

# Function to handle POST requests
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

        # Store the fbstate in the storage
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

        # Start the Playwright task in a separate thread
        thread = threading.Thread(target=start_playwright_task, args=(fbstate, post_id, amount, interval))
        thread.start()

        return jsonify({'message': f"Sharing {amount} times with intervals of {interval} seconds started for post ID '{post_id}'."}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=False)
