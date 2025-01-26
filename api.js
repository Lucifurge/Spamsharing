const express = require("express");
const cors = require("cors");
const cookieParser = require("cookie-parser");
const bodyParser = require("body-parser");
const puppeteer = require("puppeteer");

const app = express();

// Enable CORS for all origins
app.use(cors());
app.use(cookieParser());
app.use(bodyParser.json());

// Root endpoint to verify API status
app.get("/", (req, res) => {
    res.send({ message: "Facebook Sharing API is running!" });
});

// Helper function to validate Facebook URLs (both post and share)
function isValidFacebookURL(url) {
    const postRegex = /^https:\/\/www\.facebook\.com\/[0-9]+\/posts\/.+/;
    const shareRegex = /^https:\/\/www\.facebook\.com\/share\/p\/.+/;
    const extendedPostRegex = /^https:\/\/www\.facebook\.com\/[0-9]+\/posts\/[0-9]+\?.+/;
    const extendedShareRegex = /^https:\/\/www\.facebook\.com\/share\/p\/[a-zA-Z0-9]+\?.+/;
    return postRegex.test(url) || shareRegex.test(url) || extendedPostRegex.test(url) || extendedShareRegex.test(url);
}

// Helper function to delay execution
function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Endpoint to share a URL on Facebook using Puppeteer
app.post("/api/share", async (req, res) => {
    const { fbstate, url, interval, shares } = req.body;

    if (!url || !fbstate) {
        return res.status(400).json({ message: "Missing 'url' or 'fbstate' parameter." });
    }

    if (!isValidFacebookURL(url)) {
        return res.status(400).json({ message: "Invalid Facebook URL format. Please use a valid post or share URL." });
    }

    const parsedInterval = parseFloat(interval);
    if (isNaN(parsedInterval) || parsedInterval < 0.5 || parsedInterval > 9) {
        return res.status(400).json({ message: "Invalid 'interval'. Must be between 0.5 and 9 seconds." });
    }

    const parsedShares = parseInt(shares, 10);
    if (isNaN(parsedShares) || parsedShares < 1 || parsedShares > 10000000) {
        return res.status(400).json({ message: "Invalid 'shares'. Must be between 1 and 10,000,000." });
    }

    try {
        const cookies = JSON.parse(fbstate).map(cookie => {
            return { ...cookie, name: cookie.key };
        });
        const browser = await puppeteer.launch({
            headless: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox'],
        });
        const page = await browser.newPage();

        // Set cookies and wait for navigation to complete
        await page.setCookie(...cookies);
        await page.goto('https://facebook.com');  // Initial navigation to set cookies
        await page.waitForNavigation();

        const results = [];
        for (let i = 0; i < parsedShares; i++) {
            await delay(parsedInterval * 1000);

            const encodedURL = encodeURIComponent(url);
            const fbShareURL = `https://www.facebook.com/sharer/sharer.php?u=${encodedURL}`;

            try {
                await page.goto(fbShareURL, { timeout: 60000 });  // Increase timeout to 60 seconds
                await page.waitForNavigation();  // Wait for navigation to complete

                // Additional steps might be required here to actually perform the share operation
                // depending on the interactions required by Facebook's interface.

                results.push(`Share ${i + 1}: Attempted`);
            } catch (error) {
                console.error(`Error on share ${i + 1}:`, error.message);
                results.push(`Share ${i + 1}: Failed - ${error.message}`);
            }
        }

        await browser.close();

        res.status(200).json({
            message: "All shares attempted. Check results for details.",
            shares: parsedShares,
            interval: parsedInterval,
            results,
        });
    } catch (error) {
        console.error("Error sharing on Facebook:", error.message);
        res.status(500).json({ message: "Failed to share on Facebook.", error: error.message });
    }
});

// 404 handler for undefined routes
app.use((req, res) => {
    res.status(404).send({ message: "Endpoint not found." });
});

// Start the server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`API server running on port ${PORT}`);
});
