"""Naver blog publisher v5 - Direct Input Injection (No Button Click)"""
import time
import logging
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from config import settings

logger = logging.getLogger(__name__)


class NaverBlogPublisherV5:
    """V5: 버튼 클릭 없이 input 직접 조작 (OS 창 회피)"""
    
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
                
                # 이미지 업로드 (V5 방식 - 버튼 클릭 없이)
                logger.info(f"📷 Uploading {len(all_images)} images...")
                self._upload_images_v5(main_frame, all_images)
                
                # 발행
                logger.info("📤 Publishing...")
                url = self._publish_post(page)
                
                logger.info(f"✅ SUCCESS: {url}")
                time.sleep(2)
                
                return url
                
            except Exception as e:
                logger.error(f"❌ Failed: {e}")
                
                screenshot_path = Path(settings.output_dir) / "error_v5.png"
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
    
    def _upload_images_v5(self, frame, images: list[Path]):
        """
        이미지 업로드 V5 (핵심 개선!)
        버튼 클릭 SKIP → input 직접 생성/조작 → OS 창 안 뜸
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
                
                # V5 핵심: input을 JavaScript로 생성/조작 (버튼 클릭 없이!)
                abs_path = str(img_path.absolute())
                
                # input 생성 또는 기존 input 활용
                result = frame.evaluate(f"""
                    (filePath) => {{
                        // 1. 기존 hidden input 찾기
                        let input = document.querySelector('#hidden-file');
                        
                        // 2. 없으면 새로 생성
                        if (!input) {{
                            input = document.createElement('input');
                            input.type = 'file';
                            input.id = 'hidden-file-custom';
                            input.style.display = 'none';
                            input.accept = 'image/*';
                            document.body.appendChild(input);
                        }}
                        
                        // 3. change 이벤트 리스너 추가
                        let uploaded = false;
                        input.addEventListener('change', (e) => {{
                            uploaded = true;
                        }});
                        
                        // 4. 파일 경로 정보 반환 (Playwright가 파일 설정할 수 있도록)
                        return {{
                            inputId: input.id,
                            inputExists: true
                        }};
                    }}
                """, abs_path)
                
                logger.info(f"    → Input ready: {result['inputId']}")
                
                # Playwright로 파일 설정 (OS 창 안 뜸!)
                input_selector = f"#{result['inputId']}"
                file_input = frame.locator(input_selector).first
                
                # 중요: Playwright의 set_input_files는 FileChooser를 트리거하지 않음
                # 미리 생성된 input에 직접 설정
                file_input.set_input_files(abs_path)
                logger.info(f"    ✅ File set via Playwright")
                
                # change 이벤트 수동 트리거
                frame.evaluate(f"""
                    () => {{
                        const input = document.querySelector('#{result['inputId']}');
                        if (input && input.files.length > 0) {{
                            // 파일 정보 확인
                            const file = input.files[0];
                            console.log('File:', file.name, file.size);
                            
                            // change 이벤트 발생
                            const event = new Event('change', {{ bubbles: true, cancelable: true }});
                            input.dispatchEvent(event);
                            
                            return {{ success: true, fileName: file.name }};
                        }}
                        return {{ success: false }};
                    }}
                """)
                
                logger.info("    → Change event triggered")
                
                # 업로드 대기
                time.sleep(4)
                
                # 확인
                img_elements = frame.locator(".se-component-content img, .se-image-resource img, img[src*='blogpfthumb'], img[src*='storep-phinf']")
                count = img_elements.count()
                logger.info(f"    → Editor images: {count}")
                
                if count >= i + 1:
                    logger.info(f"    ✅ Image {i+1} confirmed!")
                else:
                    logger.warning(f"    ⚠️ Image {i+1} not verified (expected {i+1}, found {count})")
                
            except Exception as e:
                logger.error(f"    ❌ Image {i+1} failed: {e}")
                import traceback
                traceback.print_exc()
    
    def _publish_post(self, page) -> str:
        """발행 버튼 클릭"""
        try:
            publish_btn = page.locator("button.publish_btn__jBfZy, button[class*='publish_btn']").first
            publish_btn.wait_for(state="visible", timeout=10000)
            
            logger.info("  → Clicking publish...")
            publish_btn.click()
            
            # URL 변경 대기
            time.sleep(3)
            
            # Check if published
            if "Redirect" not in page.url:
                url = page.url
                logger.info(f"  ✅ Published: {url}")
                return url
            else:
                # Still on write page, maybe need confirmation
                logger.warning("  ⚠️ Still on write page, looking for confirmation...")
                time.sleep(2)
                return page.url
            
        except Exception as e:
            logger.error(f"Publish failed: {e}")
            raise


if __name__ == "__main__":
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    print("Use test_v5.py for testing")
