"""반자동 네이버 블로그 발행 - 90% 자동 + Luke가 발행 버튼만 클릭"""
import time
import logging
from pathlib import Path
from playwright.sync_api import sync_playwright
from config import settings

logger = logging.getLogger(__name__)


class NaverBlogPublisherSemiAuto:
    """반자동: 제목+이미지 자동 입력, 발행만 수동"""
    
    def __init__(self):
        self.blog_url = settings.naver_blog_url
        self.category_no = "28"
    
    def publish(self, title: str, html_content: str, images: list[Path], footer_images: list[Path] = None) -> str:
        """
        반자동 발행: 제목과 이미지를 자동으로 업로드하고 브라우저를 열어둠
        
        Returns:
            "MANUAL_PUBLISH_REQUIRED" - Luke가 발행 버튼 클릭 필요
        """
        if footer_images is None:
            footer_images = []
        
        all_images = list(images) + list(footer_images)
        
        with sync_playwright() as p:
            # Launch browser (non-headless, 창을 열어둠)
            logger.info("🌐 Opening browser for semi-auto publish...")
            browser = p.chromium.launch(
                headless=False,  # 창 보이게
                slow_mo=50
            )
            
            # Load cookies
            cookies = self._load_cookies()
            context = browser.new_context()
            if cookies:
                context.add_cookies(cookies)
            
            page = context.new_page()
            page.set_default_timeout(15000)
            
            try:
                # Navigate
                write_url = f"{self.blog_url}?Redirect=Write&categoryNo={self.category_no}"
                logger.info(f"📍 Navigating: {write_url}")
                page.goto(write_url, wait_until="networkidle")
                
                # Wait for mainFrame
                main_frame = page.frame(name="mainFrame") or page.frame(url=lambda url: "PostWriteForm" in url)
                if not main_frame:
                    page.wait_for_selector("#mainFrame", timeout=10000)
                    main_frame = page.frame("mainFrame")
                
                if not main_frame:
                    raise Exception("mainFrame not found")
                
                logger.info("✅ mainFrame loaded")
                time.sleep(2)
                
                # Remove ALL overlays aggressively
                logger.info("🧹 Removing overlays...")
                main_frame.evaluate("""
                    () => {
                        // Remove everything that could block
                        document.querySelectorAll('[class*="popup"], [class*="help"], [class*="overlay"], [class*="dim"], .se-floating-material-container').forEach(el => el.remove());
                        document.body.style.overflow = 'visible';
                    }
                """)
                
                # Set title directly via DOM
                logger.info(f"📝 Setting title: {title}")
                safe_title = title.replace("'", "\\'")
                main_frame.evaluate(f"""
                    () => {{
                        const titleEl = document.querySelector('.se-component.se-documentTitle span.__se-node');
                        if (titleEl) {{
                            titleEl.textContent = '{safe_title}';
                            titleEl.innerText = '{safe_title}';
                        }}
                    }}
                """)
                logger.info("✅ Title set")
                
                # Upload images - use file chooser interception (no dialog!)
                logger.info(f"📷 Uploading {len(all_images)} images...")
                
                for i, img_path in enumerate(all_images):
                    logger.info(f"  [{i+1}/{len(all_images)}] {img_path.name}")
                    
                    try:
                        # Set up file chooser handler BEFORE clicking button
                        # This intercepts the file dialog
                        with page.expect_file_chooser() as fc_info:
                            # Now click the button (will trigger file chooser)
                            main_frame.evaluate("""
                                () => {
                                    const btn = document.querySelector('.se-image-toolbar-button, button[data-name="image"]');
                                    if (btn) btn.click();
                                }
                            """)
                        
                        file_chooser = fc_info.value
                        
                        # Set file (this happens BEFORE dialog shows)
                        file_chooser.set_files(str(img_path.absolute()))
                        
                        logger.info(f"    ✅ Uploaded")
                        time.sleep(1.5)  # Wait for upload to complete
                        
                    except Exception as e:
                        logger.warning(f"    ⚠️ Image {i+1} failed: {e}")
                        # Continue anyway
                
                logger.info("✅ All images uploaded")
                
                # Click 임시저장 (Save Draft) button
                logger.info("💾 Clicking 임시저장 button...")
                
                try:
                    # Switch back to main page (out of iframe) to find save button
                    # Save button is outside iframe
                    save_btn = page.locator("button[class*='save_btn'], button:has-text('저장')").first
                    save_btn.wait_for(state="visible", timeout=5000)
                    save_btn.click()
                    logger.info("✅ 임시저장 clicked!")
                    
                    time.sleep(2)
                    
                    # Success message
                    logger.info("\n" + "="*60)
                    logger.info("💾 임시저장 완료!")
                    logger.info("="*60)
                    logger.info(f"제목: {title}")
                    logger.info(f"이미지: {len(all_images)}장")
                    logger.info("")
                    logger.info("👉 네이버 블로그에서 임시저장 글을 열어 발행해주세요!")
                    logger.info("   (PC/모바일 어디서든 가능)")
                    logger.info("="*60)
                    
                    # Return special code to indicate draft saved
                    return "DRAFT_SAVED"
                    
                except Exception as save_error:
                    logger.error(f"임시저장 실패: {save_error}")
                    logger.info("⚠️ 임시저장 버튼을 찾지 못했습니다")
                    logger.info("   브라우저를 10초간 열어둡니다 - 수동으로 저장해주세요")
                    time.sleep(10)
                    return "DRAFT_SAVE_FAILED"
                
            except Exception as e:
                logger.error(f"Error: {e}")
                # Take screenshot
                screenshot_path = Path(settings.output_dir) / "semi_auto_error.png"
                screenshot_path.parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(screenshot_path))
                raise
                
            finally:
                # Don't close automatically
                pass
    
    def _load_cookies(self):
        """Load cookies"""
        import pickle
        cookie_file = Path('.naver_cookies.pkl')
        
        if not cookie_file.exists():
            return None
        
        try:
            data = pickle.loads(cookie_file.read_bytes())
            cookies = data.get('cookies', [])
            
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
