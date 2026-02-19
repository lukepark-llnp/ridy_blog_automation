"""Naver blog publisher using Selenium"""
import time
import logging
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from config import settings
from session_manager import SessionManager

logger = logging.getLogger(__name__)


class NaverBlogPublisher:
    """Automated Naver blog publishing with session management"""
    
    def __init__(self):
        self.blog_url = settings.naver_blog_url
        self.profile_path = settings.chrome_profile_path
        self.driver = None
        self.session_manager = SessionManager()
    
    def _init_driver(self):
        """Initialize Chrome driver"""
        options = Options()
        
        # Stability options (no user-data-dir for now to avoid crashes)
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1400,1000')
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        # Anti-detection
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Use ChromeDriver (try user bin first, then homebrew)
        import os
        chromedriver_path = os.path.expanduser('~/bin/chromedriver')
        if not os.path.exists(chromedriver_path):
            chromedriver_path = '/opt/homebrew/bin/chromedriver'
        service = Service(chromedriver_path)
        self.driver = webdriver.Chrome(service=service, options=options)
        
        logger.info("Chrome driver initialized")
    
    def login_once(self):
        """
        One-time manual login to save session
        Run this once before automating
        """
        self._init_driver()
        
        try:
            # Go to Naver
            self.driver.get("https://naver.com")
            logger.info("Opening Naver for manual login...")
            logger.info("Please log in manually in the browser window.")
            logger.info("After logging in, press Enter here to save the session.")
            
            input("\nPress Enter after logging in...")
            
            # Save cookies
            self.session_manager.save_cookies(self.driver)
            
            # Test if logged in
            self.driver.get(self.blog_url)
            time.sleep(2)
            
            if "blog.naver.com" in self.driver.current_url:
                logger.info("✅ Login successful! Session & cookies saved.")
            else:
                logger.warning("⚠️ Could not verify login. Please try again.")
                
        finally:
            if self.driver:
                self.driver.quit()
    
    def publish(self, title: str, html_content: str, images: list[Path], footer_images: list[Path] = None) -> str:
        """
        Publish blog post with images
        
        Args:
            title: Blog post title
            html_content: HTML content
            images: List of image file paths (watermarked photos)
            footer_images: List of footer image paths (고정 배너)
            
        Returns:
            Published blog post URL
        """
        if footer_images is None:
            footer_images = []
        
        # Combine main images + footer images
        all_images = list(images) + list(footer_images)
        self._init_driver()
        
        try:
            # Ensure logged in
            if not self.session_manager.ensure_login(self.driver):
                raise Exception(
                    "네이버 로그인이 필요합니다.\n\n"
                    "다음 명령어를 실행해주세요:\n"
                    "python3 naver_publisher.py"
                )
            
            logger.info("✅ Login verified")
            # Navigate to blog write page
            write_url = f"{self.blog_url}/PostWriteForm.naver"
            self.driver.get(write_url)
            logger.info(f"Navigating to: {write_url}")
            logger.info(f"Total images to upload: {len(all_images)} (main: {len(images)}, footer: {len(footer_images)})")
            
            # Wait for editor to load
            wait = WebDriverWait(self.driver, 15)
            
            # Switch to editor iframe (Naver uses iframe for editor)
            iframe = wait.until(
                EC.presence_of_element_located((By.ID, "mainFrame"))
            )
            self.driver.switch_to.frame(iframe)
            
            # Fill title
            title_input = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input.se-input"))
            )
            title_input.clear()
            title_input.send_keys(title)
            logger.info(f"Title entered: {title}")
            
            # Select category
            try:
                # Click category dropdown (selector may need adjustment)
                category_btn = self.driver.find_element(By.XPATH, "//button[contains(@class, 'category') or contains(text(), '카테고리')]")
                category_btn.click()
                logger.info("Category dropdown clicked")
                time.sleep(1)
                
                # Find and click the target category
                target_category = settings.naver_blog_category
                category_option = wait.until(
                    EC.element_to_be_clickable((By.XPATH, f"//a[contains(text(), '{target_category}') or @title='{target_category}']"))
                )
                category_option.click()
                logger.info(f"Category selected: {target_category}")
                time.sleep(1)
            except Exception as cat_error:
                logger.warning(f"Category selection failed (will use default): {cat_error}")
                # Continue anyway - post will go to default category
            
            # Switch to content editor iframe
            content_iframe = wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "se-component-content"))
            )
            self.driver.switch_to.frame(content_iframe)
            
            # Insert HTML content
            # (Naver editor usually needs content pasted or typed)
            # For images, use file upload
            
            # TODO: Implement image upload logic
            # Naver blog editor has specific upload flow
            # This is a placeholder - needs actual implementation
            
            logger.warning("⚠️ Image upload not yet fully implemented")
            logger.info("Manual step required: Upload images via UI")
            
            # Insert text content (simplified)
            editor_body = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[contenteditable='true']"))
            )
            
            # Simple text insertion (HTML support varies)
            self.driver.execute_script(
                "arguments[0].innerHTML = arguments[1];",
                editor_body,
                html_content
            )
            logger.info("Content inserted")
            
            # Switch back to main frame
            self.driver.switch_to.default_content()
            
            # Find and click publish button
            # (Button selector needs verification with actual Naver blog UI)
            publish_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '발행')]"))
            )
            publish_btn.click()
            logger.info("Publish button clicked")
            
            # Wait for publish to complete
            time.sleep(3)
            
            # Get published URL
            published_url = self.driver.current_url
            logger.info(f"✅ Published: {published_url}")
            
            return published_url
            
        except Exception as e:
            logger.error(f"Publishing failed: {e}")
            
            # Take screenshot for debugging
            screenshot_path = Path(settings.output_dir) / "error_screenshot.png"
            screenshot_path.parent.mkdir(parents=True, exist_ok=True)
            self.driver.save_screenshot(str(screenshot_path))
            logger.info(f"Error screenshot saved: {screenshot_path}")
            
            raise
            
        finally:
            if self.driver:
                self.driver.quit()


# CLI for one-time login setup
if __name__ == "__main__":
    print("🔐 Naver Blog Login Setup")
    print("=" * 50)
    publisher = NaverBlogPublisher()
    publisher.login_once()
