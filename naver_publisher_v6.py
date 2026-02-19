"""Naver blog publisher v6 - Playwright FileChooser API (영상과 동일한 방식)"""
import time
import logging
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout, FileChooser
from config import settings

logger = logging.getLogger(__name__)


class NaverBlogPublisherV6:
    """V6: Playwright FileChooser API 사용 (OS 창 가로채기)"""
    
    def __init__(self):
        self.blog_url = settings.naver_blog_url
        self.blog_id = "ridyservice"
        self.category_no = "28"
    
    def publish(self, title: str, html_content: str, images: list[Path], footer_images: list[Path] = None) -> str:
        """완전 자동 발행"""
        if footer_images is None:
            footer_images = []
        
        all_images = list(images) + list(footer_images)
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False,
                args=['--disable-blink-features=AutomationControlled']
            )
            
            cookies = self._load_cookies()
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )
            
            if cookies:
                context.add_cookies(cookies)
                logger.info(f"✅ Loaded {len(cookies)} cookies")
            
            page = context.new_page()
            page.set_default_timeout(30000)
            
            try:
                write_url = f"{self.blog_url}?Redirect=Write&categoryNo={self.category_no}"
                logger.info(f"📍 Opening: {write_url}")
                page.goto(write_url, wait_until="networkidle")
                
                if "nid.naver.com" in page.url:
                    raise Exception("로그인 필요")
                
                logger.info("⏳ Waiting for mainFrame...")
                page.wait_for_selector("#mainFrame", timeout=10000)
                main_frame = page.frame(name="mainFrame")
                
                if not main_frame:
                    raise Exception("mainFrame not found")
                
                logger.info("✅ mainFrame loaded")
                
                # 팝업 제거
                self._kill_all_popups(main_frame)
                
                # 제목
                logger.info(f"📝 Title: {title}")
                self._set_title(main_frame, title)
                
                # 이미지 업로드 (V6 방식 - FileChooser API)
                logger.info(f"📷 Uploading {len(all_images)} images...")
                self._upload_images_v6(page, main_frame, all_images)
                
                # 발행
                logger.info("📤 Publishing...")
                url = self._publish_post(page)
                
                logger.info(f"✅ SUCCESS: {url}")
                time.sleep(2)
                
                return url
                
            except Exception as e:
                logger.error(f"❌ Failed: {e}")
                
                screenshot_path = Path(settings.output_dir) / "error_v6.png"
                screenshot_path.parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(screenshot_path), full_page=True)
                logger.info(f"Screenshot: {screenshot_path}")
                
                raise
                
            finally:
                browser.close()
    
    def _load_cookies(self):
        """쿠키 로드"""
        import pickle
        cookie_file = Path('.naver_cookies.pkl')
        
        if not cookie_file.exists():
            return None
        
        try:
            data = pickle.loads(cookie_file.read_bytes())
            cookies = data.get('cookies', [])
            
            pw_cookies = []
            for c in cookies:
                pw_c = {
                    'name': c['name'],
                    'value': c['value'],
                    'domain': c.get('domain', '.naver.com'),
                    'path': c.get('path', '/'),
                }
                if 'expires' in c:
                    pw_c['expires'] = c['expires']
                pw_cookies.append(pw_c)
            
            return pw_cookies
            
        except Exception as e:
            logger.error(f"Cookie load failed: {e}")
            return None
    
    def _kill_all_popups(self, frame):
        """팝업 제거"""
        try:
            frame.evaluate("""
                () => {
                    const killList = [
                        '.se-popup-dim',
                        '.se-popup-container',
                        '.se-help-panel',
                        '.se-popup',
                        '[class*="popup"]',
                        '[class*="modal"]',
                        '[class*="overlay"]'
                    ];
                    
                    killList.forEach(sel => {
                        document.querySelectorAll(sel).forEach(el => el.remove());
                    });
                    
                    window.alert = () => {};
                    window.confirm = () => true;
                }
            """)
            logger.info("✅ Popups killed")
            time.sleep(0.3)
        except Exception as e:
            logger.warning(f"Popup kill warning: {e}")
    
    def _set_title(self, frame, title: str):
        """제목 설정"""
        try:
            title_span = frame.locator(".se-component.se-documentTitle span.__se-node").first
            title_span.wait_for(state="attached", timeout=10000)
            
            safe_title = title.replace("'", "\\'").replace('"', '\\"')
            title_span.evaluate(f"""el => {{
                el.textContent = '{safe_title}';
                el.innerText = '{safe_title}';
                el.dispatchEvent(new Event('input', {{bubbles: true}}));
            }}""")
            
            logger.info(f"  ✅ Title set")
            time.sleep(0.5)
        except Exception as e:
            logger.error(f"Title failed: {e}")
            raise
    
    def _upload_images_v6(self, page, frame, images: list[Path]):
        """
        이미지 업로드 V6 (영상 방식 구현!)
        핵심: page.expect_file_chooser()로 OS 파일 선택 창 가로채기
        """
        for i, img_path in enumerate(images):
            logger.info(f"  [{i+1}/{len(images)}] {img_path.name}")
            
            try:
                self._kill_all_popups(frame)
                
                # 첫 이미지: 에디터 활성화
                if i == 0:
                    content = frame.locator(".se-component.se-text").first
                    content.click(force=True, timeout=3000)
                    time.sleep(0.5)
                    logger.info("    → Editor activated")
                
                # V6 핵심: FileChooser 이벤트를 미리 등록 (OS 창 가로채기!)
                # 이게 영상의 send_keys(파일경로)와 동일한 효과
                abs_path = str(img_path.absolute())
                
                # FileChooser 대기 설정
                with page.expect_file_chooser() as fc_info:
                    # 사진 버튼 클릭 (OS 창이 뜨지만 Playwright가 가로챔!)
                    for selector in [".se-image-toolbar-button", "button[data-name='image']"]:
                        try:
                            btn = frame.locator(selector).first
                            if btn.count() > 0:
                                btn.click(timeout=3000)
                                logger.info(f"    → Button clicked ({selector})")
                                break
                        except:
                            continue
                
                # FileChooser 객체 받기
                file_chooser = fc_info.value
                
                # 파일 설정 (OS 창 없이 바로 설정!)
                file_chooser.set_files(abs_path)
                logger.info(f"    ✅ File set via FileChooser")
                
                # 업로드 대기 (서버 업로드 시간)
                time.sleep(4)
                
                # 확인
                img_elements = frame.locator(".se-component-content img, .se-image-resource img, img[src*='blogpfthumb'], img[src*='phinf']")
                count = img_elements.count()
                
                if count >= i + 1:
                    logger.info(f"    ✅ Image {i+1} confirmed! (total: {count})")
                else:
                    logger.warning(f"    ⚠️ Image {i+1} not verified (expected {i+1}, found {count})")
                    # Continue anyway
                
            except Exception as e:
                logger.error(f"    ❌ Image {i+1} failed: {e}")
                import traceback
                traceback.print_exc()
    
    def _publish_post(self, page) -> str:
        """발행 버튼 클릭"""
        try:
            # Try multiple selectors
            publish_btn = page.locator("button.publish_btn__jBfZy, button[class*='publish_btn'], .se-popup-button-publish").first
            publish_btn.wait_for(state="visible", timeout=10000)
            
            logger.info("  → Clicking publish...")
            publish_btn.click()
            
            # Wait for navigation
            time.sleep(3)
            
            # Check URL
            url = page.url
            if "Redirect" not in url and "PostView" in url or "/PostList" in url or url.endswith(self.blog_id):
                logger.info(f"  ✅ Published!")
                return url
            else:
                logger.warning(f"  ⚠️ Unexpected URL: {url}")
                return url
            
        except Exception as e:
            logger.error(f"Publish failed: {e}")
            raise


if __name__ == "__main__":
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    print("Use test_v6.py for testing")
