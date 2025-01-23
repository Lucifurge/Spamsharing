const axios = require('axios');
const C3CUtility = require('c3c-utility'); // Hypothetical C3C utility

// Initialize C3C utility (replace with actual setup)
const c3cUtility = new C3CUtility({
  someConfig: 'configuration_value', // Replace with actual configuration
});

// Cookies
const cookies = [
  {"key":"sb","value":"_hO8Zqv2WYqGeG-5q3HklftT","domain":"facebook.com","path":"/","hostOnly":false,"creation":"2025-01-23T07:59:23.668Z","lastAccessed":"2025-01-23T07:59:23.668Z"},
  {"key":"ps_l","value":"1","domain":"facebook.com","path":"/","hostOnly":false,"creation":"2025-01-23T07:59:23.668Z","lastAccessed":"2025-01-23T07:59:23.668Z"},
  {"key":"ps_n","value":"1","domain":"facebook.com","path":"/","hostOnly":false,"creation":"2025-01-23T07:59:23.668Z","lastAccessed":"2025-01-23T07:59:23.668Z"},
  {"key":"datr","value":"_hO8ZrKKxAOagCc8Ek4hXbTZ","domain":"facebook.com","path":"/","hostOnly":false,"creation":"2025-01-23T07:59:23.668Z","lastAccessed":"2025-01-23T07:59:23.668Z"},
  {"key":"dpr","value":"0.800000011920929","domain":"facebook.com","path":"/","hostOnly":false,"creation":"2025-01-23T07:59:23.668Z","lastAccessed":"2025-01-23T07:59:23.668Z"},
  {"key":"locale","value":"en_US","domain":"facebook.com","path":"/","hostOnly":false,"creation":"2025-01-23T07:59:23.668Z","lastAccessed":"2025-01-23T07:59:23.668Z"},
  {"key":"c_user","value":"100014474223301","domain":"facebook.com","path":"/","hostOnly":false,"creation":"2025-01-23T07:59:23.668Z","lastAccessed":"2025-01-23T07:59:23.668Z"},
  {"key":"fr","value":"1vWrls4Y4y2nqSl4T.AWUqy8rQqiHhcWY4mlkq3pgG5qE.BnkemY..AAA.0.0.BnkemY.AWUb_CgRhRk","domain":"facebook.com","path":"/","hostOnly":false,"creation":"2025-01-23T07:59:23.668Z","lastAccessed":"2025-01-23T07:59:23.668Z"},
  {"key":"xs","value":"15%3AKsl4d85MrKMRfA%3A2%3A1737606326%3A-1%3A3006%3A%3AAcV4DvwZjtVVoN5aLkd8ueZXIZFX4DjgtXS3wHl93Q","domain":"facebook.com","path":"/","hostOnly":false,"creation":"2025-01-23T07:59:23.668Z","lastAccessed":"2025-01-23T07:59:23.668Z"},
  {"key":"wd","value":"1707x822","domain":"facebook.com","path":"/","hostOnly":false,"creation":"2025-01-23T07:59:23.668Z","lastAccessed":"2025-01-23T07:59:23.668Z"},
  {"key":"presence","value":"C%7B%22t3%22%3A%5B%5D%2C%22utc3%22%3A1737618474523%2C%22v%22%3A1%7D","domain":"facebook.com","path":"/","hostOnly":false,"creation":"2025-01-23T07:59:23.668Z","lastAccessed":"2025-01-23T07:59:23.668Z"}
];

// Convert cookies array to a string
const cookiesString = cookies.map(cookie => `${cookie.key}=${cookie.value}`).join('; ');

const shareUrl = 'https://www.facebook.com/share/15dLqe5JCP/';
let sharedCount = 0;
const shareCount = 10;
const timeInterval = 4000;

const sharePost = async () => {
  try {
    // Make a request to the Facebook Graph API to share a post
    const response = await c3cUtility.post(
      'https://graph.facebook.com/me/feed',
      {
        link: shareUrl,
        privacy: { value: 'SELF' },
        no_story: true,
      },
      {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
          'Cookie': cookiesString
        }
      }
    );

    sharedCount++;
    console.log(`Post shared: ${sharedCount}`);

    if (sharedCount === shareCount) {
      clearInterval(timer);
      console.log('Finished sharing posts.');
      process.exit(0); // Exit the process once done
    }
  } catch (error) {
    console.error('Failed to share post:', error.response.data);
  }
};

const timer = setInterval(sharePost, timeInterval);

// Start sharing immediately
const startSharing = async () => {
  await sharePost(); // Initial call
  setInterval(sharePost, timeInterval); // Subsequent calls
};

startSharing();
