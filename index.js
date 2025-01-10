require('dotenv').config(); // Load environment variables

const express = require('express');
const puppeteer = require('puppeteer');
const { createClient } = require('@supabase/supabase-js');
const bodyParser = require('body-parser');
const winston = require('winston');
const cors = require('cors');

// Initialize Express app and middleware
const app = express();
const port = process.env.PORT || 3000;

// Use CORS middleware and specify the frontend URL
const allowedOrigins = ['https://frontend-253d.onrender.com']; // Frontend URL
app.use(cors({
  origin: allowedOrigins,
  methods: ['GET', 'POST'],
  allowedHeaders: ['Content-Type']
}));

// Middleware for parsing JSON
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
    const browser = await puppeteer.launch({ headless: true });
    const page = await browser.newPage();

    cookies.forEach(cookie => {
      page.setCookie(cookie);
    });

    await page.goto(postLink);
    await page.click('button[data-testid="share_button"]');
    await page.waitForTimeout(5000); // Wait for share to complete

    logger.info(`Successfully shared post: ${fbstate}`);
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
    const { data, error } = await supabase
      .from('shares')
      .insert([{ post_id: fbstate, fb_cookie_id: 1, interval_seconds: interval, share_count: shares, status: 'Started' }]);

    if (error) {
      logger.error('Error inserting share log:', error);
      return res.status(500).json({ message: 'Error inserting share log into database' });
    }

    const { data: cookiesData, error: cookiesError } = await supabase
      .from('facebook_cookies')
      .select('*')
      .eq('user_id', 1); // Adjust user ID as needed

    if (cookiesError) {
      logger.error('Error fetching cookies:', cookiesError);
      return res.status(500).json({ message: 'Error fetching cookies from database' });
    }

    for (let i = 0; i < shares; i++) {
      await shareOnFacebook(postLink, fbstate, cookiesData);
      logger.info(`Shared ${i + 1} of ${shares}`);
      await new Promise(resolve => setTimeout(resolve, interval * 1000)); // Wait between shares
    }

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
