from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)

# Enable CORS for the frontend URL
CORS(app, resources={r"/submit": {"origins": "https://frontend-253d.onrender.com"}})

# Store fbstate data in memory (this could be saved to a database or file in a real-world scenario)
fbstate_storage = []

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

        # Validate and parse the Facebook URL
        post_id = None
        if url.startswith("https://www.facebook.com/"):
            if "/posts/" in url:
                # Format: https://www.facebook.com/user/posts/postid
                parts = url.split("/")
                try:
                    post_id = parts[5]  # Extract the post ID
                except IndexError:
                    return jsonify({'error': 'Malformed Facebook post URL'}), 400
            elif "/share/p/" in url:
                # Format: https://www.facebook.com/share/p/postid
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

        # Simulate sharing action (delay based on amount and interval)
        result = f"{amount} shares of post ID '{post_id}' completed in intervals of {interval} seconds"

        return jsonify({'message': result})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
