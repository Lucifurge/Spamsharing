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

        # Set up Selenium WebDriver
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode (without GUI)
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

        # Open Facebook's login page to set the cookies
        driver.get("https://www.facebook.com")
        time.sleep(3)  # Allow time for the page to load

        # Load cookies into the browser session
        load_facebook_cookies(driver, fbstate)

        # Refresh the page to apply cookies
        driver.refresh()
        time.sleep(5)  # Wait for the session to be established

        # Simulate the share action multiple times with the specified interval
        for i in range(amount):
            share_post(driver, post_id)
            time.sleep(interval)

        driver.quit()

        return jsonify({'message': f"{amount} shares of post ID '{post_id}' completed in intervals of {interval} seconds"})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
