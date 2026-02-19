"""Naver blog publisher using Playwright - 완전 자동화"""
import time
import logging
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from config import settings
from session_manager import SessionManager

logger = logging.getLogger(__name__)


class NaverBlogPublisherPlaywright:
    """Playwright 기반 네이버 블로그 자동 발행"""
    
    def __init__(self):
        self.blog_url = settings.naver_blog_url
        self.blog_id = "ridyservice"
        self.category_no = "28"  # 출고 현황
        self.session_manager = SessionManager()
        self.playwright = None
        self.browser = None
        self.page = None
    
    def login_once(self):
        """수동 로그인 세션 저장"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            
            page.goto("https://naver.com")
            logger.info("Opening Naver for manual login...")
            logger.info("Please log in manually in the browser window.")
            
            input("\nPress Enter after logging in...")
            
            # Save cookies
            cookies = context.cookies()
            import pickle
            cookie_file = Path('.naver_cookies.pkl')
            cookie_data = {
                'cookies': cookies,
                'saved_at': __import__('datetime').datetime.now().isoformat()
            }
            cookie_file.write_bytes(pickle.dumps(cookie_data))
            logger.info(f"✅ Cookies saved: {len(cookies)} items")
            
            # Test
            page.goto(self.blog_url)
            time.sleep(2)
            
            if "blog.naver.com" in page.url:
                logger.info("✅ Login successful!")
            else:
                logger.warning("⚠️ Could not verify login.")
            
            browser.close()
    
    def publish(self, title: str, html_content: str, images: list[Path], footer_images: list[Path] = None) -> str:
        """
        완전 자동 블로그 발행
        
        Args:
            title: 제목
            html_content: HTML 내용 (미사용 - 이미지만)
            images: 워터마크된 이미지들
            footer_images: 푸터 이미지들
            
        Returns:
            발행된 URL
        """
        if footer_images is None:
            footer_images = []
        
        all_images = list(images) + list(footer_images)
        
        with sync_playwright() as p:
            # Launch browser
            logger.info("🚀 Launching Playwright Chromium...")
            browser = p.chromium.launch(
                headless=False,  # 디버깅용, 나중에 True로
                slow_mo=100  # 느리게 실행 (안정성)
            )
            
            # Load cookies
            cookies = self._load_cookies()
            context = browser.new_context()
            if cookies:
                context.add_cookies(cookies)
                logger.info(f"✅ Loaded {len(cookies)} cookies")
            
            page = context.new_page()
            
            # Set longer timeout
            page.set_default_timeout(30000)  # 30 seconds
            
            try:
                # Navigate to write page
                write_url = f"{self.blog_url}?Redirect=Write&categoryNo={self.category_no}"
                logger.info(f"📍 Navigating to: {write_url}")
                page.goto(write_url, wait_until="networkidle")
                
                # Check if redirected to login
                if "nid.naver.com" in page.url or "login" in page.url.lower():
                    raise Exception("로그인 필요 - 쿠키가 만료되었습니다")
                
                logger.info(f"✅ Page loaded: {page.url}")
                
                # Wait for main iframe
                logger.info("⏳ Waiting for mainFrame iframe...")
                main_frame = page.frame(name="mainFrame") or page.frame(url=lambda url: "PostWriteForm" in url)
                
                if not main_frame:
                    # Try by selector
                    page.wait_for_selector("#mainFrame", timeout=10000)
                    main_frame = page.frame("mainFrame")
                
                if not main_frame:
                    raise Exception("mainFrame iframe not found")
                
                logger.info("✅ mainFrame found")
                
                # Close any popups/help panels
                self._close_popups(main_frame)
                
                # Fill title
                logger.info(f"📝 Filling title: {title}")
                self._fill_title(main_frame, title)
                
                # Upload images
                logger.info(f"📷 Uploading {len(all_images)} images...")
                self._upload_images(main_frame, all_images)
                
                # Publish
                logger.info("📤 Publishing...")
                published_url = self._publish_post(page)
                
                logger.info(f"✅ Successfully published: {published_url}")
                
                # Wait a bit before closing
                time.sleep(2)
                
                return published_url
                
            except Exception as e:
                logger.error(f"❌ Publishing failed: {e}")
                
                # Screenshot
                screenshot_path = Path(settings.output_dir) / "playwright_error.png"
                screenshot_path.parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(screenshot_path), full_page=True)
                logger.info(f"Screenshot saved: {screenshot_path}")
                
                raise
                
            finally:
                browser.close()
    
    def _load_cookies(self):
        """Load cookies from file"""
        import pickle
        cookie_file = Path('.naver_cookies.pkl')
        
        if not cookie_file.exists():
            return None
        
        try:
            data = pickle.loads(cookie_file.read_bytes())
            cookies = data.get('cookies', [])
            
            # Convert to Playwright format
            pw_cookies = []
            for cookie in cookies:
                pw_cookie = {
                    'name': cookie['name'],
                    'value': cookie['value'],
                    'domain': cookie.get('domain', '.naver.com'),
                    'path': cookie.get('path', '/'),
                }
                if 'expires' in cookie:
                    pw_cookie['expires'] = cookie['expires']
                
                pw_cookies.append(pw_cookie)
            
            return pw_cookies
            
        except Exception as e:
            logger.error(f"Failed to load cookies: {e}")
            return None
    
    def _close_popups(self, frame):
        """Close all popups and overlays - AGGRESSIVE MODE"""
        try:
            # Aggressive JavaScript removal
            frame.evaluate("""
                () => {
                    // Remove ALL overlays and popups
                    const killSelectors = [
                        '.se-popup-dim',
                        '.se-popup-container',
                        '.se-help-panel',
                        '.se-floating-material-container',
                        '.se-floating-material-menu',
                        '[class*="popup"]',
                        '[class*="overlay"]',
                        '[class*="modal"]'
                    ];
                    
                    killSelectors.forEach(sel => {
                        document.querySelectorAll(sel).forEach(el => {
                            el.remove();  // Completely remove from DOM
                        });
                    });
                    
                    // Also set body overflow to visible
                    document.body.style.overflow = 'visible';
                }
            """)
            
            logger.info("✅ Aggressively removed all popups")
            time.sleep(0.5)
            
        except Exception as e:
            logger.warning(f"Popup closing failed: {e}")
    
    def _fill_title(self, frame, title: str):
        """Fill blog post title"""
        try:
            # Wait for title component
            title_locator = frame.locator(".se-component.se-documentTitle")
            title_locator.wait_for(state="attached", timeout=10000)  # Just attached, not visible
            
            # Find editable span
            title_span = title_locator.locator("span.__se-node").first
            
            # Set title directly via JavaScript (bypasses visibility checks)
            # Escape quotes in title
            safe_title = title.replace("'", "\\'").replace('"', '\\"')
            title_span.evaluate(f"""el => {{
                el.textContent = '{safe_title}';
                el.innerText = '{safe_title}';
                // Trigger events
                el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                el.dispatchEvent(new Event('change', {{ bubbles: true }}));
            }}""")
            
            logger.info(f"✅ Title set: {title}")
            time.sleep(0.5)
            
        except Exception as e:
            logger.error(f"Failed to fill title: {e}")
            raise
    
    def _upload_images(self, frame, images: list[Path]):
        """Upload all images"""
        for i, image_path in enumerate(images):
            logger.info(f"  [{i+1}/{len(images)}] {image_path.name}")
            
            try:
                # Close popups before each upload
                self._close_popups(frame)
                
                # Click on content area to activate insert menu (first image only)
                if i == 0:
                    logger.info("    → Clicking content area...")
                    content_area = frame.locator(".se-component.se-text").first
                    content_area.wait_for(state="attached", timeout=5000)
                    # Force click to activate
                    content_area.click(force=True, timeout=3000)
                    time.sleep(1)
                
                # Use toolbar button (more stable than insert menu)
                # Toolbar is always visible
                toolbar_img_btn = frame.locator(".se-image-toolbar-button, button[data-name='image']").first
                
                if toolbar_img_btn.count() > 0:
                    toolbar_img_btn.evaluate("el => el.click()")
                    logger.info("    → Toolbar image button clicked")
                else:
                    # Fallback to insert menu
                    insert_btn = frame.locator(".se-insert-menu-button-image").first
                    insert_btn.evaluate("el => el.click()")
                    logger.info("    → Insert menu button clicked")
                
                time.sleep(1)
                
                # Find and use file input
                # Playwright can set files on hidden inputs!
                file_input = frame.locator("input[type='file']").first
                
                # Set the file
                file_input.set_input_files(str(image_path.absolute()))
                logger.info(f"    → File uploaded: {image_path.name}")
                
                # Wait for upload to complete
                time.sleep(2)
                
                # Verify image appeared
                images_in_editor = frame.locator(".se-component-content img")
                if images_in_editor.count() >= i + 1:
                    logger.info(f"    ✅ Image {i+1} confirmed in editor")
                else:
                    logger.warning(f"    ⚠️ Could not verify image {i+1}")
                
            except Exception as e:
                logger.error(f"    ❌ Failed to upload image {i+1}: {e}")
                # Continue with next image
    
    def _publish_post(self, page) -> str:
        """Click publish button and get URL"""
        try:
            # Switch back to main page (out of iframe)
            # Find publish button
            publish_btn = page.locator("button[class*='publish_btn']").first
            publish_btn.wait_for(state="visible", timeout=10000)
            
            logger.info("  → Clicking publish button...")
            publish_btn.click()
            
            # Wait for navigation to published post
            page.wait_for_url(lambda url: "blog.naver.com" in url and "Redirect" not in url, timeout=10000)
            
            published_url = page.url
            logger.info(f"  ✅ Published: {published_url}")
            
            return published_url
            
        except Exception as e:
            logger.error(f"Failed to publish: {e}")
            raise


# CLI
if __name__ == "__main__":
    print("🔐 Naver Blog Login Setup (Playwright)")
    print("=" * 50)
    publisher = NaverBlogPublisherPlaywright()
    publisher.login_once()
