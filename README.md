# Google Large Screen Quality Guidelines Monitor

A automated webpage content monitoring system that tracks changes to Android's Adaptive App Quality Guidelines and sends email notifications when updates are detected.

## Overview

This project monitors 8 Android developer documentation pages for content changes:

- [Adaptive App Quality Guidelines](https://developer.android.com/docs/quality-guidelines/adaptive-app-quality)
- [Tier 3 - Adaptive Ready](https://developer.android.com/docs/quality-guidelines/adaptive-app-quality/tier-3)
- [Tier 2 - Adaptive Optimized](https://developer.android.com/docs/quality-guidelines/adaptive-app-quality/tier-2)
- [Tier 1 - Adaptive Differentiated](https://developer.android.com/docs/quality-guidelines/adaptive-app-quality/tier-1)
- [Desktop Experiences](https://developer.android.com/docs/quality-guidelines/adaptive-app-quality/experiences/desktop)
- [Foldables Experiences](https://developer.android.com/docs/quality-guidelines/adaptive-app-quality/experiences/foldables)
- [Camera & Audio Experiences](https://developer.android.com/docs/quality-guidelines/adaptive-app-quality/experiences/camera-audio)
- [Stylus Experiences](https://developer.android.com/docs/quality-guidelines/adaptive-app-quality/experiences/stylus)

## Features

- **Automated Monitoring**: GitHub Actions workflow runs daily at 8:00 AM (Asia/Shanghai timezone)
- **Content Extraction**: Uses BeautifulSoup to extract main article content, filtering out navigation, sidebar, and footer elements
- **Change Detection**: Compares current content with stored version using Python's difflib
- **Email Notifications**: Sends consolidated email notifications via Gmail SMTP when changes are detected
- **Version Tracking**: Each URL's content is stored in a separate Markdown file for historical tracking

## Project Structure

```
GoogleLargeScreenQualityGuidelines/
├── monitor.py              # Main Python monitoring script
├── requirements.txt        # Python dependencies
├── content.md              # Main page content snapshot
├── tier-3.md               # Tier 3 guidelines content
├── tier-2.md               # Tier 2 guidelines content
├── tier-1.md               # Tier 1 guidelines content
├── desktop.md              # Desktop experiences content
├── foldables.md            # Foldables experiences content
├── camera-audio.md         # Camera & Audio experiences content
├── stylus.md               # Stylus experiences content
├── README.md               # This file
└── .github/
    └── workflows/
        └── monitor.yml     # GitHub Actions workflow configuration
```

## Setup

### Prerequisites

- Python 3.11+
- Gmail account with App Password enabled

### GitHub Secrets Configuration

Before the workflow can send email notifications, configure the following secrets in your repository:

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Add the following repository secrets:

| Secret Name | Description |
|-------------|-------------|
| `GMAIL_USER` | Your Gmail email address (used for SMTP authentication) |
| `GMAIL_PASS` | Gmail App Password (not your regular password) |
| `GMAIL_TO` | Recipient email addresses, comma-separated (e.g., `user1@example.com,user2@example.com`). If not set, emails are sent to GMAIL_USER |

To generate a Gmail App Password:
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable 2-Step Verification
3. Navigate to App Passwords
4. Generate a new app password for this project

### Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GMAIL_USER="your-email@gmail.com"
export GMAIL_PASS="your-app-password"
export GMAIL_TO="recipient1@example.com,recipient2@example.com"  # Optional: comma-separated recipients

# Run the monitor
python monitor.py
```

## Workflow Behavior

1. **First Run**: Saves initial content snapshots without sending notifications (establishes baseline)
2. **Daily Check**: Compares current webpage content with stored snapshots
3. **Change Detected**: Sends consolidated email with diffs for all changed URLs
4. **Commit Changes**: Automatically commits updated content files to the repository

## Manual Trigger

The GitHub Actions workflow can be manually triggered from the Actions page in your repository for testing purposes.

## License

This project is for monitoring publicly available Android developer documentation.