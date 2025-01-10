const express = require('express');
const puppeteer = require('puppeteer');
const { createClient } = require('@supabase/supabase-js');
const bodyParser = require('body-parser');
const winston = require('winston');
const cors = require('cors');

// Initialize the Express app and middleware
const app = express();
const port = process.env.PORT || 3000;

// Use CORS middleware and specify the frontend URL
const allowedOrigins = ['https://frontend-253d.onrender.com'];
app.use(cors({
  origin: allowedOrigins,
  methods: ['GET', 'POST', 'OPTIONS'],
  allowedHeaders: ['Content-Type'],
}));

// Middleware for parsing JSON
app.use(bodyParser.json());

// Supabase connection
const supabaseUrl = 'https://fpautuvsjzoipbkuufyl.supabase.co';
const supabaseKey = 'your_supabase_key';
const supabase = createClient(supabaseUrl, supabaseKey);

// Logger setup using Winston
const logger = winston.createLogger({
  level: 'info',
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: 'logs/app.log' }),
  ],
});

// Function to validate and set cookies
async function setCookies(page, cookies) {
  if (!Array.isArray(cookies)) {
    throw new Error('Invalid fbstate format: Expected an array of cookies.');
  }

  const formattedCookies = cookies.map(cookie => {
    if (!cookie.key || !cookie.value || !cookie.domain || !cookie.path) {
      throw new Error('Invalid cookie format. Each cookie must contain "key", "value", "domain", and "path".');
    }
    return {
      name: cookie.key,
      value: cookie.value,
      domain: cookie.domain,
      path: cookie.path,
      httpOnly: cookie.hostOnly === false, // Set httpOnly based on hostOnly
      secure: true, // Assuming secure cookies are required
      sameSite: 'Lax',
    };
  });

  await page.setCookie(...formattedCookies);
}

// Function to simulate Facebook post sharing
async function shareOnFacebook(postLink, fbstateCookies) {
  let browser;
  try {
    browser = await puppeteer.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
    });
    const page = await browser.newPage();

    // Set cookies
    await setCookies(page, fbstateCookies);

    // Navigate to the post link
    await page.goto(postLink, { waitUntil: 'networkidle2' });

    // Simulate clicking the share button
    await page.waitForSelector('button[data-testid="share_button"]', { timeout: 10000 });
    await page.click('button[data-testid="share_button"]');

    // Wait for the share action to complete
    await page.waitForTimeout(5000);

    logger.info(`Successfully shared post: ${postLink}`);
  } catch (err) {
    logger.error('Error in shareOnFacebook:', err);
    throw err;
  } finally {
    if (browser) {
      await browser.close();
    }
  }
}

// API route to trigger sharing
app.post('/share', async (req, res) => {
  const { fbstate, postLink, interval, shares } = req.body;

  if (!fbstate || !postLink || !interval || !shares) {
    return res.status(400).json({ message: 'Missing required parameters.' });
  }

  try {
    // Insert the share data into Supabase with status 'Started'
    const { error } = await supabase
      .from('shares')
      .insert([{ post_id: postLink, fb_cookie_id: 1, interval_seconds: interval, share_count: shares, status: 'Started' }]);

    if (error) {
      logger.error('Error inserting share log:', error);
      return res.status(500).json({ message: 'Error inserting share log into database.' });
    }

    // Loop to simulate the sharing process
    for (let i = 0; i < shares; i++) {
      await shareOnFacebook(postLink, fbstate);
      logger.info(`Shared ${i + 1} of ${shares}`);
      await new Promise(resolve => setTimeout(resolve, interval * 1000));
    }

    // Update the share log status in the database to 'Completed'
    const { error: updateError } = await supabase
      .from('shares')
      .update({ status: 'Completed' })
      .eq('post_id', postLink);

    if (updateError) {
      logger.error('Error updating share status:', updateError);
      return res.status(500).json({ message: 'Error updating share status.' });
    }

    res.json({ message: `Successfully shared ${shares} posts.` });
  } catch (err) {
    logger.error('Error occurred during the sharing process:', err);
    res.status(500).json({ message: 'Error occurred during the sharing process.' });
  }
});

// Handle preflight OPTIONS requests for CORS
app.options('*', cors());

// Start the server
app.listen(port, () => {
  logger.info(`Server is running on port ${port}`);
});
