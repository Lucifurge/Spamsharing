const express = require("express");
const cookieParser = require("cookie-parser");
const bodyParser = require("body-parser");
const axios = require("axios");

const app = express();
app.use(cookieParser());
app.use(bodyParser.json());

// Root endpoint to verify API status
app.get("/", (req, res) => {
    res.send({ message: "Facebook Sharing API is running!" });
});

// Endpoint to set cookies dynamically
app.post("/api/set-cookies", (req, res) => {
    const { cookies } = req.body;

    if (!Array.isArray(cookies)) {
        return res.status(400).json({ message: "Invalid cookies format. Must be an array." });
    }

    cookies.forEach(cookie => {
        res.cookie(cookie.key, cookie.value, {
            domain: cookie.domain || "facebook.com",
            path: cookie.path || "/",
            httpOnly: cookie.hostOnly === false,
            secure: true,
            sameSite: "Lax",
        });
    });

    res.status(200).json({ message: "Cookies set successfully." });
});

// Endpoint to share a URL on Facebook
app.get("/api/share", async (req, res) => {
    const { url, fbstate } = req.query;

    if (!url || !fbstate) {
        return res.status(400).json({ message: "Missing 'url' or 'fbstate' parameter." });
    }

    try {
        const cookies = JSON.parse(fbstate);

        // Constructing cookie header
        const cookieString = cookies
            .map(cookie => `${cookie.key}=${cookie.value}`)
            .join("; ");

        // Facebook sharer API endpoint
        const fbShareURL = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`;

        // Send request to Facebook sharer
        const response = await axios.get(fbShareURL, {
            headers: {
                Cookie: cookieString,
                "User-Agent":
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            },
        });

        res.status(200).json({
            message: "Share URL accessed successfully.",
            facebookResponse: response.data,
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
