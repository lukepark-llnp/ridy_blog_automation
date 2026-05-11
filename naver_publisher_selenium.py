"""Naver blog publisher - Selenium (영상 인사이트 100% 구현)"""
import time
import logging
import pickle
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pyperclip
from bs4 import BeautifulSoup
from config import settings

logger = logging.getLogger(__name__)


class NaverBlogPublisherSelenium:
    """Selenium 기반 - 영상 인사이트 그대로 구현"""
    
    def __init__(self):
        self.blog_url = settings.naver_blog_url
        self.blog_id = "ridyservice"
        self.blog_pw = "llnp301510!"
        self.category_no = "28"
        self.driver = None
    
    def login_with_clipboard(self):
        """수동 로그인 (영구 프로필 사용)"""
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        # 사용자 프로필 유지 (쿠키/세션 영구 저장)
        profile_dir = Path(settings.chrome_profile_path)
        profile_dir.mkdir(parents=True, exist_ok=True)
        options.add_argument(f"user-data-dir={profile_dir}")

        self.driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(self.driver, 10)

        try:
            logger.info("🔐 Navigating to login...")
            self.driver.get("https://nid.naver.com/nidlogin.login")
            
            # 이미 로그인 되어있는지 확인
            if "nid.naver.com" not in self.driver.current_url:
                logger.info("✅ Already logged in (profile reused)")
                return
            
            logger.info("🛑 Automatic input disabled. Please login MANUALLY.")
            logger.info("👉 직접 아이디/비번을 입력하고 로그인해주세요.")
            
            # 로그인 확인 루프
            max_wait = 300  # 5분 대기
            waited = 0
            while waited < max_wait:
                if "nid.naver.com" not in self.driver.current_url:
                    logger.info("✅ Login successful!")
                    break
                
                if waited % 5 == 0:
                    logger.info(f"⏳ Waiting for manual login... ({waited}s)")
                
                time.sleep(1)
                waited += 1
            
            if waited >= max_wait:
                logger.error("❌ Login timeout")
                return

            # 중요: 로그인 완료 후 메인 페이지로 이동하여 전체 쿠키 획득
            logger.info("🔐 Navigating to naver.com to capture all cookies...")
            self.driver.get("https://www.naver.com")
            time.sleep(2)
            
            # 쿠키 저장 (백업용)
            cookies = self.driver.get_cookies()
            cookie_file = Path('.naver_cookies_selenium.pkl')
            cookie_data = {
                'cookies': cookies,
                'saved_at': __import__('datetime').datetime.now().isoformat()
            }
            cookie_file.write_bytes(pickle.dumps(cookie_data))
            logger.info(f"💾 Saved {len(cookies)} cookies")
            
        finally:
            if self.driver:
                self.driver.quit()
    
    def publish(self, title: str, html_content: str, images: list[Path], footer_images: list[Path] = None, data: dict = None, tags: list[str] = None) -> str:
        """
        완전 자동 발행 (영상 방식)
        
        Args:
            title: 제목
            html_content: HTML 내용
            images: 워터마크된 이미지
            footer_images: 푸터 이미지
            data: 원본 입력 데이터 (DOM 빌더용)
            tags: SEO 태그 리스트 (LLM 생성)
        """
        if footer_images is None:
            footer_images = []
        
        if data is None:
            data = {}
            
        if tags is None:
            tags = []
        
        all_images = list(images) + list(footer_images)
        
        # 브라우저 설정
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        # 사용자 프로필 유지 (쿠키/세션 영구 저장)
        profile_dir = Path(settings.chrome_profile_path)
        options.add_argument(f"user-data-dir={profile_dir}")
        
        self.driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(self.driver, 20)
        
        try:
            # JSON 쿠키를 항상 로드 (blog.naver.com 도메인 쿠키 보장)
            # 먼저 naver.com 접속
            self.driver.get("https://naver.com")
            time.sleep(2)
            
            # JSON 쿠키 로드 (크롬 프로필과 상관없이 항상 시도)
            if self._load_cookies_json():
                logger.info("✅ JSON cookies loaded")
                self.driver.refresh()
                time.sleep(2)
            
            # 로그인 확인
            if "nid.naver.com" not in self.driver.current_url:
                logger.info("✅ Logged in successfully")
            else:
                logger.warning("⚠️ Login check failed, will retry at write page")
            
            # 글쓰기 페이지
            write_url = f"{self.blog_url}?Redirect=Write&categoryNo={self.category_no}"
            logger.info(f"📍 Opening: {write_url}")
            self.driver.get(write_url)
            time.sleep(3)
            
            # 로그인 체크 (실패 시 수동 로그인 대기)
            if "nid.naver.com" in self.driver.current_url:
                logger.warning("⚠️ Login required! Switching to manual login mode...")
                logger.info("👉 로그인 창이 떴습니다. 직접 로그인을 완료해주세요.")
                
                # 로그인 대기 루프 (5분)
                max_wait = 300
                waited = 0
                while waited < max_wait:
                    if "nid.naver.com" not in self.driver.current_url:
                        logger.info("✅ Login detected! Continuing...")
                        
                        # ⭐ 중요: 로그인 성공 후 즉시 쿠키 저장!
                        self._save_cookies_json()
                        logger.info("💾 Cookies saved for next time")
                        
                        break
                    
                    if waited % 10 == 0:
                        logger.info(f"⏳ Waiting for login... ({waited}s)")
                    
                    time.sleep(1)
                    waited += 1
                
                if waited >= max_wait:
                    raise Exception("Login timeout")
                
                # 다시 글쓰기 페이지로 이동 (혹시 메인으로 갔을 수도 있으니)
                self.driver.get(write_url)
                time.sleep(2)
            
            # iframe 전환 (핵심!)
            logger.info("⏳ Waiting for mainFrame iframe...")
            # 타임아웃을 60초로 증가
            wait_iframe = WebDriverWait(self.driver, 60)
            wait_iframe.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "mainFrame")))
            logger.info("✅ mainFrame switched")
            
            # 팝업 제거
            try:
                cancel_btn = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".se-popup-button-cancel"))
                )
                cancel_btn.click()
                logger.info("✅ Popup closed")
                time.sleep(0.5)
            except:
                logger.info("No popup")
            
            # 제목 입력 (Actions API 사용)
            logger.info(f"📝 Title: {title}")
            
            try:
                from selenium.webdriver.common.action_chains import ActionChains
                from selenium.webdriver.common.keys import Keys
                
                # 제목 span 요소 찾기
                title_span = self.driver.find_element(By.CSS_SELECTOR, ".se-component.se-documentTitle span.__se-node")
                
                # Actions로 클릭 및 타이핑
                actions = ActionChains(self.driver)
                
                # 클릭해서 포커스
                actions.click(title_span).perform()
                time.sleep(0.5)
                
                # 기존 내용 전체 선택
                cmd_or_ctrl = Keys.COMMAND if __import__('platform').system() == "Darwin" else Keys.CONTROL
                actions.key_down(cmd_or_ctrl).send_keys('a').key_up(cmd_or_ctrl).perform()
                time.sleep(0.2)
                
                # 제목 타이핑
                actions.send_keys(title).perform()
                time.sleep(0.5)
                
                # 확인
                typed_text = title_span.text
                logger.info(f"  ✅ Title typed: {typed_text}")
                
                # 본문 영역으로 이동 (Enter 키 사용 - 가장 확실)
                logger.info("  → Moving to content area with Enter key...")
                actions.send_keys(Keys.RETURN).perform()
                time.sleep(0.5)
                
                # JavaScript로 확실하게 본문 영역에 포커스
                try:
                    focus_script = """
                    // 본문 편집 영역 찾기
                    var contentArea = document.querySelector('div[contenteditable="true"]');
                    if (contentArea) {
                        // 포커스
                        contentArea.focus();
                        
                        // 커서를 맨 끝으로
                        var range = document.createRange();
                        var sel = window.getSelection();
                        range.selectNodeContents(contentArea);
                        range.collapse(false);
                        sel.removeAllRanges();
                        sel.addRange(range);
                        
                        return true;
                    }
                    return false;
                    """
                    focus_result = self.driver.execute_script(focus_script)
                    if focus_result:
                        logger.info("  ✅ Content area focused (JavaScript)")
                    else:
                        logger.warning("  ⚠️ Content area focus failed")
                    time.sleep(0.3)
                except Exception as e:
                    logger.warning(f"  ⚠️ Focus script failed: {e}")
                
            except Exception as e:
                logger.error(f"  ❌ Title setting failed: {e}")
                raise
            
            # 본문 내용 작성 (Center 포맷터 사용 - 정렬 지원!)
            logger.info("📝 Writing content with Center formatter...")
            try:
                from naver_dom_builder_v2 import build_naver_dom_v2
                from naver_formatter_center import NaverFormatterCenter
                
                # DOM 빌더로 요소 리스트 생성
                if isinstance(data, list):
                    # 이미 구조화된 데이터(REFERENCE_TEXT)인 경우
                    elements = data
                else:
                    # HTML에서 변환해야 하는 경우
                    elements = build_naver_dom_v2(html_content, data)
                
                # Center 포맷터 생성 (정렬 지원!)
                formatter = NaverFormatterCenter(self.driver)
                
                # 요소 순서대로 입력 (element-by-element with formatting)
                logger.info(f"  📝 Inserting {len(elements)} elements with formatting...")
                
                for i, elem in enumerate(elements):
                    elem_type = elem.get('type')
                    logger.info(f"    [{i+1}/{len(elements)}] {elem_type}")
                    
                    try:
                        if elem_type == 'text':
                            formatter.type_text(
                                text=elem.get('content', ''),
                                align=elem.get('align', 'left'),
                                bold=elem.get('bold', False)
                            )
                        
                        elif elem_type == 'sticker':
                            formatter.insert_sticker(elem.get('sticker_id', 45))
                        
                        elif elem_type == 'divider':
                            formatter.insert_divider()
                        
                        elif elem_type == 'list':
                            formatter.type_list(
                                elem.get('items', []),
                                align=elem.get('align', 'left')
                            )
                        
                        elif elem_type == 'link':
                            formatter.insert_link(
                                url=elem.get('url', ''),
                                text=elem.get('text', '')
                            )
                        
                        elif elem_type == 'image_placeholder':
                            # 이미지는 나중에 별도 업로드
                            pass
                        
                        elif elem_type == 'image_group':
                            # 이미지 그룹 - 버퍼 flush 후 즉시 업로드
                            logger.info(f"      → Image group: {elem.get('count', 0)} images")
                            
                            # 버퍼 flush
                            if hasattr(formatter, 'finalize'):
                                formatter.finalize()
                            
                            # 해당 그룹의 이미지들 업로드
                            indices = elem.get('indices', [])
                            group_images = [all_images[idx] for idx in indices if idx < len(all_images)]
                            
                            if group_images:
                                logger.info(f"      → Uploading {len(group_images)} images as group...")
                                # as_group=True로 전달 (여러 이미지를 한 번에 업로드)
                                self._upload_images_selenium(group_images, as_group=True)
                                logger.info(f"      ✅ Image group uploaded")
                    
                    except Exception as e:
                        logger.warning(f"      ⚠️ Failed: {e}")
                
                logger.info(f"  ✅ Content processing complete ({len(elements)} elements)")
                
                # Finalize - 남은 버퍼 내용을 실제로 붙여넣기 (Simple formatter만 해당)
                if hasattr(formatter, 'finalize'):
                    logger.info("  📤 Finalizing remaining content (flushing buffer)...")
                    formatter.finalize()
                    logger.info("  ✅ Content flushed to editor")
                    
            except Exception as e:
                logger.warning(f"  ⚠️ Content writing failed: {e} - continuing anyway")
                import traceback
                traceback.print_exc()
            
            # 이미지 업로드 (image_group이 없을 때만)
            has_image_group = any(elem.get('type') == 'image_group' for elem in elements)
            
            if has_image_group:
                logger.info(f"📷 Images already uploaded via image_group")
            else:
                logger.info(f"📷 Uploading {len(all_images)} images (Selenium method)...")
                self._upload_images_selenium(all_images)
            
            # 제목 재확인 및 재설정 (이미지 업로드 후 사라질 수 있음)
            logger.info("📝 Re-checking title...")
            try:
                title_check = self.driver.execute_script("""
                    const titleSpan = document.querySelector('.se-component.se-documentTitle span.__se-node');
                    return titleSpan ? titleSpan.textContent : '';
                """)
                
                if not title_check or title_check.strip() == '':
                    logger.warning("  ⚠️ Title disappeared! Re-typing...")
                    
                    from selenium.webdriver.common.action_chains import ActionChains
                    
                    # Actions로 다시 타이핑
                    title_span = self.driver.find_element(By.CSS_SELECTOR, ".se-component.se-documentTitle span.__se-node")
                    
                    actions = ActionChains(self.driver)
                    actions.click(title_span).perform()
                    time.sleep(0.5)
                    
                    # 전체 선택
                    cmd_or_ctrl = Keys.COMMAND if __import__('platform').system() == "Darwin" else Keys.CONTROL
                    actions.key_down(cmd_or_ctrl).send_keys('a').key_up(cmd_or_ctrl).perform()
                    time.sleep(0.2)
                    
                    # 타이핑
                    actions.send_keys(title).perform()
                    time.sleep(0.5)
                    
                    logger.info(f"  ✅ Title re-typed: {title}")
                else:
                    logger.info(f"  ✅ Title still present: {title_check}")
            except Exception as e:
                logger.warning(f"  ⚠️ Title check failed: {e}")
            
            # === 발행 프로세스 (자가 복구 포함) ===
            max_publish_step_retries = 2
            last_publish_error = None

            for pub_step_attempt in range(max_publish_step_retries + 1):
                try:
                    if pub_step_attempt > 0:
                        logger.info(f"🔄 발행 단계 재시도 {pub_step_attempt}/{max_publish_step_retries}...")
                        # 에러 팝업 정리
                        self._dismiss_error_popup()
                        time.sleep(2)
                        # 페이지 새로고침 대신 에디터로 복귀 시도
                        self.driver.switch_to.default_content()
                        try:
                            self.driver.switch_to.frame("mainFrame")
                        except:
                            pass

                    logger.info(f"📤 Publishing (2-step){f' [retry {pub_step_attempt}]' if pub_step_attempt > 0 else ''}...")

                    # 발행 전 에러 팝업 정리
                    self.driver.switch_to.default_content()
                    try:
                        self.driver.switch_to.frame("mainFrame")
                    except:
                        pass
                    popup_cleared = self._dismiss_error_popup()
                    if popup_cleared:
                        logger.info("  🧹 Pre-publish: cleared lingering error popup")
                        time.sleep(1)

                    # Step 1: 우측 상단 "발행" 버튼 클릭 → 모달 열기
                    logger.info("  Step 1: Opening publish modal...")

                    publish_btn = self._find_publish_button()

                    if publish_btn:
                        self.driver.execute_script("arguments[0].click();", publish_btn)
                        logger.info("  ✅ Clicked publish button (JS)")
                        time.sleep(3)
                    else:
                        logger.error("  ❌ Publish button not found anywhere!")
                        self.driver.save_screenshot("publish_btn_not_found.png")
                        raise Exception("PUBLISH_BTN_NOT_FOUND: 발행 버튼을 찾을 수 없습니다")

                    # Step 2: 모달 대기 후 태그 입력 + 발행 버튼 클릭
                    logger.info("  Step 2: Waiting for publish modal...")
                    time.sleep(3)

                    # 모달이 열렸는지 확인 (tag-input 존재 여부)
                    modal_opened = False
                    try:
                        self.driver.find_element(By.ID, "tag-input")
                        modal_opened = True
                    except:
                        # 에러 팝업이 모달을 가리고 있을 수 있음
                        if self._dismiss_error_popup():
                            logger.warning("  🧹 Error popup was blocking publish modal - dismissed")
                            time.sleep(2)
                            # 발행 버튼 다시 클릭
                            publish_btn = self._find_publish_button()
                            if publish_btn:
                                self.driver.execute_script("arguments[0].click();", publish_btn)
                                time.sleep(3)
                                try:
                                    self.driver.find_element(By.ID, "tag-input")
                                    modal_opened = True
                                except:
                                    pass

                    if not modal_opened:
                        raise Exception("MODAL_BLOCKED: 발행 모달이 열리지 않습니다 (에러 팝업 또는 네이버 오류)")

                    # 태그 입력 (첫 시도에만)
                    if pub_step_attempt == 0:
                        self._input_seo_tags(tags, data)

                    logger.info("  Step 2-2: Clicking modal publish button...")

                    modal_click_success = self.driver.execute_script("""
                        const allButtons = Array.from(document.querySelectorAll('button'));
                        const publishButtons = allButtons.filter(btn => btn.textContent.includes('발행'));
                        if (publishButtons.length > 0) {
                            const modalBtn = publishButtons[publishButtons.length - 1];
                            modalBtn.click();
                            return {success: true, text: modalBtn.textContent.trim(), total: publishButtons.length};
                        }
                        return {success: false, total: publishButtons.length};
                    """)

                    if modal_click_success and modal_click_success.get('success'):
                        logger.info(f"  ✅ Clicked modal publish button: '{modal_click_success.get('text')}' ({modal_click_success.get('total')} publish buttons found)")
                    else:
                        raise Exception("MODAL_BTN_NOT_FOUND: 모달 내 발행 버튼을 찾을 수 없습니다")

                    # 발행 완료 대기 - URL 변경 확인
                    logger.info("  ⏳ Waiting for publish to complete...")
                    max_wait = 60
                    waited = 0

                    while waited < max_wait:
                        time.sleep(1)
                        waited += 1
                        current_url = self.driver.current_url

                        if 'Redirect=Write' not in current_url:
                            logger.info(f"  ✅ Published! Redirected to: {current_url}")
                            time.sleep(1)

                            self._save_cookies_json()
                            return current_url

                        # 대기 중 에러 팝업 감지
                        if waited % 10 == 0:
                            if self._dismiss_error_popup():
                                logger.warning(f"  🧹 Error popup appeared during publish wait - dismissed (will retry)")
                                raise Exception("POPUP_DURING_PUBLISH: 발행 중 에러 팝업 발생 - 네이버 파일 전송 오류")

                        if waited % 5 == 0:
                            logger.info(f"    Still waiting... ({waited}/{max_wait}s)")

                    # 타임아웃
                    # 팝업 확인
                    if self._dismiss_error_popup():
                        raise Exception("PUBLISH_TIMEOUT_POPUP: 발행 타임아웃 - 에러 팝업이 발행을 차단함")
                    else:
                        raise Exception(f"PUBLISH_TIMEOUT: 발행 타임아웃 - {max_wait}초 대기 후에도 페이지 전환 없음")

                except Exception as step_error:
                    last_publish_error = step_error
                    error_code = str(step_error).split(':')[0] if ':' in str(step_error) else 'UNKNOWN'
                    logger.error(f"  ❌ Publish step failed [{error_code}]: {step_error}")

                    # 재시도 가능한 에러인지 판단
                    retryable_codes = ['POPUP_DURING_PUBLISH', 'PUBLISH_TIMEOUT_POPUP', 'MODAL_BLOCKED', 'PUBLISH_TIMEOUT']
                    if error_code in retryable_codes and pub_step_attempt < max_publish_step_retries:
                        logger.info(f"  🔄 Retryable error - will retry publish step...")
                        continue
                    else:
                        raise

            # 모든 발행 단계 재시도 실패
            if last_publish_error:
                raise last_publish_error
            
        except Exception as e:
            logger.error(f"❌ Failed: {e}")
            
            # 스크린샷
            screenshot_path = Path(settings.output_dir) / "error_selenium.png"
            screenshot_path.parent.mkdir(parents=True, exist_ok=True)
            self.driver.save_screenshot(str(screenshot_path))
            logger.info(f"Screenshot: {screenshot_path}")
            
            raise
            
        finally:
            if self.driver:
                self.driver.quit()
    
    def _find_publish_button(self):
        """발행 버튼 탐색 (여러 전략)"""
        publish_btn = None

        # [시도 1] iframe 밖에서 CSS Selector
        self.driver.switch_to.default_content()
        time.sleep(0.5)
        try:
            publish_btn = self.driver.find_element(By.CSS_SELECTOR, "button.publish_btn__m9KHH, button[data-click-area='tpb.publish']")
            logger.info("  → Found publish button by selector (outside iframe)")
            return publish_btn
        except:
            pass

        # [시도 2] iframe 밖에서 텍스트 검색
        try:
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                if btn.is_displayed() and "발행" in btn.text and "예약" not in btn.text:
                    logger.info("  → Found publish button by text (outside iframe)")
                    return btn
        except:
            pass

        # [시도 3] iframe 안에서 검색
        try:
            self.driver.switch_to.frame("mainFrame")
            publish_btn = self.driver.find_element(By.CSS_SELECTOR, "button.publish_btn__m9KHH, button[data-click-area='tpb.publish']")
            logger.info("  → Found publish button by selector (inside iframe)")
            return publish_btn
        except:
            self.driver.switch_to.default_content()

        # [시도 4] JS 탐색
        self.driver.switch_to.default_content()
        publish_btn = self.driver.execute_script("""
            var btns = document.querySelectorAll('button');
            for (var i = 0; i < btns.length; i++) {
                if (btns[i].textContent.includes('발행') && !btns[i].textContent.includes('예약')) {
                    return btns[i];
                }
            }
            return null;
        """)
        if publish_btn:
            logger.info("  → Found publish button by JS")
        return publish_btn

    def _input_seo_tags(self, tags, data):
        """SEO 태그 입력"""
        logger.info("  Step 2-1: Inputting SEO tags...")
        try:
            if not tags:
                from seo_generator import generate_seo_tags
                tags = generate_seo_tags(data)

            final_tags = tags[:30]
            logger.info(f"    Tags ({len(final_tags)}개): {', '.join(final_tags[:5])}...")

            tag_input = self.driver.find_element(By.ID, "tag-input")
            if tag_input:
                tag_input.click()
                time.sleep(0.5)

                for i, tag in enumerate(final_tags):
                    tag_input.send_keys(tag)
                    time.sleep(0.1)
                    tag_input.send_keys(Keys.RETURN)
                    time.sleep(0.1)
                    if (i + 1) % 10 == 0:
                        logger.info(f"      Progress: {i+1}/{len(final_tags)} tags")

                logger.info(f"    ✅ Tags entered: {len(final_tags)}개")
                time.sleep(5)
            else:
                logger.warning("    ⚠️ Tag input field (#tag-input) not found")
        except Exception as e:
            logger.warning(f"    ⚠️ Tag input failed: {e}")

    def _save_cookies_json(self):
        """Save cookies to JSON file (more robust than pickle)"""
        try:
            cookies = self.driver.get_cookies()
            cookie_path = Path(settings.cookie_json_path)
            import json
            with open(cookie_path, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, indent=2)
            logger.info(f"💾 Saved {len(cookies)} cookies to JSON")
        except Exception as e:
            logger.error(f"Failed to save cookies: {e}")

    def _load_cookies_json(self):
        """Load cookies from JSON file (naver-cafe 스킬 방식)"""
        cookie_path = Path(settings.cookie_json_path)
        if not cookie_path.exists():
            logger.info("  ℹ️ No saved cookies found")
            return False
            
        try:
            import json
            with open(cookie_path, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            
            # 도메인 설정 (쿠키 추가 전 필수)
            self.driver.get("https://naver.com")
            time.sleep(1)
            
            # naver-cafe처럼 필수 필드만 필터링
            clean_cookies = []
            for c in cookies:
                if 'name' in c and 'value' in c and 'domain' in c and 'path' in c:
                    # 필수 필드만 추출
                    c_clean = {
                        k: v for k, v in c.items() 
                        if k in ['name', 'value', 'domain', 'path', 'expires', 'expiry', 'httpOnly', 'secure', 'sameSite']
                    }
                    
                    # expiry 타입 변환
                    if 'expiry' in c_clean:
                        try:
                            c_clean['expiry'] = int(c_clean['expiry'])
                        except:
                            del c_clean['expiry']
                    
                    clean_cookies.append(c_clean)
            
            # 쿠키 추가
            added = 0
            for cookie in clean_cookies:
                try:
                    self.driver.add_cookie(cookie)
                    added += 1
                except Exception as e:
                    logger.debug(f"    Skip cookie '{cookie.get('name')}': {e}")
                    pass
            
            logger.info(f"✅ Loaded {added}/{len(cookies)} cookies from JSON")
            return added > 0
            
        except Exception as e:
            logger.error(f"Failed to load cookies: {e}")
            return False

    def login_with_clipboard(self):
        """수동 로그인 (영구 프로필 + JSON 쿠키)"""
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        # 사용자 프로필 유지
        profile_dir = Path(settings.chrome_profile_path)
        profile_dir.mkdir(parents=True, exist_ok=True)
        options.add_argument(f"user-data-dir={profile_dir}")
        
        self.driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(self.driver, 10)
        
        try:
            # 쿠키 로드 시도
            if self._load_cookies_json():
                self.driver.refresh()
                time.sleep(2)
            
            logger.info("🔐 Navigating to login...")
            self.driver.get("https://nid.naver.com/nidlogin.login")
            
            # 이미 로그인 되어있는지 확인
            if "nid.naver.com" not in self.driver.current_url:
                logger.info("✅ Already logged in (profile/cookie reused)")
                self._save_cookies_json() # 갱신
                return
            
            logger.info("🛑 Automatic input disabled. Please login MANUALLY.")
            logger.info("👉 직접 아이디/비번을 입력하고 로그인해주세요.")
            
            # 로그인 확인 루프
            max_wait = 300
            waited = 0
            while waited < max_wait:
                if "nid.naver.com" not in self.driver.current_url:
                    logger.info("✅ Login successful!")
                    break
                
                if waited % 5 == 0:
                    logger.info(f"⏳ Waiting for manual login... ({waited}s)")
                
                time.sleep(1)
                waited += 1
            
            if waited >= max_wait:
                logger.error("❌ Login timeout")
                return

            # 중요: 로그인 완료 후 메인 페이지로 이동하여 전체 쿠키 획득
            logger.info("🔐 Navigating to naver.com to capture all cookies...")
            self.driver.get("https://www.naver.com")
            time.sleep(3)
            
            # 쿠키 저장
            self._save_cookies_json()
            
        finally:
            if self.driver:
                self.driver.quit()
    
    def _dismiss_error_popup(self):
        """네이버 에디터 에러 팝업 감지 및 닫기"""
        try:
            # "확인" 버튼이 있는 에러 팝업 찾기
            confirm_btns = self.driver.find_elements(By.XPATH,
                "//*[contains(@class, 'popup') or contains(@class, 'modal') or contains(@class, 'layer')]"
                "//button[contains(text(), '확인')]"
            )
            for btn in confirm_btns:
                if btn.is_displayed():
                    btn.click()
                    logger.info("  🔄 Dismissed error popup (확인 button)")
                    time.sleep(1)
                    return True

            # JS로도 시도
            dismissed = self.driver.execute_script("""
                var btns = document.querySelectorAll('button');
                for (var i = 0; i < btns.length; i++) {
                    var btn = btns[i];
                    if (btn.offsetParent !== null && btn.textContent.trim() === '확인') {
                        var parent = btn.closest('.layer_popup, .popup, .modal, [class*="layer"], [class*="popup"]');
                        if (parent) { btn.click(); return true; }
                    }
                }
                return false;
            """)
            if dismissed:
                logger.info("  🔄 Dismissed error popup (JS)")
                time.sleep(1)
                return True
        except:
            pass
        return False

    def _find_file_input(self):
        """파일 input 요소 탐색 (여러 전략)"""
        # 전략 1: 직접 탐색
        try:
            inputs = self.driver.find_elements(By.XPATH, "//input[@type='file']")
            if inputs:
                return inputs[0]
        except:
            pass

        # 전략 2: 사진 버튼 클릭 후 탐색
        try:
            selectors = [
                ".se-image-toolbar-button",
                "button.se-image-toolbar-button",
                "[data-name='image']",
                "button[data-name='image']",
            ]
            for sel in selectors:
                btns = self.driver.find_elements(By.CSS_SELECTOR, sel)
                if btns and btns[0].is_displayed():
                    self.driver.execute_script("arguments[0].click();", btns[0])
                    time.sleep(1.5)
                    inputs = self.driver.find_elements(By.XPATH, "//input[@type='file']")
                    if inputs:
                        return inputs[0]
        except:
            pass

        # 전략 3: JS로 file input 생성 시도
        try:
            file_input = self.driver.execute_script("""
                var existing = document.querySelector('input[type="file"]');
                if (existing) return existing;
                // 이미지 버튼을 JS로 찾아 클릭
                var toolbar = document.querySelector('.se-toolbar');
                if (toolbar) {
                    var imgBtn = toolbar.querySelector('[data-name="image"], .se-image-toolbar-button');
                    if (imgBtn) { imgBtn.click(); }
                }
                return null;
            """)
            if file_input:
                return file_input
            time.sleep(1.5)
            inputs = self.driver.find_elements(By.XPATH, "//input[@type='file']")
            if inputs:
                return inputs[0]
        except:
            pass

        return None

    def _upload_images_selenium(self, images: list[Path], as_group: bool = False):
        """
        이미지 업로드 (에러 팝업 감지 + 재시도 로직 포함)
        """
        if not images:
            return

        abs_paths = [str(img.absolute()) for img in images]
        max_retries = 3

        for attempt in range(max_retries):
            try:
                # 에러 팝업이 떠있으면 먼저 닫기
                self._dismiss_error_popup()

                # 파일 input 탐색
                file_input = self._find_file_input()

                if file_input:
                    logger.info(f"  📤 Sending {len(images)} images...{f' (retry {attempt+1})' if attempt > 0 else ''}")
                    file_input.send_keys("\n".join(abs_paths))

                    # 업로드 대기
                    wait_time = 5 + len(images) * 1.5
                    time.sleep(wait_time)

                    # 에러 팝업 체크 (업로드 직후)
                    if self._dismiss_error_popup():
                        logger.warning(f"  ⚠️ Upload error detected after send (attempt {attempt+1}/{max_retries})")
                        time.sleep(3)
                        continue  # 재시도

                    # 콜라주(그룹) 처리
                    if as_group and len(images) > 1:
                        self._handle_collage_popup()

                    # 커서를 맨 끝으로 이동
                    time.sleep(1)
                    self.driver.execute_script("""
                        var editor = document.querySelector('div[contenteditable="true"]');
                        if (editor) {
                            var p = document.createElement('p');
                            p.innerHTML = '<br>';
                            editor.appendChild(p);
                            var range = document.createRange();
                            range.selectNodeContents(p);
                            range.collapse(false);
                            var sel = window.getSelection();
                            sel.removeAllRanges();
                            sel.addRange(range);
                            p.scrollIntoView();
                        }
                    """)
                    time.sleep(0.5)

                    logger.info(f"  ✅ Upload complete & Cursor moved to end")
                    return  # 성공
                else:
                    logger.warning(f"  ⚠️ File input not found (attempt {attempt+1}/{max_retries})")
                    if attempt < max_retries - 1:
                        time.sleep(3)
                        continue

            except Exception as e:
                logger.warning(f"  ⚠️ Upload attempt {attempt+1} failed: {e}")
                if attempt < max_retries - 1:
                    self._dismiss_error_popup()
                    time.sleep(3)
                    continue

        # 모든 재시도 실패
        logger.error(f"  ❌ Image upload failed after {max_retries} attempts - skipping")
        self._dismiss_error_popup()  # 마지막으로 팝업 정리

    def _handle_collage_popup(self):
        """콜라주(이미지 그룹) 버튼 클릭 처리"""
        logger.info("  👀 Checking for 'Collage' options...")
        time.sleep(1)
        
        try:
            # '콜라주' 텍스트가 포함된 버튼/라벨 찾기
            # 1. 팝업/툴바에서 찾기
            collage_btns = self.driver.find_elements(By.XPATH, "//*[contains(text(), '콜라주')]")
            
            clicked = False
            for btn in collage_btns:
                if btn.is_displayed():
                    # 상위 요소가 버튼일 수 있음
                    parent = btn.find_element(By.XPATH, "./..")
                    try:
                        btn.click()
                        logger.info("    👉 Clicked 'Collage' button (direct)!")
                        clicked = True
                        break
                    except:
                        try:
                            parent.click()
                            logger.info("    👉 Clicked 'Collage' button (parent)!")
                            clicked = True
                            break
                        except:
                            pass
            
            if not clicked:
                logger.info("  ⚠️ 'Collage' button not found directly. Trying to reveal toolbar...")
                # 이미지가 선택되지 않아서 툴바가 안 떴을 수 있음 -> 첫 번째 이미지 클릭
                try:
                    imgs = self.driver.find_elements(By.CSS_SELECTOR, ".se-component-content img")
                    if imgs:
                        imgs[0].click()
                        time.sleep(1)
                        
                        # 다시 찾기
                        collage_btns = self.driver.find_elements(By.XPATH, "//*[contains(text(), '콜라주')]")
                        for btn in collage_btns:
                            if btn.is_displayed():
                                btn.click()
                                logger.info("    👉 Clicked 'Collage' button after selecting image!")
                                clicked = True
                                break
                except:
                    pass
            
            if clicked:
                time.sleep(2) # 적용 대기
            else:
                logger.warning("  ⚠️ Failed to click 'Collage' (button not found)")
                
        except Exception as e:
            logger.warning(f"  ⚠️ Error handling collage: {e}")

    
    def _insert_content_elements_v2(self, elements: list[dict]):
        """
        DOM 빌더 v2 요소들을 네이버 에디터에 정교하게 삽입
        
        가운데 정렬, 볼드, 구분선, 리스트 등 정확히 구현
        """
        logger.info("  📝 Inserting content elements...")
        
        for i, elem in enumerate(elements):
            elem_type = elem.get('type')
            logger.info(f"    [{i+1}/{len(elements)}] {elem_type}")
            
            try:
                if elem_type == 'text':
                    self._insert_text(elem)
                    
                elif elem_type == 'sticker':
                    self._insert_sticker(elem)
                    
                elif elem_type == 'divider':
                    self._insert_divider()
                    
                elif elem_type == 'list':
                    self._insert_list(elem)
                    
                elif elem_type == 'link':
                    self._insert_link(elem)
                    
                elif elem_type == 'image_placeholder':
                    # 이미지는 나중에 일괄 업로드
                    pass
                    
            except Exception as e:
                logger.warning(f"      ⚠️ Failed to insert element {i+1}: {e}")
                import traceback
                traceback.print_exc()
        
        logger.info("  ✅ All elements inserted")
    
    def _insert_sticker(self, elem: dict):
        """네이버 스티커 삽입"""
        sticker_id = elem.get('sticker_id', 45)
        align = elem.get('align', 'center')
        
        # 스티커 삽입 방법: 스티커 버튼 클릭 → 스티커 선택
        # 간단한 방법: JavaScript로 이미지 블록 생성
        
        # 네이버 스티커 URL 패턴 (추정)
        # 실제 URL은 테스트 후 조정 필요
        sticker_url = f"https://ssl.pstatic.net/static/pwe/address/sticker_{sticker_id:03d}.png"
        
        js_code = """
        (function(stickerUrl, align) {
            const container = document.querySelector('.se-main-container');
            if (!container) return false;
            
            // 스티커 블록 생성
            const stickerBlock = document.createElement('div');
            stickerBlock.className = 'se-component se-image se-l-default';
            if (align === 'center') {
                stickerBlock.style.textAlign = 'center';
            }
            
            const img = document.createElement('img');
            img.src = stickerUrl;
            img.style.maxWidth = '200px';
            img.style.height = 'auto';
            
            stickerBlock.appendChild(img);
            container.appendChild(stickerBlock);
            
            return true;
        })(arguments[0], arguments[1]);
        """
        
        result = self.driver.execute_script(js_code, sticker_url, align)
        if result:
            logger.info(f"      ✅ Sticker {sticker_id} inserted")
        else:
            logger.warning(f"      ⚠️ Sticker insert failed")
            # Fallback: 텍스트 이모지
            fallback_emoji = '🐶' if sticker_id == 45 else '🐶❤️'
            self._insert_text({
                'content': fallback_emoji,
                'align': align,
                'size': 'xlarge',
                'bold': False
            })
    
    def _insert_text(self, elem: dict):
        """텍스트 삽입 (정렬, 볼드, 크기)"""
        content = elem.get('content', '')
        align = elem.get('align', 'left')
        bold = elem.get('bold', False)
        size = elem.get('size', 'normal')
        
        # JavaScript로 텍스트 + 스타일 삽입 (arguments 사용)
        js_code = """
        (function(contentText, align, size, bold) {
            // 본문 영역
            const container = document.querySelector('.se-main-container');
            if (!container) return false;
            
            // 새 텍스트 블록 생성
            const textBlock = document.createElement('div');
            textBlock.className = 'se-component se-text se-l-default';
            
            // 내용
            const p = document.createElement('p');
            p.className = '__se-node';
            
            // 정렬
            if (align === 'center') {
                p.style.textAlign = 'center';
            } else if (align === 'right') {
                p.style.textAlign = 'right';
            }
            
            // 크기
            let fontSize = '16px';
            if (size === 'xlarge') {
                fontSize = '80px';  // 큰 이모지
            } else if (size === 'large') {
                fontSize = '60px';
            } else if (size === 'small') {
                fontSize = '14px';
            }
            p.style.fontSize = fontSize;
            
            // 볼드
            if (bold) {
                p.style.fontWeight = 'bold';
            }
            
            // 텍스트 (줄바꿈 처리)
            const lines = contentText.split('\\n');
            lines.forEach((line, idx) => {
                if (idx > 0) p.appendChild(document.createElement('br'));
                p.appendChild(document.createTextNode(line));
            });
            
            textBlock.appendChild(p);
            container.appendChild(textBlock);
            
            return true;
        })(arguments[0], arguments[1], arguments[2], arguments[3]);
        """
        
        result = self.driver.execute_script(js_code, content, align, size, bold)
        if result:
            logger.info(f"      ✅ Text inserted: {content[:50]}")
        else:
            logger.warning(f"      ⚠️ Text insert failed")
    
    def _insert_divider(self):
        """구분선 삽입"""
        js_code = """
        (function() {
            const container = document.querySelector('.se-main-container');
            if (!container) return false;
            
            // 구분선 블록
            const divider = document.createElement('div');
            divider.className = 'se-component se-divider';
            
            const hr = document.createElement('hr');
            hr.className = '__se-node';
            hr.style.border = '0';
            hr.style.borderTop = '1px solid #ddd';
            hr.style.margin = '30px 0';
            
            divider.appendChild(hr);
            container.appendChild(divider);
            
            return true;
        })();
        """
        
        result = self.driver.execute_script(js_code)
        if result:
            logger.info(f"      ✅ Divider inserted")
    
    def _insert_list(self, elem: dict):
        """리스트 삽입 (불렛)"""
        items = elem.get('items', [])
        bullet = elem.get('bullet', '•')
        
        js_code = f"""
        (function() {{
            const container = document.querySelector('.se-main-container');
            if (!container) return false;
            
            // 리스트 블록
            const listBlock = document.createElement('div');
            listBlock.className = 'se-component se-text se-l-default';
            
            const ul = document.createElement('ul');
            ul.style.listStyle = 'none';
            ul.style.padding = '0';
            
            const items = {str(items).replace("'", '"')};
            
            items.forEach(item => {{
                const li = document.createElement('li');
                li.style.marginBottom = '8px';
                li.textContent = '{bullet} ' + item;
                ul.appendChild(li);
            }});
            
            listBlock.appendChild(ul);
            container.appendChild(listBlock);
            
            return true;
        }})();
        """
        
        result = self.driver.execute_script(js_code)
        if result:
            logger.info(f"      ✅ List inserted ({len(items)} items)")
    
    def _insert_link(self, elem: dict):
        """링크 삽입"""
        text = elem.get('text', '')
        url = elem.get('url', '')
        align = elem.get('align', 'left')
        color = elem.get('color', 'blue')
        
        js_code = f"""
        (function() {{
            const container = document.querySelector('.se-main-container');
            if (!container) return false;
            
            // 링크 블록
            const linkBlock = document.createElement('div');
            linkBlock.className = 'se-component se-text se-l-default';
            
            const p = document.createElement('p');
            if ('{align}' === 'center') {{
                p.style.textAlign = 'center';
            }}
            
            const a = document.createElement('a');
            a.href = '{url}';
            a.textContent = '{text}';
            a.style.color = '{color}';
            a.style.textDecoration = 'none';
            a.target = '_blank';
            
            p.appendChild(a);
            linkBlock.appendChild(p);
            container.appendChild(linkBlock);
            
            return true;
        }})();
        """
        
        result = self.driver.execute_script(js_code)
        if result:
            logger.info(f"      ✅ Link inserted: {text}")
    
    def _insert_content_elements(self, elements: list[dict]):
        """
        DOM 빌더 요소들을 네이버 에디터에 삽입
        
        간단한 방식: Enter로 줄바꿈하면서 텍스트 입력
        나중에 정교하게 개선 예정
        """
        from selenium.webdriver.common.action_chains import ActionChains
        actions = ActionChains(self.driver)
        
        # 본문 영역 클릭
        try:
            content_area = self.driver.find_element(By.CLASS_NAME, "se-main-container")
            content_area.click()
            time.sleep(0.5)
        except:
            logger.warning("  ⚠️ Content area not found")
            return
        
        for elem in elements:
            elem_type = elem.get('type')
            
            if elem_type == 'emoji':
                # 큰 이모지 (가운데 정렬)
                char = elem.get('char', '🐶')
                size = elem.get('size', 80)
                
                # 가운데 정렬 버튼 클릭 (툴바에서)
                # TODO: 정렬 기능 구현
                
                # 이모지 타이핑
                actions.send_keys(char).perform()
                time.sleep(0.2)
                actions.send_keys(Keys.RETURN).perform()
                time.sleep(0.2)
                
            elif elem_type == 'text':
                # 텍스트 (정렬, 볼드, 크기)
                content = elem.get('content', '')
                align = elem.get('align', 'left')
                bold = elem.get('bold', False)
                size = elem.get('size', 'normal')
                
                # TODO: 정렬, 볼드, 크기 적용
                
                # 텍스트 타이핑 (pyperclip 사용 - 한글 안전)
                import pyperclip
                pyperclip.copy(content)
                
                cmd_or_ctrl = Keys.COMMAND if __import__('platform').system() == "Darwin" else Keys.CONTROL
                actions.key_down(cmd_or_ctrl).send_keys('v').key_up(cmd_or_ctrl).perform()
                time.sleep(0.3)
                actions.send_keys(Keys.RETURN).perform()
                time.sleep(0.2)
                
            elif elem_type == 'divider':
                # 구분선
                # TODO: 구분선 삽입 기능 구현
                # 일단 줄바꿈으로 대체
                actions.send_keys(Keys.RETURN).perform()
                time.sleep(0.1)
                
            elif elem_type == 'list':
                # 리스트 (불렛 포인트)
                items = elem.get('items', [])
                
                for item in items:
                    # TODO: 불렛 포인트 적용
                    # 일단 "· " 접두사
                    pyperclip.copy(f"· {item}")
                    
                    cmd_or_ctrl = Keys.COMMAND if __import__('platform').system() == "Darwin" else Keys.CONTROL
                    actions.key_down(cmd_or_ctrl).send_keys('v').key_up(cmd_or_ctrl).perform()
                    time.sleep(0.2)
                    actions.send_keys(Keys.RETURN).perform()
                    time.sleep(0.1)
                
                # 리스트 끝에 빈 줄
                actions.send_keys(Keys.RETURN).perform()
                time.sleep(0.2)
                
            elif elem_type == 'image_placeholder':
                # 이미지 플레이스홀더 (실제 이미지는 나중에 업로드)
                # 일단 스킵
                pass


if __name__ == "__main__":
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    if len(sys.argv) > 1 and sys.argv[1] == "login":
        print("🔐 Selenium Login (Clipboard Method)")
        print("=" * 60)
        publisher = NaverBlogPublisherSelenium()
        publisher.login_with_clipboard()
    else:
        print("Usage:")
        print("  python naver_publisher_selenium.py login")
        print("\nOr use test_selenium.py for full test")
