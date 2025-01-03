import time
from pyppeteer import launch
import sys

async def share_post(page, post_id):
    try:
        await page.goto(f"https://www.facebook.com/{post_id}")
        await page.waitForSelector('div[aria-label="Share"]')  # Ensure the share button is loaded
        share_button = await page.querySelector('div[aria-label="Share"]')
        await share_button.click()
        await page.waitForSelector('button[aria-label="Post"]')  # Ensure post button is loaded
        post_button = await page.querySelector('button[aria-label="Post"]')
        await post_button.click()
        time.sleep(5)  # Wait for the post to be shared
    except Exception as e:
        print(f"Error sharing post: {e}")
        sys.exit(1)

async def run_browser(fbstate, post_id, amount, interval):
    try:
        browser = await launch(headless=True, args=['--no-sandbox', '--disable-dev-shm-usage'])
        page = await browser.newPage()

        # Load Facebook and set cookies
        await page.goto("https://www.facebook.com")
        time.sleep(3)  # Allow time for the page to load

        # Load the fbstate cookies (for login)
        for cookie in fbstate:
            cookie_dict = {
                "name": cookie["key"],
                "value": cookie["value"],
                "domain": cookie["domain"],
                "path": cookie["path"],
                "secure": False,
                "httpOnly": False
            }
            page.context.addCookies([cookie_dict])

        await page.reload()
        time.sleep(5)  # Wait for the session to be established

        # Perform the share action multiple times with the specified interval
        for i in range(amount):
            await share_post(page, post_id)
            time.sleep(interval)  # Wait between shares

        await browser.close()
        print(f"Successfully shared {amount} times for post ID: {post_id}")

    except Exception as e:
        print(f"Error running browser task: {e}")
        sys.exit(1)

# Entry point for the script
if __name__ == '__main__':
    # Arguments passed from the Flask app or manually set for testing
    fbstate = [
        {"key": "your_cookie_name", "value": "your_cookie_value", "domain": ".facebook.com", "path": "/"}
    ]
    post_id = "1234567890"  # Replace with actual post ID
    amount = 5  # Number of shares to perform
    interval = 10  # Interval between shares in seconds

    # Run the browser task
    import asyncio
    asyncio.run(run_browser(fbstate, post_id, amount, interval))
