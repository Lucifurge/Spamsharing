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
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZwYXV0dXZzanpvaXBia3V1ZnlsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzY1MTg1NDMsImV4cCI6MjA1MjA5NDU0M30.c3lfVfxkbuvSbROKj_OYRewQAcgBMnJaSDAB4pspIHk';
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
async function setCookies(page, fbstate) {
  const cookies = JSON.parse(fbstate);

  // Validate the structure of each cookie
  cookies.forEach(cookie => {
    if (!cookie.key || !cookie.value || !cookie.domain || !cookie.path) {
      throw new Error('Invalid cookie format. Each cookie must contain "key", "value", "domain", and "path".');
    }
  });

  const formattedCookies = cookies.map(cookie => ({
    name: cookie.key,
    value: cookie.value,
    domain: cookie.domain,
    path: cookie.path,
    httpOnly: cookie.hostOnly === false,
    secure: true,
    sameSite: 'Lax',
  }));

  await page.setCookie(...formattedCookies);
}

// Function to simulate Facebook post sharing
async function shareOnFacebook(postLink, fbstate) {
  let browser;
  try {
    browser = await puppeteer.launch({
      headless: true, // Running in headless mode
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
    });
    const page = await browser.newPage();

    // Set cookies
    await setCookies(page, fbstate);

    // Navigate to the post link with retry logic
    let navigationSuccessful = false;
    for (let i = 0; i < 3; i++) {
      try {
        await page.goto(postLink, { waitUntil: 'networkidle2', timeout: 180000 }); // Increase timeout
        navigationSuccessful = true;
        break;
      } catch (error) {
        logger.error(`Navigation attempt ${i + 1} failed: ${error}`);
      }
    }
    if (!navigationSuccessful) {
      throw new Error('Failed to navigate to the post link after multiple attempts');
    }

    // Wait for the page to load completely
    await page.waitForNavigation({ waitUntil: 'networkidle0', timeout: 180000 });

    // Wait for the share button to appear and be visible using XPath
    await page.waitForXPath('//button[@name="share" or @data-testid="share_button"]', { timeout: 180000 });

    // Click the share button using XPath
    const [shareButton] = await page.$x('//button[@name="share" or @data-testid="share_button"]');
    if (shareButton) {
      await shareButton.click();
    } else {
      throw new Error('Share button not found');
    }

    // Wait for the post to be shared
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

// API route to handle sharing requests
app.post('/share', async (req, res) => {
  const { fbstate, postLink, interval, shares } = req.body;

  if (!fbstate || !postLink || !interval || !shares) {
    return res.status(400).json({ message: 'Missing required parameters.' });
  }

  try {
    const { error: insertError } = await supabase
      .from('shares')
      .insert([{ post_id: postLink, fb_cookie_id: 1, interval_seconds: interval, share_count: shares, status: 'Started', fbstate }]);

    if (insertError) {
      logger.error('Error inserting share log:', insertError);
      return res.status(500).json({ message: 'Error inserting share log into database.' });
    }

    for (let i = 0; i < shares; i++) {
      await shareOnFacebook(postLink, fbstate);
      logger.info(`Shared ${i + 1} of ${shares}`);
      await new Promise(resolve => setTimeout(resolve, interval * 1000));
    }

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
    logger.error('Error during the sharing process:', err);
    res.status(500).json({ message: 'Error occurred during the sharing process.' });
  }
});

// Endpoint to generate Facebook share URL
app.post('/generate-share-url', (req, res) => {
  const { postLink } = req.body;

  if (!postLink) {
    return res.status(400).json({ message: 'Post link is required.' });
  }

  try {
    const facebookShareUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(postLink)}`;
    res.json({ message: 'Share URL generated successfully.', shareUrl: facebookShareUrl });
  } catch (error) {
    logger.error('Error generating share URL:', error);
    res.status(500).json({ message: 'Error generating share URL.' });
  }
});

// Preflight OPTIONS requests
app.options('*', cors());

// Start the server
app.listen(port, () => {
  logger.info(`Server is running on port ${port}`);
});
