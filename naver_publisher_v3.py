"""Naver blog publisher v3 - 영상 인사이트 적용 (Anti-Bot Detection)"""
import time
import logging
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import pyperclip  # pip install pyperclip
from config import settings

logger = logging.getLogger(__name__)


class NaverBlogPublisherV3:
    """영상 인사이트 기반 개선:
    1. 클립보드 붙여넣기 로그인 (봇 탐지 우회)
    2. 숨겨진 input[type=file] 직접 사용
    3. 공격적 팝업 제거
    4. Anti-detection 헤더
    """
    
    def __init__(self):
        self.blog_url = settings.naver_blog_url
        self.blog_id = "ridyservice"
        self.blog_pw = "llnp301510!"
        self.category_no = "28"
    
    def login_with_clipboard(self):
        """
        클립보드 붙여넣기 방식 로그인 (봇 탐지 우회)
        영상 핵심: send_keys 대신 pyperclip + Ctrl+V
        """
        with sync_playwright() as p:
            # Anti-detection 브라우저 설정
            browser = p.chromium.launch(
                headless=False,
                args=[
                    '--disable-blink-features=AutomationControlled',  # 자동화 감지 비활성화
                    '--disable-dev-shm-usage',
                    '--disable-infobars',
                    '--start-maximized'
                ]
            )
            
            # User-Agent 설정
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            
            page = context.new_page()
            
            # 로그인 페이지 이동
            logger.info("🔐 Navigating to Naver login...")
            page.goto("https://nid.naver.com/nidlogin.login")
            page.wait_for_load_state("networkidle")
            
            try:
                # 아이디 입력 - 클립보드 방식 (핵심!)
                logger.info("📋 ID input (clipboard method)...")
                id_input = page.locator("#id")
                id_input.click()
                
                # 클립보드에 복사
                pyperclip.copy(self.blog_id)
                time.sleep(0.3)
                
                # Mac: Command+V, Windows/Linux: Control+V
                import platform
                if platform.system() == "Darwin":  # Mac
                    page.keyboard.press("Meta+v")
                else:
                    page.keyboard.press("Control+v")
                
                time.sleep(0.5)
                logger.info("  ✅ ID pasted")
                
                # 비밀번호 입력 - 클립보드 방식
                logger.info("📋 Password input (clipboard method)...")
                pw_input = page.locator("#pw")
                pw_input.click()
                
                pyperclip.copy(self.blog_pw)
                time.sleep(0.3)
                
                if platform.system() == "Darwin":
                    page.keyboard.press("Meta+v")
                else:
                    page.keyboard.press("Control+v")
                
                time.sleep(0.5)
                logger.info("  ✅ Password pasted")
                
                # 로그인 버튼 클릭
                login_btn = page.locator("#log\\.login")
                login_btn.click()
                
                logger.info("⏳ Waiting for login...")
                time.sleep(3)
                
                # 로그인 성공 확인
                if "nid.naver.com" not in page.url:
                    logger.info("✅ Login successful!")
                    
                    # 쿠키 저장
                    cookies = context.cookies()
                    import pickle
                    cookie_file = Path('.naver_cookies.pkl')
                    cookie_data = {
                        'cookies': cookies,
                        'saved_at': __import__('datetime').datetime.now().isoformat()
                    }
                    cookie_file.write_bytes(pickle.dumps(cookie_data))
                    logger.info(f"💾 Saved {len(cookies)} cookies")
                    
                else:
                    logger.warning("⚠️ Still on login page - manual intervention needed")
                    input("\nPress Enter after completing login/captcha...")
                    
                    # 재저장
                    cookies = context.cookies()
                    import pickle
                    cookie_file = Path('.naver_cookies.pkl')
                    cookie_data = {
                        'cookies': cookies,
                        'saved_at': __import__('datetime').datetime.now().isoformat()
                    }
                    cookie_file.write_bytes(pickle.dumps(cookie_data))
                    logger.info(f"💾 Saved {len(cookies)} cookies (after manual login)")
                
            finally:
                browser.close()
    
    def publish(self, title: str, html_content: str, images: list[Path], footer_images: list[Path] = None) -> str:
        """
        완전 자동 발행 (영상 인사이트 적용)
        """
        if footer_images is None:
            footer_images = []
        
        all_images = list(images) + list(footer_images)
        
        with sync_playwright() as p:
            # Anti-detection 브라우저
            browser = p.chromium.launch(
                headless=False,
                args=['--disable-blink-features=AutomationControlled'],
                slow_mo=50
            )
            
            # 쿠키 로드
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
                # 글쓰기 페이지
                write_url = f"{self.blog_url}?Redirect=Write&categoryNo={self.category_no}"
                logger.info(f"📍 Opening: {write_url}")
                page.goto(write_url, wait_until="networkidle")
                
                # 로그인 체크
                if "nid.naver.com" in page.url:
                    raise Exception("로그인 필요 - login_with_clipboard() 먼저 실행하세요")
                
                # mainFrame 대기
                logger.info("⏳ Waiting for mainFrame...")
                page.wait_for_selector("#mainFrame", timeout=10000)
                main_frame = page.frame(name="mainFrame") or page.frame("mainFrame")
                
                if not main_frame:
                    raise Exception("mainFrame not found")
                
                logger.info("✅ mainFrame loaded")
                
                # 공격적 팝업 제거 (영상 인사이트)
                self._kill_all_popups(main_frame)
                
                # 제목 입력
                logger.info(f"📝 Title: {title}")
                self._set_title(main_frame, title)
                
                # 이미지 업로드 (영상 인사이트 - hidden input 직접 사용)
                logger.info(f"📷 Uploading {len(all_images)} images...")
                self._upload_images_v3(main_frame, all_images)
                
                # 발행
                logger.info("📤 Publishing...")
                url = self._publish_post(page)
                
                logger.info(f"✅ SUCCESS: {url}")
                time.sleep(2)
                
                return url
                
            except Exception as e:
                logger.error(f"❌ Failed: {e}")
                
                # 스크린샷
                screenshot_path = Path(settings.output_dir) / "error_v3.png"
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
        """
        공격적 팝업 제거 (영상 인사이트)
        try-except로 감싸서 실패해도 계속 진행
        """
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
                        '[class*="overlay"]',
                        '.se-floating-material-container'
                    ];
                    
                    killList.forEach(sel => {
                        document.querySelectorAll(sel).forEach(el => el.remove());
                    });
                    
                    // Alert 처리
                    window.alert = () => {};
                    window.confirm = () => true;
                }
            """)
            logger.info("✅ Popups killed")
            time.sleep(0.3)
        except Exception as e:
            logger.warning(f"Popup kill warning: {e}")
    
    def _set_title(self, frame, title: str):
        """제목 설정 (JavaScript 직접)"""
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
    
    def _upload_images_v3(self, frame, images: list[Path]):
        """
        이미지 업로드 v3 (영상 인사이트)
        핵심: 1) 사진 버튼 클릭 → 2) 숨겨진 input[type='file'] 직접 사용
        """
        for i, img_path in enumerate(images):
            logger.info(f"  [{i+1}/{len(images)}] {img_path.name}")
            
            try:
                # 팝업 제거
                self._kill_all_popups(frame)
                
                # 첫 이미지: 콘텐츠 영역 클릭해서 에디터 활성화
                if i == 0:
                    content = frame.locator(".se-component.se-text").first
                    content.click(force=True, timeout=3000)
                    time.sleep(0.5)
                    logger.info("    → Content area activated")
                
                # 1단계: 사진 버튼 클릭 (input[type='file'] 생성 트리거)
                # Try multiple selectors
                clicked = False
                for selector in [
                    ".se-image-toolbar-button",  # Toolbar 버튼
                    "button[data-name='image']",  # Data attribute
                    ".se-insert-menu-button-image",  # Insert menu
                ]:
                    try:
                        img_btn = frame.locator(selector).first
                        if img_btn.count() > 0:
                            # Use JavaScript click to bypass visibility
                            img_btn.evaluate("el => el.click()")
                            logger.info(f"    → Image button clicked ({selector})")
                            clicked = True
                            time.sleep(0.5)
                            break
                    except:
                        continue
                
                if not clicked:
                    logger.warning("    ⚠️ Could not click image button")
                    # Try clicking content area to reset
                    content = frame.locator(".se-component.se-text").first
                    content.click(force=True, timeout=3000)
                    time.sleep(0.3)
                    continue
                
                # 2단계: input[type=file] 찾기 (영상 핵심!)
                # 버튼 클릭 후 input이 생성됨 - id="hidden-file"
                file_input = frame.locator("#hidden-file, input[type='file']").first
                file_input.wait_for(state="attached", timeout=5000)
                logger.info("    → File input found")
                
                # 파일 직접 설정 (절대 경로)
                abs_path = str(img_path.absolute())
                file_input.set_input_files(abs_path)
                
                logger.info(f"    ✅ File set: {img_path.name}")
                
                # 업로드 완료 대기 (서버 업로드 시간)
                time.sleep(3)
                
                # 확인
                img_elements = frame.locator(".se-component-content img, .se-image-resource img")
                count = img_elements.count()
                if count >= i + 1:
                    logger.info(f"    ✅ Image {i+1} confirmed ({count} total)")
                else:
                    logger.warning(f"    ⚠️ Image {i+1} not verified (found {count})")
                
            except Exception as e:
                logger.error(f"    ❌ Image {i+1} failed: {e}")
                # Continue anyway
    
    def _publish_post(self, page) -> str:
        """발행 버튼 클릭"""
        try:
            # iframe 밖으로
            publish_btn = page.locator("button[class*='publish_btn']").first
            publish_btn.wait_for(state="visible", timeout=10000)
            
            logger.info("  → Clicking publish...")
            publish_btn.click()
            
            # URL 변경 대기
            page.wait_for_url(
                lambda url: "blog.naver.com" in url and "Redirect" not in url,
                timeout=10000
            )
            
            url = page.url
            logger.info(f"  ✅ Published: {url}")
            return url
            
        except Exception as e:
            logger.error(f"Publish failed: {e}")
            raise


# CLI
if __name__ == "__main__":
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    publisher = NaverBlogPublisherV3()
    
    if len(sys.argv) > 1 and sys.argv[1] == "login":
        print("🔐 Login with Clipboard Method (Anti-Bot Detection)")
        print("=" * 60)
        publisher.login_with_clipboard()
    else:
        print("Usage:")
        print("  python naver_publisher_v3.py login    # 클립보드 방식 로그인")
        print("\nOr use publish() method from code")
