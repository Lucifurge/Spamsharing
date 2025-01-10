const express = require('express');
const puppeteer = require('puppeteer');
const { createClient } = require('@supabase/supabase-js');
const bodyParser = require('body-parser');
const winston = require('winston');

// Initialize the Express app and middleware
const app = express();
const port = process.env.PORT || 3000;
app.use(bodyParser.json());

// Supabase connection
const supabaseUrl = 'https://fpautuvsjzoipbkuufyl.supabase.co';
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZwYXV0dXZzanpvaXBia3V1ZnlsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzY1MTg1NDMsImV4cCI6MjA1MjA5NDU0M30.c3lfVfxkbuvSbROKj_OYRewQAcgBMnJaSDAB4pspIHk';
const supabase = createClient(supabaseUrl, supabaseKey);

// Logger setup using Winston
const logger = winston.createLogger({
  level: 'info',
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: 'logs/app.log' })
  ]
});

// Function to simulate Facebook post sharing
async function shareOnFacebook(postLink, fbstate, cookies) {
  try {
    // Launch Puppeteer and open Facebook
    const browser = await puppeteer.launch({ headless: true });
    const page = await browser.newPage();

    // Login to Facebook with cookies from the Supabase DB
    cookies.forEach(cookie => {
      page.setCookie(cookie);
    });

    // Navigate to the post link
    await page.goto(postLink);

    // Simulate the action of clicking the share button
    await page.click('button[data-testid="share_button"]');

    // Wait for the share action to complete
    await page.waitForTimeout(5000); // 5 seconds wait

    // Optionally, capture a success message or confirm the share
    logger.info(`Successfully shared post: ${fbstate}`);

    // Close the browser
    await browser.close();
  } catch (err) {
    logger.error('Error in shareOnFacebook:', err);
    throw new Error('Error in shareOnFacebook');
  }
}

// API route to trigger sharing
app.post('/share', async (req, res) => {
  const { fbstate, postLink, interval, shares } = req.body;

  if (!fbstate || !postLink || !interval || !shares) {
    return res.status(400).json({ message: 'Missing required parameters' });
  }

  try {
    // Insert the share data into Supabase with status 'Started'
    const { data, error } = await supabase
      .from('shares')
      .insert([{ post_id: fbstate, fb_cookie_id: 1, interval_seconds: interval, share_count: shares, status: 'Started' }]);

    if (error) {
      logger.error('Error inserting share log:', error);
      return res.status(500).json({ message: 'Error inserting share log into database' });
    }

    // Fetch cookies from the database for login
    const { data: cookiesData, error: cookiesError } = await supabase
      .from('facebook_cookies')
      .select('*')
      .eq('user_id', 1); // assuming you store the cookies for the user in this table

    if (cookiesError) {
      logger.error('Error fetching cookies:', cookiesError);
      return res.status(500).json({ message: 'Error fetching cookies from database' });
    }

    // Loop to simulate the sharing process for the specified number of shares
    for (let i = 0; i < shares; i++) {
      await shareOnFacebook(postLink, fbstate, cookiesData); // Share once for each iteration
      logger.info(`Shared ${i + 1} of ${shares}`);
      await new Promise(resolve => setTimeout(resolve, interval * 1000)); // Wait for the specified interval
    }

    // Update the share log status in the database to 'Completed'
    const { data: updatedData, error: updateError } = await supabase
      .from('shares')
      .update({ status: 'Completed' })
      .eq('post_id', fbstate);

    if (updateError) {
      logger.error('Error updating share status:', updateError);
      return res.status(500).json({ message: 'Error updating share status' });
    }

    return res.json({ message: `Successfully shared ${shares} posts.` });
  } catch (err) {
    logger.error('Error occurred during the sharing process:', err);
    return res.status(500).json({ message: 'Error occurred during the sharing process' });
  }
});

// Start the server
app.listen(port, () => {
  logger.info(`Server is running on port ${port}`);
});
