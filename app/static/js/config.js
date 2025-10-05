// Configuration file for Google Forms integration and other external services
const CONFIG = {
    // Google Forms Survey Configuration - YOUR ACTUAL SURVEY
    FEEDBACK_FORM_URL: 'https://docs.google.com/forms/d/e/1FAIpQLSfjqhqiC3mDT3UU2R5oupe08Kr5ESuNTseKPQbEbwjPMumnRw/viewform',
    
    // Form configuration
    FORM_CONFIG: {
        // If your form supports pre-filling, you can add entry IDs here
        // Get these by inspecting your form's HTML or using the pre-filled URL feature
        TEAM_COUNT_ENTRY: 'entry.123456789',     // Replace with actual entry ID for team count
        ALGORITHM_ENTRY: 'entry.987654321',      // Replace with actual entry ID for algorithm
        TIMESTAMP_ENTRY: 'entry.456789123',      // Replace with actual entry ID for timestamp
        RESULTS_ENTRY: 'entry.789123456'         // Replace with actual entry ID for results data
    },
    
    // Application settings
    APP_CONFIG: {
        SHOW_FEEDBACK_AFTER_RESULTS: true,       // Show feedback section after team formation
        AUTO_COPY_RESULTS: false,                // Automatically copy results to clipboard
        ENABLE_PDF_DOWNLOAD: false,              // Enable PDF download (requires implementation)
        ENABLE_SHARE_API: true                   // Enable Web Share API if available
    }
};

// Export configuration for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
}