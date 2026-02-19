"""Naver blog publisher using Selenium - V2 (완전 구현)"""
import time
import logging
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from config import settings
from session_manager import SessionManager

logger = logging.getLogger(__name__)


class NaverBlogPublisherV2:
    """Automated Naver blog publishing with session management"""
    
    def __init__(self):
        self.blog_url = settings.naver_blog_url
        self.blog_id = "ridyservice"
        self.category_no = "28"  # 출고 현황
        self.driver = None
        self.session_manager = SessionManager()
    
    def _init_driver(self):
        """Initialize Chrome driver"""
        options = Options()
        
        # Stability options
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1400,1000')
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        # Anti-detection
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Use ChromeDriver
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
            
            # Navigate to blog write page (with category "출고 현황")
            write_url = f"{self.blog_url}?Redirect=Write&categoryNo={self.category_no}"
            self.driver.get(write_url)
            logger.info(f"Navigating to: {write_url}")
            logger.info(f"Total images to upload: {len(all_images)} (main: {len(images)}, footer: {len(footer_images)})")
            
            # Wait for page to load completely
            time.sleep(3)
            
            # Wait for main frame to load (increased timeout)
            wait = WebDriverWait(self.driver, 30)
            
            try:
                # Debug: Check page source for iframes
                page_source = self.driver.page_source
                iframe_count = page_source.count("<iframe")
                logger.info(f"📄 Page has {iframe_count} iframes")
                
                if "mainFrame" in page_source:
                    logger.info("✅ mainFrame found in page source")
                else:
                    logger.warning("⚠️ mainFrame NOT found in page source!")
                    
                    # Save page source for debugging
                    debug_path = Path(settings.output_dir) / "page_source_debug.html"
                    debug_path.write_text(page_source[:5000], encoding='utf-8')  # First 5000 chars
                    logger.info(f"Page source sample saved: {debug_path}")
                
                # Switch to mainFrame iframe
                logger.info("Waiting for mainFrame iframe...")
                iframe = wait.until(
                    EC.presence_of_element_located((By.ID, "mainFrame"))
                )
                self.driver.switch_to.frame(iframe)
                logger.info("✅ Switched to mainFrame iframe")
                
                # Wait for editor to be ready
                time.sleep(3)
                
                # Check if editor loaded
                wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".se-component.se-documentTitle"))
                )
                logger.info("✅ Editor loaded")
                
            except Exception as iframe_error:
                logger.error(f"Failed to load editor iframe: {iframe_error}")
                # Take screenshot
                screenshot_path = Path(settings.output_dir) / "iframe_error_screenshot.png"
                screenshot_path.parent.mkdir(parents=True, exist_ok=True)
                self.driver.save_screenshot(str(screenshot_path))
                logger.info(f"Screenshot saved: {screenshot_path}")
                
                # Save full page source
                full_source_path = Path(settings.output_dir) / "error_page_source.html"
                full_source_path.write_text(self.driver.page_source, encoding='utf-8')
                logger.info(f"Full page source saved: {full_source_path}")
                
                raise Exception(f"에디터 로딩 실패: {iframe_error}")
            
            # === 1. Fill title ===
            self._fill_title(wait, title)
            
            # === 2. Upload images ===
            self._upload_images(wait, all_images)
            
            # === 3. Add text content (if any) ===
            # For now, we rely on images; text can be added if needed
            
            # === 4. Publish ===
            published_url = self._publish_post(wait)
            
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
                # Don't quit immediately - wait for confirmation
                logger.info("Waiting 3s before closing browser...")
                time.sleep(3)
                self.driver.quit()
    
    def _close_all_popups(self):
        """Close all popups/overlays that might block interactions"""
        try:
            # Close help panel
            close_buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                ".se-help-panel-close-button, .se-popup-button-close, .se-popup-button-cancel")
            for btn in close_buttons:
                try:
                    if btn.is_displayed():
                        btn.click()
                        time.sleep(0.3)
                        logger.info("  → Closed popup/help panel")
                except:
                    pass
            
            # Hide popup overlays with JavaScript
            self.driver.execute_script("""
                document.querySelectorAll('.se-popup-dim, .se-popup-container, .se-help-panel').forEach(el => {
                    el.style.display = 'none';
                });
            """)
            logger.info("  → Hidden all popup overlays")
            
        except Exception as e:
            logger.warning(f"Could not close popups: {e}")
    
    def _fill_title(self, wait, title: str):
        """Fill blog post title"""
        try:
            logger.info("Filling title...")
            
            # Close any popups first
            self._close_all_popups()
            
            # Find title component
            title_component = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".se-component.se-documentTitle"))
            )
            logger.info("  → Title component found")
            
            # Find the editable span
            title_span = title_component.find_element(By.CSS_SELECTOR, "span.__se-node")
            logger.info("  → Editable span found")
            
            # Use JavaScript to set title directly (bypasses click interception)
            logger.info("  → Setting title via JavaScript...")
            self.driver.execute_script(
                "arguments[0].textContent = arguments[1];",
                title_span,
                title
            )
            
            # Trigger input event to make editor recognize the change
            self.driver.execute_script(
                "arguments[0].dispatchEvent(new Event('input', { bubbles: true }));",
                title_span
            )
            
            logger.info(f"✅ Title entered: {title}")
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Failed to fill title: {e}")
            # Take screenshot
            screenshot_path = Path(settings.output_dir) / "title_error_screenshot.png"
            self.driver.save_screenshot(str(screenshot_path))
            logger.info(f"Error screenshot: {screenshot_path}")
            raise
    
    def _upload_images(self, wait, images: list[Path]):
        """Upload images to blog post"""
        try:
            # Close all popups before starting
            self._close_all_popups()
            time.sleep(0.5)
            
            for i, image_path in enumerate(images):
                logger.info(f"Uploading image {i+1}/{len(images)}: {image_path.name}")
                
                # Close popups again before each image (they may reappear)
                self._close_all_popups()
                
                # Focus content area without clicking (use JavaScript)
                if i == 0:
                    text_component = wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".se-component.se-text"))
                    )
                    # Focus using JavaScript instead of click
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", text_component)
                    time.sleep(0.5)
                
                # Find insert menu image button
                insert_menu_btn = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".se-insert-menu-button-image"))
                )
                
                # Click using JavaScript to bypass any overlays
                self.driver.execute_script("arguments[0].click();", insert_menu_btn)
                logger.info(f"  → Clicked insert image button (JS)")
                time.sleep(1)
                
                # Find file input (it may be hidden)
                file_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
                
                # Try to find the active file input
                file_input = None
                for inp in file_inputs:
                    if inp.is_displayed() or inp.get_attribute('accept'):
                        file_input = inp
                        break
                
                if not file_input and file_inputs:
                    file_input = file_inputs[0]  # Use first one as fallback
                
                if not file_input:
                    # Alternative: Look for upload button and trigger file dialog
                    logger.warning("No file input found, looking for alternative upload method...")
                    
                    # Try finding "내 컴퓨터" button
                    upload_btns = self.driver.find_elements(By.XPATH, "//button[contains(text(), '내 컴퓨터')]")
                    if upload_btns:
                        upload_btns[0].click()
                        time.sleep(0.5)
                        
                        # Now try again
                        file_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
                        if file_inputs:
                            file_input = file_inputs[-1]  # Use last one (most recent)
                
                if not file_input:
                    raise Exception(f"Could not find file input for image {i+1}")
                
                # Send file path
                absolute_path = str(image_path.absolute())
                file_input.send_keys(absolute_path)
                logger.info(f"  → File path sent: {absolute_path}")
                
                # Wait for upload to complete
                time.sleep(2)
                
                # Check for upload progress/completion
                # (Naver may show a progress indicator - wait for it)
                try:
                    # Wait for image to appear in editor
                    wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, f".se-component-content img"))
                    )
                    logger.info(f"  ✅ Image {i+1} uploaded successfully")
                except:
                    logger.warning(f"  ⚠️ Could not verify image {i+1} upload")
                
                time.sleep(1)
            
            logger.info(f"✅ All {len(images)} images uploaded")
            
        except Exception as e:
            logger.error(f"Failed to upload images: {e}")
            raise
    
    def _publish_post(self, wait) -> str:
        """Click publish button and get published URL"""
        try:
            # Switch back to default content (out of iframe)
            self.driver.switch_to.default_content()
            
            # Wait a moment for iframe to be ready
            time.sleep(1)
            
            # Find publish button (outside iframe)
            publish_btn = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[class*='publish_btn']"))
            )
            
            logger.info("Clicking publish button...")
            publish_btn.click()
            time.sleep(3)
            
            # Wait for redirect to published post
            wait.until(lambda d: "blog.naver.com" in d.current_url and "Redirect" not in d.current_url)
            
            published_url = self.driver.current_url
            logger.info(f"✅ Published: {published_url}")
            
            return published_url
            
        except Exception as e:
            logger.error(f"Failed to publish: {e}")
            raise


# CLI for one-time login setup
if __name__ == "__main__":
    print("🔐 Naver Blog Login Setup")
    print("=" * 50)
    publisher = NaverBlogPublisherV2()
    publisher.login_once()
