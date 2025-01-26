const express = require("express");
const cors = require("cors"); // Import CORS package
const cookieParser = require("cookie-parser");
const bodyParser = require("body-parser");
const axios = require("axios");

const app = express();

// Enable CORS for all origins
app.use(cors());  // Apply the CORS middleware globally
app.use(cookieParser());
app.use(bodyParser.json());

// Root endpoint to verify API status
app.get("/", (req, res) => {
    res.send({ message: "Facebook Sharing API is running!" });
});

// Helper function to validate Facebook URLs (both post and share)
function isValidFacebookURL(url) {
    const postRegex = /^https:\/\/www\.facebook\.com\/[0-9]+\/posts\/.+$/;
    const shareRegex = /^https:\/\/www\.facebook\.com\/share\/p\/.+$/;
    return postRegex.test(url) || shareRegex.test(url);
}

// Endpoint to share a URL on Facebook
app.post("/api/share", async (req, res) => {
    const { fbstate, url, interval, shares } = req.body;

    if (!url || !fbstate) {
        return res.status(400).json({ message: "Missing 'url' or 'fbstate' parameter." });
    }

    // Validate Facebook URL
    if (!isValidFacebookURL(url)) {
        return res.status(400).json({ message: "Invalid Facebook URL format. Please use a valid post or share URL." });
    }

    // Validate interval (0.5 to 9 seconds)
    const parsedInterval = parseFloat(interval);
    if (isNaN(parsedInterval) || parsedInterval < 0.5 || parsedInterval > 9) {
        return res.status(400).json({ message: "Invalid 'interval'. Must be between 0.5 and 9 seconds." });
    }

    // Validate shares (1 to 10 million)
    const parsedShares = parseInt(shares, 10);
    if (isNaN(parsedShares) || parsedShares < 1 || parsedShares > 10000000) {
        return res.status(400).json({ message: "Invalid 'shares'. Must be between 1 and 10,000,000." });
    }

    try {
        const cookies = JSON.parse(fbstate);

        // Constructing cookie header
        const cookieString = cookies
            .map(cookie => `${cookie.key}=${cookie.value}`)
            .join("; ");

        const results = [];
        for (let i = 0; i < parsedShares; i++) {
            // Simulate interval delay
            await new Promise(resolve => setTimeout(resolve, parsedInterval * 1000));

            // Encode the URL for Facebook's sharer endpoint
            const encodedURL = encodeURIComponent(url);

            // Facebook sharer API endpoint
            const fbShareURL = `https://www.facebook.com/sharer/sharer.php?u=${encodedURL}`;

            // Send request to Facebook sharer
            const response = await axios.get(fbShareURL, {
                headers: {
                    Cookie: cookieString,
                    "User-Agent":
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.6834.110 Safari/537.36",
                },
            });

            results.push(`Share ${i + 1}: Successful`);
        }

        res.status(200).json({
            message: "All shares completed successfully.",
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
