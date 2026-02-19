"""Naver session management with cookie backup"""
import json
import pickle
import logging
import time
from pathlib import Path
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SessionManager:
    """Manage Naver login session with cookie backup"""
    
    def __init__(self, cookie_file: str = ".naver_cookies.pkl"):
        self.cookie_file = Path(cookie_file)
    
    def save_cookies(self, driver):
        """Save cookies from driver"""
        try:
            cookies = driver.get_cookies()
            
            # Save with timestamp
            data = {
                'cookies': cookies,
                'saved_at': datetime.now().isoformat(),
                'user_agent': driver.execute_script("return navigator.userAgent")
            }
            
            self.cookie_file.write_bytes(pickle.dumps(data))
            logger.info(f"Cookies saved: {len(cookies)} items")
            
        except Exception as e:
            logger.error(f"Failed to save cookies: {e}")
    
    def load_cookies(self, driver) -> bool:
        """Load cookies into driver"""
        if not self.cookie_file.exists():
            logger.warning("No cookie file found")
            return False
        
        try:
            data = pickle.loads(self.cookie_file.read_bytes())
            cookies = data['cookies']
            saved_at = datetime.fromisoformat(data['saved_at'])
            
            # Check if cookies are too old (30 days)
            if datetime.now() - saved_at > timedelta(days=30):
                logger.warning("Cookies expired (>30 days)")
                return False
            
            # Navigate to domain first
            driver.get("https://naver.com")
            
            # Load cookies
            for cookie in cookies:
                try:
                    # Remove expiry for persistent cookies
                    if 'expiry' in cookie:
                        del cookie['expiry']
                    driver.add_cookie(cookie)
                except Exception as e:
                    logger.debug(f"Skipped cookie: {e}")
            
            logger.info(f"Cookies loaded: {len(cookies)} items (saved {saved_at})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load cookies: {e}")
            return False
    
    def is_logged_in(self, driver) -> bool:
        """Check if still logged in to Naver"""
        try:
            # Simple check: Try to access blog write page
            # If logged in, it will work; if not, it will redirect to login
            test_url = "https://blog.naver.com/ridyservice"
            driver.get(test_url)
            time.sleep(2)
            
            current_url = driver.current_url
            
            # If we're on the blog page (not redirected to login), we're logged in
            if "blog.naver.com" in current_url and "nid.naver.com" not in current_url:
                logger.info("✅ Already logged in")
                return True
            
            logger.warning("❌ Not logged in")
            return False
            
        except Exception as e:
            logger.error(f"Login check failed: {e}")
            return False
    
    def ensure_login(self, driver) -> bool:
        """
        Ensure driver is logged in, using cookies if available
        
        Returns:
            bool: True if logged in, False if manual login required
        """
        # Try loading cookies
        if self.load_cookies(driver):
            if self.is_logged_in(driver):
                return True
        
        # Manual login required
        logger.warning("Manual login required")
        return False
