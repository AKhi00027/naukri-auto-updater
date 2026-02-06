# Naukri Auto-Updater 🚀

Automated Selenium script to update your Naukri.com profile daily, keeping it on top of recruiter searches.

## Why Use This?

Naukri.com's algorithm prioritizes recently updated profiles in recruiter searches. This automation:
- **Updates your profile daily at 9 AM** (customizable)
- **Keeps you visible** to recruiters actively searching
- **Requires zero manual effort** once set up
- **Uses subtle changes** (adding/removing spaces) that don't alter your profile content
- **Built by a QA Engineer** with production-grade error handling

## Features

✅ Automated daily profile updates
✅ Randomized timing to appear natural (±15 minutes)
✅ Multiple fallback update strategies
✅ Comprehensive logging
✅ Headless browser operation
✅ macOS cron/launchd scheduling
✅ Secure credential management

## Prerequisites

- **Python 3.7+**
- **Google Chrome browser**
- **ChromeDriver** (matching your Chrome version)
- **macOS** (adapts easily to Linux/Windows)

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/AKhi00027/naukri-auto-updater.git
cd naukri-auto-updater
```

### 2. Install Dependencies

```bash
# Install Python packages
pip3 install selenium

# Or use requirements.txt
echo "selenium==4.15.2" > requirements.txt
pip3 install -r requirements.txt
```

### 3. Download ChromeDriver

**Option 1: Manual Download**
```bash
# Check your Chrome version: Chrome > About Chrome
# Download matching ChromeDriver from:
# https://chromedriver.chromium.org/downloads

# Move to PATH
sudo mv chromedriver /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
```

**Option 2: Auto-manage (Recommended)**
```bash
pip3 install webdriver-manager
```

Then update line 42 in `naukri_auto_update.py`:
```python
from webdriver_manager.chrome import ChromeDriverManager
service = Service(ChromeDriverManager().install())
self.driver = webdriver.Chrome(service=service, options=chrome_options)
```

### 4. Configure Credentials

**Option A: Using config.json (Recommended)**

```bash
cp config.json.template config.json
nano config.json
```

Update with your credentials:
```json
{
  "email": "your_naukri_email@gmail.com",
  "password": "your_password",
  "update_time": "09:00",
  "randomize_minutes": 15
}
```

**Option B: Using Environment Variables**

```bash
# Add to ~/.zshrc or ~/.bash_profile
export NAUKRI_EMAIL="your_email@gmail.com"
export NAUKRI_PASSWORD="your_password"

source ~/.zshrc
```

### 5. Test Run

```bash
python3 naukri_auto_update.py
```

You should see:
```
✅ Profile updated at 2026-02-06 21:15:32
```

### 6. Schedule Daily Updates

#### Option A: Cron (Simple)

```bash
# Edit crontab
crontab -e

# Add this line (runs daily at 9 AM)
0 9 * * * cd /path/to/naukri-auto-updater && /usr/local/bin/python3 naukri_auto_update.py

# View scheduled jobs
crontab -l
```

#### Option B: launchd (Recommended for macOS)

Create `~/Library/LaunchAgents/com.naukri.autoupdate.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.naukri.autoupdate</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/Users/YOUR_USERNAME/naukri-auto-updater/naukri_auto_update.py</string>
    </array>
    
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    
    <key>StandardOutPath</key>
    <string>/Users/YOUR_USERNAME/naukri-auto-updater/stdout.log</string>
    
    <key>StandardErrorPath</key>
    <string>/Users/YOUR_USERNAME/naukri-auto-updater/stderr.log</string>
</dict>
</plist>
```

Load the job:
```bash
launchctl load ~/Library/LaunchAgents/com.naukri.autoupdate.plist

# Test immediately
launchctl start com.naukri.autoupdate

# Check status
launchctl list | grep naukri
```

## How It Works

1. **Login**: Securely logs into your Naukri account
2. **Navigate**: Goes to your profile page
3. **Update**: Makes a minor change (adds/removes trailing space in resume headline)
4. **Save**: Clicks save, refreshing the "Last Updated" timestamp
5. **Close**: Exits browser and logs success

### Update Strategies (with fallbacks)

1. **Primary**: Update Resume Headline (most effective)
2. **Fallback**: Edit Key Skills section
3. **Additional**: Can extend to Profile Summary, etc.

## Monitoring

### View Logs

```bash
# Application logs
tail -f ~/naukri_updates.log

# launchd logs (if using Option B)
tail -f ~/naukri-auto-updater/stdout.log
tail -f ~/naukri-auto-updater/stderr.log
```

### Email Alerts (Optional)

Add to `naukri_auto_update.py`:

```python
import smtplib
from email.mime.text import MIMEText

def send_alert(status, message):
    msg = MIMEText(f"Naukri Update {status}: {message}")
    msg['Subject'] = f'Naukri Auto-Update {status}'
    msg['From'] = 'your_email@gmail.com'
    msg['To'] = 'your_email@gmail.com'
    
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login('your_email@gmail.com', 'app_password')
        smtp.send_message(msg)
```

## Security Best Practices

⚠️ **NEVER commit credentials to Git**

```bash
# Create .gitignore
echo "config.json" >> .gitignore
echo "*.log" >> .gitignore
echo "__pycache__/" >> .gitignore
```

## Troubleshooting

### "ChromeDriver version mismatch"
```bash
# Check Chrome version
google-chrome --version

# Download matching ChromeDriver
# Or use webdriver-manager (auto-updates)
```

### "Login failed"
- Verify credentials in config.json
- Check if Naukri added CAPTCHA
- Try manual login first to ensure account is accessible

### "Script runs but profile not updated"
- Check logs: `tail -f ~/naukri_updates.log`
- Run in non-headless mode (comment out `--headless` line)
- Verify XPath selectors haven't changed

### Cron job not running
```bash
# Check cron syntax
crontab -l

# Use absolute paths
which python3  # Use this path in crontab
pwd  # Use full path to script
```

## Project Structure

```
naukri-auto-updater/
├── naukri_auto_update.py      # Main script
├── config.json.template       # Configuration template
├── requirements.txt           # Python dependencies (create this)
├── README.md                  # This file
├── .gitignore                # Git ignore patterns
└── logs/                     # Auto-generated logs
```

## Contributing

Feel free to:
- Report issues
- Suggest improvements
- Submit pull requests

This is a personal automation project, contributions welcome!

## Legal & Ethical Considerations

- ✅ **Automates your own profile** (not scraping data)
- ✅ **Makes legitimate updates** (subtle formatting changes)
- ✅ **Respects rate limits** (once daily with randomization)
- ⚠️ Review Naukri.com's Terms of Service
- ⚠️ Use responsibly

## Author

**Akhilesh Kumar Singh**
- Senior Software Engineer - Test @ Trucaller
- QA Automation Expert | Selenium, Appium, Playwright
- [GitHub Profile](https://github.com/AKhi00027)

## License

MIT License - Feel free to use and modify

## Acknowledgments

- Built with Selenium WebDriver
- Inspired by the need for better recruiter visibility
- Designed for QA engineers and automation enthusiasts

---

**⭐ Star this repo if it helped you land more interviews!**
