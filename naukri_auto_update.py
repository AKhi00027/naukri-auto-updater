#!/usr/bin/env python3
"""
Naukri Profile Auto-Update Script
Author: Akhilesh Kumar Singh
Purpose: Daily profile update to stay on top of recruiter searches
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
import time
import random
from datetime import datetime
import logging
import json
import os

# Setup logging
LOG_FILE = os.path.expanduser('~/naukri_updates.log')
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class NaukriAutoUpdater:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.driver = None
        
    def setup_driver(self):
        """Initialize Chrome driver with options"""
        chrome_options = Options()
        # Run in headless mode (no browser window)
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.maximize_window()
        logging.info("Chrome driver initialized")
        
    def login(self):
        """Login to Naukri"""
        try:
            self.driver.get('https://www.naukri.com/nlogin/login')
            time.sleep(2)
            
            # Enter email
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "usernameField"))
            )
            email_field.send_keys(self.email)
            
            # Enter password
            password_field = self.driver.find_element(By.ID, "passwordField")
            password_field.send_keys(self.password)
            
            # Click login button
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            # Wait for login to complete
            time.sleep(5)
            logging.info("Login successful")
            return True
            
        except Exception as e:
            logging.error(f"Login failed: {str(e)}")
            return False
    
    def update_profile(self):
        """Make minor updates to profile"""
        try:
            # Navigate to profile page
            self.driver.get('https://www.naukri.com/mnjuser/profile')
            time.sleep(3)
            
            # Strategy 1: Update Resume Headline (most effective)
            self.update_resume_headline()
            
            # Add random delay to appear natural
            time.sleep(random.randint(2, 5))
            
            logging.info("Profile updated successfully")
            return True
            
        except Exception as e:
            logging.error(f"Profile update failed: {str(e)}")
            return False
    
    def update_resume_headline(self):
        """Update resume headline with minor change"""
        try:
            # Click edit button for resume headline
            edit_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@id='lazyResumeHead']//span[contains(@class, 'edit')]"))
            )
            edit_button.click()
            time.sleep(2)
            
            # Find the headline text area
            headline_textarea = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//textarea[contains(@id, 'resumeHeadlineTxt')]"))
            )
            
            # Get current text
            current_text = headline_textarea.get_attribute('value')
            
            # Make a minor change (add/remove space at the end)
            if current_text.endswith(' '):
                new_text = current_text.rstrip()
            else:
                new_text = current_text + ' '
            
            # Clear and enter new text
            headline_textarea.clear()
            headline_textarea.send_keys(new_text)
            time.sleep(1)
            
            # Click save button
            save_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Save')]")
            save_button.click()
            time.sleep(2)
            
            logging.info("Resume headline updated")
            
        except Exception as e:
            logging.error(f"Resume headline update failed: {str(e)}")
            # Try alternative strategy
            self.update_key_skills()
    
    def update_key_skills(self):
        """Alternative: Reorder key skills"""
        try:
            # Click edit button for key skills
            edit_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@id='lazyKeySkills']//span[contains(@class, 'edit')]"))
            )
            edit_button.click()
            time.sleep(2)
            
            # Just click save without changes (still updates timestamp)
            save_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Save')]")
            save_button.click()
            time.sleep(2)
            
            logging.info("Key skills section updated")
            
        except Exception as e:
            logging.error(f"Key skills update failed: {str(e)}")
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            logging.info("Browser closed")

def load_config():
    """Load configuration from config.json"""
    config_path = os.path.expanduser('~/naukri_auto_update/config.json')
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    return None

def main():
    """Main execution function"""
    # Load config or use environment variables
    config = load_config()
    
    if config:
        EMAIL = config.get('email')
        PASSWORD = config.get('password')
        RANDOMIZE_MINUTES = config.get('randomize_minutes', 15)
    else:
        # Use environment variables
        EMAIL = os.getenv('NAUKRI_EMAIL')
        PASSWORD = os.getenv('NAUKRI_PASSWORD')
        RANDOMIZE_MINUTES = 15
    
    if not EMAIL or not PASSWORD:
        logging.error("Email or password not configured")
        print("❌ Error: Email or password not configured")
        return
    
    # Add randomization to timing (±15 minutes by default)
    random_delay = random.randint(0, RANDOMIZE_MINUTES * 60)
    time.sleep(random_delay)
    
    updater = NaukriAutoUpdater(EMAIL, PASSWORD)
    
    try:
        logging.info("=== Starting Naukri Auto Update ===")
        
        updater.setup_driver()
        
        if updater.login():
            updater.update_profile()
            logging.info("Update completed successfully")
            print(f"✅ Profile updated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            logging.error("Login failed, update aborted")
            print("❌ Update failed - check logs")
            
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        print(f"❌ Error: {str(e)}")
        
    finally:
        updater.close()

if __name__ == "__main__":
    main()
