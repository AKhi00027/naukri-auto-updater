#!/usr/bin/env python3
"""
Naukri Profile Auto-Update Script
Author: Akhilesh Kumar Singh
Purpose: Daily profile update to stay on top of recruiter searches
"""

import json
import logging
import os
import random
import smtplib
import time
from datetime import datetime
from email.mime.text import MIMEText

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

# Setup logging
LOG_FILE = os.path.expanduser('~/naukri_updates.log')
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
CONFIG_PATH = os.path.expanduser('~/naukri_auto_update/config.json')

class NaukriAutoUpdater:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.driver = None

    def _safe_click(self, element):
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});",
            element,
        )
        try:
            element.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", element)

    def _pick_variant(self, current_text, variants):
        if not variants:
            return None
        normalized = [
            v.strip()
            for v in variants
            if isinstance(v, str) and v.strip()
        ]
        if not normalized:
            return None
        current = (current_text or "").strip()
        candidates = [v for v in normalized if v != current]
        return random.choice(candidates or normalized)

    def _set_text_value(self, element, value):
        self.driver.execute_script(
            "arguments[0].value = arguments[1];"
            "arguments[0].dispatchEvent(new Event('input', {bubbles: true}));"
            "arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
            element,
            value,
        )

    def _find_clickable(self, selectors, timeout=12):
        if not selectors:
            raise ValueError("No selectors provided")
        end_time = time.time() + timeout
        last_exc = None
        while time.time() < end_time:
            for by, selector in selectors:
                try:
                    elements = self.driver.find_elements(by, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            logging.info("Found clickable element: %s %s", by, selector)
                            return element
                except Exception as e:
                    last_exc = e
            time.sleep(0.2)
        if last_exc:
            raise last_exc
        raise TimeoutException(f"No clickable element found for selectors: {selectors}")

    def _find_visible(self, selectors, timeout=12):
        if not selectors:
            raise ValueError("No selectors provided")
        last_exc = None
        for by, selector in selectors:
            try:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.visibility_of_element_located((by, selector))
                )
                logging.info("Found visible element: %s %s", by, selector)
                return element
            except Exception as e:
                last_exc = e
        raise last_exc

    def _dump_debug(self, label):
        try:
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            debug_dir = os.path.expanduser('~/naukri_auto_update/debug')
            os.makedirs(debug_dir, exist_ok=True)
            base = os.path.join(debug_dir, f"{label}_{ts}")
            self.driver.save_screenshot(base + ".png")
            with open(base + ".html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            logging.info("Saved debug files: %s(.png/.html)", base)
        except Exception as e:
            logging.error("Failed to save debug files: %s", repr(e))

    def _is_login_page(self):
        try:
            if "nlogin" in (self.driver.current_url or ""):
                return True
            return bool(self.driver.find_elements(By.ID, "usernameField"))
        except Exception:
            return False

    def _setup_firefox(self, config):
        firefox_options = FirefoxOptions()
        # Run in headless mode (no browser window)
        # firefox_options.add_argument('-headless')
        firefox_options.add_argument('--width=1280')
        firefox_options.add_argument('--height=800')
        firefox_options.set_preference("dom.webnotifications.enabled", False)
        firefox_options.set_preference("dom.push.enabled", False)

        firefox_binary = config.get('firefox_binary')
        geckodriver_path = config.get('geckodriver_path')
        if firefox_binary:
            firefox_options.binary_location = firefox_binary
        if geckodriver_path:
            service = FirefoxService(geckodriver_path)
            self.driver = webdriver.Firefox(service=service, options=firefox_options)
        else:
            self.driver = webdriver.Firefox(options=firefox_options)
        logging.info("Firefox driver initialized")

    def _setup_chrome(self, config):
        chrome_options = Options()
        # Run in headless mode (no browser window)
        # chrome_options.add_argument('--headless')
        chrome_options.add_argument('--window-size=1280,800')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-notifications')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-software-rasterizer')
        driver_path = config.get('chromedriver_path')
        chrome_binary = config.get('chrome_binary')
        profile_dir = config.get('chrome_profile_dir')
        logging.info(
            "Chrome launch config binary=%s driver=%s profile=%s",
            chrome_binary,
            driver_path,
            profile_dir,
        )
        if chrome_binary:
            chrome_options.binary_location = chrome_binary
        if profile_dir:
            os.makedirs(profile_dir, exist_ok=True)
            chrome_options.add_argument(f'--user-data-dir={profile_dir}')
            chrome_options.add_argument('--no-first-run')
            chrome_options.add_argument('--no-default-browser-check')
        if driver_path:
            service = Service(driver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            self.driver = webdriver.Chrome(options=chrome_options)
        logging.info("Chrome driver initialized")

    def setup_driver(self, browser_override=None, allow_fallback=True):
        """Initialize browser driver with options"""
        config = load_config() or {}
        browser = (browser_override or config.get('browser') or 'chrome').lower()
        fallback_browser = (config.get('fallback_browser') or 'firefox').lower()
        logging.info("Browser selected: %s", browser)

        if browser == 'firefox':
            self._setup_firefox(config)
            return

        try:
            self._setup_chrome(config)
        except Exception as e:
            logging.error("Chrome driver init failed: %s", repr(e))
            if allow_fallback and fallback_browser == 'firefox':
                logging.info("Falling back to Firefox driver")
                self._setup_firefox(config)
            else:
                raise
        
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
    
    def update_profile(self, headline_variants=None, summary_variants=None):
        """Make minor updates to profile"""
        try:
            # Navigate to profile page
            self.driver.get('https://www.naukri.com/mnjuser/profile')
            time.sleep(3)
            logging.info("Profile page url=%s title=%s", self.driver.current_url, self.driver.title)
            if self._is_login_page():
                logging.error("Login required; profile page not accessible")
                self._dump_debug("login_required")
                return False
            if "captcha" in (self.driver.page_source or "").lower():
                logging.error("Captcha detected; manual intervention required")
                self._dump_debug("captcha")
                return False

            tasks = [
                lambda: self.update_resume_headline(headline_variants),
                lambda: self.update_profile_summary(summary_variants),
            ]
            random.shuffle(tasks)

            for task in tasks:
                if task():
                    logging.info("Profile updated successfully")
                    return True
                # Add random delay to appear natural
                time.sleep(random.randint(2, 5))

            if self.update_key_skills():
                logging.info("Profile updated successfully via key skills")
                return True

            logging.error("Profile update failed")
            return False
        except Exception as e:
            logging.error(f"Profile update failed: {str(e)}")
            return False
    
    def update_resume_headline(self, variants=None):
        """Update resume headline with minor change"""
        try:
            # Click edit button for resume headline
            edit_button = self._find_clickable([
                (By.XPATH, "//div[@id='lazyResumeHead']//span[contains(@class, 'edit')]"),
                (By.XPATH, "//div[contains(., 'Resume Headline')]//span[contains(@class, 'edit')]"),
                (By.XPATH, "//button[contains(@class, 'edit') and ancestor::*[contains(., 'Resume Headline')]]"),
            ])
            self._safe_click(edit_button)
            time.sleep(1)
            
            # Find the headline text area
            headline_textarea = self._find_visible([
                (By.XPATH, "//textarea[contains(@id, 'resumeHeadlineTxt') or contains(@id, 'resumeHeadline') or contains(@name, 'resumeHeadline')]"),
                (By.XPATH, "//textarea[contains(@placeholder, 'headline') or contains(@placeholder, 'Headline')]"),
            ])
            self._safe_click(headline_textarea)
            
            # Get current text
            current_text = headline_textarea.get_attribute('value')
            
            new_text = self._pick_variant(current_text, variants)
            if not new_text:
                # Make a minor change (add/remove space at the end)
                if current_text.endswith(' '):
                    new_text = current_text.rstrip()
                else:
                    new_text = current_text + ' '
            
            # Clear and enter new text
            self._set_text_value(headline_textarea, new_text)
            time.sleep(1)
            
            # Click save button
            save_button = self._find_clickable([
                (By.XPATH, "//div[contains(@class, 'resumeHeadlineEdit') and contains(@class, 'flipOpen')]//button[contains(., 'Save') or contains(., 'SAVE')]"),
                (By.XPATH, "//form[@name='resumeHeadlineForm']//button[contains(., 'Save') or contains(., 'SAVE')]"),
                (By.XPATH, "//button[contains(., 'Save') or contains(., 'SAVE')]"),
            ])
            self._safe_click(save_button)
            time.sleep(2)
            
            logging.info("Resume headline updated")
            return True
            
        except Exception as e:
            logging.error("Resume headline update failed: %s", repr(e))
            self._dump_debug("resume_headline_failed")
            return False

    def update_profile_summary(self, variants=None):
        """Update profile summary with a variant"""
        try:
            if not variants:
                logging.info("No profile summary variants configured; skipping")
                return False

            edit_button = self._find_clickable([
                (By.XPATH, "//div[@id='lazyProfileSummary']//span[contains(@class, 'edit')]"),
                (By.XPATH, "//div[contains(., 'Profile Summary')]//span[contains(@class, 'edit')]"),
                (By.XPATH, "//button[contains(@class, 'edit') and ancestor::*[contains(., 'Profile Summary')]]"),
            ])
            self._safe_click(edit_button)
            time.sleep(1)

            summary_textarea = self._find_visible([
                (By.XPATH, "//textarea[contains(@id, 'profileSummaryTxt') or contains(@id, 'profileSummary') or contains(@name, 'profileSummary')]"),
                (By.XPATH, "//textarea[contains(@placeholder, 'Summary') or contains(@placeholder, 'summary')]"),
            ])
            self._safe_click(summary_textarea)

            current_text = summary_textarea.get_attribute('value')
            new_text = self._pick_variant(current_text, variants)
            if not new_text:
                logging.info("No alternate profile summary variant; skipping")
                return False

            self._set_text_value(summary_textarea, new_text)
            time.sleep(1)

            save_button = self._find_clickable([
                (By.XPATH, "//div[contains(@class, 'keySkillsEdit') and contains(@class, 'flipOpen')]//button[@id='saveKeySkills']"),
                (By.XPATH, "//form[@name='keySkillsForm']//button[@id='saveKeySkills']"),
                (By.XPATH, "//div[contains(@class, 'keySkillsEdit') and contains(@class, 'flipOpen')]//button[contains(., 'Save') or contains(., 'SAVE')]"),
            ])
            self._safe_click(save_button)
            time.sleep(2)

            logging.info("Profile summary updated")
            return True
        except Exception as e:
            logging.error("Profile summary update failed: %s", repr(e))
            self._dump_debug("profile_summary_failed")
            return False
    
    def update_key_skills(self):
        """Alternative: Reorder key skills"""
        try:
            # Click edit button for key skills
            edit_button = self._find_clickable([
                (By.XPATH, "//div[@id='lazyKeySkills']//span[contains(@class, 'edit')]"),
                (By.XPATH, "//div[contains(., 'Key skills') or contains(., 'Key Skills')]//span[contains(@class, 'edit')]"),
                (By.XPATH, "//button[contains(@class, 'edit') and ancestor::*[contains(., 'Key skills') or contains(., 'Key Skills')]]"),
            ])
            self._safe_click(edit_button)
            time.sleep(2)
            
            # Just click save without changes (still updates timestamp)
            save_button = self._find_clickable([
                (By.XPATH, "//button[contains(., 'Save') or contains(., 'SAVE')]"),
            ])
            self._safe_click(save_button)
            time.sleep(2)
            
            logging.info("Key skills section updated")
            return True
            
        except Exception as e:
            logging.error("Key skills update failed: %s", repr(e))
            self._dump_debug("key_skills_failed")
            return False
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            logging.info("Browser closed")

def load_config():
    """Load configuration from config.json"""
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    return None

def send_alert(status, message, config=None):
    config = config or {}
    alert_from = config.get('alert_from')
    alert_to = config.get('alert_to')
    alert_password = config.get('alert_app_password')
    if not alert_from or not alert_to or not alert_password:
        logging.warning("Alert credentials not configured; skipping email alert")
        return

    msg = MIMEText(f"Naukri Update {status}: {message}")
    msg['Subject'] = f'Naukri Auto-Update {status}'
    msg['From'] = alert_from
    msg['To'] = alert_to

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(alert_from, alert_password)
        smtp.send_message(msg)

def main():
    """Main execution function"""
    # Load config or use environment variables
    config = load_config()
    
    if config:
        EMAIL = config.get('email')
        PASSWORD = config.get('password')
        RANDOMIZE_MINUTES = config.get('randomize_minutes', 15)
        headline_variants = config.get('headline_variants', [])
        summary_variants = config.get('summary_variants', [])
    else:
        # Use environment variables
        EMAIL = os.getenv('NAUKRI_EMAIL')
        PASSWORD = os.getenv('NAUKRI_PASSWORD')
        RANDOMIZE_MINUTES = 15
        headline_variants = []
        summary_variants = []
    alert_config = config or {}
    
    if not EMAIL or not PASSWORD:
        logging.error("Email or password not configured")
        print("❌ Error: Email or password not configured")
        return
    
    # Add randomization to timing (±15 minutes by default)
    random_delay = random.randint(0, RANDOMIZE_MINUTES * 60)
    logging.info(
        "Run triggered ts=%s pid=%s config=%s randomize_minutes=%s random_delay_seconds=%s",
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        os.getpid(),
        CONFIG_PATH,
        RANDOMIZE_MINUTES,
        random_delay,
    )
    time.sleep(random_delay)
    
    updater = NaukriAutoUpdater(EMAIL, PASSWORD)
    browser = (config.get('browser') or 'chrome').lower() if config else 'chrome'
    fallback_browser = (config.get('fallback_browser') or 'firefox').lower() if config else 'firefox'
    fallback_on_failure = config.get('fallback_on_failure', True) if config else True
    
    try:
        logging.info("=== Starting Naukri Auto Update ===")
        
        updated = False
        updater.setup_driver()

        if updater.login():
            updated = updater.update_profile(headline_variants, summary_variants)
        else:
            logging.error("Login failed, update aborted")

        if (
            not updated
            and browser == 'chrome'
            and fallback_on_failure
            and fallback_browser == 'firefox'
        ):
            logging.warning("Chrome update failed; retrying with Firefox fallback")
            updater.close()
            updater.setup_driver(browser_override='firefox', allow_fallback=False)
            if updater.login():
                updated = updater.update_profile(headline_variants, summary_variants)
            else:
                logging.error("Fallback login failed")

        if updated:
            logging.info("Update completed successfully")
            print(f"✅ Profile updated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            send_alert("Success", "Profile updated successfully", alert_config)
        else:
            logging.error("Update failed - profile not updated")
            print("❌ Update failed - check logs")
            send_alert("Failed", "Profile update failed", alert_config)
            
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        print(f"❌ Error: {str(e)}")
        send_alert("Error", str(e), alert_config)
        
    finally:
        updater.close()

if __name__ == "__main__":
    main()
